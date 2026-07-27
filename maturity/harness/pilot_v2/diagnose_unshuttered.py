"""Step 0d — how wide is the channel once the clock factor is removed?

diagnose_shutter established that observer.py reports

    saddle_prox = saddle * (1.0 - frac_left)          # state * clock

where `frac_left` comes from tau[...,1], which the Ears never touch. The clock
factor drags 56-81% of readouts below journal.SADDLE_SETTLED (0.20), so the
journal's mood bucket sat in its floor bucket most of the time and the measured
channel width was 33.3%.

`saddle` — the state term alone — is recoverable READ-ONLY from `lobe_coord`,
which is already an observer readout key:

    saddle = max(0, 1 - ||lobe_coord| - flip_thresh| / flip_thresh)

observer.py is substrate-gate-hashed and is NOT touched: this is arithmetic on
a key the Observer already publishes.

Measures paired charged-vs-neutral divergence for buckets built on:
  A. saddle_prox with the journal's fixed edges (0.20/0.60)  = what T-INT used
  B. saddle      with the journal's fixed edges              = shutter removed
  C. saddle      with empirical tertile edges                = floor effect also
                                                               removed
Deaf control must stay 0% in every variant, or the number is not
text-attributable and means nothing.

Run: python diagnose_unshuttered.py [--seeds 48]
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

SETTLED, TORN = 0.20, 0.60          # journal.py edges


def bucket(v, lo, hi):
    return "settled" if v < lo else ("torn" if v >= hi else "between")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=48)
    args = ap.parse_args()

    import compat
    import arms as A
    from arms_v2 import A2bFeedSevered
    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)

    from observer import Observer
    thresh = Observer(model).flip_thresh

    def saddle_of(r):
        ax = abs(float(r["lobe_coord"]))
        return max(0.0, 1.0 - abs(ax - thresh) / thresh)

    t0, rows = time.time(), []
    for label, mk in (("A0_intact (hearing)", lambda: A.A0Intact(model)),
                      ("A2b_severed (deaf)", lambda: A2bFeedSevered(model))):
        for seed in range(args.seeds):
            rc = act_run(mk(), st.build_ic2(seed, "charged"))[-1]
            rn = act_run(mk(), st.build_ic2(seed, "neutral"))[-1]
            rows.append(dict(arm=label, seed=seed,
                             sp_c=float(rc["saddle_proximity"]),
                             sp_n=float(rn["saddle_proximity"]),
                             sd_c=saddle_of(rc), sd_n=saddle_of(rn)))
    (HERE / "out_unshuttered.json").write_text(json.dumps(rows, indent=1))

    intact = [r for r in rows if r["arm"].startswith("A0")]
    allsd = np.array([r["sd_c"] for r in intact] + [r["sd_n"] for r in intact])
    t1, t2 = float(np.percentile(allsd, 33.3)), float(np.percentile(allsd, 66.7))
    print(f"=== unshuttered channel width  (n={args.seeds} paired seeds)")
    print(f"    flip_thresh={thresh:.4f}   saddle tertile edges: "
          f"{t1:.3f} / {t2:.3f}")
    print(f"\n    {'variant':44s} {'intact':>8s} {'deaf':>8s}")
    variants = [
        ("A. saddle_prox, fixed edges  (= T-INT)", "sp", SETTLED, TORN),
        ("B. saddle, fixed edges       (unshuttered)", "sd", SETTLED, TORN),
        ("C. saddle, tertile edges     (+ floor fix)", "sd", t1, t2),
    ]
    out = {}
    for name, key, lo, hi in variants:
        cell = {}
        for label in ("A0_intact (hearing)", "A2b_severed (deaf)"):
            sub = [r for r in rows if r["arm"] == label]
            d = sum(1 for r in sub
                    if bucket(r[f"{key}_c"], lo, hi) != bucket(r[f"{key}_n"], lo, hi))
            cell[label] = d / len(sub) * 100
        out[name] = cell
        print(f"    {name:44s} {cell['A0_intact (hearing)']:7.1f}% "
              f"{cell['A2b_severed (deaf)']:7.1f}%")

    print("\n--- reading:")
    a = out["A. saddle_prox, fixed edges  (= T-INT)"]["A0_intact (hearing)"]
    c = out["C. saddle, tertile edges     (+ floor fix)"]["A0_intact (hearing)"]
    print(f"    T-INT ran against a {a:.1f}% channel and returned DiD 0.042.")
    print(f"    Unshuttered + floor-corrected, the channel is {c:.1f}%.")
    if c > a:
        print(f"    Widening factor {c/max(a,1e-9):.2f}x. At T-INT's measured")
        print(f"    conversion rate (0.042/0.333 = 12.6% of available difference")
        print(f"    turned into a flipped answer), a {c:.1f}% channel projects to")
        print(f"    DiD ~{c/100*0.126:.3f} against a 0.20 bar — so a wider channel")
        print(f"    alone is {'ENOUGH' if c/100*0.126 >= 0.20 else 'NOT ENOUGH'};")
        print(f"    conversion, not width, is then the binding constraint.")
    print(f"\n({time.time()-t0:.0f}s)  raw -> out_unshuttered.json")


if __name__ == "__main__":
    main()
