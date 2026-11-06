"""Teich v0.7 gate K1 (PREREG_V07 §2): can someone holding its full state, with unlimited compute, steer a tie?
Per trial, at a moment of a lab life, "midnight" is LEAD ticks ahead. The adversary chooses one of A mentions (a
mention's effect on its body: one dial step, body.set_dial) to make the deliberation of virtual k land on a target.
  v0.6 control, adversary A: simulates each input to midnight (no Sky) and picks the first that lands; outcome as seen.
  v0.7, adversary A: the same simulation (it cannot know the beacon); the outcome is lived with the Sky's touch.
  v0.7, adversary B: simulates each input to the touch, then G guessed beacons each to midnight; picks the input with
       the highest estimated probability; the outcome is lived with the true touch.
The true touch: C7.touch with b = sky_v07.b_of(randomness of round BASE + trial, trial), SKY_LEAD ticks before
midnight. Genome functions only: body.run, C7.touch, DC.u_of, DC.deliberate.
    python3 k1_steer_v07.py SEED TRIALS BEACONS.json OUT.json [BASE] [--control-ignores-input]
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np

import creature_v07 as C7
import delib_cert as DC
import genome_v04 as GN
import sky_v07 as SKY

LEAD, A, G = 10800, 16, 8


def u_of(st):
    pc, P, V = st
    return DC.u_of(int(pc[0]), float(P[0, 1]), float(V[0, 2]))


def main(seed, trials, beacons, out, base, ignore):
    rng = np.random.default_rng(seed)
    c = C7.birth(seed=seed, t0=0.0); b = c.body
    st = (c.pc, c.P, c.V)
    res = []; t0 = time.time()
    for t in range(trials):
        st = b.run(*st, int(rng.integers(3600, 6 * 3600)))[0]
        k = int(rng.integers(2, 10)); target = int(rng.integers(0, k))
        # a smart adversary (P4b's): first the handles its read-out thought (particle 0) passes through before midnight
        path, s0 = [], (st[0][:1].copy(), st[1][:1].copy(), st[2][:1].copy())
        for _ in range(LEAD // 60):
            s0 = b.run(*s0, 60)[0]; pc0 = int(s0[0][0])
            if pc0 < GN.G - 1 and pc0 != GN.SELF and pc0 not in path:
                path.append(pc0)
        hs = (path + [int(h) for h in rng.permutation(GN.G - 1) if h not in path])[:A]
        guesses = rng.random(G)
        bc = beacons[str(base + t)]; true_b = SKY.b_of(bc["randomness"], t)

        def live(h, touch_b=None, part=None):
            n0 = int(b.n[h])
            if not ignore:
                b.set_dial(h, min(n0 + 1, GN.N_MAX))
            try:
                if touch_b is None:
                    s = b.run(*st, LEAD)[0]
                else:
                    s = part if part is not None else b.run(*st, LEAD - C7.SKY_LEAD)[0]
                    P, V = C7.touch(s[1], s[2], touch_b)
                    s = b.run(s[0], P, V, C7.SKY_LEAD)[0]
                return DC.deliberate(k, u_of(s))[0]
            finally:
                b.set_dial(h, n0)

        def pre(h):
            n0 = int(b.n[h])
            if not ignore:
                b.set_dial(h, min(n0 + 1, GN.N_MAX))
            try:
                return b.run(*st, LEAD - C7.SKY_LEAD)[0]
            finally:
                b.set_dial(h, n0)
        seen = [live(h) for h in hs]                                  # what A computes (and v0.6's real outcomes)
        pick_a = next((i for i, ch in enumerate(seen) if ch == target), 0)
        v06 = seen[pick_a] == target
        v07_a = live(hs[pick_a], true_b) == target
        est = []
        parts = []
        for h in hs:                                                  # B: to the touch, then G guessed beacons
            s = pre(h); parts.append(s)
            n0 = int(b.n[h])
            if not ignore:
                b.set_dial(h, min(n0 + 1, GN.N_MAX))
            try:
                hits = 0
                for gb in guesses:
                    P, V = C7.touch(s[1], s[2], float(gb))
                    hits += DC.deliberate(k, u_of(b.run(s[0], P, V, C7.SKY_LEAD)[0]))[0] == target
            finally:
                b.set_dial(h, n0)
            est.append(hits / G)
        pick_b = int(np.argmax(est))
        v07_b = live(hs[pick_b], true_b, part=parts[pick_b]) == target
        res.append({"k": k, "target": target, "path_handles": len(path), "distinct_seen": len(set(seen)), "v06_A": bool(v06), "v07_A": bool(v07_a), "v07_B": bool(v07_b),
                    "B_estimate": float(max(est)), "round": base + t})
        json.dump({"seed": seed, "ignore_input": ignore, "trials": res, "seconds": time.time() - t0}, open(out, "w"))
        print(seed, "trial", t, round(time.time() - t0), "s", flush=True)


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    seed, trials, bpath, out = int(a[0]), int(a[1]), a[2], a[3]
    base = int(a[4]) if len(a) > 4 else 6_400_000 + 100 * (seed - 14100)
    main(seed, trials, json.load(open(bpath)), out, base, "--control-ignores-input" in sys.argv)
