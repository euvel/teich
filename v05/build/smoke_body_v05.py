"""Step-1 smoke on the REAL body (design seed 8100, 2 days): the v0.5 creature with strikes and caution-moving truth.
Measures the L-CL budget (self's work / body's work) and runs live verify on its real record stream."""
import json
import random
import sys
import time

import creature_v05 as C5
import genome_v04 as GN
import self_sim as SS
from f1_v05 import check_log

DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 2
rng = random.Random(8100); T0 = 1_000_000.0
c = C5.load_state(C5.dump_state(C5.birth(seed=8100, t0=T0)))
# give its self a history so caution and probes actually move in a 2-day smoke (design truth: kinds 0-2 MINE)
c.me.caution = [2, 2, 1, 0, 0, 0, 0, 0, 0]
t_self = t_body = 0.0
body_run = c.body.run
def timed_run(*a, **k):
    global t_body
    t = time.perf_counter(); out = body_run(*a, **k); t_body += time.perf_counter() - t; return out
c.body.run = timed_run
for meth in ("present", "decide", "nightly", "readings"):
    f = getattr(c.me, meth)
    def wrap(*a, _f=f, **k):
        global t_self
        t = time.perf_counter(); out = _f(*a, **k); t_self += time.perf_counter() - t; return out
    setattr(c.me, meth, wrap)
for d in range(DAYS):
    for ci in range(4):
        c.advance(int(T0 + d * GN.DAY + 10_000 + ci * 15_000 - c.t0) - c.n)
        props, wrong = [], []
        for _ in range(rng.randrange(3, 8)):
            k = rng.randrange(97); kind = int(GN.REGION_OF[k]); cw = 1 + SS._pick(rng, SS.CW_P)
            props.append({"cluster": k, "sign": 1, "text_sha256": f"{d}{ci}{k}".encode().hex(), "cn": cw, "cf": 5})
            wrong.append(rng.random() < SS.ERR[("MINE", "GIVEN", "FINE")[kind % 3]][cw - 1])
        items = c.present(props, f"c{d}-{ci}", "organ")
        c.decide(f"c{d}-{ci}", {it["pid"] for it, w in zip(items, wrong) if it["shown"] and w}, "founder")
c.advance(int(T0 + DAYS * GN.DAY + 600 - c.t0) - c.n)
f = check_log(c.outbox)
kinds = {}
for r in c.outbox:
    kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
blob = C5.dump_state(c)
out = {"days": DAYS, "records": kinds, "live_verify": f, "self_seconds": round(t_self, 3), "body_seconds": round(t_body, 1),
       "self_share_of_body": round(t_self / t_body, 5), "LCL_budget_1pct": t_self / t_body <= 0.01,
       "blob_roundtrip": C5.dump_state(C5.load_state(blob)) == blob, "pending_question": c.me.pending_question}
print(json.dumps(out, indent=1))
