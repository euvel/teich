"""Drill the whole v0.5 path on a throwaway cloud seat (never the real one), with stand-in hearings (no Ears):
  1. genesis back-dated DAYS days, then ONE wake lives all of it (timed: a wake must fit its 15-minute lease)
  2. the founder's three-commit conversation: its question is delivered with the reason it logged last night — which
     that wake already flushed to the cloud log (amendment 1's path: read through log-read's `rec`)
  3. a door word and an answer; a second wake across the next night
  4. live verify over the whole cloud log + outbox; diary pages and the public log file
    python3 drill_v05.py v05-drill OUT_DIR [DAYS]
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "build"))
import creature_v05 as C5               # noqa: E402
import diary_md_v05 as DM               # noqa: E402
import seat_v05 as S                    # noqa: E402
import self_text_v05 as TX              # noqa: E402
from cloud_v04 import CloudSeatV04      # noqa: E402
from f1_v05 import check_log            # noqa: E402

name, out = sys.argv[1], Path(sys.argv[2]); days = float(sys.argv[3]) if len(sys.argv) > 3 else 2.3
assert name != "teich-05", "the drill never touches the real seat"
seat = CloudSeatV04(name); res = {"seat": name}
assert not seat.peek().get("alive"), f"{name} already holds a drill creature — use a fresh drill name"
t0 = float(int(time.time() - days * 86400))
c = C5.birth(seed=20261023, t0=t0, identity="drill"); blob = C5.dump_state(c)
seat.genesis_import(blob, 0, "drill"); res["genesis_bytes"] = len(blob)

t = time.time(); res["wake1"] = S.wake(seat, max_ticks=250_000, log=print); res["wake1_seconds"] = round(time.time() - t)
st = seat.s.state(); res["after_wake1"] = {"n_ticks": st["n_ticks"], "blob_bytes": len(st["state_blob"]), "log_seq": seat.log_seq()}

q, inputs, grown, prop = S.ask(seat)                       # its reason was flushed by wake 1: comes from log-read
res["question"] = q and {"q": q["q"], "shown": TX.question(q["q"], inputs)}
props = [{"cluster": 38, "sign": 1, "text_sha256": "ab" * 32, "cn": 5, "cf": 5},
         {"cluster": 70, "sign": -1, "text_sha256": "cd" * 32, "cn": 2, "cf": 5}]
items = S.present(seat, props, "drill-1", "stand-in", ["duduk"])
ans = {"act_id": q["act_id"], "answered": True, "landed": None} if q else None
res["decide"] = S.decide(seat, "drill-1", {items[1]["pid"]} if items[1]["shown"] else set(), "founder", ans)

t = time.time(); res["wake2"] = S.wake(seat, now=time.time() + 86400, max_ticks=250_000, log=print)
res["wake2_seconds"] = round(time.time() - t)
st = seat.s.state(); logged = [r["rec"] for r in seat.log_read()]
c, recs = DM.stream(st["state_blob"], logged)
res["round_trip_over_the_wire"] = C5.dump_state(C5.load_state(st["state_blob"])) == st["state_blob"]
res["log_rows"] = len(logged); res["records"] = len(recs)
res["log_seq_contiguous"] = [r["seq"] for r in recs] == list(range(1, len(recs) + 1))
res["live_verify"] = check_log(recs)
res["diary_pages"] = DM.write(st["state_blob"], out, logged, out / "records.jsonl")
res["final"] = {"n_ticks": st["n_ticks"], "blob_bytes": len(st["state_blob"]), "version": c.growth["version"],
                "snapshots": seat.peek()["snapshots"]}
bad = sum(res["live_verify"][k] for k in ("completeness", "receipt", "consequence", "necessity"))
res["passed"] = (res["wake1"] == res["wake2"] == "woke" and res["question"] is not None and res["round_trip_over_the_wire"]
                 and res["log_seq_contiguous"] and bad == 0 and len(res["diary_pages"]) >= 2)
json.dump(res, open(out / "drill.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
