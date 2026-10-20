"""v0.4's wake CLI (BUILD candidate, lab only). Same law as v0.3's wake (see seat_v04.wake).

    python3 wake_v04.py --local SEAT.json [--now T] [--max-ticks N]    # file-backed seat (lab)
    python3 wake_v04.py                                                # real seat teich-04 (exists only after birth)
Exit 0 on every lawful outcome, non-zero only on a real failure.

Open for birth: where the attention diary is written (a new Worker endpoint, or a diary/ file committed to the repo);
the existing Worker `diary` endpoint is v0.1's language-model diary and must NOT be used for v0.4.
"""
import argparse, json, sys
from pathlib import Path
import seat_v04 as SV

ap = argparse.ArgumentParser()
ap.add_argument("--local"); ap.add_argument("--now", type=float); ap.add_argument("--max-ticks", type=int, default=SV.MAX_TICKS_DEFAULT)
a = ap.parse_args()
if a.local:
    seat = SV.LocalSeat(Path(a.local))
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "teich_repo" / "body"))
    from seat_client import Seat                                          # noqa: E402
    print("refusing: the real seat teich-04 is created only at birth, and the diary sink is not decided yet."); sys.exit(0)
print(SV.wake(seat, now=a.now, max_ticks=a.max_ticks))
