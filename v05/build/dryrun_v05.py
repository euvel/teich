"""End-to-end dry run of the founder's real tools with the real Ears v7 (Kaggle; design seed 9990, local lab seat).
Exactly the calls talk_v05.py and grow_v05.py make, scripted over 4 days of life:
  day 0  "My friend plays the duduk." twice           -> 'duduk' waits at its door
  day 1  it asks about 'duduk' (with its true reason); the founder answers -> a candidate binding
  day 2  it asks again; the same answer on another day -> bound
  day 3  its growth proposal is shown (status, delivers nothing) and approved -> v0.5.1; then "I love the duduk."
Asserts the whole path and runs live verify on the seat's record stream.
    python3 dryrun_v05.py OUT.json [SEED]
"""
import json
import sys
from pathlib import Path

import creature_v05 as C5
import ears_v07 as EM
import genome_v04 as GN
import seat_v04 as SV
import seat_v05 as S
import self_text_v05 as TX
import talk_v05 as T5
from f1_v05 import check_log

T0 = 1_000_000.0
seat = SV.LocalSeat(Path(sys.argv[1]).with_suffix(".seat.json"))
if seat.path.exists():
    seat.path.unlink()
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 9990          # 9990 = design seed; amendment 1 re-look: 9991
seat.genesis_import(C5.dump_state(C5.birth(seed=SEED, t0=T0, identity="dry-run")), 0, "dry-run")
ears = EM.EarsV7()
log = []


def talk(text, day, k, answering=True):
    now = T0 + day * GN.DAY + 20_000 + k * 3_000
    q, inputs, grown, prop = S.ask(seat, now=now)
    ears.cluster_of.update(grown)
    shown_q = TX.question(q["q"], inputs) if q else None
    props, door, landed = T5.build(ears, text, q if (q and answering) else None)
    items = S.present(seat, [{x: v for x, v in p.items() if x != "words"} for p in props], f"d{day}-{k}", "ears-v7", door,
                      now=now + 1)
    ans = {"act_id": q["act_id"], "answered": answering, "landed": landed} if q else None
    S.decide(seat, f"d{day}-{k}", set(), "founder", ans, now=now + 2)
    rec = {"day": day, "said": text, "question": shown_q, "heard": [[p["words"], p["cluster"]] for p in props],
           "door": door, "landed": landed}
    log.append(rec); print(json.dumps(rec, ensure_ascii=False), flush=True)
    return rec


talk("My friend plays the duduk.", 0, 0)
talk("The duduk sounded sad tonight.", 0, 1)
a1 = talk("The duduk is a musical instrument.", 1, 0)
a2 = talk("The duduk is a musical instrument.", 2, 0)
version, grown, prop = S.status(seat, now=T0 + 3 * GN.DAY + 10_000)
approved = S.growth(seat, prop["act_id"], True, "dry run", now=T0 + 3 * GN.DAY + 10_001) if prop else None
after = talk("I love the duduk.", 3, 1)
S.wake(seat, now=T0 + 4 * GN.DAY + 600, run_gate=False, log=lambda *x: None)
st = json.loads(seat.path.read_text())
c = C5.load_state(st["blob"])
stream = st["log"] + [r for r in c.outbox if r["seq"] > (st["log"][-1]["seq"] if st["log"] else 0)]
duduk_cluster = a1["landed"]
out = {"conversations": log,
       "door_after_day0": "duduk" in log[0]["door"] and "duduk" in log[1]["door"],
       "asked_about_duduk_with_reason": all(x["question"] and "duduk" in x["question"][0] for x in (a1, a2)),
       "answers_landed_same_cluster": a1["landed"] is not None and a1["landed"] == a2["landed"],
       "binding": [r for r in stream if r["kind"] == "binding"],
       "proposal_shown_and_approved": prop is not None and approved == "0.5.1", "version": c.growth["version"],
       "heard_after_growth": [w for w, cl in after["heard"] if w == "duduk" and cl == duduk_cluster],
       "door_after_growth": after["door"], "live_verify": check_log(stream)}
out["passed"] = (out["door_after_day0"] and out["asked_about_duduk_with_reason"] and out["answers_landed_same_cluster"]
                 and len(out["binding"]) == 1 and out["proposal_shown_and_approved"] and bool(out["heard_after_growth"])
                 and "duduk" not in out["door_after_growth"]
                 and sum(out["live_verify"][k] for k in ("completeness", "receipt", "consequence", "necessity")) == 0)
json.dump(out, open(sys.argv[1], "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in out.items() if k != "conversations"}, indent=1, ensure_ascii=False))
