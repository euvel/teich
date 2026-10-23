"""Law L-CL, part (c): the meaning demonstration. On quiet nights (no conversation, so the world adds nothing), an ORACLE
that copies the body and lives the next night in advance predicts the BODY-PATH sides exactly — at the cost of living
it. Its self's cheap predictor (same side as last night, the best a cheap model can do) gets about half. GIVEN therefore
means "knowable only at the cost of living it", not "unknowable".
    python3 oracle_v05.py SEED NIGHTS OUT.json
"""
import copy
import json
import sys
import time

import creature_v05 as C5
import genome_v04 as GN


def main(seed, nights, out):
    T0 = 1_000_000.0
    c = C5.load_state(C5.dump_state(C5.birth(seed=seed, t0=T0)))
    c.thinking = False                                        # the oracle concerns the main body's paths
    c.advance(4 * GN.DAY)                                     # settle every handle (3 quiet nights + 1)
    rows, t_oracle, t_cheap = [], 0.0, 0.0
    for _ in range(nights):
        pend = c.me.pending_body                              # the self's cheap predictions for the coming night
        t = time.perf_counter()
        twin = copy.deepcopy(c)                               # the oracle: copy the body, live the night first
        twin.advance(GN.DAY)
        tw = next(r for r in reversed(twin.outbox) if r["kind"] == "night-reading")
        t_oracle += time.perf_counter() - t
        t = time.perf_counter()
        c.advance(GN.DAY)
        t_cheap += time.perf_counter() - t
        real = next(r for r in reversed(c.outbox) if r["kind"] == "night-reading")
        n = hit_cheap = hit_oracle = 0
        for j, (settled_hex, side) in pend["path"].items():
            j = int(j)
            if real["lengths"][j] is None:
                continue
            now = float.fromhex(real["lengths"][j]) - float.fromhex(settled_hex)
            if now == 0.0:
                continue
            truth = 1 if now > 0 else -1
            o = float.fromhex(tw["lengths"][j]) - float.fromhex(settled_hex)
            n += 1; hit_cheap += truth == side; hit_oracle += truth == (1 if o > 0 else -1)
        rows.append({"predictions": n, "cheap_hits": hit_cheap, "oracle_hits": hit_oracle,
                     "oracle_reading_identical": tw["lengths"] == real["lengths"]})
    n = sum(r["predictions"] for r in rows)
    res = {"nights": nights, "predictions": n,
           "cheap_hit_rate": sum(r["cheap_hits"] for r in rows) / n, "oracle_hit_rate": sum(r["oracle_hits"] for r in rows) / n,
           "oracle_cost_vs_living": t_oracle / t_cheap, "rows": rows}
    res["passed"] = res["oracle_hit_rate"] == 1.0 and all(r["oracle_reading_identical"] for r in rows)
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
