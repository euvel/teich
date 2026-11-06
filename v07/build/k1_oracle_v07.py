"""Teich v0.7, the makers' influence in bits (PREREG_V07 §2, reported with K1): the BEST an insider can do.
Particles never interact, and the tie is read from particle 0 alone, so an insider who holds its state can compute,
for each input, the exact odds over the beacon that the deliberation lands on its target (M sampled beacons, each
input with its own sample). The oracle insider picks the input with the highest odds: p_t = max_h P_h.
  influence_bits = log2(mean_t p_t / mean_t 1/k_t)   (0 = no influence; log2 k = full control)
The max over noisy estimates is biased upward, so this OVERstates influence; the null control (input ignored)
measures that bias floor. Also recorded, per trial: whether v0.6 (no touch) could be steered by any input.
Trials as K1: a random moment of a lab life, LEAD before midnight, 16 mentions (particle 0's path first), k in 2..9.
    python3 k1_oracle_v07.py SEED TRIALS OUT.json [M=4000] [--control-ignores-input]
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np

import creature_v07 as C7
import delib_cert as DC
import genome_v04 as GN

LEAD, A = 10800, 16


def main(seed, trials, out, M, ignore):
    rng = np.random.default_rng(seed)
    c = C7.birth(seed=seed, t0=0.0); b = c.body
    st = (c.pc[:1].copy(), c.P[:1].copy(), c.V[:1].copy())       # particle 0 alone: it never meets the others
    res = []; t0 = time.time()
    for t in range(trials):
        st = b.run(*st, int(rng.integers(3600, 6 * 3600)))[0]
        k = int(rng.integers(2, 10)); target = int(rng.integers(0, k))
        path, s0 = [], st
        for _ in range(LEAD // 60):
            s0 = b.run(*s0, 60)[0]; pc0 = int(s0[0][0])
            if pc0 < GN.G - 1 and pc0 != GN.SELF and pc0 not in path:
                path.append(pc0)
        hs = (path + [int(h) for h in rng.permutation(GN.G - 1) if h not in path])[:A]
        odds, v06 = [], []
        for h in hs:
            n0 = int(b.n[h])
            if not ignore:
                b.set_dial(h, min(n0 + 1, GN.N_MAX))
            try:
                s = b.run(*st, LEAD - C7.SKY_LEAD)[0]
                m = b.run(*s, C7.SKY_LEAD)[0]
                v06.append(DC.deliberate(k, DC.u_of(int(m[0][0]), float(m[1][0, 1]), float(m[2][0, 2])))[0])
                rows = [C7.touch(s[1], s[2], float(x)) for x in rng.random(M)]
                P = np.vstack([r[0] for r in rows]); V = np.vstack([r[1] for r in rows])
                pc, P, V = b.run(np.repeat(s[0], M), P, V, C7.SKY_LEAD)[0]
                hit = sum(DC.deliberate(k, DC.u_of(int(pc[i]), float(P[i, 1]), float(V[i, 2])))[0] == target
                          for i in range(M))
                odds.append(hit / M)
            finally:
                b.set_dial(h, n0)
        res.append({"k": k, "target": target, "path_handles": len(path), "odds": odds, "oracle_p": max(odds),
                    "v06_steerable": target in v06, "v06_distinct": len(set(v06))})
        json.dump({"seed": seed, "M": M, "ignore_input": ignore, "trials": res, "seconds": time.time() - t0},
                  open(out, "w"))
        print(seed, "trial", t, round(time.time() - t0), "s", flush=True)


def bits(paths, boot=10000, seed=0):
    """influence_bits over all trials in the given outputs, with a bootstrap 95 % upper bound."""
    T = [t for p in paths for t in json.load(open(p))["trials"]]
    p = np.array([t["oracle_p"] for t in T]); q = np.array([1 / t["k"] for t in T])
    r = np.random.default_rng(seed); i = r.integers(0, len(T), (boot, len(T)))
    bs = np.log2(p[i].mean(1) / q[i].mean(1))
    return {"trials": len(T), "influence_bits": float(np.log2(p.mean() / q.mean())),
            "upper95_bits": float(np.quantile(bs, 0.95)), "full_control_bits": float(np.log2(1 / q.mean())),
            "v06_steerable": float(np.mean([t["v06_steerable"] for t in T]))}


if __name__ == "__main__":
    if sys.argv[1] == "bits":                       # python3 k1_oracle_v07.py bits OUT1.json OUT2.json ...
        print(json.dumps(bits(sys.argv[2:]), indent=1)); raise SystemExit
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    main(int(a[0]), int(a[1]), a[2], int(a[3]) if len(a) > 3 else 4000, "--control-ignores-input" in sys.argv)
