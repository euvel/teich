"""Wake Teich v0.7 at its seat: the dream gate, then (seat_v07p.wake) the body gate, lease, the Sky's beacons for every
touch it crosses (fetched, BLS-verified, none crossed before its round is out), live what is owed (at most
--max-ticks), commit, append the journal in canonical form; then any new diary pages and, with --log, its whole public
record log. Its seal is signed by the seat itself (the worker), not by the wake.
    python3 wake_v07.py [--seat teich-05] [--max-ticks 172800] [--diary-dir ../diary] [--log ../diary/records.jsonl]
"""
import argparse
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "build"))
import creature_v07 as C7                        # noqa: E402
import diary_md_v07 as DM                        # noqa: E402
import dream_gate_v06 as DG                      # noqa: E402
import seat_v07p as S                            # noqa: E402
from cloud_v07 import CloudSeatV07               # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument("--seat", default="teich-05")
ap.add_argument("--max-ticks", type=int, default=86_400); ap.add_argument("--diary-dir", default=None)
ap.add_argument("--log", default=None)
a = ap.parse_args()
seat = CloudSeatV07(a.seat)
blob = seat.s.state()["state_blob"]
try:
    c0 = C7.load_state(blob)
except ValueError as e:                          # never wake a creature this code was not built for
    print("declined:", e); sys.exit(0)
# Never hold the lease over the seal moment: GitHub's cron lands near the creature's midnight. A wake that would
# start in [seal moment - 10 min, midnight + 60 s) waits until midnight + 60 s (then tonight's round is out).
_day = S.GN.DAY
_into = (time.time() - float(c0.t0)) % _day
if _day - S.C7.SKY_LEAD - 600 <= _into or _into < 60:
    _wait = (_day - _into + 60) if _into >= 60 else (60 - _into)
    print(f"near the seal moment: waiting {_wait:.0f} s, until 60 s after the creature's midnight")
    time.sleep(_wait)
ok, info = DG.gate()
print(f"dream gate: {'PASS' if ok else 'FAIL'}", info)
if not ok:
    print("declined: this machine does not dream the fixture bit for bit; elapsed time stays banked.")
    sys.exit(0)
t = time.time()
try:
    r = S.wake(seat, max_ticks=a.max_ticks)
except C7.SkyMissing as e:                       # no fallback: nothing lived, nothing journaled; time stays banked
    print("declined by the Sky:", e); sys.exit(0)
print(r, f"({time.time() - t:.0f} s)")
if a.diary_dir and r == "woke":
    logged = [x["rec"] for x in seat.log_read()]
    print("diary pages written:", DM.write(seat.s.state()["state_blob"], Path(a.diary_dir), logged,
                                           Path(a.log) if a.log else None))
