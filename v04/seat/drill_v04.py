"""Drill the whole v0.4 path on a throwaway cloud seat (never the real one): genesis, wake, a two-commit conversation
with synthetic proposals (no Ears), wakes across a night boundary is NOT attempted (it would need a day of ticks)."""
import json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "build"))
import creature_v04s as CS, seat_v04s as SVS
from cloud_v04 import CloudSeatV04
name = sys.argv[1]
assert name != "teich-04", "the drill never touches the real seat"
seat = CloudSeatV04(name)
print("peek", seat.peek())
print("wake", SVS.wake(seat, run_gate=True))
props = [{"cluster": 8, "sign": 1, "text_sha256": "aa" * 32, "cn": 5, "cf": 5},
         {"cluster": 40, "sign": -1, "text_sha256": "bb" * 32, "cn": 2, "cf": 5}]
items = SVS.present(seat, props, "drill-1", "drill-organ")
print("present", items)
out = SVS.decide(seat, "drill-1", {items[1]["pid"]}, "founder")
print("decide", out)
st = seat.s.state(); c = CS.load_state(st["state_blob"])
print("state n", c.n, "blob bytes", len(st["state_blob"]), "outbox kinds", [r["kind"] for r in c.outbox])
assert CS.dump_state(c) == st["state_blob"], "blob does not round-trip over the wire"
print("round-trip over the wire: exact | lease_open", st["lease_open"], "| snapshots", seat.peek()["snapshots"])
