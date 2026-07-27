"""Step 0 — does what is SAID to the core change what the core DOES, later?

Offline (no Mouth, no API, no judge). Retired seeds only (0-95).

The T-INT null localised the failure to the coupling channel: the journal
transmitted a text-attributable difference in only 25-33% of conversations, so
the DiD could never clear 0.20. Before building anything on a NEW channel we
measure the channel first (REPORT_tint_screen §4.3, standing rule).

The proposed channel is not narration but ACTION: the discrete things the core
commits to — which wing it is on, whether it is about to leave it, how much it
churned. Those are recorded, not described, so no Mouth and no lexicon stand
between the state and the measurement.

Four questions, in the order that can kill the design fastest:

  Q1 REPRODUCIBLE?  Same seed, same script, run twice: identical act sequence?
                    (`lambda_running` failed exactly this and nobody checked
                    until a control arm broke. Every act channel must pass
                    before it is allowed to carry anything.)
  Q2 DEAF ZERO?     A2b charged vs neutral must diverge in 0% of seeds — its
                    trajectories are bit-identical, so any divergence is a bug
                    in the diagnostic, not a signal.
  Q3 WIDTH LATER?   A0 charged vs neutral: in what fraction of seeds does the
                    act sequence differ AT THE PROBE — i.e. after the gap of
                    300/900/1800 unspoken ticks? This is the ceiling on any
                    screen built on this channel, and the "later" is the whole
                    point: a memoryless input->output map diverges at the pivot
                    turn and nowhere else.
  Q4 NOT HOLLOW?    A3 lavalamp (matched marginals, no ears) must ALSO be 0%:
                    it moves, but what is said cannot reach it. A channel that
                    a lavalamp passes is measuring life, not coupling — the
                    exact error T4 made in the v1.5 gate.

Run: python diagnose_acts.py [--seeds 48]
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import numpy as np  # noqa: E402

import scripts_tint as st  # noqa: E402

# Act channels. Each is a deterministic function of (tau, ell, phi) plus the
# Observer's within-window switch counter — read-only inspection of
# body/observer.py confirms none of them touches `_v`, the unseeded
# power-iteration vector that made `lambda_running` unusable.
CHANNELS = {
    "basin":        lambda r: int(r["basin"]),
    "will_flip":    lambda r: bool(r["will_flip"]),
    "n_switches":   lambda r: int(r["n_switches"]),
    "steps_switch": lambda r: int(r["steps_to_switch"]),
    # the journal's coarse mood bucket, kept for direct comparison with the
    # 33.3% that diagnose_channel.py measured on the old channel
    "saddle_bucket": lambda r: ("settled" if r["saddle_proximity"] < 0.20
                                else "torn" if r["saddle_proximity"] >= 0.60
                                else "between"),
    # the act pair: what it is committed to, and whether it is about to leave
    "act(basin,will_flip)": lambda r: (int(r["basin"]), bool(r["will_flip"])),
}


def act_run(arm, script):
    """Step a core through a script; return the per-turn list of readout dicts."""
    arm.start(script["seed"])
    reads = []
    for text, kind in zip(script["turns"], script["kind"]):
        _ro, _ev, _f, meta = arm.step(text, st.ticks_for(kind))
        reads.append(meta.get("readout"))
    return reads


def chan(reads, fn):
    """Project a run onto one act channel: one value per turn."""
    return [None if r is None else fn(r) for r in reads]


def pivot_index(script):
    return script["kind"].index("charged")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=48)
    args = ap.parse_args()

    import compat
    import arms as A
    from arms_v2 import A2bFeedSevered

    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)

    n = args.seeds
    t0 = time.time()

    # ---------------------------------------------------------------- Q1
    # Reproducibility, before anything is allowed to carry a signal.
    print("=== Q1  reproducible?  (same seed, same script, run twice)")
    repro = {k: 0 for k in CHANNELS}
    n_rep = min(8, n)
    for seed in range(n_rep):
        s = st.build_ic2(seed, "charged")
        a = act_run(A.A0Intact(model), s)
        b = act_run(A.A0Intact(model), s)
        for k, fn in CHANNELS.items():
            if chan(a, fn) == chan(b, fn):
                repro[k] += 1
    for k in CHANNELS:
        ok = "OK " if repro[k] == n_rep else "FAIL"
        print(f"    {ok} {k:22s} identical in {repro[k]}/{n_rep} repeats")
    usable = [k for k in CHANNELS if repro[k] == n_rep]
    if not usable:
        print("\n    no reproducible act channel — design is dead here. STOP.")
        return

    # ---------------------------------------------------------------- Q2/Q3
    # Paired charged/neutral, hearing core and deaf control.
    print(f"\n=== Q2/Q3  paired divergence  ({n} seeds x 2 conditions x 2 arms)")
    arms = {"A0_intact (hearing)": lambda: A.A0Intact(model),
            "A2b_severed (deaf)": lambda: A2bFeedSevered(model)}
    results = {}
    intact_reads = []
    by_gap = {g: {k: [0, 0] for k in usable} for g in st.GAPS}   # gap -> [diff, n]
    charged_probe = {}                                          # seed -> {k: value}
    for label, mk in arms.items():
        at_probe = {k: 0 for k in usable}
        at_pivot = {k: 0 for k in usable}
        post_any = {k: 0 for k in usable}
        for seed in range(n):
            sc, sn = st.build_ic2(seed, "charged"), st.build_ic2(seed, "neutral")
            rc, rn = act_run(mk(), sc), act_run(mk(), sn)
            if label.startswith("A0"):
                intact_reads += [r for r in rc if r is not None]
                charged_probe[seed] = {k: chan(rc, CHANNELS[k])[-1] for k in usable}
            p = pivot_index(sc)
            for k in usable:
                cc, cn = chan(rc, CHANNELS[k]), chan(rn, CHANNELS[k])
                if cc[-1] != cn[-1]:
                    at_probe[k] += 1
                    if label.startswith("A0"):
                        by_gap[sc["gap"]][k][0] += 1
                if label.startswith("A0"):
                    by_gap[sc["gap"]][k][1] += 1
                if cc[p] != cn[p]:
                    at_pivot[k] += 1
                if cc[p + 1:] != cn[p + 1:]:
                    post_any[k] += 1
        results[label] = (at_probe, at_pivot, post_any)
        print(f"\n  --- {label}")
        print(f"      {'channel':22s} {'at pivot':>10s} {'later(any)':>12s} "
              f"{'AT PROBE':>10s}")
        for k in usable:
            print(f"      {k:22s} {at_pivot[k]/n*100:9.1f}% "
                  f"{post_any[k]/n*100:11.1f}% {at_probe[k]/n*100:9.1f}%")

    # ---------------------------------------------------------------- Q4
    # Lavalamp: matched marginals drawn from the intact runs, no ears.
    print(f"\n=== Q4  lavalamp control  (matched marginals, cannot hear)")
    def col(key):
        return np.array([float(r[key]) for r in intact_reads])
    stats = dict(basin_p=[float((col("basin") < 0).mean()),
                          float((col("basin") > 0).mean())],
                 saddle=(float(col("saddle_proximity").mean()),
                         float(col("saddle_proximity").std())),
                 **{"lambda": (float(col("lambda_running").mean()),
                               float(col("lambda_running").std()))},
                 steps=(float(col("steps_to_switch").mean()),
                        float(col("steps_to_switch").std())),
                 flip_p=float(col("will_flip").mean()),
                 nsw=(float(col("n_switches").mean()),
                      float(col("n_switches").std())))
    lava_probe = {k: 0 for k in usable}
    for seed in range(n):
        sc, sn = st.build_ic2(seed, "charged"), st.build_ic2(seed, "neutral")
        arm_c, arm_n = A.A3LavaLamp(stats), A.A3LavaLamp(stats)
        arm_c.start(seed); arm_n.start(seed)
        rc = [arm_c._draw() for _ in sc["turns"]]
        rn = [arm_n._draw() for _ in sn["turns"]]
        for k in usable:
            if chan(rc, CHANNELS[k])[-1] != chan(rn, CHANNELS[k])[-1]:
                lava_probe[k] += 1
    for k in usable:
        print(f"      {k:22s} {lava_probe[k]/n*100:9.1f}%  at probe")

    # ------------------------------------------------------- decorrelation
    # How different are two UNRELATED lives? Paired divergence cannot exceed
    # this: once the perturbation has been amplified past the system's own
    # memory the two runs are simply two independent trajectories, and the
    # channel then carries "something was said" but not "what was said".
    print("\n=== decorrelation reference  (seed s vs seed s+1, both charged)")
    decorr = {k: 0 for k in usable}
    pairs = [(s, s + 1) for s in range(n - 1)]
    for a, b in pairs:
        for k in usable:
            if charged_probe[a][k] != charged_probe[b][k]:
                decorr[k] += 1
    for k in usable:
        print(f"      {k:22s} {decorr[k]/len(pairs)*100:9.1f}%  "
              f"(saturation ceiling)")

    # ---------------------------------------------------------- gap profile
    print("\n=== gap profile  (A0 paired divergence at the probe, by gap length)")
    print(f"      {'channel':22s} " + " ".join(f"{g:>8d}t" for g in st.GAPS))
    for k in usable:
        row = " ".join(f"{by_gap[g][k][0]/max(1,by_gap[g][k][1])*100:8.1f}%"
                       for g in st.GAPS)
        print(f"      {k:22s} {row}")

    # ---------------------------------------------------------------- reading
    a0p, a0pv, a0post = results["A0_intact (hearing)"]
    a2p, _, _ = results["A2b_severed (deaf)"]
    print("\n--- reading:")
    clean = [k for k in usable if a2p[k] == 0 and lava_probe[k] == 0]
    if not clean:
        print("    NO channel has both controls at 0% — nothing here is")
        print("    text-attributable. STOP and fix the diagnostic.")
    for k in sorted(clean, key=lambda k: -a0p[k]):
        print(f"    {k:22s} width at probe = {a0p[k]/n*100:5.1f}%   "
              f"(deaf {a2p[k]}/{n}, lava {lava_probe[k]}/{n})")
    best = max(clean, key=lambda k: a0p[k]) if clean else None
    if best:
        print(f"\n    widest clean channel: {best} at {a0p[best]/n*100:.1f}%")
        print(f"    old journal channel (mood bucket) measured 33.3% and the")
        print(f"    screen built on it returned DiD 0.042 against a 0.20 bar.")
        print(f"    carry-over check: divergence at the pivot turn "
              f"{a0pv[best]/n*100:.1f}% -> still there at the probe "
              f"{a0p[best]/n*100:.1f}%")
    print(f"\n({time.time()-t0:.0f}s, {n} seeds)")


if __name__ == "__main__":
    main()
