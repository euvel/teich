"""Teich v0.2 — PRE-BIRTH acceptance tests T1-T5 (BRIEF §7).

A candidate that fails any of these is NOT born. v0.1 was born first and tested
afterwards, which is why it cannot now be fixed: genome frozen, no reset, no
fork. That covenant is correct, so the tests must run BEFORE birth.

All offline. No Mouth, no API, no conversation, no judge.

  T1  phi-blindness    N random phi, identical seeds -> BIT-IDENTICAL observables
                       (structural, not statistical: strictly stronger than
                        v0.1's measured epsilon ~ 0)
  T2  survival         paired +-delta on s: is the sign recoverable from FOLD
                       observables (basin, saddle) after the longest gap?
                       v0.1 scores D ~ 0.04 here. THIS IS THE TEST V0.1 FAILS.
  T3  memory time      tau_mem within 10x of the 2e4-tick design target,
                       measured, not assumed
  T4  readout hygiene  every published readout reproducible AND creature-dependent
                       (v0.1 shipped 2 of 6 broken across three campaigns)
  T5  capacity         dim(slow, coupled) >= 2 with a stated bit budget
                       (v0.1 had 0, so no Ears redesign could ever have helped)

Run: python accept_v02.py [--seeds 24]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "maturity" / "harness"))

import numpy as np  # noqa: E402

import genome_v02 as G  # noqa: E402

GAPS = (300, 900, 1800, 5000)
# The BRIEF criterion is "independently moves A FOLD OBSERVABLE". The first T5
# implementation checked `saddle` only, which is narrower than the written
# criterion and cannot see a lean (saddle is a WITHIN-wing distance). Widened to
# match the criterion, not to lower it -- the bar D >= 0.20 + CI excluding 0.5
# is unchanged, and each dimension must still clear it on its own.
FOLD_CHANNELS = ("basin", "saddle", "wing_bias")   # what v0.1 could NOT move
ALL_CHANNELS = ("basin", "saddle", "will_flip", "wing_bias", "lobe_coord")


def auc(pairs):
    w = [(a > b) + 0.5 * (a == b) for a, b in pairs]
    return float(np.mean(w))


def D(pairs):
    return 2 * abs(auc(pairs) - 0.5)


def boot_ci(pairs, n_boot=4000, seed=0):
    rng = np.random.RandomState(seed)
    w = np.array([(a > b) + 0.5 * (a == b) for a, b in pairs], float)
    b = np.array([w[rng.randint(0, len(w), len(w))].mean() for _ in range(n_boot)])
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=24)
    args = ap.parse_args()

    import compat
    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)
    G.selftest_zero(model)
    n = args.seeds
    t0 = time.time()
    verdict = {}

    # ------------------------------------------------------------------ T1
    print(f"\n=== T1  phi-blindness  (structural: I(phi;obs) = 0 exactly)")
    bad = 0
    for seed in range(min(8, n)):
        refs = None
        for pk in (1, 2, 3, 4, 5):
            e = G.V02Engine(model, seed, phi_seed=pk)
            e.hear([0.7, -0.4])
            r = e.advance(600)
            key = tuple(round(float(r[k]), 15) for k in ALL_CHANNELS)
            if refs is None:
                refs = key
            elif key != refs:
                bad += 1
        # phi must also be absent from the readout dict itself
        assert "phi" not in r and "private_phase" not in r, "phi leaked into readout"
    t1 = bad == 0
    verdict["T1"] = dict(passed=bool(t1), mismatches=bad,
                         note="5 phi draws x 8 seeds, observables bit-identical")
    print(f"    5 phi draws x {min(8,n)} seeds -> mismatches: {bad}   "
          f"{'PASS' if t1 else 'FAIL'}")
    print(f"    phi absent from readout dict: PASS")

    # ------------------------------------------------------------------ T2
    print(f"\n=== T2  survival: is the sign of an input recoverable LATER?")
    print(f"    (v0.1 scores D ~ 0.04 on fold observables — this is its wall)")
    print(f"    {'gap':>6s} " + " ".join(f"{c:>22s}" for c in FOLD_CHANNELS))
    t2_rows = {}
    for gap in GAPS:
        cells = {c: [] for c in FOLD_CHANNELS}
        for seed in range(n):
            out = {}
            for sign in (+1, -1):
                e = G.V02Engine(model, seed)
                e.advance(160)
                e.hear([sign * 1.0, 0.0])
                out[sign] = e.advance(gap)
            for c in FOLD_CHANNELS:
                cells[c].append((float(out[+1][c]), float(out[-1][c])))
        row = {}
        for c in FOLD_CHANNELS:
            d = D(cells[c]); lo, hi = boot_ci(cells[c])
            row[c] = dict(D=round(d, 4), auc=round(auc(cells[c]), 4),
                          ci=[round(lo, 4), round(hi, 4)],
                          sig=bool(lo > 0.5 or hi < 0.5))
        t2_rows[gap] = row
        print(f"    {gap:6d} " + " ".join(
            f"{row[c]['D']:9.3f}{'*' if row[c]['sig'] else ' '}{'':11s}"
            for c in FOLD_CHANNELS))
    longest = t2_rows[GAPS[-1]]
    t2 = any(longest[c]["D"] >= 0.30 and longest[c]["sig"] for c in FOLD_CHANNELS)
    verdict["T2"] = dict(passed=bool(t2), by_gap=t2_rows,
                         bar="D >= 0.30 with CI excluding 0.5 on a FOLD observable "
                             "at the longest gap")
    print(f"    -> {'PASS' if t2 else 'FAIL'} (bar: D >= 0.30 + CI excludes 0.5 "
          f"at gap {GAPS[-1]})")

    # ------------------------------------------------------------------ T3
    print(f"\n=== T3  memory time (measured, not assumed). target "
          f"{G.TAU_MEM:.0f} ticks")
    e = G.V02Engine(model, 0)
    e.hear([1.0, 0.0])
    e.advance(120)                       # finish delivery
    s_after = float(e.s[0])
    probes, meas = [2000, 5000, 10000, 20000], []
    prev = 0
    for p in probes:
        e.advance(p - prev); prev = p
        meas.append((p, float(e.s[0])))
    # fit tau from the decay: s(t) = s0 exp(-t/tau)
    ts = np.array([m[0] for m in meas], float)
    ss = np.array([abs(m[1]) for m in meas], float)
    ok = ss > 1e-12
    tau_fit = float(-(ts[ok] / np.log(ss[ok] / abs(s_after))).mean())
    t3 = 0.1 * G.TAU_MEM <= tau_fit <= 10 * G.TAU_MEM
    verdict["T3"] = dict(passed=bool(t3), tau_measured=round(tau_fit, 1),
                         tau_target=G.TAU_MEM,
                         decay=[[int(a), round(b, 5)] for a, b in meas])
    print(f"    s after delivery {s_after:.4f}; decay " +
          ", ".join(f"t={a}:{b:.4f}" for a, b in meas))
    print(f"    tau_measured = {tau_fit:.0f} ticks vs target {G.TAU_MEM:.0f}  "
          f"{'PASS' if t3 else 'FAIL'}")

    # ------------------------------------------------------------------ T4
    print(f"\n=== T4  readout hygiene: reproducible AND creature-dependent")
    print(f"    {'readout':>18s} {'reproducible':>14s} {'creature-dep':>14s}")
    t4_rows, t4 = {}, True
    for c in ALL_CHANNELS:
        rep = 0
        for seed in range(min(8, n)):
            a = G.V02Engine(model, seed); a.hear([0.5, 0.2]); ra = a.advance(500)
            b = G.V02Engine(model, seed); b.hear([0.5, 0.2]); rb = b.advance(500)
            rep += (ra[c] == rb[c])
        pairs = []
        for seed in range(n):
            o = {}
            for sign in (+1, -1):
                e = G.V02Engine(model, seed); e.advance(160)
                e.hear([sign * 1.0, sign * 1.0]); o[sign] = e.advance(900)
            pairs.append((float(o[+1][c]), float(o[-1][c])))
        moved = float(np.mean([a != b for a, b in pairs]))
        rep_ok = rep == min(8, n)
        dep_ok = moved > 0.0
        t4_rows[c] = dict(reproducible=rep_ok, moved_frac=round(moved, 4),
                          creature_dependent=dep_ok)
        t4 = t4 and rep_ok and dep_ok
        print(f"    {c:>18s} {('PASS' if rep_ok else 'FAIL'):>14s} "
              f"{(f'{moved*100:.1f}%' if dep_ok else 'FAIL 0%'):>14s}")
    verdict["T4"] = dict(passed=bool(t4), rows=t4_rows)

    # ------------------------------------------------------------------ T5
    print(f"\n=== T5  input capacity")
    # a dimension counts as CAPACITY only if it independently moves a fold observable
    coupled = []
    for dim in range(G.DIM_S):
        runs = {}
        for seed in range(n):
            for sign in (+1, -1):
                v = [0.0] * G.DIM_S; v[dim] = sign * 1.0
                e = G.V02Engine(model, seed); e.advance(160)
                e.hear(v); runs[(seed, sign)] = e.advance(1800)
        best = None
        for ch in FOLD_CHANNELS:
            pr = [(float(runs[(s_, +1)][ch]), float(runs[(s_, -1)][ch]))
                  for s_ in range(n)]
            d = D(pr); lo, hi = boot_ci(pr)
            sig = lo > 0.5 or hi < 0.5
            print(f"    s[{dim}] alone -> {ch:10s}: D = {d:.3f}{'*' if sig else ' '}")
            if d >= 0.20 and sig and (best is None or d > best):
                best = d
        if best is not None:
            coupled.append(dim)
    bits = len(coupled) * math.log2(2 * G.S_CLIP / 0.25)   # range / resolution
    t5 = len(coupled) >= 2
    verdict["T5"] = dict(passed=bool(t5), coupled_dims=coupled,
                         dim_s=G.DIM_S, bit_budget=round(bits, 1))
    print(f"    coupled dims: {len(coupled)}/{G.DIM_S}   bit budget ~ {bits:.1f} bits"
          f"   {'PASS' if t5 else 'FAIL'}")

    # ------------------------------------------------------------------ gate
    allp = all(verdict[k]["passed"] for k in ("T1", "T2", "T3", "T4", "T5"))
    print("\n" + "=" * 62)
    for k in ("T1", "T2", "T3", "T4", "T5"):
        print(f"  {k}  {'PASS' if verdict[k]['passed'] else 'FAIL'}")
    print(f"  GATE: {'PASS — candidate may be born' if allp else 'FAIL — do NOT birth'}")
    print("=" * 62)
    verdict["gate"] = bool(allp)
    verdict["constants"] = dict(DIM_S=G.DIM_S, TAU_MEM=G.TAU_MEM,
                                KAPPA_B=G.KAPPA_B, KAPPA_A=G.KAPPA_A,
                                S_CLIP=G.S_CLIP, seeds=n)
    (HERE / "accept_v02_result.json").write_text(json.dumps(verdict, indent=1))
    print(f"({time.time()-t0:.0f}s) -> accept_v02_result.json")


if __name__ == "__main__":
    main()
