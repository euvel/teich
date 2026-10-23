"""Step-3 smoke on the REAL body (design seed 8800, 6 days): questions delivered and answered by a simulated founder,
door words heard and bound, asked tags, the knowable/given/emergent kinds, live verify, receipts, blob round trip."""
import json
import random
import sys

import creature_v05 as C5
import genome_v04 as GN
import self_sim as SS
import self_text_v05 as TX
from f1_v05 import check_log, check_xkinds

DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 6
T0 = 1_000_000.0
rng = random.Random(8800)
c = C5.load_state(C5.dump_state(C5.birth(seed=8800, t0=T0)))
asked_log = []
for d in range(DAYS):
    for ci in range(3):
        c.advance(int(T0 + d * GN.DAY + 12_000 + ci * 20_000 - c.t0) - c.n)
        conv = f"c{d}-{ci}"
        q = c.deliver_question() if ci == 0 else None
        props, wrong = [], []
        for _ in range(rng.randrange(2, 6)):
            k = rng.randrange(97); cw = 1 + SS._pick(rng, SS.CW_P)
            props.append({"cluster": k, "sign": rng.choice([1, -1, 0]), "text_sha256": f"{conv}{k}".encode().hex(), "cn": cw, "cf": 5})
            wrong.append(rng.random() < 0.15)
        landed = None
        if q:
            rr = [r for r in c.outbox if r["kind"] == "reason" and r["act_id"] == q["act_id"]][-1]
            text, why = TX.question(q["q"], rr["inputs"])
            answered = rng.random() < 0.8
            asked_log.append({"day": d, "question": text, "because": why, "answered": answered})
            if answered and q["q"][0] == "region" and q["q"][1] == 8:
                props.append({"cluster": GN.SELF, "sign": 1, "text_sha256": f"{conv}self".encode().hex(), "cn": 5, "cf": 5,
                              "asked": q["act_id"]}); wrong.append(False)
            elif answered and q["q"][0] == "region":
                for p in props:
                    if int(GN.REGION_OF[p["cluster"]]) == q["q"][1]:
                        p["asked"] = q["act_id"]
            elif answered and q["q"][0] == "word":
                landed = {"komitas": 40, "frisson": 55}[q["q"][1]]
        if d in (0, 1, 2):
            c.door_heard(["komitas", "frisson"])
        items = c.present(props, conv, "organ")
        c.decide(conv, {it["pid"] for it, w in zip(items, wrong) if it["shown"] and w}, "founder")
        if q:
            c.answer(q["act_id"], asked_log[-1]["answered"], landed)
c.advance(int(T0 + DAYS * GN.DAY + 600 - c.t0) - c.n)
blob = C5.dump_state(c)
diaries = [r["entry"] for r in c.outbox if r["kind"] == "diary"]
out = {"days": DAYS, "live_verify": check_log(c.outbox), "self5_receipts": check_xkinds(c.outbox),
       "blob_roundtrip": C5.dump_state(C5.load_state(blob)) == blob,
       "questions": asked_log, "bindings": [r for r in c.outbox if r["kind"] == "binding"],
       "door": c.door, "verdicts_last_night": {k: (v["verdict"], v["n"], v["miss"]) for k, v in diaries[-1]["self"]["self5"]["kinds"].items()},
       "hearing": diaries[-1]["self"]["self5"].get("hearing"),
       "account_last_nights": [TX.sentences(e["self"])[-6:] for e in diaries[-2:]]}
print(json.dumps(out, indent=1, ensure_ascii=False))
