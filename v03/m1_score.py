"""Teich v0.3 — M1 meaning test, SCORED (one run, only after V03_SPEC_part2a.md is frozen and anchored).

Question: does the creature's own relatedness — the intersection number of its concept curves —
preserve human similarity judgements?

Data: SimLex-999 noun pairs (POS = N). Placement: concepts_v03.json (frozen, built from words only).
Primary statistic: Spearman rho between -log max(1, i(c1, c2)) and the SimLex-999 score.
PASS iff  rho >= 0.30  AND  the 95% bootstrap CI lower bound > the 97.5th percentile of the
shuffled-address null.  All random draws derive from the gate seed range (900, 901).
Reported, not gating: MiniLM cosine on the same pairs (the organ's ceiling); WordNet placement H.
"""
import json, math, os, sys
os.environ.setdefault("HF_HUB_OFFLINE", "1")
import numpy as np
from scipy.stats import spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    C = json.load(open(os.path.join(HERE, "concepts_v03.json")))["concepts"]
    pairs = []
    for i, line in enumerate(open(os.path.join(HERE, "data", "SimLex-999", "SimLex-999.txt"))):
        if i == 0:
            continue
        f = line.rstrip("\n").split("\t")
        if f[2] == "N":
            pairs.append((f[0].lower(), f[1].lower(), float(f[3])))
    assert all(a in C and b in C for a, b, _ in pairs), "a SimLex noun is missing from the birth vocabulary"
    geo = lambda a, b: -math.log(max(1, abs(C[a][0] * C[b][1] - C[a][1] * C[b][0])))
    xs = np.array([geo(a, b) for a, b, _ in pairs]); hs = np.array([s for *_, s in pairs])
    rho = spearmanr(xs, hs).correlation

    rng = np.random.default_rng(900)
    boot = [spearmanr(xs[idx], hs[idx]).correlation
            for idx in (rng.integers(0, len(pairs), len(pairs)) for _ in range(10000))]
    lo, hi = np.percentile(boot, [2.5, 97.5])

    rng = np.random.default_rng(901); words = sorted(C); vals = [C[w] for w in words]; null = []
    for _ in range(1000):
        perm = rng.permutation(len(vals)); D = {w: vals[j] for w, j in zip(words, perm)}
        null.append(spearmanr([-math.log(max(1, abs(D[a][0] * D[b][1] - D[a][1] * D[b][0])))
                               for a, b, _ in pairs], hs).correlation)
    null97 = float(np.percentile(null, 97.5))

    # reported, not gating
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
    words_used = sorted({w for a, b, _ in pairs for w in (a, b)})
    E = dict(zip(words_used, m.encode(words_used, normalize_embeddings=True)))
    cos = spearmanr([float(E[a] @ E[b]) for a, b, _ in pairs], hs).correlation

    v = dict(n_pairs=len(pairs), rho=round(float(rho), 4), ci=[round(float(lo), 4), round(float(hi), 4)],
             null_mean=round(float(np.mean(null)), 4), null_97_5=round(null97, 4),
             minilm_cosine_rho_reported=round(float(cos), 4),
             retained_fraction_reported=round(float(rho / cos), 3) if cos > 0 else None,
             passed=bool(rho >= 0.30 and lo > null97))
    json.dump(v, open(os.path.join(HERE, "out_v03", "m1_scored.json"), "w"), indent=1)
    print(json.dumps(v, indent=1)); print("M1:", "PASS" if v["passed"] else "FAIL")


if __name__ == "__main__":
    main()
