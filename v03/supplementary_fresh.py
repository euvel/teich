"""SUPPLEMENTARY (not part of the frozen verdict): G4, G5, L1 re-drawn with fresh randomness tied to the
gate seed range, because the scored harness used fixed internal seeds (4, 5000+K, 7) for these three
gates — the same draws as the rehearsal. Same bars as the spec. Reported whatever it shows."""
import json, math, numpy as np
import accept_v03 as A, genome_v03 as G
out = {}
out["G4"] = A.g4(20000, 500, seed=9004)
out["L1"] = A.l1(seed=9007)
# G5 with a fresh interference sequence: patch the sequence seed via a local copy of g5
def g5_fresh(seeds, Ks, W, warm=200):
    res = {}
    for K in Ks:
        x0 = np.concatenate([A.x0_for(s) for s in seeds]); n = len(seeds); x = np.tile(x0, 2)
        led = G.Ledger.born(x.size)
        for _ in range(warm): x = G.step(x, G.alpha_of(led.k))
        led.event(np.repeat([1, -1], n), tick=warm)
        seq = np.random.default_rng(95000 + K).choice([1, -1], size=(K, n))
        for j in range(K): led.event(np.tile(seq[j], 2), tick=warm)
        a = G.alpha_of(led.k); acc = np.zeros(x.size)
        for t in range(200 + W):
            if t >= 200: acc += G.observe(x)["neg"]
            x = G.step(x, a)
        m = acc / W; res[K] = dict(D=round(A.D(list(zip(m[:n], m[n:]))), 4),
                                   merged_frac=round(float(np.mean(led.k[:n] == led.k[n:])), 4))
    return res
out["G5"] = g5_fresh(list(range(900, 948)), [1, 4, 16, 64], 8000)
pred = {1: 1.0, 4: 0.875, 16: 0.3267, 64: 0.0029}
band = lambda p: 1.96 * math.sqrt(p * (1 - p) / 48) + 0.03
out["passes"] = {"G4": all(abs(r["diff"]) <= 0.002 for r in out["G4"]),
                 "L1": out["L1"]["mismatches"] == 0,
                 "G5": all(abs(out["G5"][K]["D"] - pred[K]) <= band(pred[K]) for K in pred)}
json.dump(out, open("out_v03/supplementary_fresh.json", "w"), indent=1)
for r in out["G4"]: print(r)
print(out["L1"]); print(out["G5"]); print(out["passes"])
