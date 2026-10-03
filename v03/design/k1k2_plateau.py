"""Teich v0.3 — day-1 kill checks K1 and K2 for the modular body (design probe, NOT a scored gate).

alpha-continued fraction map (Nakada 1981), on I_a = [a-1, a):
    T_a(x) = |1/x| - floor(|1/x| + 1 - a),   T_a(0) = 0
|T_a'(x)| = 1/x^2, so the Lyapunov exponent is  lambda(a) = E_mu[-2 log|x|].
For an absolutely continuous invariant measure, Rokhlin: entropy h(a) = lambda(a).
Literature (Nakada; Kraaikamp-Schmidt-Steiner; Carminati-Tiozzo):
    g <= a <= 1 :  h = pi^2 / (6 log(1+a))
    g^2 <= a <= g:  h = pi^2 / (6 log G)   (G = golden ratio)   <- the plateau

K1: is lambda constant on [g^2, g] (and does the method SEE variation outside it)?
K2: does an observable of x alone move with a on the plateau, and by how much (delta_0)?

Floating point note: floats are rationals, whose continued fractions terminate, so an orbit can
hit 0. Rounding usually prevents it; any orbit that gets within 1e-12 of 0 is re-seeded from a
deterministic generator and counted.
"""
import math, sys, time
import numpy as np

G = (1 + 5 ** 0.5) / 2
g = G - 1
g2 = g * g
PLATEAU = math.pi ** 2 / (6 * math.log(G))


def theory(a):
    if a >= g:
        return math.pi ** 2 / (6 * math.log(1 + a))
    if a >= g2:
        return PLATEAU
    return float("nan")            # below g^2: not constant, no closed form used here


def run(a, n_orb=20000, n_burn=200, n_iter=3000, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.uniform(a - 1, a, n_orb)
    lam_sum = 0.0; neg = 0; small = 0; big = 0; reseed = 0; count = 0
    for t in range(n_burn + n_iter):
        bad = np.abs(x) < 1e-12
        if bad.any():
            reseed += int(bad.sum()); x[bad] = rng.uniform(a - 1, a, int(bad.sum()))
        if t >= n_burn:
            lam_sum += float(np.sum(-2.0 * np.log(np.abs(x))))
            neg += int(np.sum(x < 0)); small += int(np.sum(np.abs(x) < 0.25))
            count += x.size
        y = np.abs(1.0 / x)
        x = y - np.floor(y + 1.0 - a)
    return dict(a=a, lam=lam_sum / count, p_neg=neg / count, p_small=small / count,
                reseed=reseed, n=count)


if __name__ == "__main__":
    t0 = time.time()
    plateau = [g2 + k * (g - g2) / 8 for k in range(9)]
    outside = [0.30, 0.70, 0.80, 0.90, 1.00]
    print(f"g^2={g2:.6f}  g={g:.6f}  plateau value pi^2/(6 log G) = {PLATEAU:.6f}")
    rows = []
    for a in plateau + outside:
        r = run(a, seed=int(a * 1e6)); rows.append(r)
        th = theory(a)
        print(f"a={a:.4f} {'PLATEAU' if g2 - 1e-12 <= a <= g + 1e-12 else 'outside'}  "
              f"lambda={r['lam']:.4f}  theory={th:.4f}  diff={r['lam'] - th:+.4f}  "
              f"P(x<0)={r['p_neg']:.4f}  P(|x|<.25)={r['p_small']:.4f}  reseeds={r['reseed']}  "
              f"({time.time() - t0:.0f}s)", flush=True)
    pl = [r for r in rows if g2 - 1e-12 <= r["a"] <= g + 1e-12]
    lams = np.array([r["lam"] for r in pl]); pn = np.array([r["p_neg"] for r in pl])
    print(f"\nK1 plateau lambda: mean {lams.mean():.4f}  range {lams.max() - lams.min():.4f}  "
          f"max|diff from theory| {np.max(np.abs(lams - PLATEAU)):.4f}")
    print(f"K2 P(x<0) across plateau: {pn.min():.4f} .. {pn.max():.4f}; "
          f"min adjacent gap {np.min(np.abs(np.diff(pn))):.4f}")
