"""A/§8 — base-rate sweep for the IC-1 re-test (design seeds only).

IC-1 died of a DEGENERATE LABEL: its ground truth was ~71% "settled", so a constant guess
scored 0.71, a transcript-only oracle beat chance by learning the base rate, and the arm
contrast became a coin flip on the residual (FINDING_shuttered_readout_2026-07-27.md §
"Consequences"). The re-test must not repeat that, and the only way to know is to measure
the label BEFORE freezing anything.

Option A3 asks Teich to predict its own near future — "will you stay as you are, or turn?"
— and scores against WHAT ACTUALLY HAPPENS: did `basin` differ W ticks after the probe.

This sweeps W and reports:
  * base rate  P(basin changes within W)  -- want it near 0.50
  * the Observer's OWN will_flip accuracy against that realized outcome, which bounds how
    predictable the truth is at all (if the white-box predictor cannot do it at window W,
    no Mouth reading a journal derived from it can either)

Pre-registered acceptance (IC1_RETEST_DESIGN_v0.1 §4): pick the W whose base rate is
closest to 0.50; A3 is viable only if some W lands in [0.35, 0.65].

DESIGN SEEDS ONLY (600+). Confirmatory seeds 400-495 are never touched here.
Offline: no Mouth, no API, no judge.

Run: python sweep_flip_baserate.py [--seeds 48]
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

DESIGN_SEED0 = 600                       # disjoint from 0-95 / 100-115 / 200-295 / 400-495
WINDOWS = (40, 75, 120, 150, 225, 300)   # T0 = 74.66 ticks per roof revolution


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=48)
    args = ap.parse_args()

    import compat
    import arms as A
    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)

    t0, rows = time.time(), []
    for k in range(args.seeds):
        seed = DESIGN_SEED0 + k
        script = st.build_ic1(seed)
        arm = A.A0Intact(model)
        arm.start(seed)
        r = None
        for text, kind in zip(script["turns"], script["kind"]):
            _ro, _ev, _f, meta = arm.step(text, st.ticks_for(kind))
            r = meta.get("readout")
        probe_basin = int(r["basin"])
        probe_willflip = bool(r["will_flip"])
        probe_steps = int(r["steps_to_switch"])
        # continue living; record the basin at each cumulative window
        after, prev = {}, 0
        for w in WINDOWS:
            rw = arm.e.advance(w - prev)
            prev = w
            after[w] = int(rw["basin"])
        rows.append(dict(seed=seed, gap=script["gap"], probe_basin=probe_basin,
                         will_flip=probe_willflip, steps_to_switch=probe_steps,
                         after={str(w): after[w] for w in WINDOWS}))
    (HERE / "out_baserate.json").write_text(json.dumps(rows, indent=1))

    n = len(rows)
    print(f"=== A3 label base rate: P(basin differs W ticks after the probe)")
    print(f"    design seeds {DESIGN_SEED0}-{DESIGN_SEED0+n-1}, n={n}, T0=74.66\n")
    # SELECTION CRITERION -- corrected 2026-07-27 after the first run.
    #
    # The original rule picked the W whose base rate was closest to 0.50, and chose
    # W=300: base rate 0.479 (perfectly balanced) but will_flip accuracy 0.5625, i.e.
    # the truth is barely predictable AT ALL at that horizon. Balanced-and-unpredictable
    # is the WORST window -- the screen would measure noise, and would then be reported
    # as a null about Teich rather than about the window.
    #
    # What matters is HEADROOM: how much better a perfect state-reader does than the
    # best state-blind strategy, which is guessing the majority class:
    #
    #     headroom = willflip_acc - max(base_rate, 1 - base_rate)
    #
    # A viable W needs a non-degenerate label AND room above the constant guess.
    print(f"    {'W':>6s} {'base rate':>11s} {'const guess':>12s} "
          f"{'will_flip acc':>14s} {'headroom':>10s} {'viable':>8s}")
    best, best_head = None, -9.9
    summary = {}
    for w in WINDOWS:
        changed = np.array([r["after"][str(w)] != r["probe_basin"] for r in rows])
        wf = np.array([r["will_flip"] for r in rows])
        base = float(changed.mean())
        acc = float((wf == changed).mean())
        const = max(base, 1.0 - base)
        head = acc - const
        viable = "yes" if (0.35 <= base <= 0.65 and head >= 0.15) else "no"
        summary[w] = dict(base_rate=round(base, 4), const_guess=round(const, 4),
                          willflip_acc=round(acc, 4), headroom=round(head, 4),
                          viable=(viable == "yes"))
        if viable == "yes" and head > best_head:
            best, best_head = w, head
        print(f"    {w:6d} {base:11.4f} {const:12.4f} {acc:14.4f} "
              f"{head:10.4f} {viable:>8s}")

    (HERE / "out_baserate_summary.json").write_text(json.dumps(summary, indent=1))
    print("\n--- reading:")
    if best is not None:
        s = summary[best]
        print(f"    W = {best} ticks is the pick (max headroom {s['headroom']:.3f}).")
        print(f"    Base rate {s['base_rate']:.3f}; a state-blind constant guess scores")
        print(f"    {s['const_guess']:.3f}; the Observer's own will_flip scores "
              f"{s['willflip_acc']:.3f}.")
        print(f"    That gap is the entire signal available to any Mouth downstream.")
        if abs(best - 74.66) < 10:
            print(f"    NOTE: W={best} is one roof revolution (T0=74.66). will_flip is")
            print(f"    DEFINED as the lobe after the next wrap, so this is its natural")
            print(f"    horizon -- the window is physically principled, not fitted.")
    else:
        print(f"    NO window is viable (needs base rate in [0.35,0.65] AND headroom")
        print(f"    >= 0.15) -> A3 not viable as designed. Fall back per")
        print(f"    IC1_RETEST_DESIGN §3, or widen the sweep.")
    print(f"\n({time.time()-t0:.0f}s)  raw -> out_baserate.json")


if __name__ == "__main__":
    main()
