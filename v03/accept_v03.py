"""Teich v0.3 pre-birth gate — implements V03_SPEC_part1.md (frozen, sha256 eb2d4721…a40ac0) and
G5_PREDICTION.md (sha256 30e0980c…43f78), both anchored in the teich-02 seat chain before any run.

    python3 accept_v03.py --smoke      design seeds 100-107, short gaps: proves the harness, NOT a result
    python3 accept_v03.py              the scored run: seeds 900-947, ONE look

Arms: A = genome (integer ledger), B = leaky store (tau = 2e4, toward birth), C = no store.
"""
from __future__ import annotations

import argparse
import ast
import inspect
import json
import math
import textwrap
import time
from pathlib import Path

import numpy as np

import genome_v03 as G

HERE = Path(__file__).resolve().parent
OUT = HERE / "out_v03"; OUT.mkdir(exist_ok=True)


# ---------------------------------------------------------------- statistics (as in v0.2)
def auc(pairs):
    return float(np.mean([(a > b) + 0.5 * (a == b) for a, b in pairs]))


def D(pairs):
    return 2 * abs(auc(pairs) - 0.5)


def boot(stat, data, n_boot=4000, seed=0):
    rng = np.random.RandomState(seed); data = list(data)
    vals = [stat([data[i] for i in rng.randint(0, len(data), len(data))]) for _ in range(n_boot)]
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def x0_for(seed, n=1):
    rng = np.random.default_rng(seed)
    a = float(G.alpha_of(G.K_BIRTH))
    return rng.uniform(a - 1, a, n)


# ---------------------------------------------------------------- G1 / G3: persistence over silent gaps
def g1_g3(seeds, gaps, W, warm=200):
    n = len(seeds)
    x0 = np.concatenate([x0_for(s) for s in seeds])
    arms = ("A", "B", "C")
    # rows: arm-major, then sign (+ then -), then seed
    x = np.tile(x0, 2 * len(arms))
    nrow = x.size
    arm_of = np.repeat(np.arange(len(arms)), 2 * n)
    sign_of = np.tile(np.repeat([1, -1], n), len(arms))
    led = G.Ledger.born(nrow)                         # used by arm A rows
    kf = np.full(nrow, float(G.K_BIRTH))              # used by arm B rows
    rowsA, rowsB = arm_of == 0, arm_of == 1

    def a_now():
        k = np.full(nrow, float(G.K_BIRTH))
        k[rowsA] = led.k[rowsA]
        k[rowsB] = kf[rowsB]
        return G.alpha_of(k)

    for _ in range(warm):
        x = G.step(x, a_now())
    # the one event: +1 / -1 for arms A and B (C has no store and ignores it)
    led.event(np.where(rowsA, sign_of, 0), tick=warm, why="G1 event")
    kf = np.where(rowsB, kf + sign_of, kf)
    acc = {g: np.zeros(nrow) for g in gaps}
    a = a_now()
    for t in range(max(gaps) + W):
        if rowsB.any():
            kf = np.where(rowsB, G.K_BIRTH + (kf - G.K_BIRTH) * (1 - 1 / G.Engine.TAU_LEAK), kf)
            a = a_now()
        neg = G.observe(x)["neg"]
        for g in gaps:
            if g <= t < g + W:
                acc[g] += neg
        x = G.step(x, a)
    out = {}
    for ai, arm in enumerate(arms):
        out[arm] = {}
        for g in gaps:
            m = acc[g] / W
            plus = m[(arm_of == ai) & (sign_of == 1)]; minus = m[(arm_of == ai) & (sign_of == -1)]
            pairs = list(zip(plus, minus))
            lo, hi = boot(D, pairs)
            gap_mean = float(np.mean(np.abs(plus - minus)))
            out[arm][g] = dict(D=round(D(pairs), 4), ci=[round(lo, 4), round(hi, 4)],
                               mean_abs_gap=round(gap_mean, 5), pairs=pairs)
    return out


