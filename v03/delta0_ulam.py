"""δ₀ by Ulam's transfer-operator method — deterministic, independent of the Monte Carlo orbits.

For each memory state α_k: partition [α−1, α) into n bins; push m evenly spaced points per bin through
T_α (dense quadrature, no randomness); the Ulam matrix is the resulting bin-to-bin mass transfer; its
stationary vector is the invariant density. P(x<0) = mass on negative bins. Resolution n is doubled to
show convergence. The map is uniformly expanding on the operating range (|T'| = 1/x² ≥ 1/(1−α)² > 2.8),
the setting in which Ulam's method converges (Li 1976; rigorous error bounds: Galatolo–Nisoli).

This is a deterministic numerical certificate, NOT an interval-arithmetic proof (that would also bound
the quadrature and truncation errors rigorously; see the report for what remains).
"""
import json, time
import numpy as np
import scipy.sparse as sp
import genome_v03 as G1


def p_neg_aligned(a, n, m=64, iters=400):
    """Grid aligned so 0 is a bin edge: negative part [a−1, 0) and positive part [0, a) get bins in
    proportion to their lengths."""
    nn = max(1, int(round(n * (1 - a)))); npos = n - nn
    edges = np.concatenate([np.linspace(a - 1, 0, nn + 1)[:-1], np.linspace(0, a, npos + 1)])
    widths = np.diff(edges)
    pts = (edges[:-1, None] + (np.arange(m)[None, :] + 0.5) / m * widths[:, None])
    src = np.repeat(np.arange(n), m); x = pts.ravel()
    y = np.abs(1.0 / x); y = y - np.floor(y + 1.0 - a)
    dst = np.clip(np.searchsorted(edges, y, side="right") - 1, 0, n - 1)
    P = sp.csr_matrix((np.full(x.size, 1.0 / m), (src, dst)), shape=(n, n))
    h = widths / widths.sum()
    for _ in range(iters):
        h = P.T @ h; h /= h.sum()
    return float(h[:nn].sum())


if __name__ == "__main__":
    t0 = time.time(); res = {}
    for n, m in ((1024, 64), (2048, 64), (4096, 64), (8192, 64), (8192, 256), (16384, 256)):
        key = f"{n}x{m}"; res[key] = [p_neg_aligned(float(G1.alpha_of(k)), n, m) for k in range(G1.N_STATES)]
        n = key
        gaps = -np.diff(res[n])
        print(f"{n:>10s}  P(x<0) = {np.round(res[n], 5)}  adjacent gaps {np.round(gaps, 5)}  min {gaps.min():.5f}  ({time.time()-t0:.0f}s)", flush=True)
    finest, prev = np.array(res["16384x256"]), np.array(res["8192x256"])
    out = {"P_neg_by_n": {str(k): v for k, v in res.items()},
           "delta0_ulam": float((-np.diff(finest)).min()),
           "max_change_8192_to_16384_at_m256": float(np.abs(finest - prev).max()),
           "monte_carlo_calibration_P_K": [0.61228, 0.5877, 0.55782, 0.52811, 0.49878, 0.46943, 0.44038]}
    out["max_abs_diff_vs_monte_carlo"] = float(np.abs(finest - np.array(out["monte_carlo_calibration_P_K"])).max())
    json.dump(out, open("out_v03/delta0_ulam.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "P_neg_by_n"}, indent=1))
