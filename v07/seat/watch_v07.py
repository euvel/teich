"""The Seal's watcher (SKY_SPEC_v07_v1 §3.8–3.9): keep each day's seal before its beacon exists, then check that day.
Anyone can run it; it trusts only itself, the drand League of Entropy, and the key the creature's own genome-amendment
record binds (its seal_pub), never the seat or its makers.

    python3 watch_v07.py keep                  # fetch today's seal and the latest drand round; keep it (run daily
                                               # between its seal moment and its midnight: 14:18–14:30 UTC)
    python3 watch_v07.py keep --loop           # stay up and keep every day's seal at its moment + 60 s
    python3 watch_v07.py check DAY [--no-bls]  # day DAY: signature, witnessed, head, quiet, beacon, replay; and fraud
                                               # (PENDING, exit 2, until a wake has lived that day's touch)

Kept seals live in ~/.teich_watch/<seat>/ (one file per day). A seal first seen after its beacon round leaves that
day UNWITNESSED for you: it is kept, but check() says so. If the seat ever serves you two different seals for one day,
or a seal its own published journal contradicts, `check` prints a fraud proof: the two signed seals (or the seal
and the journal), which anyone can verify with seal_v07.fraud.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "build"))
import creature_v07 as C7   # noqa: E402
import genome_v04 as GN     # noqa: E402
import seal_v07 as SL       # noqa: E402
import sky_v07 as SKY       # noqa: E402
from cloud_v07 import BASE_URL, log_public  # noqa: E402

START_URL = "https://raw.githubusercontent.com/euvel/teich/main/v07/book/START_STATE_v07.json"


def get(url, timeout=30):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"user-agent": "teich-watcher"}), timeout=timeout) as f:
        return json.loads(f.read())


def start_blob(path=None):
    """The published starting state of its v0.7 life (the migration's committed blob)."""
    d = json.loads(Path(path).read_text()) if path else get(START_URL)
    return d["state_blob"] if isinstance(d, dict) and "state_blob" in d else json.dumps(d, sort_keys=True)


def bound_pub(blob):
    """The seal key the creature's own genome-amendment record binds."""
    c = C7.load_state(blob)
    am = [r for r in c.outbox if r["kind"] == "genome-amendment" and r["amendment"].get("to_version", "").startswith("0.7")]
    if len(am) != 1 or not am[0]["amendment"].get("seal_pub"):
        raise SystemExit("the start state carries no v0.7 genome-amendment with a seal_pub: nothing to trust")
    return am[0]["amendment"]["seal_pub"]


def keep(seat, base, store: Path, proxy=None):
    served = get(f"{base}/o/{seat}/seals-public")
    latest = int(SKY.fetch("latest", proxy=proxy)["round"])         # what drand had published when we fetched
    store.mkdir(parents=True, exist_ok=True); kept = []
    for s in served["seals"]:
        if s.get("missed"):
            continue
        signed = {"seal": json.loads(s["canon"]), "sig": s["sig"], "pub": s["pub"]}
        p = store / f"day-{signed['seal']['day']:05d}.json"
        if p.exists():
            old = json.loads(p.read_text())["signed"]
            if old != signed:                                        # the seat served two seals for one day
                proof = SL.fraud(old, signed)
                (store / f"FRAUD-day-{signed['seal']['day']:05d}.json").write_text(json.dumps({"a": old, "b": signed, "proof": proof}, indent=1))
                print("FRAUD:", proof)
            continue
        w = SL.watch(signed, latest)
        p.write_text(json.dumps(w, indent=1))
        rd = C7.round_of(signed["seal"]["t0"], signed["seal"]["day"])
        kept.append((signed["seal"]["day"], "witnessed" if latest < rd else "UNWITNESSED (its beacon was already out)"))
    for d, how in kept:
        print(f"kept day {d}: {how}")
    if not kept:
        print("nothing new to keep")


def loop(seat, base, store, proxy=None):
    while True:
        try:
            nxt = get(f"{base}/o/{seat}/seals-public")["next"]
        except Exception as e:                                       # the seat unreachable: try again shortly
            print("seals-public failed:", e, flush=True); time.sleep(60); continue
        at = (nxt.get("at") or nxt.get("at_ms")) / 1000              # seals-public serves "at" (ms); seal-status "at_ms"
        wait = max(30.0, at + 60 - time.time())
        print(f"next seal: day {nxt['day']} at {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(at))}; "
              f"sleeping {wait / 60:.0f} min", flush=True)
        time.sleep(wait)
        try:
            keep(seat, base, store, proxy)
        except Exception as e:                                       # a missed fetch is an unwitnessed day, not a crash
            print("keep failed:", e, flush=True)


def check(seat, base, store, day, verify, start_path=None):
    p = store / f"day-{day:05d}.json"
    if not p.exists():
        raise SystemExit(f"no kept seal for day {day}: that day is unwitnessed for you")
    kept = json.loads(p.read_text())
    blob = start_blob(start_path); pub = bound_pub(blob)
    _, rows = log_public(seat, base)
    records = [json.loads(r["raw"]) for r in rows]
    res = SL.check(kept, blob, records, pub, verify=verify)
    res["fraud_proof"] = SL.fraud(kept["signed"], None, blob, records)
    lived = max((r["n"] + r["owed"] for r in records if r["kind"] == "op"), default=0)
    touch = day * GN.DAY + GN.DAY - C7.SKY_LEAD
    res["pending"] = (not res["clean"] and not res["fraud_proof"] and not res["beacon"] and lived < touch
                      and res["signature"] and res["head"] and res["quiet"])
    print(json.dumps(res, indent=1))
    if res["pending"]:
        print(f"day {day}: PENDING — its seal checks out so far, but its touch (tick {touch:,}) is not lived yet "
              f"(lived to {lived:,}): check again after its next wake")
        return res
    print(f"day {day}:", "CLEAN — nothing that decided that night was chosen after its beacon could be known"
          if res["clean"] else "NOT CLEAN", "| FRAUD PROOF: " + res["fraud_proof"] if res["fraud_proof"] else "")
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["keep", "check"]); ap.add_argument("day", nargs="?", type=int)
    ap.add_argument("--seat", default="teich-05"); ap.add_argument("--base", default=BASE_URL)
    ap.add_argument("--store", default=str(Path.home() / ".teich_watch"))
    ap.add_argument("--loop", action="store_true"); ap.add_argument("--no-bls", action="store_true")
    ap.add_argument("--start", default=None, help="a local copy of START_STATE_v07.json")
    ap.add_argument("--proxy", default=os.environ.get("TEICH_SKY_PROXY"))
    a = ap.parse_args(); store = Path(a.store) / a.seat
    if a.cmd == "keep":
        (loop if a.loop else keep)(a.seat, a.base, store, a.proxy)
    else:
        if a.day is None:
            raise SystemExit("check DAY")
        r = check(a.seat, a.base, store, a.day, not a.no_bls, a.start)
        sys.exit(0 if r["clean"] else 2 if r.get("pending") else 1)
