"""Gate O1 (objective order sensitivity of working memory) — spec V05_SPEC.md §3.2. Scored run at freeze (gate seeds),
design runs on design seeds. Heavy: run on Kaggle.

For every pair of the 9 thought curves: TWIN dreams from identical working particles, thoughts (c, d) vs (d, c);
CONTROL dreams: the same sequence (c, d) from different particles. Single-dream noise is estimated from the controls.
Bars (proposed, fixed at freeze):
  power        among pairs whose exact order effect >= 3 x single-dream noise, >= 80% show a twin difference >= 3 SE
  no false     among control comparisons, <= 5% exceed 3 SE
  meaning      Spearman(measured order effect, crossing number) >= 0.6
    python3 o1_v05.py SEED0 TWINS TICKS OUT.json
"""
import itertools
import json
import math
import sys

import numpy as np

import work_v05 as W


def crossing(c, d):
    (p1, q1), (p2, q2) = W.CURVES[c], W.CURVES[d]
    return abs(p1 * q2 - p2 * q1)


def main(seed0, twins, ticks, out):
    b = W.WorkBody(); NP = 256

    def read(seq, seed):
        pc, P, V = b.start(NP, seed)
        _, lh, _, _, _ = W.dream(b, pc, P, V, seq, ticks)
        return float(lh[0])

    res = []
    for k, (c, d) in enumerate(itertools.combinations(range(9), 2)):
        seeds = [seed0 + 100 * k + i for i in range(twins)]
        ab = np.array([read([c, d], s) for s in seeds]); ba = np.array([read([d, c], s) for s in seeds])
        ctl = np.array([read([c, d], s + 50) for s in seeds])
        exact = abs(W.exact_length([c, d]) - W.exact_length([d, c])) / W.exact_length([d, c])
        res.append({"pair": [c, d], "crossing": crossing(c, d), "exact_effect": exact,
                    "twin_diff": float((ab - ba).mean()), "ctl_diff": float((ab - ctl).mean()),
                    "ab": ab.tolist(), "ctl": ctl.tolist()})
        print(k, (c, d), f"exact {exact:.3%}", flush=True)
    sd = float(np.std(np.concatenate([np.array(r["ab"]) - np.array(r["ctl"]) for r in res]), ddof=1) / math.sqrt(2))
    se = sd * math.sqrt(2 / twins)
    for r in res:
        r["twin_z"] = abs(r["twin_diff"]) / se; r["ctl_z"] = abs(r["ctl_diff"]) / se
    rel_sd = sd / float(np.mean([np.mean(r["ab"]) for r in res]))
    big = [r for r in res if r["exact_effect"] >= 3 * rel_sd]
    from scipy.stats import spearmanr
    summary = {"single_dream_noise_rel": rel_sd, "pairs": len(res), "pairs_above_3x_noise": len(big),
               "power": float(np.mean([r["twin_z"] >= 3 for r in big])) if big else None,
               "false_rate": float(np.mean([r["ctl_z"] >= 3 for r in res])),
               "spearman_effect_crossing": float(spearmanr([abs(r["twin_diff"]) for r in res], [r["crossing"] for r in res])[0])}
    summary["passed"] = (summary["power"] is not None and summary["power"] >= 0.8 and summary["false_rate"] <= 0.05
                         and summary["spearman_effect_crossing"] >= 0.6)
    json.dump({"summary": summary, "pairs": res}, open(out, "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
