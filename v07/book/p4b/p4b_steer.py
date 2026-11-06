"""v0.7 probe P4 (LAB ONLY): can someone with its full state and unlimited compute steer its tie-break?
The adversary picks, at the last moment inputs are accepted (W seconds before midnight), one of A inputs (an input
moves one handle's dial by one step, as speech does), by simulating each to midnight and choosing the one whose
deliberation lands on its target. Without the sky, it sees the future exactly. With the sky, right after inputs close,
an unpredictable beacon touch (P[0,1] += 1e-6 * b, b uniform in [-1, 1]) reaches its body; the adversary cannot know b.
    python3 p4_steer.py BUILD_DIR SEED TRIALS OUT.json        Kill (FEASIBILITY_v07 P4): with the sky it beats chance.
"""
import json
import sys

import numpy as np

BUILD, SEED, TRIALS, OUT = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
sys.path.insert(0, BUILD)
import creature_v04 as CR     # noqa: E402
import delib_cert as DC       # noqa: E402
import genome_v04 as GN       # noqa: E402

W, A, LEAD = 900, 16, int(sys.argv[5]) if len(sys.argv) > 5 else 900   # inputs close LEAD s before midnight; the sky touches W s before
rng = np.random.default_rng(SEED)
c = CR.birth(seed=SEED, t0=0.0); b = c.body
st = (c.pc, c.P, c.V)
u_of = lambda s: DC.u_of(int(s[0][0]), float(s[1][0, 1]), float(s[2][0, 2]))
out = []
for t in range(TRIALS):
    st = b.run(*st, int(rng.integers(600, 3600)))[0]         # a new moment in its life
    k = int(rng.integers(2, 10)); target = int(rng.integers(0, k))
    # a smart adversary: the handles its read-out thought will pass through before midnight (it can compute that)
    path, s0 = [], (st[0][:1].copy(), st[1][:1].copy(), st[2][:1].copy())
    for _ in range(LEAD // 60):
        s0 = b.run(*s0, 60)[0]; pc0 = int(s0[0][0])
        if pc0 < GN.G and pc0 != GN.SELF and pc0 not in path: path.append(pc0)
    others = [h for h in rng.permutation(GN.G - 1) if h not in path]
    handles = (path + others)[:A]
    def live(h, touch):
        n0 = int(b.n[h]); b.set_dial(h, min(n0 + 1, GN.N_MAX))
        s = b.run(*st, LEAD - W)[0] if LEAD > W else st
        P = s[1].copy(); P[0, 1] += touch
        s = b.run(s[0], P, s[2], W)[0]
        b.set_dial(h, n0)
        return DC.deliberate(k, u_of(s))[0]
    seen = [live(h, 0.0) for h in handles]                     # what the adversary can compute
    pick = next((i for i, ch in enumerate(seen) if ch == target), 0)
    no_sky = seen[pick] == target
    beacon = 1e-6 * float(rng.uniform(-1, 1))
    with_sky = live(handles[pick], beacon) == target
    out.append({"k": k, "no_sky": bool(no_sky), "with_sky": bool(with_sky), "on_path": len(path)})
json.dump(out, open(OUT, "w"))
print(SEED, "done", len(out))