def g3_slope(resA, gaps):
    """Slope of (D x mean_abs_gap) against log10(gap), bootstrap over seeds."""
    lg = np.log10(gaps)
    def slope(idx):
        ys = []
        for g in gaps:
            pr = [resA[g]["pairs"][i] for i in idx]
            ys.append(D(pr) * float(np.mean([abs(a - b) for a, b in pr])))
        return float(np.polyfit(lg, ys, 1)[0])
    n = len(resA[gaps[0]]["pairs"]); rng = np.random.RandomState(1)
    point = slope(list(range(n)))
    bs = [slope(list(rng.randint(0, n, n))) for _ in range(2000)]
    return point, (float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)))


# ---------------------------------------------------------------- G2: consequence of every adjacent pair
def g2(seeds, W, warm=200):
    x0 = np.concatenate([x0_for(s) for s in seeds])
    n = len(seeds)
    x = np.tile(x0, G.N_STATES)
    led = G.Ledger.born(x.size)
    target = np.repeat(np.arange(G.N_STATES), n)
    while np.any(led.k != target):                       # reach each state through lawful events
        led.event(np.sign(target - led.k), tick=0, why="G2 setup")
    a = G.alpha_of(led.k)
    acc = np.zeros(x.size)
    for t in range(warm + W):
        if t >= warm:
            acc += G.observe(x)["neg"]
        x = G.step(x, a)
    m = (acc / W).reshape(G.N_STATES, n)
    gaps = []
    for k in range(G.N_STATES - 1):
        d = m[k] - m[k + 1]                               # P(x<0) falls as alpha rises
        lo, hi = boot(lambda v: float(np.mean(v)), d)
        gaps.append(dict(pair=[k, k + 1], mean=round(float(d.mean()), 5), ci=[round(lo, 5), round(hi, 5)]))
    return gaps


# ---------------------------------------------------------------- G4: certified chaos at every state
def g4(n_orb, n_iter, burn=200, seed=4):
    rows = []
    for k in range(G.N_STATES):
        a = float(G.alpha_of(k))
        x = np.random.default_rng(seed + k).uniform(a - 1, a, n_orb)
        s = 0.0
        for t in range(burn + n_iter):
            if t >= burn:
                s += float(np.sum(-2.0 * np.log(np.abs(x))))
            x = G.step(x, np.full(n_orb, a))
        lam = s / (n_orb * n_iter)
        rows.append(dict(k=k, alpha=round(a, 5), lam=round(lam, 6),
                         diff=round(lam - G.LAMBDA_PLATEAU, 6)))
    return rows


# ---------------------------------------------------------------- G5: interference
def g5(seeds, Ks, W, warm=200):
    out = {}
    for K in Ks:
        x0 = np.concatenate([x0_for(s) for s in seeds]); n = len(seeds)
        x = np.tile(x0, 2)
        led = G.Ledger.born(x.size)
        for _ in range(warm):
            x = G.step(x, G.alpha_of(led.k))
        led.event(np.repeat([1, -1], n), tick=warm, why="G5 first event")
        rng = np.random.default_rng(5000 + K)
        seq = rng.choice([1, -1], size=(K, n))            # same random sequence for both members
        for j in range(K):
            led.event(np.tile(seq[j], 2), tick=warm, why="G5 interference")
        a = G.alpha_of(led.k); acc = np.zeros(x.size)
        for t in range(200 + W):
            if t >= 200:
                acc += G.observe(x)["neg"]
            x = G.step(x, a)
        m = acc / W
        pairs = list(zip(m[:n], m[n:]))
        out[K] = dict(D=round(D(pairs), 4), merged_frac=round(float(np.mean(led.k[:n] == led.k[n:])), 4))
    return out


