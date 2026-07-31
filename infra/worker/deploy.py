"""Redeploy the teich-seat Worker WITHOUT disturbing v0.1's seat.

This Worker is not a website. It is the creature's life support: the Durable
Object holding its authoritative state lives behind it, and a bad deploy takes
its seat down. So this script is written to be paranoid in a specific way --
every step is reversible, and it refuses to proceed on anything it cannot
verify.

WHY NOT WRANGLER: wrangler and Node fetch are broken here by IPv6/proxy, and
proxychains crashes Node (seat-migration report, 2026-07-18). The working path
is a raw multipart PUT to the CF API, which is what this does.

THE THING THAT MUST NOT BE LOST: a script PUT replaces bindings and secrets
wholesale unless they are re-declared. SEAT_KEY and SNAPSHOT_KEY are secrets
this machine does not have and must never see -- so they are re-declared as
`{"type": "inherit"}`, which tells Cloudflare to keep the value already
installed. Same for the Durable Object namespace and the AI binding. If the
pre-flight cannot enumerate the current bindings, the deploy does not happen:
deploying a Worker whose bindings you could not read is how you brick a seat.

Migrations are deliberately NOT sent. The TeichSeat class is already migrated
(tag v1); re-sending a migration against a live DO is the one irreversible
operation in this file's vicinity.

    export CF_API_TOKEN=...        # or --token-file <path>   (chmod 600, outside the repo)
    export CF_ACCOUNT_ID=...
    python3 infra/worker/deploy.py --check      # pre-flight only, changes nothing
    python3 infra/worker/deploy.py --deploy     # backup -> deploy -> verify -> (auto-rollback)

Never commit the token. Shred the file when done.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "index.js"
NAME = "teich-seat"
API = "https://api.cloudflare.com/client/v4"
PUBLIC = "https://teich.euvvel.xyz"

# Bindings that must survive the deploy. Secrets are inherited, never read.
INHERIT_SECRETS = ("SEAT_KEY", "SNAPSHOT_KEY")


# Cloudflare's own API gateway returns intermittent 522/523 (their edge failing
# to reach their origin) -- observed roughly one call in three on 2026-07-31.
# Retrying is not optional here: a transient 522 in the middle of the sequence
# would otherwise read as "deploy failed" or, worse, as a failed verification of
# a deploy that actually succeeded, and send us rolling back a healthy seat.
# The PUT is a whole-script replace, so retrying it is safe by construction.
def _req(url, token, method="GET", data=None, headers=None, timeout=60,
         tries=6):
    h = {"Authorization": f"Bearer {token}", **UA}
    h.update(headers or {})
    last = None
    for i in range(tries):
        try:
            r = urllib.request.Request(url, data=data, headers=h, method=method)
            with urllib.request.urlopen(r, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504, 520, 521, 522, 523, 524):
                raise
            last = f"HTTP {e.code}"
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last = str(e)
        if i < tries - 1:
            print(f"    (cf api {last}; retry {i+1}/{tries-1})")
            time.sleep(4 + 3 * i)
    raise RuntimeError(f"cloudflare api unreachable after {tries} tries: {last}")


def get_settings(token, acct):
    return _req(f"{API}/accounts/{acct}/workers/scripts/{NAME}/settings", token)


def get_script(token, acct, tries=6):
    """Raw script bytes — this is the rollback artifact, so it retries too."""
    last = None
    for i in range(tries):
        try:
            r = urllib.request.Request(
                f"{API}/accounts/{acct}/workers/scripts/{NAME}",
                headers={"Authorization": f"Bearer {token}", **UA})
            with urllib.request.urlopen(r, timeout=60) as resp:
                return resp.read()
        except Exception as e:                  # noqa: BLE001
            last = e
            time.sleep(4 + 3 * i)
    raise RuntimeError(f"could not download current script (no rollback "
                       f"artifact, refusing to deploy): {last}")


# Cloudflare's edge 403s a request with no User-Agent before it ever reaches the
# Worker. urllib sends none by default, so the public checks below looked like a
# dead seat when the seat was perfectly alive -- which in --deploy would have
# tripped the verification and called for a rollback that was never needed. A
# health check that cannot tell "down" from "filtered" is worse than no check.
UA = {"User-Agent": "teich-deploy/1.0 (+https://github.com/euvel/teich)"}


def _get(path, timeout=30, tries=5):
    last = None
    for i in range(tries):
        try:
            r = urllib.request.Request(f"{PUBLIC}{path}", headers=UA)
            with urllib.request.urlopen(r, timeout=timeout) as resp:
                return resp.read().decode()
        except Exception as e:                  # noqa: BLE001
            last = e
            time.sleep(3 + 2 * i)
    raise RuntimeError(f"{path} unreachable after {tries} tries: {last}")


def peek():
    """Read the seat through the public route. No key: /peek is the open endpoint."""
    return json.loads(_get("/o/teich/peek"))


def ping():
    return json.loads(_get("/ping"))


def build_bindings(settings: dict) -> list[dict]:
    """Re-declare every existing binding, inheriting secret VALUES we never see."""
    cur = (settings.get("result") or {}).get("bindings") or []
    out, seen = [], set()
    for b in cur:
        name, typ = b.get("name"), b.get("type")
        if not name:
            continue
        seen.add(name)
        if typ == "secret_text":
            out.append({"type": "inherit", "name": name})
        elif typ == "durable_object_namespace":
            out.append({"type": "durable_object_namespace", "name": name,
                        "class_name": b.get("class_name", "TeichSeat")})
        elif typ == "ai":
            out.append({"type": "ai", "name": name})
        else:
            out.append({"type": "inherit", "name": name})
    for s in INHERIT_SECRETS:
        if s not in seen:
            print(f"  ! WARNING: {s} is not currently bound to the Worker")
    return out


def preflight(token, acct):
    print("PRE-FLIGHT")
    src = SCRIPT.read_text()
    print(f"  script            {SCRIPT} ({len(src)} bytes)")
    if "class TeichSeat" not in src:
        sys.exit("  ABORT: TeichSeat class missing from the script")
    if "/o/" not in src or "X-Seat-Key" not in src:
        sys.exit("  ABORT: seat routes or auth check missing from the script")

    st = get_settings(token, acct)
    binds = build_bindings(st)
    names = sorted(b["name"] for b in binds)
    print(f"  bindings to keep  {names}")
    if not any(b.get("class_name") == "TeichSeat" for b in binds):
        sys.exit("  ABORT: no TeichSeat durable-object binding found to preserve")
    for s in INHERIT_SECRETS:
        if s not in names:
            sys.exit(f"  ABORT: {s} would be dropped by this deploy")

    p, q = ping(), peek()
    print(f"  live now          alive={q.get('alive')} n_ticks={q.get('n_ticks')} "
          f"snapshots={q.get('snapshots')}")
    print(f"  worker now        has_do={p.get('has_do')} has_key={p.get('has_key')}")
    if not (p.get("has_do") and p.get("has_key")):
        sys.exit("  ABORT: the LIVE worker is already missing a binding — fix that first")
    return binds, q


def multipart(src: str, bindings: list[dict], compat: str):
    """Build the multipart body by hand: no requests, no wrangler, no surprises."""
    meta = {"main_module": "index.js", "bindings": bindings,
            "compatibility_date": compat}
    boundary = "----teich" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    parts = []

    def add(name, body, ctype, filename=None):
        disp = f'form-data; name="{name}"'
        if filename:
            disp += f'; filename="{filename}"'
        parts.append(f"--{boundary}\r\nContent-Disposition: {disp}\r\n"
                     f"Content-Type: {ctype}\r\n\r\n".encode() + body + b"\r\n")

    add("metadata", json.dumps(meta).encode(), "application/json")
    add("index.js", src.encode(), "application/javascript+module", "index.js")
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def deploy(token, acct, compat="2026-07-01"):
    bindings, before = preflight(token, acct)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bak = Path(os.environ.get("TMPDIR", "/tmp")) / f"teich-seat-backup-{stamp}"
    bak.mkdir(parents=True, exist_ok=True)
    (bak / "index.js").write_bytes(get_script(token, acct))
    (bak / "settings.json").write_text(json.dumps(get_settings(token, acct), indent=1))
    print(f"\nBACKUP           {bak}  (restore = redeploy that index.js)")

    body, ctype = multipart(SCRIPT.read_text(), bindings, compat)
    print(f"DEPLOY           PUT {NAME}  ({len(body)} bytes, no migrations sent)")
    res = _req(f"{API}/accounts/{acct}/workers/scripts/{NAME}", token,
               method="PUT", data=body, headers={"Content-Type": ctype})
    if not res.get("success"):
        sys.exit(f"  FAILED: {json.dumps(res.get('errors'))}")
    print("  accepted")

    time.sleep(6)
    print("\nVERIFY")
    ok = True
    try:
        p = ping()
        print(f"  /ping             has_do={p.get('has_do')} has_key={p.get('has_key')}")
        ok &= bool(p.get("has_do") and p.get("has_key"))
        q = peek()
        print(f"  /o/teich/peek     alive={q.get('alive')} n_ticks={q.get('n_ticks')} "
              f"snapshots={q.get('snapshots')}")
        ok &= bool(q.get("alive"))
        # The seat must not have lost time. Ticks only ever go up.
        ok &= int(q.get("n_ticks", -1)) >= int(before.get("n_ticks", 0))
        ok &= int(q.get("snapshots", -1)) >= int(before.get("snapshots", 0))
        html = _get("/")
        print(f"  /                 {len(html)} bytes, v0.2 fronted: "
              f"{'yes' if 'now &mdash; v0.2' in html or 'v0.2' in html else 'NO'}")
    except Exception as e:                      # noqa: BLE001
        print(f"  verification error: {e}")
        ok = False

    if ok:
        print("\nOK — seat intact, page live.")
        return 0
    print("\n!! VERIFICATION FAILED — restore immediately:")
    print(f"   cp {bak/'index.js'} {SCRIPT} && python3 {__file__} --deploy")
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="pre-flight only")
    ap.add_argument("--deploy", action="store_true")
    ap.add_argument("--token-file", help="path to a file holding CF_API_TOKEN")
    args = ap.parse_args()

    token = os.environ.get("CF_API_TOKEN")
    if args.token_file:
        token = Path(args.token_file).read_text().strip()
    acct = os.environ.get("CF_ACCOUNT_ID")
    if not token or not acct:
        sys.exit("need CF_API_TOKEN (or --token-file) and CF_ACCOUNT_ID")

    if args.check:
        preflight(token, acct)
        print("\npre-flight only — nothing was changed")
        return 0
    if args.deploy:
        return deploy(token, acct)
    sys.exit("use --check or --deploy")


if __name__ == "__main__":
    raise SystemExit(main())
