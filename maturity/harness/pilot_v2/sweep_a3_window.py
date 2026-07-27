"""A3 window re-calibration — on the ACTUAL A3 script this time.

sweep_flip_baserate.py measured the base rate on `build_ic1` scripts and chose
W=75. But A3 runs `build_a3`, whose probe TEXT differs, and the probe is heard
by the Ears BEFORE the gap is lived — different sentence, different forcing,
different trajectory, different base rate. The design run confirms it:
P(turn) = 0.22 on A3 scripts, not 0.375.

That matters. At base rate 0.22 the best state-blind strategy ("stay") scores
0.78, so the maximum achievable difference between arms is ~0.22 against a
pre-registered bar of 0.20 — a screen that could barely pass even if Teich
were perfect.

This re-sweeps W on `build_a3` itself and reports, per window:

    base rate P(turn)
    const guess = max(base, 1-base)
    will_flip accuracy against the realized outcome
    headroom = willflip_acc - const_guess     <- the criterion

Offline: pure core stepping, no Mouth, no API, DESIGN SEEDS ONLY (600-623).
No confirmatory seed and no reply text is touched, so W remains a choice made
from dynamics alone — never from anything a Mouth said.

Run: python sweep_a3_window.py [--seeds 24]
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

import scripts_a3 as sa  # noqa: E402

DESIGN_SEED0 = 600
WINDOWS = (40, 60, 75, 90, 110, 130, 150, 190, 225, 300, 375, 450)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=24)
    args = ap.parse_args()

    import compat
    import arms as A
    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)

    t0, rows = time.time(), []
    for k in range(args.seeds):
        seed = DESIGN_SEED0 + k
        script = sa.build_a3(seed)
        arm = A.A0Intact(model)
        arm.start(seed)
        r = None
        for text, kind in zip(script["turns"], script["kind"]):
            _ro, _ev, _f, meta = arm.step(text, sa.ticks_for(kind))
            r = meta.get("readout")
        probe_basin = int(r["basin"])
        wf = bool(r["will_flip"])
        after, prev = {}, 0
        for w in WINDOWS:
            rw = arm.e.advance(w - prev)
            prev = w
            after[w] = int(rw["basin"])
        rows.append(dict(seed=seed, gap=script["gap"], probe_basin=probe_basin,
                         will_flip=wf,
                         after={str(w): after[w] for w in WINDOWS}))
    (HERE / "out_a3_window.json").write_text(json.dumps(rows, indent=1))

    n = len(rows)
    print(f"=== A3 window sweep on build_a3 (design seeds "
          f"{DESIGN_SEED0}-{DESIGN_SEED0+n-1}, n={n}, T0=74.66)\n")
    print(f"    {'W':>6s} {'P(turn)':>9s} {'const':>8s} {'wf acc':>8s} "
          f"{'headroom':>10s} {'viable':>8s}")
    best, best_head, summary = None, -9.9, {}
    for w in WINDOWS:
        changed = np.array([r["after"][str(w)] != r["probe_basin"] for r in rows])
        wfv = np.array([r["will_flip"] for r in rows])
        base = float(changed.mean())
        acc = float((wfv == changed).mean())
        const = max(base, 1.0 - base)
        head = acc - const
        viable = "yes" if (0.35 <= base <= 0.65 and head >= 0.15) else "no"
        summary[w] = dict(base_rate=round(base, 4), const_guess=round(const, 4),
                          willflip_acc=round(acc, 4), headroom=round(head, 4),
                          viable=(viable == "yes"))
        if viable == "yes" and head > best_head:
            best, best_head = w, head
        print(f"    {w:6d} {base:9.4f} {const:8.4f} {acc:8.4f} {head:10.4f} "
              f"{viable:>8s}")

    (HERE / "out_a3_window_summary.json").write_text(json.dumps(summary, indent=1))
    print("\n--- reading:")
    if best is not None:
        s = summary[best]
        print(f"    W = {best}: P(turn) {s['base_rate']:.3f}, const guess "
              f"{s['const_guess']:.3f}, will_flip {s['willflip_acc']:.3f},")
        print(f"    headroom {s['headroom']:.3f}. Max achievable arm difference "
              f"= {s['headroom']:.3f} vs bar 0.20.")
        if s["headroom"] < 0.30:
            print(f"    NOTE: headroom is tight against the 0.20 bar. Report it.")
    else:
        print("    NO viable window on the A3 script. The screen cannot be made")
        print("    fair by choosing W; the probe text itself would have to change,")
        print("    which is a new pre-registration and a founder decision.")
    print(f"\n({time.time()-t0:.0f}s)  raw -> out_a3_window.json")


if __name__ == "__main__":
    main()
