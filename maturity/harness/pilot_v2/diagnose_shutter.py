"""Step 0c — was saddle_proximity multiplied by ~0 at the probe?

observer.py:

    frac_left   = (period - roof_phase) / period      # roof_phase = tau[...,1]
    saddle_prox = saddle * (1.0 - frac_left)

`saddle` carries the state (distance of |lobe_coord| from the flip threshold).
`frac_left` carries the CLOCK — tau[...,1] is never touched by the Ears, which
diagnose_acts confirmed empirically: steps_to_switch (derived from the same
clock) showed 0.0% paired divergence at both pivot and probe.

So the two conditions reach the probe with IDENTICAL frac_left, and whatever
state difference exists is multiplied by the same (1 - frac_left). Where that
factor is near zero, saddle_proximity is crushed toward 0 in both conditions
and the mood bucket agrees TRIVIALLY - the instrument is shuttered, and no
amount of coupling could show through it.

diagnose_acts found the saddle_bucket paired divergence collapsing with gap:
50.0% (300t) -> 43.8% (900t) -> 6.2% (1800t). Two readings:
  (a) the mark fades with time, or
  (b) the shutter closes at gap 1800.
These have opposite design consequences, so measure (1 - frac_left) per gap.

This matters beyond the diagnostic: T-INT pooled all three gaps, so if the
shutter is closed at 1800, a third of those 384 conversations were scored
through it.

Run: python diagnose_shutter.py [--seeds 48]
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

SADDLE_SETTLED, SADDLE_TORN = 0.20, 0.60      # journal.py bucket edges


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=48)
    args = ap.parse_args()

    import compat
    import arms as A
    import torch
    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)

    t0 = time.time()
    rows = []
    for seed in range(args.seeds):
        sc = st.build_ic2(seed, "charged")
        arm = A.A0Intact(model)
        arm.start(seed)
        for text, kind in zip(sc["turns"], sc["kind"]):
            _ro, _ev, _f, meta = arm.step(text, st.ticks_for(kind))
        e = arm.e
        obs = e.obs
        rp = float(obs._roof_phase(e.tau).item())
        frac_left = (obs.period - rp) / obs.period
        x = float(obs._lobe_coord(e.tau).abs().item())
        saddle = max(0.0, 1.0 - abs(x - obs.flip_thresh) / obs.flip_thresh)
        rows.append(dict(seed=seed, gap=sc["gap"], frac_left=frac_left,
                         gate=1.0 - frac_left, saddle=saddle,
                         saddle_prox=saddle * (1.0 - frac_left)))
    (HERE / "out_shutter.json").write_text(json.dumps(rows, indent=1))

    print(f"=== shutter check: the (1 - frac_left) gate at the probe, by gap")
    print(f"    {'gap':>6s} {'n':>3s} {'gate=1-frac_left':>18s} {'saddle(state)':>15s} "
          f"{'saddle_prox':>13s} {'% below SETTLED':>16s}")
    for g in st.GAPS:
        sub = [r for r in rows if r["gap"] == g]
        gate = np.array([r["gate"] for r in sub])
        sad = np.array([r["saddle"] for r in sub])
        sp = np.array([r["saddle_prox"] for r in sub])
        below = float((sp < SADDLE_SETTLED).mean()) * 100
        print(f"    {g:6d} {len(sub):3d} {gate.mean():9.4f} +-{gate.std():6.4f} "
              f"{sad.mean():10.4f}{'':5s} {sp.mean():9.4f}{'':4s} {below:13.1f}%")

    print("\n--- reading:")
    for g in st.GAPS:
        sub = [r for r in rows if r["gap"] == g]
        gate = np.mean([r["gate"] for r in sub])
        sad = np.mean([r["saddle"] for r in sub])
        print(f"    gap {g:5d}: state signal present ({sad:.3f}) but attenuated "
              f"x{gate:.3f} -> reported {sad*gate:.3f}")
    print("\n    If the gate collapses at 1800 while `saddle` does not, the")
    print("    saddle_bucket decay (50.0 -> 43.8 -> 6.2%) is a SHUTTERED")
    print("    INSTRUMENT, not a fading mark — and T-INT scored a third of its")
    print("    conversations through it.")
    print(f"\n({time.time()-t0:.0f}s)  raw -> out_shutter.json")


if __name__ == "__main__":
    main()
