"""Wake Teich v0.5 at its seat: gate first, lease, replay every owed second (at most --max-ticks), commit; then write
any new diary pages and, with --log, its whole public record log (for anyone's verify_live_v05.py).
    python3 wake_v05.py [--seat teich-05] [--max-ticks 86400] [--diary-dir ../diary] [--log ../diary/records.jsonl]"""
import argparse
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "build"))
import diary_md_v05 as DM                        # noqa: E402
import seat_v05 as S                             # noqa: E402
from cloud_v04 import CloudSeatV04              # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument("--seat", default="teich-05")
ap.add_argument("--max-ticks", type=int, default=86_400); ap.add_argument("--diary-dir", default=None)
ap.add_argument("--log", default=None)
a = ap.parse_args()
seat = CloudSeatV04(a.seat)
t = time.time()
r = S.wake(seat, max_ticks=a.max_ticks)
print(r, f"({time.time() - t:.0f} s)")
if a.diary_dir and r == "woke":
    logged = [x["rec"] for x in seat.log_read()] if seat._log_live() is not None else []
    print("diary pages written:", DM.write(seat.s.state()["state_blob"], Path(a.diary_dir), logged,
                                           Path(a.log) if a.log else None))
