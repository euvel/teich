"""Install one secret on the teich-seat Worker through the CF API (wrangler is broken here: see deploy.py), reading its
value from a chmod-600 file. The value is never printed. Existing secrets and bindings are untouched (this is the
per-secret endpoint, not a script PUT).
    python3 infra/worker/put_secret.py SEAL_KEY ~/.teich_seal_key
Credentials as deploy.py: env CF_API_TOKEN / CF_ACCOUNT_ID, or ~/.teich_cf_token and ~/.teich_cf_account (chmod 600).
"""
from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deploy import API, NAME, _req  # noqa: E402


def cred(env, path):
    if os.environ.get(env):
        return os.environ[env].strip()
    p = Path.home() / path
    return p.read_text().strip() if p.exists() else None


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: put_secret.py NAME VALUE_FILE")
    name, vf = sys.argv[1], Path(sys.argv[2]).expanduser()
    if name not in ("SEAL_KEY",):
        sys.exit(f"{name}: only SEAL_KEY is installed by this tool (the others are inherited, never re-sent)")
    if stat.S_IMODE(vf.stat().st_mode) & 0o077:
        sys.exit(f"{vf} must be chmod 600")
    value = vf.read_text().strip()
    token, acct = cred("CF_API_TOKEN", ".teich_cf_token"), cred("CF_ACCOUNT_ID", ".teich_cf_account")
    if not token or not acct:
        sys.exit("need CF credentials (see deploy.py)")
    body = json.dumps({"name": name, "text": value, "type": "secret_text"}).encode()
    r = _req(f"{API}/accounts/{acct}/workers/scripts/{NAME}/secrets", token, method="PUT", data=body,
             headers={"content-type": "application/json"})
    ok = isinstance(r, dict) and r.get("success")
    print(f"{name}:", "installed" if ok else f"FAILED {json.dumps((r or {}).get('errors'))}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
