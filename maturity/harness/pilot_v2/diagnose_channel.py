"""Channel diagnostic — does the C1 journal actually CARRY the charged/neutral
difference to the Mouth? Offline (no API), retired seeds only (0-95), so it
touches neither design seeds (100-115) nor confirmatory seeds (200-295).

The DiD can only be non-zero if the hearing core's journal TEXT differs between
the charged and neutral conditions — that text is the entire coupling channel.
This measures exactly that, and separates three ways it can differ:

  any    : the journal tail shown to the Mouth is not character-identical
  drift  : the "something in me has shifted noticeably" clause differs
           (journal.DRIFT_NOTABLE = 0.25, compared TURN TO TURN)
  mood   : the settled / between / torn bucket differs at the probe

A2b (deaf) is run as a control on the diagnostic itself: its journals must be
identical in 100% of seeds, since its trajectories are bit-identical.

Run: python diagnose_channel.py [--seeds 48]
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

DRIFT_CLAUSE = "shifted noticeably"
MOODS = ("settled", "somewhere between settled and torn", "torn, close to an edge")


def journal_run(arm, script):
    """Step a core through a script, returning the journal tail at each turn."""
    arm.start(script["seed"])
    tails = []
    for text, kind in zip(script["turns"], script["kind"]):
        tail, _ev, _f, _meta = arm.step(text, st.ticks_for(kind))
        tails.append(tail)
    return tails


def mood_of(tail: str):
    last = tail.strip().split("\n")[-1].lower()
    for m in reversed(MOODS):          # longest/most specific first
        if m in last:
            return m
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=48)
    args = ap.parse_args()

    import compat
    import arms as A
    from arms_v2 import A2bFeedSevered, C1Journal

    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)

    stats = {}
    for label, mk in (("A0_intact (hearing)", lambda: C1Journal(A.A0Intact(model))),
                      ("A2b_severed (deaf)", lambda: C1Journal(A2bFeedSevered(model)))):
        any_d = drift_d = mood_d = 0
        for seed in range(args.seeds):
            tc = journal_run(mk(), st.build_ic2(seed, "charged"))
            tn = journal_run(mk(), st.build_ic2(seed, "neutral"))
            probe_c, probe_n = tc[-1], tn[-1]
            if probe_c != probe_n:
                any_d += 1
            if (DRIFT_CLAUSE in probe_c) != (DRIFT_CLAUSE in probe_n):
                drift_d += 1
            if mood_of(probe_c) != mood_of(probe_n):
                mood_d += 1
        n = args.seeds
        stats[label] = (any_d / n, drift_d / n, mood_d / n)
        print(f"\n=== {label}  ({n} seeds)")
        print(f"    journal tail differs at the probe : {any_d/n*100:5.1f}%  ({any_d}/{n})")
        print(f"    'shifted noticeably' clause differs: {drift_d/n*100:5.1f}%  ({drift_d}/{n})")
        print(f"    mood bucket differs at the probe  : {mood_d/n*100:5.1f}%  ({mood_d}/{n})")

    a0 = stats["A0_intact (hearing)"][0]
    a2 = stats["A2b_severed (deaf)"][0]
    print("\n--- reading:")
    print(f"    coupling channel carries a difference in {a0*100:.0f}% of seeds.")
    print(f"    deaf control differs in {a2*100:.0f}% (MUST be 0 — bit-identical trajectories).")
    print("    The DiD's ceiling is set by this number: the Mouth cannot report a")
    print("    state difference the journal never showed it.")


if __name__ == "__main__":
    main()
