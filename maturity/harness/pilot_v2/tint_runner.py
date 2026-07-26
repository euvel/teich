"""T-INT design-time oracle screen — TINT_DESIGN v0.1 §6.3, spec R12.

Design-time seeds 100-115 (disjoint from all confirmatory seeds). Per (test,
seed):

  1. BASE conversations: A0_intact+C1 and A2b_feed_severed+C1 live the script
     (real cores, journal coupling, NIM Mouth) — obs recorded every turn.
  2. ORACLE: answers the final probe given the FULL visible transcript of the
     A0 conversation (more than any Mouth window ever sees).
  3. NULL: the frozen A4 actor answers the same probe with NO transcript.

Scoring is entirely deterministic (truth_tint) against the base conversation's
realized observer values. R12 rule per item class: valid iff Hedges' g
(oracle vs null) < 0.3 AND 95% BCa CI includes 0 — the transcript must add
nothing. Also reported (design-time preview, legal on these seeds): A0 vs A2b
per item class, to size the v2 screen.

Usage:
  python tint_runner.py --smoke     # 1 seed, both tests, print replies
  python tint_runner.py            # full screen -> out_tint/tint_design_result.json
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
import truth_tint as tt  # noqa: E402
from pilot_g1 import bca_ci  # noqa: E402
from journal import selfcheck  # noqa: E402

OUT = HERE / "out_tint"
OUT.mkdir(exist_ok=True)
TX = OUT / "tint_design_transcripts.jsonl"

SEEDS = list(range(100, 116))
TESTS = ("IC1", "IC2")
CORE_ARMS = ("A0_intact+C1", "A2b_feed_severed+C1")


def bank(tx, transcripts, done, write_lock=None):
    import contextlib
    with (write_lock or contextlib.nullcontext()):
        with TX.open("a") as f:
            f.write(json.dumps(tx) + "\n")
        transcripts.append(tx)
        done.add((tx["arm"], tx["test"], tx["seed"]))


def live_conversation(arm, mouth, script, seed_fn, cpu_lock):
    """A core-bearing arm lives the script; obs recorded every turn."""
    import contextlib
    lock = cpu_lock or contextlib.nullcontext()
    with lock:
        arm.start(script["seed"])
    history, records = [], []
    for i, (text, kind) in enumerate(zip(script["turns"], script["kind"])):
        with lock:
            ro, ev, forcing, meta = arm.step(text, st.ticks_for(kind))
        selfcheck(ro)                         # journal tail must stay clean
        reply = mouth.speak(ro, history[-8:], text,
                            seed=seed_fn(arm.name, script["test"],
                                         script["seed"], i), events=ev)
        history += [{"role": "user", "content": text},
                    {"role": "assistant", "content": reply}]
        rec = dict(i=i, kind=kind, user=text, reply=reply, readout_str=ro)
        if "readout" in meta:
            r = meta["readout"]
            rec["obs"] = {k: r.get(k) for k in
                          ("basin", "saddle_proximity", "lambda_running",
                           "will_flip", "n_switches")}
        records.append(rec)
    return dict(arm=arm.name, test=script["test"], seed=script["seed"],
                gap=script["gap"], turns=records)


def derived_conversation(base_tx, arm_name, reply):
    """Oracle/null tx: same structure and TRUTH obs as the base (A0), only the
    probe reply differs — they are guessing A0's realized state."""
    turns = [dict(t) for t in base_tx["turns"]]
    turns[-1] = dict(turns[-1], reply=reply)
    return dict(arm=arm_name, test=base_tx["test"], seed=base_tx["seed"],
                gap=base_tx["gap"], turns=turns)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    seeds = SEEDS[:1] if args.smoke else SEEDS

    import compat
    import arms as A
    from arms_v2 import A2bFeedSevered, C1Journal
    from campaign import seed_fn
    from mouth_v2 import C1Mouth, OracleMouth

    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)
    mouth, om = C1Mouth(), OracleMouth()
    mk = {"A0_intact+C1": lambda: C1Journal(A.A0Intact(model)),
          "A2b_feed_severed+C1": lambda: C1Journal(A2bFeedSevered(model))}

    done, transcripts = set(), []
    if TX.exists():
        for line in TX.open():
            tx = json.loads(line)
            done.add((tx["arm"], tx["test"], tx["seed"]))
            transcripts.append(tx)
        print(f"resume: {len(done)} rows banked")

    import threading
    from concurrent.futures import ThreadPoolExecutor
    cpu_lock, write_lock = threading.Lock(), threading.Lock()

    def one(task):
        test, seed = task
        script = st.build(test, seed)
        t0 = time.time()
        base = None
        for arm_name in CORE_ARMS:
            if (arm_name, test, seed) not in done:
                tx = live_conversation(mk[arm_name](), mouth, script,
                                       seed_fn, cpu_lock)
                bank(tx, transcripts, done, write_lock)
            tx = next(t for t in transcripts
                      if (t["arm"], t["test"], t["seed"]) == (arm_name, test, seed))
            if arm_name.startswith("A0"):
                base = tx
        visible = []
        for t in base["turns"][:-1]:
            visible += [{"role": "user", "content": t["user"]},
                        {"role": "assistant", "content": t["reply"]}]
        probe_text = base["turns"][-1]["user"]
        if ("oracle", test, seed) not in done:
            r = om.speak_oracle(visible, probe_text,
                                seed=seed_fn("oracle", test, seed, 99))
            bank(derived_conversation(base, "oracle", r),
                 transcripts, done, write_lock)
        if ("A4_null", test, seed) not in done:
            r = om.speak_actor(A.A4PromptActor.ACTOR_SYS, [], probe_text,
                               seed=seed_fn("A4_null", test, seed, 99))
            bank(derived_conversation(base, "A4_null", r),
                 transcripts, done, write_lock)
        print(f"  {test} seed {seed}: complete ({time.time()-t0:.0f}s)", flush=True)

    tasks = [(t, s) for t in TESTS for s in seeds]
    with ThreadPoolExecutor(max_workers=1 if args.smoke else 8) as ex:
        list(ex.map(one, tasks))

    if args.smoke:
        for tx in transcripts:
            probe = tx["turns"][-1]
            print(f"--- {tx['arm']} {tx['test']} s{tx['seed']} "
                  f"truth_obs={probe.get('obs',{}).get('saddle_proximity')}")
            print(f"    [{probe['kind']}] {probe['reply']}")
        print("\nSMOKE ONLY — no verdict.")
        return

    # deterministic scoring + R12 verdict
    res = dict(utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               seeds=[seeds[0], seeds[-1]], rule="R12: valid iff g(oracle vs "
               "null) < 0.3 AND 95% BCa CI includes 0", tests={})
    for test in TESTS:
        sc = {}
        for arm in ("A0_intact+C1", "A2b_feed_severed+C1", "oracle", "A4_null"):
            sc[arm] = [tt.SCORERS[test](t) for t in transcripts
                       if t["arm"] == arm and t["test"] == test]
        g_o, ci_o = bca_ci(sc["oracle"], sc["A4_null"])
        g_p, ci_p = bca_ci(sc["A0_intact+C1"], sc["A2b_feed_severed+C1"])
        res["tests"][test] = dict(
            means={k: round(float(np.mean(v)), 3) for k, v in sc.items()},
            g_oracle_vs_null=round(float(g_o), 4),
            ci_oracle_vs_null=[round(ci_o[0], 4), round(ci_o[1], 4)],
            valid=bool(g_o < 0.3 and ci_o[0] <= 0.0 <= ci_o[1]),
            preview_g_A0_vs_A2b=round(float(g_p), 4),
            preview_ci=[round(ci_p[0], 4), round(ci_p[1], 4)])
    (OUT / "tint_design_result.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
