"""Step 0b — is the mark DIRECTIONAL, and is its direction set by WHAT was said?

diagnose_acts.py found paired charged-vs-neutral divergence ABOVE the
cross-seed decorrelation ceiling (basin 62.5% vs 42.2%). Divergence cannot
exceed the decorrelation rate by scrambling — scrambling IS that rate — so the
excess implies a consistent push rather than noise. That inference is indirect
(it leans on a cross-seed null) and ~2 sigma. This tests it directly.

Two questions, in increasing order of what they would license:

  D1 DIRECTIONAL?  Does the charged pivot move the core the SAME WAY across
                   seeds? Measured as the signed paired delta
                   (charged - neutral) in saddle_proximity at the probe.
                   Continuous, paired, so far more powerful than any binary
                   channel. Null: mean delta = 0.
  D2 CONTENT?      Does the SIGN of the delta track the SIGN of what was said?
                   The CHARGED bank is Ears-calibrated with known valence
                   (proud +0.262, gift +0.156, failing -0.152, STOP -0.163;
                   scripts_tint selects by seed % 4). If positive and negative
                   sentences push the core in opposite directions, the coupling
                   carries WHAT was said, not merely THAT something was.

D1 without D2 = the core is pushed, but any strong sentence pushes it the same
way (an arousal/energy effect, content-blind). D2 is the one that matters, and
it is the first test in this program that could show content-bearing coupling
without a Mouth, a lexicon, or a judge anywhere in the path.

EXPLORATORY. Retired seeds (0-47), no pre-registration, no gate. A positive
result here buys the right to pre-register a real screen; it decides nothing.

Run: python diagnose_direction.py [--seeds 48]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import numpy as np  # noqa: E402

import scripts_tint as st  # noqa: E402
from diagnose_acts import act_run  # noqa: E402

# Ears-measured valence of the CHARGED bank (scripts_tint.py header, calibrated
# 2026-07-26). Index = position in st.CHARGED = seed % 4.
VALENCE = np.array([+0.262, -0.152, -0.163, +0.156])
AROUSAL = np.array([+0.148, +0.043, -0.028, -0.092])


def boot_ci(x, n_boot=10000, seed=0, alpha=0.05):
    rng = np.random.RandomState(seed)
    x = np.asarray(x, float)
    b = np.array([x[rng.randint(0, len(x), len(x))].mean() for _ in range(n_boot)])
    return float(x.mean()), (float(np.percentile(b, 100 * alpha / 2)),
                             float(np.percentile(b, 100 * (1 - alpha / 2))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=48)
    args = ap.parse_args()

    import compat
    import arms as A
    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)

    n, t0 = args.seeds, time.time()
    rows = []
    for seed in range(n):
        sc = st.build_ic2(seed, "charged")
        sn = st.build_ic2(seed, "neutral")
        rc = act_run(A.A0Intact(model), sc)
        rn = act_run(A.A0Intact(model), sn)
        pc, pn = rc[-1], rn[-1]
        k = seed % len(st.CHARGED)
        rows.append(dict(
            seed=seed, gap=sc["gap"], bank=k,
            valence=float(VALENCE[k]), arousal=float(AROUSAL[k]),
            d_saddle=float(pc["saddle_proximity"] - pn["saddle_proximity"]),
            d_lobe=float(pc["lobe_coord"] - pn["lobe_coord"]),
            basin_c=int(pc["basin"]), basin_n=int(pn["basin"]),
            nsw_c=int(pc["n_switches"]), nsw_n=int(pn["n_switches"])))
    (HERE / "out_direction.json").write_text(json.dumps(rows, indent=1))

    d = np.array([r["d_saddle"] for r in rows])
    v = np.array([r["valence"] for r in rows])
    a = np.array([r["arousal"] for r in rows])

    # ------------------------------------------------------------------ D1
    print(f"=== D1  is the mark directional?  (signed paired delta, n={n})")
    m, (lo, hi) = boot_ci(d)
    print(f"    d_saddle (charged - neutral): mean {m:+.4f}  95% CI [{lo:+.4f}, {hi:+.4f}]")
    print(f"    sd {d.std(ddof=1):.4f}   mean|d| {np.abs(d).mean():.4f}   "
          f"P(d>0) {float((d > 0).mean()):.3f}")
    print(f"    -> {'DIRECTIONAL' if lo > 0 or hi < 0 else 'no net direction'} "
          f"(CI {'excludes' if lo > 0 or hi < 0 else 'includes'} 0)")

    # ------------------------------------------------------------------ D2
    print(f"\n=== D2  is the direction set by WHAT was said?")
    pos, neg = d[v > 0], d[v < 0]
    mp, (plo, phi_) = boot_ci(pos)
    mn, (nlo, nhi) = boot_ci(neg)
    print(f"    positive-valence sentences (n={len(pos)}): mean d {mp:+.4f} "
          f"[{plo:+.4f}, {phi_:+.4f}]")
    print(f"    negative-valence sentences (n={len(neg)}): mean d {mn:+.4f} "
          f"[{nlo:+.4f}, {nhi:+.4f}]")
    diff, (dlo, dhi) = boot_ci(np.concatenate([pos, -neg])) if len(pos) and len(neg) \
        else (float("nan"), (float("nan"), float("nan")))
    print(f"    separation (pos - neg): {mp - mn:+.4f}")
    r_v = float(np.corrcoef(v, d)[0, 1])
    r_a = float(np.corrcoef(a, d)[0, 1])
    print(f"    r(valence, d_saddle) = {r_v:+.4f}    "
          f"r(arousal, d_saddle) = {r_a:+.4f}")
    print(f"    -> {'CONTENT-BEARING' if abs(r_v) > 0.3 else 'no valence signal'} "
          f"at |r|>0.3")

    # per-sentence breakdown: 4 banks x 12 seeds, the honest resolution here
    print(f"\n    per-sentence (n={n//4} each):")
    for k, txt in enumerate(st.CHARGED):
        dk = np.array([r["d_saddle"] for r in rows if r["bank"] == k])
        print(f"      v={VALENCE[k]:+.3f} a={AROUSAL[k]:+.3f}  "
              f"mean d {dk.mean():+.4f}  sd {dk.std(ddof=1):.4f}   {txt[:44]!r}")

    # ------------------------------------------------------------- basin push
    bc = np.array([r["basin_c"] for r in rows])
    bn = np.array([r["basin_n"] for r in rows])
    print(f"\n=== basin marginals (the 62.5%/42.2% finding, tested directly)")
    print(f"    P(basin=+1) charged {float((bc > 0).mean()):.3f}   "
          f"neutral {float((bn > 0).mean()):.3f}")
    disc = bc != bn
    if disc.sum():
        up = int(((bc > 0) & disc).sum()); dn = int(((bc < 0) & disc).sum())
        print(f"    discordant pairs {int(disc.sum())}/{n}: "
              f"charged went +1 in {up}, -1 in {dn}  (McNemar-style; "
              f"{'ASYMMETRIC' if abs(up-dn) > np.sqrt(up+dn) else 'symmetric'})")
    print(f"\n({time.time()-t0:.0f}s)  raw -> out_direction.json")


if __name__ == "__main__":
    main()
