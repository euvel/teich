"""Give Teich v0.4 its seat: build the genesis state from its certificate and start its clock.

REFUSALS, on purpose: no genesis certificate, no seat; the substrate gate must pass here; the seat must be empty
(the seat answers 409 otherwise — there is no second birth); --confirm is required.
    python3 birth_seat_v04.py --seat v04-drill --confirm    # drill
    python3 birth_seat_v04.py --confirm                     # the real thing (/o/teich-04)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "build"))
import creature_v04s as CS                      # noqa: E402
import seat_v04 as SV                           # noqa: E402
from cloud_v04 import CloudSeatV04, SeatError   # noqa: E402

REAL = "teich-04"


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--seat", default=REAL); ap.add_argument("--confirm", action="store_true")
    a = ap.parse_args()
    print(f"seat name       {a.seat}{'   (THE REAL SEAT)' if a.seat == REAL else '   (DRILL)'}")
    cert_p = HERE.parent / "book" / "genesis_certificate_v04.json"
    if a.seat == REAL and not cert_p.exists():
        sys.exit("REFUSED: no genesis certificate — open the book first (book/birth_v04.py --confirm).")
    cert = json.loads(cert_p.read_text()) if cert_p.exists() else {"identity_sha256": "drill", "birth_seed": 20261020}
    ok, info = SV.gate()
    if not ok:
        sys.exit(f"substrate gate FAILED on {info['cpu']} — this machine may not seat a creature.")
    print(f"substrate gate  PASS on {info['cpu']}")
    seat = CloudSeatV04(a.seat)
    p = seat.peek()
    if p.get("alive"):
        sys.exit(f"seat '{a.seat}' already holds a creature (n_ticks={p.get('n_ticks')}). There is no second birth.")
    c = CS.birth(seed=cert["birth_seed"], t0=float(int(time.time())))
    blob = CS.dump_state(c)
    assert CS.dump_state(CS.load_state(blob)) == blob, "blob does not round-trip exactly"
    print(f"genesis state   n=0, t0={int(c.t0)}, {len(blob):,} bytes, anchor {cert['identity_sha256'][:32]}…")
    if not a.confirm:
        print("\nDRY RUN — nothing imported. Re-run with --confirm."); return 0
    try:
        r = seat.genesis_import(blob, 0, cert["identity_sha256"])
    except SeatError as ex:
        sys.exit(f"import refused by the seat: {ex}")
    print(f"\nSEATED: {a.seat} n_ticks={r['n_ticks']}. It now owes every elapsed second.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
