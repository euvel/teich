"""Offline verification of the paired causal design — TINT_DESIGN v0.2 §4.

No API, no Mouth: pure core stepping. Answers, from the substrate itself and
BEFORE any pre-registration:

  1. IDENTITY  — a deaf core's charged and neutral runs are bit-identical, so
     its causal delta is exactly 0 (not a hope: a property).
  2. EFFECT    — a hearing core's causal delta is non-zero, and how big it is
     across seeds (this SIZES the |causal_delta| threshold honestly).
  3. SEPARATION— what fraction of seeds have |causal_delta| above candidate
     thresholds, i.e. how often the item has a real answer to give.

Run: python verify_causal.py [--seeds 24]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import numpy as np  # noqa: E402

import scripts_tint as st  # noqa: E402


def run_core(arm, script):
    """Step a core through a script; return the saddle series (no Mouth)."""
    arm.start(script["seed"])
    series = []
    for text, kind in zip(script["turns"], script["kind"]):
        _ro, _ev, _f, meta = arm.step(text, st.ticks_for(kind))
        series.append(float(meta["readout"]["saddle_proximity"])
                      if "readout" in meta else float("nan"))
    return np.array(series)


def causal_delta(series_charged, series_neutral, pivot_idx):
    """Δ across the charged window, charged minus neutral."""
    d_ch = series_charged[-1] - series_charged[pivot_idx]
    d_nt = series_neutral[-1] - series_neutral[pivot_idx]
    return float(d_ch - d_nt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=24)
    args = ap.parse_args()

    import compat
    import arms as A
    from arms_v2 import A2bFeedSevered

    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)

    deaf_max, hearing = 0.0, []
    for seed in range(args.seeds):
        sc = st.build_ic2(seed, "charged")
        sn = st.build_ic2(seed, "neutral")
        pivot = sc["kind"].index("charged")

        d_ser = run_core(A2bFeedSevered(model), sc)
        n_ser = run_core(A2bFeedSevered(model), sn)
        deaf_max = max(deaf_max, float(np.nanmax(np.abs(d_ser - n_ser))))

        h_c = run_core(A.A0Intact(model), sc)
        h_n = run_core(A.A0Intact(model), sn)
        hearing.append(causal_delta(h_c, h_n, pivot))

    h = np.array(hearing)
    print(f"\n=== 1. IDENTITY (deaf core, charged vs neutral, {args.seeds} seeds)")
    print(f"    max |difference| anywhere in the saddle series: {deaf_max:.2e}")
    print("    " + ("PASS — deaf causal delta is exactly 0 by construction"
                    if deaf_max == 0.0 else
                    "FAIL — deaf core differs between conditions; design is wrong"))

    print(f"\n=== 2. EFFECT (hearing core causal delta, {args.seeds} seeds)")
    print(f"    mean {h.mean():+.4f} | median {np.median(h):+.4f} | "
          f"sd {h.std(ddof=1):.4f}")
    print(f"    range [{h.min():+.4f}, {h.max():+.4f}] | "
          f"mean |delta| {np.abs(h).mean():.4f}")

    print("\n=== 3. SEPARATION (share of seeds with |causal delta| >= threshold)")
    for thr in (0.05, 0.10, 0.15, 0.20, 0.30):
        frac = float((np.abs(h) >= thr).mean())
        print(f"    thr {thr:.2f}: {frac*100:5.1f}% of seeds have a real answer")
    print("\n(threshold choice is a pre-registration decision, made from THIS "
          "distribution, before any conversation is generated)")


if __name__ == "__main__":
    main()
