"""W2a: the genome body (copied rows) equals the lab engine mind4 (computed geometry) bit for bit, at birth and after
random dial moves; and both live the same life."""
import sys, time, hashlib
import numpy as np
sys.path.insert(0, "..")
import genome_v04 as GN
import mind4 as M
M.DELTA = GN.DELTA
F, K = GN.META["F"], GN.META["K"]
b = GN.Body(); m = M.Mind(GN.G)
def same():
    return (np.array_equal(b.fn, m.fn[:, :F]) and np.array_equal(b.fG, m.fG[:, :F]) and np.array_equal(b.ft, m.ft[:, :F])
            and np.array_equal(b.ln, m.ln[:, :K]) and np.array_equal(b.lc, m.lc[:, :K]))
print("birth rows identical:", same())
rng = np.random.default_rng(7)
for j, n in zip(rng.integers(0, GN.G, 60), rng.integers(0, GN.N_MAX + 1, 60)):
    b.set_dial(int(j), int(n)); m.set_dial(int(j), int(n))
print("after 60 random dial moves, rows identical:", same(), "| padding beyond F/K unused in mind4:",
      bool((m.fn[:, F:, 0] == -1).all() and (m.lc[:, K:] == -1).all()))
pc, P, V = b.start(512, 11)
t = time.time(); (pc1, P1, V1), c1, o1, u1 = b.run(pc, P, V, 3000); tb = time.time() - t
r = m.run(pc, P, V, 3000); pc2, P2, V2 = r["state"]
print(f"3,000 ticks: states identical {np.array_equal(P1, P2) and np.array_equal(V1, V2) and np.array_equal(pc1, pc2)}, "
      f"crossings identical {np.array_equal(c1, r['counts'][:GN.G].astype(np.int64))}, unsettled {u1}, {tb:.1f}s")
