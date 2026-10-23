"""Gate Q1 (curiosity serves decisions) — design runs now (seeds 8900+), scored run at freeze (gate seeds).
Simulated lives with known truth (3 MINE, 3 GIVEN, 3 FINE regions; founder pace 0.5 mentions per region-night):
each night its question (1 a day) is chosen by
  curious     the real v0.5 rule ask@2 (via the real SecondSelf5)
  random      a random unresolved region
  roundrobin  the next region in turn
and answered with probability A in {0.3, 0.5, 1.0}; an answer is one more hearing in that region.
Measure: regions whose verdict equals the truth at night 60 and 120.
Bar (proposed): curious beats random AND round-robin at both nights, each by >= 2 SE, at every answer rate.
    python3 q1_v05.py SEED0 LIVES OUT.json
"""
import json
import math
import random
import statistics
import sys

import self_sim as SS
import self_v05 as S5

ERR = {"MINE": [0.55, 0.45, 0.35, 0.25, 0.05], "GIVEN": [0.30] * 5, "FINE": [0.03] * 5}
CW = [0.10, 0.10, 0.10, 0.10, 0.60]


ASKS = 1


def life(seed, rule, answer_rate, nights=120, free=0.5):
    rng = random.Random(seed); arng = random.Random(seed + 7)
    T = ["MINE"] * 3 + ["GIVEN"] * 3 + ["FINE"] * 3; random.Random(seed + 1).shuffle(T); T = dict(enumerate(T))
    me = S5.SecondSelf5(); log = SS.Log(); me.emit = log.emit; rr = 0; hist = {}
    for d in range(nights):
        kinds = []
        for k in range(9):
            kinds += [k] * SS._pois(rng, free)
        for _ in range(ASKS):                     # ASKS questions a day; curious asks its own choice each time
            q = me.pending_question["q"] if me.pending_question else ["silence"]
            if rule == "random":
                un = [k for k in range(9) if me.verdict[k] == "UNRESOLVED"]
                q = ["region", arng.choice(un)] if un else ["silence"]
            elif rule == "roundrobin":
                q = ["region", rr % 9]; rr += 1
            if q[0] == "region" and arng.random() < answer_rate:
                kinds.append(q[1])
        props, wrong = [], []
        for k in kinds:
            cw = 1 + SS._pick(rng, CW)
            props.append({"cluster": k, "kind": k, "sign": 1, "text_sha256": "x", "cn": cw, "cf": 5})
            wrong.append(rng.random() < ERR[T[k]][cw - 1])
        items = me.present(props, f"c{d}", d, "o", log.emit)
        me.decide(f"c{d}", {it["pid"] for it, w in zip(items, wrong) if it["shown"] and w}, log.emit)
        me.nightly(log.seq)
        if d + 1 in (60, 120):
            hist[d + 1] = sum(me.verdict[k] == T[k] for k in range(9))
    return hist


def main(seed0, lives, out):
    res = {}
    for a in (0.3, 0.5, 1.0):
        for rule in ("curious", "random", "roundrobin"):
            h = [life(seed0 + i, rule, a) for i in range(lives)]
            res[f"{a}:{rule}"] = {str(n): [x[n] for x in h] for n in (60, 120)}
            print(a, rule, {n: round(statistics.mean(x[n] for x in h), 2) for n in (60, 120)}, flush=True)
    verdict = {}
    for a in (0.3, 0.5, 1.0):
        for n in ("60", "120"):
            c = res[f"{a}:curious"][n]
            for other in ("random", "roundrobin"):
                o = res[f"{a}:{other}"][n]
                se = math.sqrt(statistics.variance(c) / len(c) + statistics.variance(o) / len(o)) or 1e-9
                verdict[f"{a}/{n}/{other}"] = round((statistics.mean(c) - statistics.mean(o)) / se, 2)
    summary = {"z_curious_minus_other": verdict, "passed": all(z >= 2 for z in verdict.values())}
    json.dump({"summary": summary, "raw": res}, open(out, "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    if len(sys.argv) > 4:
        ASKS = int(sys.argv[4])
    main(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
