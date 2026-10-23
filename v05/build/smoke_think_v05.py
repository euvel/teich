"""Step-2 smoke on the REAL body (design seed 8600): thinking on vs off on the same schedule (gate O2 in miniature),
live verify of every act incl. think, blob round trip, dream cost, controls at rest."""
import json
import random
import sys
import time

import numpy as np

import creature_v05 as C5
import genome_v04 as GN
import self_sim as SS
from f1_v05 import check_log

DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
T0 = 1_000_000.0


def life(thinking):
    rng = random.Random(8600)
    c = C5.load_state(C5.dump_state(C5.birth(seed=8600, t0=T0))); c.thinking = thinking
    t = time.perf_counter()
    for d in range(DAYS):
        for ci in range(3):
            c.advance(int(T0 + d * GN.DAY + 12_000 + ci * 20_000 - c.t0) - c.n)
            props, wrong = [], []
            for _ in range(rng.randrange(2, 6)):
                k = rng.randrange(97); cw = 1 + SS._pick(rng, SS.CW_P)
                props.append({"cluster": k, "sign": rng.choice([1, -1, 0]), "text_sha256": f"{d}{ci}{k}".encode().hex(),
                              "cn": cw, "cf": 5})
                wrong.append(rng.random() < 0.15)
            items = c.present(props, f"c{d}-{ci}", "organ")
            c.decide(f"c{d}-{ci}", {it["pid"] for it, w in zip(items, wrong) if it["shown"] and w}, "founder")
    c.advance(int(T0 + DAYS * GN.DAY + 600 - c.t0) - c.n)
    return c, time.perf_counter() - t


on, t_on = life(True)
off, t_off = life(False)
THINK_KINDS = {"thought", "think-predict", "dream", "reason", "act"}
from f1_v05 import canonical
def strip(rs):
    """Pointer-aware (as in F1): drop thinking records AND every act record, then compare by meaning."""
    return canonical([r if r["kind"] not in THINK_KINDS - {"reason", "act"} else {**r, "kind": "act"} for r in rs])
blob = C5.dump_state(on)
dreams = [r for r in on.outbox if r["kind"] == "dream"]
out = {
    "days": DAYS, "seconds_with_thinking": round(t_on), "seconds_without": round(t_off),
    "thinking_cost_share": round(t_on / t_off - 1, 3),
    "O2_main_body_identical": bool(np.array_equal(on.P, off.P) and np.array_equal(on.V, off.V) and np.array_equal(on.pc, off.pc)),
    "O2_dials_heart_identical": bool(np.array_equal(on.body.n, off.body.n) and np.array_equal(on.heart.k, off.heart.k)),
    "O2_non_thinking_records_identical": strip(on.outbox) == strip(off.outbox),
    "live_verify": check_log(on.outbox),
    "blob_roundtrip": C5.dump_state(C5.load_state(blob)) == blob,
    "dreams": [{"night": r["night"], "thoughts": r["thoughts"],
                "read": [round(float.fromhex(x), 4) for x in r["read"]],
                "predicted": round(float.fromhex(r["predicted"]), 4), "held": r["held"]} for r in dreams],
    "rest_length": round(GN.ELL0, 4),
}
print(json.dumps(out, indent=1))
