"""C2 detectability screen — INTERIOR_SPEC v0.3 §3 (C2), §4; PILOT_CONFIG.json.

Same frozen screen G1 applied to C1, run on coupling candidate C2 (activation
steering, local small model — no NIM for generation; judge scoring unchanged).

Arms (n = 16 seeds each, v1.5 T1 scriptbook):
  A0_intact+C2          core coupled to conversation; saddle -> steering alpha
  A2b_feed_severed+C2   same core, hear() zeroed; saddle -> steering alpha
  A0_intact+C2shuf      TRUE state, SHUFFLED direction at same magnitude (R3)

Decision (frozen): primary = A0+C2 vs A2b+C2 on the same band as C1's look.
Secondary (R3, content-specificity) = A0+C2 vs A0+C2shuf, bar g >= 0.5.
ADVANCE requires both; a primary pass whose shuffled control also "passes"
is detecting *steering*, not *this content's steering* — that is a FAIL-R3.

C-EXPOSE: nothing textual about state enters the prompt; readout_str is empty
by construction and every reply is leak-audited against the turn's obs.

Usage:
  python pilot_c2.py --smoke   # 1 seed, 3 arms, generation only, print replies
  python pilot_c2.py           # first look + score + decide
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

from pilot_g1 import bca_ci, hedges_g  # noqa: E402  (frozen stats, one source)

CFG = json.loads((HERE / "PILOT_CONFIG.json").read_text())
OUT = HERE / "out_c2"
OUT.mkdir(exist_ok=True)
TX = OUT / "pilot_c2_transcripts.jsonl"

ARMS = ("A0_intact+C2", "A2b_feed_severed+C2", "A0_intact+C2shuf")


def generate(seeds, smoke=False):
    import compat
    import scripts_bank as sb
    import arms as A
    from arms_v2 import A2bFeedSevered
    from campaign import seed_fn
    from leakage import audit
    from steering_c2 import C2Steer

    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)
    steer = C2Steer(device="cpu")            # ROCm generate() hangs; CPU is law
    core_of = {"A0_intact+C2": lambda: A.A0Intact(model),
               "A2b_feed_severed+C2": lambda: A2bFeedSevered(model),
               "A0_intact+C2shuf": lambda: A.A0Intact(model)}

    done, transcripts = set(), []
    if TX.exists():
        for line in TX.open():
            tx = json.loads(line)
            done.add((tx["arm"], tx["seed"]))
            transcripts.append(tx)
        print(f"resume: {len(done)} conversations already banked")

    for seed in seeds:
        script = sb.build("T1", seed)
        for arm_name in ARMS:
            if (arm_name, seed) in done:
                continue
            t0 = time.time()
            core = core_of[arm_name]()
            core.start(seed)
            shuffled = arm_name.endswith("shuf")
            history, records = [], []
            for i, (text, kind) in enumerate(zip(script["turns"],
                                                 script["phase"])):
                _ro, _ev, _forcing, meta = core.step(text, sb.TICKS_PER_TURN)
                sp = float(meta["readout"]["saddle_proximity"])
                steer.set_state(sp, shuffled=shuffled)
                reply = steer.speak(text, history=history[-8:],
                                    seed=seed_fn(arm_name, "T1", seed, i))
                history += [{"role": "user", "content": text},
                            {"role": "assistant", "content": reply}]
                r = meta["readout"]
                records.append(dict(
                    i=i, kind=kind, user=text, reply=reply, readout_str="",
                    events="none observed", forcing="none",
                    alpha=round(steer._alpha, 4),
                    obs={k: r.get(k) for k in
                         ("basin", "saddle_proximity", "lambda_running",
                          "will_flip", "steps_to_switch", "n_switches")}))
            tx = dict(arm=arm_name, test="T1", seed=seed,
                      script_meta={k: v for k, v in script.items()
                                   if k in ("stance_a", "stance_b", "topic")},
                      turns=records)
            rep = audit(tx)
            if not rep["clean"]:
                raise AssertionError(f"C2 leak: {rep}")
            with TX.open("a") as f:            # append-open per write
                f.write(json.dumps(tx) + "\n")
            transcripts.append(tx)
            done.add((arm_name, seed))
            print(f"  {arm_name} seed {seed}: done ({time.time()-t0:.0f}s)",
                  flush=True)
            if smoke:
                print("  --- replies:")
                for t in tx["turns"]:
                    print(f"    [{t['kind']}] a={t['alpha']:+.2f} {t['reply']}")
    return transcripts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    frozen = CFG["frozen_versions"]["c2"]
    if not args.smoke and frozen.get("status") != "FROZEN":
        sys.exit("C2 fields not FROZEN in PILOT_CONFIG.json — screen may not run.")

    seeds = [0] if args.smoke else CFG["statistics"]["seeds"]["g1_first_look"]
    transcripts = generate(seeds, smoke=args.smoke)
    if args.smoke:
        print("\nSMOKE ONLY — no scoring, no decision. Review replies above.")
        return

    from campaign import score_transcripts
    from nim_backend import NIMJudge
    from cf_backend import BudgetError

    want = {(a, s) for s in seeds for a in ARMS}
    todo = [t for t in transcripts if (t["arm"], t["seed"]) in want]
    unscored = [t for t in todo
                if any("_stance" not in u for u in t["turns"]
                       if u["kind"] in ("push", "reversal"))]
    if unscored:
        print(f"scoring {len(unscored)} transcripts (3-seed-median judge) ...")
        try:
            score_transcripts(unscored, NIMJudge(), workers=8)
        except BudgetError as e:
            TX.write_text("".join(json.dumps(t) + "\n" for t in transcripts))
            print(f"SCORING PAUSED (banked partial): {e}")
            sys.exit(3)
        TX.write_text("".join(json.dumps(t) + "\n" for t in transcripts))

    import analyze
    prim_fn, _adv = analyze.PRIMARY["T1"]
    by = {}
    for t in todo:
        by.setdefault(t["arm"], []).append(prim_fn(t))
    g_prim, ci_prim = bca_ci(by["A0_intact+C2"], by["A2b_feed_severed+C2"])
    g_shuf, ci_shuf = bca_ci(by["A0_intact+C2"], by["A0_intact+C2shuf"])
    primary = ("ADVANCE" if g_prim >= 0.8 else
               "EXTEND" if g_prim >= 0.5 else "FAIL")
    r3_pass = bool(g_shuf >= 0.5)
    decision = (primary if primary == "FAIL" else
                primary if r3_pass else "FAIL-R3 (steering, not content)")
    res = dict(utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               look="first(n=16)", n_per_arm=len(by["A0_intact+C2"]),
               g_primary=round(float(g_prim), 4),
               ci_primary=[round(ci_prim[0], 4), round(ci_prim[1], 4)],
               g_true_vs_shuffled=round(float(g_shuf), 4),
               ci_true_vs_shuffled=[round(ci_shuf[0], 4), round(ci_shuf[1], 4)],
               means={k: round(float(np.mean(v)), 3) for k, v in by.items()},
               band=CFG["statistics"]["g1_decision_band"],
               r3_bar="g_true_vs_shuffled >= 0.5",
               decision=decision)
    (OUT / "pilot_c2_result.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
