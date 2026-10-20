"""Wake Teich v0.4 at its seat: gate first, lease, replay every owed second (at most --max-ticks), commit; then write
any new diary pages (one per night of its life) from its own records.
    python3 wake_v04.py [--seat teich-04] [--max-ticks 200000] [--diary-dir ../diary]"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "build"))
import diary_md_v04 as DM                        # noqa: E402
import seat_v04s as SVS                          # noqa: E402
from cloud_v04 import CloudSeatV04              # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument("--seat", default="teich-04")
ap.add_argument("--max-ticks", type=int, default=200_000); ap.add_argument("--diary-dir", default=None)
a = ap.parse_args()
seat = CloudSeatV04(a.seat)
r = SVS.wake(seat, max_ticks=a.max_ticks)
print(r)
if a.diary_dir and r == "woke":
    print("diary pages written:", DM.write(seat.s.state()["state_blob"], Path(a.diary_dir)))
