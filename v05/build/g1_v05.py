"""Gate G1 (growth keeps its word) — body half, twin lives (design seed 9000 now; gate seeds at freeze).

Both lives: same birth, same schedule. A door word is heard, asked about, answered on two different days -> bound;
at that night its self proposes a growth with its own pre-registered prediction. Then life A APPROVES, life B REFUSES,
and both live on. Checks:
  nothing_else   A == B in body, dials, heart, commitments, self state, and every record by meaning — except the growth
                 records themselves (and the growth/door bookkeeping)
  receipts       after growth every claim still recomputes: live verify (acts), the v0.5 kinds, v0.4's self claims
  identity       new identity = sha256(previous + sha256(amendment)); version 0.5.1
  prediction     the map it grew equals the "hear" its prediction registered
(The Ears half — the grown words are now heard as those concepts and every other word exactly as before — runs with
the Ears on Kaggle: g1_ears_v05.py.)
    python3 g1_v05.py DAYS OUT.json
"""
import hashlib
import json
import random
import sys

import numpy as np

import creature_v05 as C5
import genome_v04 as GN
import self_sim as SS
from f1_v05 import canonical, check_log, check_xkinds

DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 5
SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 9000          # 9000 = design seed; the scored run passes a gate seed
T0 = 1_000_000.0
WORD, CLUSTER = "komitas", 40


def life(approve):
    rng = random.Random(SEED)
    c = C5.load_state(C5.dump_state(C5.birth(seed=SEED, t0=T0, identity="g1-drill")))
    decided = False
    for d in range(DAYS):
        for ci in range(3):
            c.advance(int(T0 + d * GN.DAY + 12_000 + ci * 20_000 - c.t0) - c.n)
            conv = f"c{d}-{ci}"
            if c.growth["proposal"] and not decided:
                c.decide_growth(c.growth["proposal"]["act_id"], approve, "twin test"); decided = True
            q = c.deliver_question() if ci == 0 else None
            props, wrong = [], []
            for _ in range(rng.randrange(2, 5)):
                k = rng.randrange(97); cw = 1 + SS._pick(rng, SS.CW_P)
                props.append({"cluster": k, "sign": 1, "text_sha256": f"{conv}{k}".encode().hex(), "cn": cw, "cf": 5})
                wrong.append(rng.random() < 0.15)
            if d < 2:
                c.door_heard([WORD])
            items = c.present(props, conv, "organ")
            c.decide(conv, {it["pid"] for it, w in zip(items, wrong) if it["shown"] and w}, "founder")
            if q:
                c.answer(q["act_id"], True, CLUSTER if q["q"] == ["word", WORD] else None)
    c.advance(int(T0 + DAYS * GN.DAY + 600 - c.t0) - c.n)
    return c


A, B = life(True), life(False)
GROWTH_KINDS = {"growth", "growth-refused"}
ca = canonical([r for r in A.outbox if r["kind"] not in GROWTH_KINDS])
cb = canonical([r for r in B.outbox if r["kind"] not in GROWTH_KINDS])
sa = {k: v for k, v in A.me.to_json().items()}; sb = {k: v for k, v in B.me.to_json().items()}
g = [r for r in A.outbox if r["kind"] == "growth"]
prop = [r for r in A.outbox if r["kind"] == "growth-proposal"]
ident_ok = False
if g:
    am = g[0]["amendment"]
    a_sha = hashlib.sha256(json.dumps(am, sort_keys=True).encode()).hexdigest()
    ident_ok = (a_sha == g[0]["amendment_sha"]
                and hashlib.sha256((g[0]["prev_identity"] + a_sha).encode()).hexdigest() == g[0]["identity"]
                and g[0]["prev_identity"] == "g1-drill")
blocks = [r["entry"]["self"] for r in A.outbox if r["kind"] == "diary"]
ch, bad = SS.verify(A.outbox, blocks)
out = {
    "days": DAYS, "proposed": [r["bindings"] for r in prop], "approved_in_A": bool(g), "refused_in_B": any(r["kind"] == "growth-refused" for r in B.outbox),
    "nothing_else_body": bool(np.array_equal(A.P, B.P) and np.array_equal(A.V, B.V) and np.array_equal(A.pc, B.pc)),
    "nothing_else_dials_heart_commitments": bool(np.array_equal(A.body.n, B.body.n) and np.array_equal(A.heart.k, B.heart.k)
                                                 and A.frozen == B.frozen),
    "nothing_else_self_state": sa == sb,
    "nothing_else_records": ca == cb,
    "receipts_acts": check_log(A.outbox), "receipts_v05_kinds": check_xkinds(A.outbox), "receipts_v04_self": [ch, len(bad)],
    "identity_chain_recomputes": ident_ok, "version": A.growth["version"],
    "prediction_holds": bool(prop) and A.ears_map() == prop[0]["prediction"]["hear"],
}
out["passed"] = (out["approved_in_A"] and out["refused_in_B"] and out["nothing_else_body"]
                 and out["nothing_else_dials_heart_commitments"] and out["nothing_else_self_state"]
                 and out["nothing_else_records"] and sum(out["receipts_acts"][k] for k in ("completeness", "receipt", "consequence", "necessity")) == 0
                 and out["receipts_v05_kinds"]["mismatches"] == 0 and out["receipts_v04_self"][1] == 0
                 and ident_ok and out["version"] == "0.5.1" and out["prediction_holds"])
json.dump(out, open(sys.argv[2] if len(sys.argv) > 2 else "g1_design.json", "w"), indent=1)
print(json.dumps(out, indent=1))
