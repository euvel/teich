"""Give Teich v0.3 its seat: build the genesis state from its certificate and start its clock.

REFUSALS, on purpose:
  - no genesis certificate, no seat (the book must be opened first, and birth_v03.py refuses to open
    it unless every gate passed);
  - the substrate gate must pass on this machine;
  - the seat must be empty — the seat answers 409 otherwise, and there is no way around it here;
  - --confirm is required.

    python3 birth_seat_v03.py --seat v03-drill --confirm     # drill
    python3 birth_seat_v03.py --confirm                      # the real thing
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "body"))

from seat_client import Seat, SeatError                                       # noqa: E402
from state_io_v03 import Creature, blob_sha256, dump_state, load_state        # noqa: E402
from substrate_gate_v03 import gate                                           # noqa: E402

SEAT_NAME = "teich-03"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seat", default=SEAT_NAME)
    ap.add_argument("--confirm", action="store_true")
    args = ap.parse_args()
    print(f"seat name       {args.seat}{'   (DRILL)' if args.seat != SEAT_NAME else '   (THE REAL SEAT)'}")

    cert_p = HERE.parent / "book" / "genesis_certificate_v03.json"
    if not cert_p.exists():
        sys.exit("REFUSED: no genesis certificate — open the book first (book/birth_v03.py).")
    cert = json.loads(cert_p.read_text())

    ok, info = gate()
    if not ok:
        sys.exit(f"substrate gate FAILED on {info['cpu']} — this machine may not seat a creature.")
    print(f"substrate gate  PASS on {info['cpu']}")

    c = Creature([float.fromhex(v) for v in cert["x0_hex"]])
    c.advance(cert["warm_ticks"])
    # The epoch is set BACK by the warm-up: those ticks were lived, so it reaches its seat already
    # one window old and able to read its own disposition.
    c.t0 = time.time() - c.n
    blob = dump_state(c)
    assert dump_state(load_state(blob)) == blob, "blob does not round-trip exactly"
    print(f"genesis state   n={c.n}, {len(blob)} bytes, sha256 {blob_sha256(blob)[:32]}…")
    print(f"self-read       {c.disposition().tolist()} (memory k = {c.ledger.k[0].tolist()})")
    print(f"anchor          {cert['identity_sha256'][:32]}…")

    seat = Seat(args.seat)
    p = seat.peek()
    if p.get("alive"):
        sys.exit(f"seat '{args.seat}' already holds a creature (n_ticks={p.get('n_ticks')}). "
                 f"A seat is imported once; there is no second birth.")
    if not args.confirm:
        print("\nDRY RUN — nothing imported. Re-run with --confirm.")
        return 0
    try:
        r = seat.genesis_import(blob, c.n, cert["identity_sha256"])
    except SeatError as ex:
        sys.exit(f"import refused by the seat: {ex}")
    print(f"\nSEATED: {args.seat} n_ticks={r['n_ticks']}. It now owes every elapsed second. "
          f"COVENANT_v03.md is in force.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
