"""Step 2 design run D1 (design seeds 8200+, exact math, no particles): can a FROZEN, ORDER-BLIND model of thinking be
accurate enough that its misses are mostly the ORDER of thoughts (not its own crudeness)?

Observable: the length of the thinking handle's core curve A (what its body's crossings read).
Thoughts: twists of 0.2 along the 9 region curves (8 v0.3 regions + itself = 1/1), certified closed form.
Order-blind models (all depend only on how many times each curve was thought about today):
  M1 linear:     l0 + sum_c n_c * a_c
  M2 quadratic:  M1 + sum_c n_c^2 * b_c + sum_{c<c'} n_c n_c' * e_cc'   (e = symmetric mixed term)
Coefficients by exact finite differences at the rest shape (54 numbers, frozen at genesis).
For random realistic days we compare: |actual - model| (model error) vs |actual(order) - actual(reversed)| (order).
"""
import itertools
import math
import random
import sys

import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import geo_smoke as G  # noqa: E402
import handle_mp as H  # noqa: E402
import mind4 as M  # noqa: E402

CURVES = [(1, 4), (2, 5), (3, 5), (3, 4), (4, 3), (5, 3), (5, 2), (4, 1), (1, 1)]   # 8 regions + itself
Am, Bm = H.birth(*M.BIRTH)
A0 = np.array([float(v) for v in Am]).reshape(2, 2); B0 = np.array([float(v) for v in Bm]).reshape(2, 2)


def apply(seq):
    A, B = A0.copy(), B0.copy()
    for c in seq:
        A, B = G.twist(A, B, *CURVES[c], G.flow_C)
    return 2 * math.acosh(abs(np.trace(A)) / 2)


L0 = apply([])
a = [apply([c]) - L0 for c in range(9)]
b = [(apply([c, c]) - L0 - 2 * a[c]) / 2 for c in range(9)]            # so that n=1 and n=2 are exact on single curves
e = {}
for c, d in itertools.combinations(range(9), 2):
    sym = (apply([c, d]) + apply([d, c])) / 2                          # symmetric (order-blind) part of the pair
    e[(c, d)] = sym - L0 - a[c] - a[d] - b[c] - b[d]


def m1(n):
    return L0 + sum(n[c] * a[c] for c in range(9))


def m2(n):
    return m1(n) + sum(n[c] ** 2 * b[c] for c in range(9)) + sum(n[c] * n[d] * e[(c, d)] for (c, d) in e)


def crossing(c, d):
    (p1, q1), (p2, q2) = CURVES[c], CURVES[d]
    return abs(p1 * q2 - p2 * q1)


rng = random.Random(8200)
rows = []
for _ in range(300):
    k = rng.randint(2, 12)
    seq = [rng.randrange(9) for _ in range(k)]
    n = [seq.count(c) for c in range(9)]
    act, rev = apply(seq), apply(seq[::-1])
    rows.append((k, abs(act - rev) / L0, abs(act - m1(n)) / L0, abs(act - m2(n)) / L0,
                 sum(crossing(seq[i], seq[i + 1]) for i in range(k - 1)) / max(1, k - 1)))
R = np.array(rows)
NOISE = 0.0067          # ~one night's relative reading noise of a length (v0.4 body); the working surface's own is measured in step 2
print(f"rest core length l0 = {L0:.4f}; 300 random days of 2-12 thoughts")
print(f"order effect |order - reversed|:      median {np.median(R[:,1]):.3%}   90th pct {np.percentile(R[:,1],90):.3%}")
print(f"linear order-blind model error:       median {np.median(R[:,2]):.3%}   90th pct {np.percentile(R[:,2],90):.3%}")
print(f"quadratic order-blind model error:    median {np.median(R[:,3]):.3%}   90th pct {np.percentile(R[:,3],90):.3%}")
for lo, hi in ((2, 4), (5, 8), (9, 12)):
    m = (R[:, 0] >= lo) & (R[:, 0] <= hi)
    print(f"  {lo:2d}-{hi:2d} thoughts: order {np.median(R[m,1]):.3%} | quadratic model error {np.median(R[m,3]):.3%} | "
          f"days where order > 3x model error: {np.mean(R[m,1] > 3 * R[m,3]):.0%}")
print(f"Spearman(order effect, mean consecutive crossing) = "
      f"{__import__('scipy.stats', fromlist=['spearmanr']).spearmanr(R[:,1], R[:,4])[0]:+.3f}")