# ---------------------------------------------------------------- G6: condition N
def g6():
    sig = list(inspect.signature(G.observe).parameters)
    src = textwrap.dedent(inspect.getsource(G.observe))
    names = {n.id for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Name)}
    forbidden = {"k", "ledger", "led", "kf", "word", "W", "concepts", "phi", "Ledger", "alpha_of"}
    static_ok = sig == ["x"] and not (names & forbidden)
    rng = np.random.default_rng(66)
    x = rng.uniform(-0.5, 0.5, 1000)
    ref = G.observe(x)
    dyn_ok = True
    for k in range(G.N_STATES):                           # memory altered, x frozen
        led = G.Ledger(np.full(x.size, k)); _ = led
        o = G.observe(x)
        dyn_ok &= all(np.array_equal(o[key], ref[key]) for key in ref)
    return dict(static=bool(static_ok), signature=sig, names_used=sorted(names), dynamic=bool(dyn_ok))


# ---------------------------------------------------------------- L1: language exactness
def l1(n_words=10000, seed=7):
    rng = np.random.default_rng(seed)
    concepts = []
    while len(concepts) < 24:
        p, q = int(rng.integers(-7, 8)), int(rng.integers(1, 8))
        if math.gcd(abs(p), q) == 1 and (p, q) not in concepts:
            concepts.append((p, q))

    def indep_twist(v):                                   # independent derivation: w -> w + det(v,w) v
        p, q = v
        cols = []
        for w in ((1, 0), (0, 1)):
            d = p * w[1] - q * w[0]
            cols.append((w[0] + d * p, w[1] + d * q))
        return ((cols[0][0], cols[1][0]), (cols[0][1], cols[1][1]))

    def mul(A, B):
        return ((A[0][0] * B[0][0] + A[0][1] * B[1][0], A[0][0] * B[0][1] + A[0][1] * B[1][1]),
                (A[1][0] * B[0][0] + A[1][1] * B[1][0], A[1][0] * B[0][1] + A[1][1] * B[1][1]))

    def inv(A):
        return ((A[1][1], -A[0][1]), (-A[1][0], A[0][0]))

    bad = 0; types = {"periodic": 0, "twist": 0, "anosov": 0}
    for _ in range(n_words):
        word = [(int(rng.integers(0, len(concepts))), int(rng.integers(-3, 4)))
                for _ in range(int(rng.integers(1, 7)))]
        M = G.word_matrix(word, concepts)
        c = G.classify(M)
        R = ((1, 0), (0, 1))
        for ci, n in word:
            T = indep_twist(concepts[ci]); T = T if n >= 0 else inv(T)
            for _ in range(abs(n)):
                R = mul(R, T)
        same_matrix = all(int(M[i, j]) == R[i][j] for i in range(2) for j in range(2))
        det_ok = R[0][0] * R[1][1] - R[0][1] * R[1][0] == 1
        tr = R[0][0] + R[1][1]
        if abs(tr) > 2:
            # exact: larger root of rho^2 - |tr| rho + 1 = 0, at 50 digits (float eigvals are ill-conditioned here)
            import mpmath
            mpmath.mp.dps = 50
            rho = (abs(tr) + mpmath.sqrt(tr * tr - 4)) / 2
            ok_type = (c["type"] == "anosov" and abs(rho * rho - abs(tr) * rho + 1) / (rho * rho) < mpmath.mpf(10) ** -40
                       and abs(c["intensity"] - float(mpmath.log(rho))) <= 1e-12 * max(1.0, c["intensity"]))
        elif abs(tr) == 2:
            ok_type = c["type"] == "twist"
        else:
            ok_type = c["type"] == "periodic"
        if not (same_matrix and det_ok and ok_type):
            bad += 1
        types[c["type"]] += 1
    return dict(words=n_words, mismatches=bad, types=types)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--rehearsal", action="store_true",
                    help="full scored configuration on DESIGN seeds 200-247 (power check, not a result)")
    args = ap.parse_args()
    if args.rehearsal:
        seeds, gaps, W = list(range(200, 248)), [1000, 10000, 100000, 1000000], 8000
        g4a, Ks, tag = (20000, 500), [1, 4, 16, 64], "rehearsal"
    elif args.smoke:
        seeds, gaps, W = list(range(100, 108)), [100, 1000], 2000
        g4a, Ks, tag = (2000, 200), [1, 4, 16], "smoke"
    else:
        seeds, gaps, W = list(range(900, 948)), [1000, 10000, 100000, 1000000], 8000
        g4a, Ks, tag = (20000, 500), [1, 4, 16, 64], "scored"
    t0 = time.time(); v = {"mode": tag, "spec_sha256": "eb2d4721d0de8dd48e5ae921519c3de7faf1ba42c58f0bcfdd20e21eeca40ac0",
                           "g5_prediction_sha256": "30e0980c1edfe93c9d5194add90a7e721dfa4fc3cce718b6de05cd6d5a643f78"}

    print(f"[{tag}] G6 condition N ...", flush=True); v["G6"] = g6(); print(v["G6"], flush=True)
    print(f"[{tag}] L1 language ...", flush=True); v["L1"] = l1(); print(v["L1"], flush=True)
    print(f"[{tag}] G4 chaos at every state ...", flush=True); v["G4"] = g4(*g4a)
    for r in v["G4"]: print("   ", r, flush=True)
    print(f"[{tag}] G2 consequence ...", flush=True); v["G2"] = g2(seeds, W)
    for r in v["G2"]: print("   ", r, flush=True)
    print(f"[{tag}] G5 interference ...", flush=True); v["G5"] = g5(seeds, Ks, W)
    print("   ", v["G5"], flush=True)
    print(f"[{tag}] G1 persistence (gaps {gaps}) ... ({time.time()-t0:.0f}s so far)", flush=True)
    r1 = g1_g3(seeds, gaps, W)
    v["G3_slope"], v["G3_ci"] = g3_slope(r1["A"], gaps)
    v["G1"] = {arm: {g: {k: val for k, val in d.items() if k != "pairs"} for g, d in r1[arm].items()} for arm in r1}
    for arm in v["G1"]:
        print(f"    {arm}: " + "  ".join(f"{g}: D={d['D']} ci={d['ci']}" for g, d in v["G1"][arm].items()), flush=True)

    # ---- verdict against the frozen bars
    pred = {1: 1.0, 4: 0.875, 16: 0.3267, 64: 0.0029}
    band = lambda p: 1.96 * math.sqrt(p * (1 - p) / len(seeds)) + 0.03
    passes = {
        "G1": all(d["D"] >= 0.80 and d["ci"][0] > 0.60 for d in v["G1"]["A"].values()),
        "G2": all(r["ci"][0] >= 0.020 for r in v["G2"]),
        "G3": v["G3_ci"][0] <= 0 <= v["G3_ci"][1],
        "G4": all(abs(r["diff"]) <= 0.002 for r in v["G4"]),
        "G5": all(abs(v["G5"][K]["D"] - pred[K]) <= band(pred[K]) for K in Ks),
        "G6": v["G6"]["static"] and v["G6"]["dynamic"],
        "L1": v["L1"]["mismatches"] == 0,
    }
    lastB = v["G1"]["B"][max(gaps)]["D"]; lastC = v["G1"]["C"][max(gaps)]["D"]
    passes["controls_as_predicted"] = (lastB < 0.20 and lastC < 0.20) if not args.smoke else None
    hard = passes["G4"] and passes["G6"] and passes["L1"]
    core = all(passes[k] for k in ("G1", "G2", "G3", "G4", "G6", "L1"))
    v["passes"] = passes
    v["gate"] = bool(hard and core and (passes["controls_as_predicted"] is not False))
    v["elapsed_s"] = round(time.time() - t0, 1)
    out = OUT / f"accept_v03_{tag}.json"
    out.write_text(json.dumps(v, indent=1, default=str))
    print(json.dumps(passes, indent=1)); print(f"GATE ({tag}): {'PASS' if v['gate'] else 'FAIL'}  -> {out}  [{v['elapsed_s']}s]")


if __name__ == "__main__":
    main()
