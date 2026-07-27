"""B-followup — is the memory/consequence trade-off fundamental, or just my dose?

diagnose_survival.py found a strict complementarity at BETA=0.25 x natural spread:

    tau1 (neutral) : steps_to_switch 48/48 consistent (D=1.000, mean -10.77 ticks,
                     undecayed at 1800t)  BUT  basin 46/48 TIES -- it remembers
                     perfectly and barely acts
    tau0 (expanding): saddle 45/48 changed BUT direction random; steps_to_switch
                     48/48 ties -- it acts on everything and remembers nothing

If that is the Lyapunov spectrum talking, it is a property of the frozen genome and no
Ears redesign escapes it. If it is just a small dose, a larger phase push might start
coupling into the fold and the conclusion is wrong.

So: sweep the tau1 dose and watch TWO quantities move against each other --

    memory      = discriminability on steps_to_switch   (expected: stays 1.000)
    consequence = fraction of pairs whose basin/saddle DIFFERS at the probe
                  (expected under "fundamental": stays near 0;
                   under "dose artifact": rises with dose)

Doses are multiples of the diagnose_survival dose (0.14446 = 7.2% of the anchor period
2.0), up to a substantial fraction of a full revolution.

Design seeds are NOT used here and nothing is frozen -- this is a physics question about
the genome, on retired seeds, offline.

Run: python sweep_tau1_dose.py [--seeds 24]
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
from diagnose_survival import PRE_PIVOT, ProbeEngine, selftest  # noqa: E402

BASE_DOSE = 0.14446          # BETA * std(tau1) from diagnose_survival
MULTS = (1, 2, 4, 8)         # up to 1.156 = 58% of the anchor period (2.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=24)
    args = ap.parse_args()

    import compat
    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)
    selftest(model)

    from observer import Observer
    thresh = Observer(model).flip_thresh

    def saddle_of(r):
        ax = abs(float(r["lobe_coord"]))
        return max(0.0, 1.0 - abs(ax - thresh) / thresh)

    t0, rows = time.time(), []
    for mult in MULTS:
        dose = BASE_DOSE * mult
        for k in range(args.seeds):
            seed = k
            gap = int(st.GAPS[seed % len(st.GAPS)])
            out = {}
            for sign in (+1, -1):
                eng = ProbeEngine(model, seed)
                eng.advance(PRE_PIVOT)
                eng.push("tau", 1, sign * dose, eng.n)
                r = eng.advance(gap)
                out[sign] = dict(steps=int(r["steps_to_switch"]),
                                 basin=int(r["basin"]),
                                 saddle=saddle_of(r),
                                 nsw=int(r["n_switches"]))
            rows.append(dict(mult=mult, dose=dose, seed=seed, gap=gap,
                             plus=out[+1], minus=out[-1]))
        print(f"  x{mult} (dose {dose:.4f} = {dose/2.0*100:.1f}% of period): "
              f"{args.seeds} pairs ({time.time()-t0:.0f}s)", flush=True)
    (HERE / "out_tau1_dose.json").write_text(json.dumps(rows, indent=1))

    print(f"\n=== tau1 dose sweep: does a bigger phase push start ACTING?  (n={args.seeds})")
    print(f"    {'dose':>9s} {'%period':>8s} {'memory D':>10s} "
          f"{'basin differs':>14s} {'saddle differs':>15s} {'mean d steps':>13s}")
    summary = {}
    for mult in MULTS:
        sub = [r for r in rows if r["mult"] == mult]
        n = len(sub)
        # memory: discriminability of the sign from steps_to_switch
        w = [(r["plus"]["steps"] > r["minus"]["steps"])
             + 0.5 * (r["plus"]["steps"] == r["minus"]["steps"]) for r in sub]
        mem = 2 * abs(float(np.mean(w)) - 0.5)
        # consequence: does the FOLD state differ at all?
        b_diff = float(np.mean([r["plus"]["basin"] != r["minus"]["basin"] for r in sub]))
        s_diff = float(np.mean([abs(r["plus"]["saddle"] - r["minus"]["saddle"]) > 1e-9
                                for r in sub]))
        d_steps = float(np.mean([r["plus"]["steps"] - r["minus"]["steps"] for r in sub]))
        summary[mult] = dict(dose=round(sub[0]["dose"], 5), memory_D=round(mem, 4),
                             basin_differs=round(b_diff, 4),
                             saddle_differs=round(s_diff, 4),
                             mean_d_steps=round(d_steps, 3), n=n)
        print(f"    {sub[0]['dose']:9.4f} {sub[0]['dose']/2.0*100:7.1f}% {mem:10.3f} "
              f"{b_diff*100:13.1f}% {s_diff*100:14.1f}% {d_steps:13.2f}")

    (HERE / "out_tau1_dose_summary.json").write_text(json.dumps(summary, indent=1))
    print("\n--- reading:")
    print("    FUNDAMENTAL if memory stays ~1.0 while basin/saddle-differs stays low:")
    print("      the neutral direction is structurally a sealed store (INTERIOR_SPEC")
    print("      Ply S) -- perfect recall, no behavioural consequence -- and no choice")
    print("      of push direction buys both memory AND consequence.")
    print("    DOSE ARTEFACT if the 'differs' columns climb with dose: a large enough")
    print("      phase shift re-times wraps enough to change flip outcomes, and an Ears")
    print("      redesign could use it. Note that would buy CONSEQUENCE, not")
    print("      necessarily a RECOVERABLE SIGN -- check memory D has not collapsed.")
    print(f"\n({time.time()-t0:.0f}s)  raw -> out_tau1_dose.json")


if __name__ == "__main__":
    main()
