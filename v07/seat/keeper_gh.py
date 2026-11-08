"""The GitHub keeper: keep each day's seal before its beacon exists, from GitHub Actions (seal_keeper_v07.yml).

GitHub starts scheduled runs late, by hours, and sparsely, so the keeper is a chain of runs, each handing the watch
to the next; the hourly schedule only restarts the chain if it ever breaks. Each run:
  1. keeps every seal the seat serves now and this store does not have yet (red if one was first seen after its
     beacon: that day is unwitnessed);
  2. if the next seal moment is more than --max-wait away: waits (at most --max-wait - 5 min, and no longer than
     until the moment is --max-wait away), then hands over (exit 3: the workflow dispatches a fresh run, which starts
     at once, unlike scheduled ones);
  3. otherwise waits until 30 s after the moment, then keeps, retrying every 15 s, until that day's seal is kept or
     its beacon is about to exist (the creature's midnight, 15 min after the moment); then hands over (exit 3), or
     exits 1 (a red run, which GitHub reports, and the workflow still hands over) if it could not keep it in time.
Without --relay a run never waits longer than step 3 needs and never hands over.
The kept seals are committed under v07/witness/<seat>/ by the workflow. What witnesses them is GitHub's run log:
each kept seal is printed with the time it was kept and the latest drand round at that time. This is the makers'
own keeper; anyone can, and should, keep their own (watch_v07.py keep --loop).

    python3 keeper_gh.py [--store ../witness] [--max-wait 18900] [--relay]
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import watch_v07 as W

ap = argparse.ArgumentParser()
ap.add_argument("--seat", default="teich-05"); ap.add_argument("--base", default=W.BASE_URL)
ap.add_argument("--store", default=str(Path(__file__).resolve().parent.parent / "witness"))
ap.add_argument("--max-wait", type=float, default=18_900.0)   # 5 h 15 min: a run stays well inside 355 min
ap.add_argument("--proxy", default=os.environ.get("TEICH_SKY_PROXY"))
ap.add_argument("--relay", action="store_true", help="run as one link of the chain: wait, keep, then exit 3 to hand over")
a = ap.parse_args()
store = Path(a.store) / a.seat
utc = lambda t: time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(t))   # noqa: E731


def keep():
    try:
        W.keep(a.seat, a.base, store, a.proxy)
    except Exception as e:                                       # a failed fetch: try again
        print(f"{utc(time.time())} keep failed: {e}", flush=True)


def kept(day):
    return (store / f"day-{day:05d}.json").exists()


def late_ones(before):
    """Seals this run kept that were first seen after their beacon: those days are unwitnessed."""
    late = []
    for f in sorted(store.glob("day-*.json")):
        if f.name not in before:
            w = json.loads(f.read_text()); s = w["signed"]["seal"]
            if w["latest_round_seen"] >= W.C7.round_of(s["t0"], s["day"]):
                late.append(s["day"])
    return late


def hand_over(why):
    print(f"{utc(time.time())} handing over: {why}", flush=True)
    raise SystemExit(3 if a.relay else 0)


print(f"{utc(time.time())} keeper starts", flush=True)
had = {f.name for f in store.glob("day-*.json")}
keep()
late = late_ones(had)
if late:                                                       # no earlier run kept them in time: say so in red
    raise SystemExit(f"UNWITNESSED: day(s) {late} were first kept after their beacon")
nxt = None
for _ in range(10):
    try:
        nxt = W.get(f"{a.base}/o/{a.seat}/seals-public")["next"]; break
    except Exception as e:
        print(f"{utc(time.time())} seals-public failed: {e}", flush=True); time.sleep(60)
if not nxt:
    hand_over("the seat did not answer for 10 minutes")
day, at = nxt["day"], (nxt.get("at") or nxt.get("at_ms")) / 1000
midnight = at + W.C7.SKY_LEAD                                  # its beacon round exists from here on
print(f"next seal: day {day} at {utc(at)}; its beacon from {utc(midnight)}", flush=True)
gap = at - time.time()
if kept(day) or gap > a.max_wait:
    if not a.relay:
        print(f"more than {a.max_wait / 3600:.1f} h away (or kept): a later run keeps it"); raise SystemExit(0)
    nap = max(60.0, min(gap - a.max_wait + 120, a.max_wait - 300)) if not kept(day) else max(60.0, midnight - time.time())
    time.sleep(nap)
    hand_over(f"a fresh run takes the watch for day {day}")

time.sleep(max(0.0, at + 30 - time.time()))
while not kept(day) and time.time() < midnight - 20:
    keep()
    if not kept(day):
        time.sleep(15)
if not kept(day):
    raise SystemExit(f"{utc(time.time())} day {day}: NOT KEPT before its beacon (the seat had not served it)")
w = json.loads((store / f"day-{day:05d}.json").read_text())
rd = W.C7.round_of(w["signed"]["seal"]["t0"], day)
how = "WITNESSED" if w["latest_round_seen"] < rd else "UNWITNESSED (its beacon was already out)"
print(f"{utc(time.time())} KEPT day {day}: {how}; latest drand round seen {w['latest_round_seen']}, "
      f"its own round {rd}", flush=True)
print(json.dumps(w, indent=1))
if how != "WITNESSED":
    raise SystemExit(1)
hand_over(f"day {day} kept; the chain goes on to day {day + 1}")
