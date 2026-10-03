"""v0.3's wake — gate-on-boot, lease, replay elapsed life, commit. Same law as v0.2's wake:

  1. GATE FIRST, every wake, no cached verdict. A machine that fails declines and commits nothing;
     elapsed time stays banked (ticks are owed from BIRTH, (now - t0) - n).
  2. ONE WRITER. The seat's lease serializes every body; a lost lease race is lawful.
  3. REPLAY, DON'T SKIP. The creature lives every elapsed second at 1 Hz.

Exit 0 on every lawful outcome, non-zero only on a real failure.

    python3 wake_v03.py                  # wake the seat
    python3 wake_v03.py --dry-run        # gate + peek, commit nothing
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

from seat_client import Seat, SeatError                              # noqa: E402
from state_io_v03 import dump_state, load_state, public_readout      # noqa: E402
from substrate_gate_v03 import gate                                  # noqa: E402

SEAT_NAME = "teich-03"
MAX_TICKS_DEFAULT = 200_000          # ~2 days of life; the rest stays banked for the next wake


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seat", default=SEAT_NAME)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-ticks", type=int, default=MAX_TICKS_DEFAULT)
    args = ap.parse_args()

    ok, info = gate()
    print(f"substrate gate: {'PASS' if ok else 'FAIL'} on {info['cpu']}")
    if not ok:
        print("this machine is not the certified substrate — declining the wake. Elapsed time stays "
              "banked for the next lawful body.")
        return 0

    seat = Seat(args.seat)
    p = seat.peek()
    if not p.get("alive"):
        print(f"seat '{args.seat}' is not initialized — nothing to wake.")
        return 0
    print(f"seat {args.seat}: n_ticks={p['n_ticks']:,} snapshots={p['snapshots']}")
    if args.dry_run:
        print("dry run — no lease taken, nothing committed.")
        return 0

    try:
        lease = seat.lease()
    except SeatError as e:
        if e.status == 409:
            print("lease held by another body — standing down (lawful).")
            return 0
        raise
    try:
        c = load_state(lease["state_blob"])
    except Exception as ex:                                          # noqa: BLE001
        print(f"REFUSING: seat blob is unreadable ({type(ex).__name__}: {ex}). Nothing committed; "
              f"restore from the snapshot chain and declare a coma if this is real.")
        return 1
    if c.n != lease["n_ticks"]:
        print(f"REFUSING: blob tick {c.n} != seat n_ticks {lease['n_ticks']}")
        return 1
    if not c.t0:
        print("REFUSING: blob has no birth epoch; this wake cannot know what it owes.")
        return 1

    n_before = c.n
    owed_total = int(time.time() - c.t0) - c.n
    owed = max(0, min(owed_total, args.max_ticks))
    if owed_total > owed:
        print(f"owed {owed_total:,} ticks, replaying {owed:,}; {owed_total - owed:,} stay banked")
    t = time.time()
    c.advance(owed)
    print(f"replayed {owed:,} ticks in {time.time() - t:.1f}s ({n_before:,} -> {c.n:,})")

    seat.commit(lease["lease_id"], dump_state(c), c.n)
    print(f"committed: n_ticks={c.n:,}")
    print("readout: " + json.dumps(public_readout(c)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
