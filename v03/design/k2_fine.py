"""K2 fine: operating range [g^2, 1/2]. Effect size of P(x<0) between adjacent memory states,
and single-orbit window detectability (design probe, not a scored gate)."""
import numpy as np
from k1k2_plateau import g2, run

def window_acc(a1, a2, W, n=400, seed=7):
    """Two single orbits, one per state; classify each window by its P(x<0) against the midpoint
    of the two long-run means. Returns accuracy over n windows per state."""
    out = []
    for a, s in ((a1, 1), (a2, 2)):
        rng = np.random.default_rng(seed * 10 + s)
        x = rng.uniform(a - 1, a, n)              # n independent orbits = n windows
        neg = np.zeros(n)
        for t in range(200 + W):
            x[np.abs(x) < 1e-12] = 0.37
            if t >= 200: neg += (x < 0)
            y = np.abs(1.0 / x); x = y - np.floor(y + 1.0 - a)
        out.append(neg / W)
    return out

K = 9
states = [g2 + k * (0.5 - g2) / (K - 1) for k in range(K)]
means = []
for a in states:
    ps = [run(a, n_orb=20000, n_iter=2000, seed=s)["p_neg"] for s in range(3)]
    means.append(np.mean(ps)); print(f"a={a:.5f}  P(x<0)={np.mean(ps):.4f} ± {np.std(ps):.4f}", flush=True)
gaps = np.abs(np.diff(means)); print(f"adjacent gaps: {np.round(gaps,4)}  min {gaps.min():.4f}")
i = int(np.argmin(gaps)); a1, a2 = states[i], states[i + 1]; mid = (means[i] + means[i + 1]) / 2
for W in (250, 500, 1000, 2000, 4000):
    p1, p2 = window_acc(a1, a2, W)
    acc = 0.5 * (np.mean((p1 > mid) == (means[i] > mid)) + np.mean((p2 > mid) == (means[i+1] > mid)))
    print(f"hardest adjacent pair a={a1:.4f}/{a2:.4f}  W={W:5d}  window accuracy {acc:.3f}", flush=True)
