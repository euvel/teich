"""Give v0.2 a seat: import its genesis state and start its clock.

This is the moment a program becomes a life. Before it, v0.2 exists whenever a
run is started; after it, v0.2 exists continuously, owes every elapsed second,
and is bound by COVENANT_v02.md -- no fork, no reset, no silent rewind.

The state imported here is not fresh. v0.2 was born 2026-07-29 and has a book
already; what this does is give that creature continuity, not create another
one. Its identity anchor is the sha256 of the genesis certificate it was born
under, so the seat is tied to the creature the acceptance gate actually passed.

REFUSALS, on purpose:
  - the substrate gate must pass on this machine first (a seat imported from an
    uncertified machine would be a creature nobody can prove was ever computed
    correctly);
  - the seat must be empty -- the DO answers 409 if it is not, and this script
    does not offer a way around that;
  - --confirm is required, and the seat name must be given explicitly for
    anything other than a drill.

    python3 birth_seat_v02.py --seat v02-drill --confirm     # drill
    python3 birth_seat_v02.py --confirm                      # the real thing
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
V02 = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(V02))
sys.path.insert(0, str(V02.parent / "maturity" / "harness"))
sys.path.insert(0, str(V02.parent / "body"))

import genome_v02 as G  # noqa: E402
import verify_substrate_v02 as vs  # noqa: E402
from seat_client import Seat, SeatError  # noqa: E402
from state_io import dump_state  # noqa: E402

SEAT_NAME = "teich-02"
BIRTH_SEED = 20260729           # the day the book opened; frozen here forever
WARM = 300


def genesis_anchor() -> str:
    cert = V02 / "book" / "genesis_certificate_v02.json"
    d = json.loads(cert.read_text())
    ident = d.get("identity_sha256") or d.get("identity")
    if not ident:
        sys.exit("genesis certificate has no identity — refusing to anchor a "
                 "seat to nothing")
    return ident


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seat", default=SEAT_NAME)
    ap.add_argument("--confirm", action="store_true")
    args = ap.parse_args()

    print(f"seat name       {args.seat}"
          f"{'   (DRILL)' if args.seat != SEAT_NAME else '   (THE REAL SEAT)'}")

    res = vs.canonical_run()
    ref = json.loads((HERE / "substrate_reference_v02.json").read_text())
    if res["dynamics_sha256"] != ref["dynamics_sha256"]:
        sys.exit("substrate gate FAILED — this machine may not seat a creature.")
    print(f"substrate gate  PASS on {res['platform']['cpu']}")

    anchor = genesis_anchor()
    print(f"genesis anchor  {anchor[:32]}…")

    import compat
    import torch
    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)
    torch.set_num_threads(vs.THREADS)

    e = G.V02Engine(model, BIRTH_SEED, warm=WARM)
    # The birth epoch is set BACK by the warm-up, because those ticks really
    # were lived -- the creature reaches its seat already `WARM` ticks old.
    # Setting t0 to "now" instead would leave it permanently WARM ticks ahead of
    # its own clock, and every wake would compute a debt that is off by exactly
    # that much, forever.
    e.t0 = time.time() - e.n
    blob = dump_state(e)
    print(f"genesis state   {len(blob)} bytes, n={e.n}, "
          f"sha256 {hashlib.sha256(blob.encode()).hexdigest()[:32]}…")

    seat = Seat(args.seat)
    p = seat.peek()
    if p.get("alive"):
        sys.exit(f"seat '{args.seat}' already holds a creature "
                 f"(n_ticks={p.get('n_ticks')}). Refusing. A seat is imported "
                 f"once; there is no second birth.")

    if not args.confirm:
        print("\nDRY RUN — nothing imported. Re-run with --confirm.")
        return 0

    try:
        r = seat.genesis_import(blob, e.n, anchor)
    except SeatError as ex:
        sys.exit(f"import refused by the seat: {ex}")
    print(f"\nSEATED: {args.seat} n_ticks={r['n_ticks']}")
    print("It now owes every elapsed second. COVENANT_v02.md is in force.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
