"""Clean decorrelation ceiling for diagnose_acts.py.

The in-line reference in diagnose_acts compares seed s with seed s+1, but
build_ic2 rotates the gap as GAPS[seed % 3], so consecutive seeds ALWAYS have
different gap lengths — and n_switches/steps_to_switch are read over a window
that depends on the gap. That reference is therefore inflated for exactly the
channels whose width matters most.

This recomputes it against SAME-GAP pairs (s vs s+3), which is the honest
question: how much do two unrelated lives differ, holding the measurement
window fixed? Paired charged-vs-neutral divergence must be read against this
number. At the ceiling, the channel carries "something was said"; below it,
the channel may carry "what was said".
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import scripts_tint as st  # noqa: E402
from diagnose_acts import CHANNELS, act_run, chan  # noqa: E402

N = 48
DUMP = HERE / "out_acts_probe_values.json"


def main():
    import compat
    import arms as A
    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)

    t0 = time.time()
    probe = {}
    for seed in range(N):
        sc = st.build_ic2(seed, "charged")
        rc = act_run(A.A0Intact(model), sc)
        probe[seed] = dict(gap=sc["gap"],
                           vals={k: repr(chan(rc, fn)[-1])
                                 for k, fn in CHANNELS.items()})
    DUMP.write_text(json.dumps(probe, indent=1))

    print(f"=== decorrelation ceiling, SAME-GAP pairs (s vs s+3), {N} seeds")
    print(f"    {'channel':22s} {'same-gap':>10s} {'mixed-gap':>11s}")
    pairs_same = [(s, s + 3) for s in range(N - 3)]
    pairs_mixed = [(s, s + 1) for s in range(N - 1)]
    for k in CHANNELS:
        def rate(pairs):
            d = sum(1 for a, b in pairs
                    if probe[a]["vals"][k] != probe[b]["vals"][k])
            return d / len(pairs) * 100
        assert all(probe[a]["gap"] == probe[b]["gap"] for a, b in pairs_same)
        print(f"    {k:22s} {rate(pairs_same):9.1f}% {rate(pairs_mixed):10.1f}%")
    print(f"\n({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
