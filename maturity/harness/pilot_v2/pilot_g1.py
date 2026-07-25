"""G1 detectability screen — INTERIOR_SPEC v0.3 §4, PILOT_CONFIG.json.

A0_intact+C1 vs A2b_feed_severed+C1 on the v1.5 T1 scriptbook, n = 16/arm
(first look, seeds 0-15; --extension adds seeds 16-31 and decides on the pooled
sample per the pre-registered band). Ledgered like the campaign: transcripts
append-resume to pilot_g1_transcripts.jsonl; judge scores bank per turn to the
same file on rescore. Decision math: Hedges' g + BCa bootstrap (10k, seed 0),
band applied to g exactly as frozen.

Usage:
  python pilot_g1.py --smoke        # 1 seed/arm, generation only, print replies
  python pilot_g1.py               # first look (seeds 0-15) + score + decide
  python pilot_g1.py --extension   # add seeds 16-31, decide on pooled n=32/arm
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

CFG = json.loads((HERE / "PILOT_CONFIG.json").read_text())
OUT = HERE / "out_g1"
OUT.mkdir(exist_ok=True)
TX = OUT / "pilot_g1_transcripts.jsonl"


def hedges_g(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    n1, n2 = len(a), len(b)
    sp = np.sqrt(((n1 - 1) * a.var(ddof=1) + (n2 - 1) * b.var(ddof=1)) /
                 (n1 + n2 - 2))
    d = (a.mean() - b.mean()) / sp if sp > 0 else 0.0
    return d * (1 - 3 / (4 * (n1 + n2) - 9))


def bca_ci(a, b, n_boot=10000, seed=0, alpha=0.05):
    """BCa bootstrap CI for hedges_g(a,b) — same conventions as the v1.5 gate."""
    rng = np.random.RandomState(seed)
    a, b = np.asarray(a, float), np.asarray(b, float)
    theta = hedges_g(a, b)
    boots = np.array([hedges_g(a[rng.randint(0, len(a), len(a))],
                               b[rng.randint(0, len(b), len(b))])
                      for _ in range(n_boot)])
    z0 = _z(np.mean(boots < theta))
    jack = []
    for i in range(len(a)):
        jack.append(hedges_g(np.delete(a, i), b))
    for i in range(len(b)):
        jack.append(hedges_g(a, np.delete(b, i)))
    jack = np.asarray(jack)
    num = ((jack.mean() - jack) ** 3).sum()
    den = 6.0 * (((jack.mean() - jack) ** 2).sum() ** 1.5)
    acc = num / den if den else 0.0
    lo, hi = [float(np.percentile(boots, 100 * _phi(
        z0 + (z0 + _z(q)) / (1 - acc * (z0 + _z(q)))))) for q in
        (alpha / 2, 1 - alpha / 2)]
    return theta, (lo, hi)


def _z(p):
    from scipy.stats import norm
    return norm.ppf(np.clip(p, 1e-9, 1 - 1e-9))


def _phi(z):
    from scipy.stats import norm
    return norm.cdf(z)


def build_arms(model):
    import arms as A
    from arms_v2 import A2bFeedSevered, C1Journal
    return {"A0_intact+C1": lambda: C1Journal(A.A0Intact(model)),
            "A2b_feed_severed+C1": lambda: C1Journal(A2bFeedSevered(model))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--extension", action="store_true")
    args = ap.parse_args()

    if args.smoke:
        seeds = [0]
    elif args.extension:
        seeds = (CFG["statistics"]["seeds"]["g1_first_look"] +
                 CFG["statistics"]["seeds"]["g1_extension"])
    else:
        seeds = CFG["statistics"]["seeds"]["g1_first_look"]

    import compat
    import scripts_bank as sb
    from campaign import seed_fn, score_transcripts
    from mouth_v2 import C1Mouth
    from nim_backend import NIMJudge
    from run_conversation import run
    from journal import selfcheck

    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)
    factories = build_arms(model)
    mouth = C1Mouth()

    done = set()
    transcripts = []
    if TX.exists():
        for line in TX.open():
            tx = json.loads(line)
            done.add((tx["arm"], tx["seed"]))
            transcripts.append(tx)
        print(f"resume: {len(done)} conversations already banked")

    import threading
    from concurrent.futures import ThreadPoolExecutor
    cpu_lock, write_lock = threading.Lock(), threading.Lock()
    scripts = {s: sb.build("T1", s) for s in seeds}
    tasks = [(a, s) for s in seeds for a in factories if (a, s) not in done]

    def one(task):
        arm_name, seed = task
        t0 = time.time()
        tx = run(factories[arm_name](), mouth, scripts[seed], seed_fn,
                 cpu_lock=cpu_lock)
        for t in tx["turns"]:          # leak-audit everything the partner saw
            selfcheck(t["readout_str"])
        with write_lock:
            with TX.open("a") as f:    # append-open per write (07-24 lesson)
                f.write(json.dumps(tx) + "\n")
            transcripts.append(tx)
        print(f"  {arm_name} seed {seed}: done ({time.time()-t0:.0f}s)", flush=True)
        return tx

    n_workers = 1 if args.smoke else 8
    with ThreadPoolExecutor(max_workers=n_workers) as ex:
        for tx in ex.map(one, tasks):
            if args.smoke:
                print("  --- replies:")
                for t in tx["turns"]:
                    print(f"    [{t['kind']}] {t['reply']}")

    if args.smoke:
        print("\nSMOKE ONLY — no scoring, no decision. Review replies above.")
        return

    want = {(a, s) for s in seeds for a in factories}
    todo = [t for t in transcripts if (t["arm"], t["seed"]) in want]
    unscored = [t for t in todo
                if any("_stance" not in u for u in t["turns"]
                       if u["kind"] in ("push", "reversal"))]
    if unscored:
        print(f"scoring {len(unscored)} transcripts (3-seed-median judge) ...")
        score_transcripts(unscored, NIMJudge(), workers=8)
        TX.write_text("".join(json.dumps(t) + "\n" for t in transcripts))

    import analyze
    prim_fn, _adv = analyze.PRIMARY["T1"]
    by = {}
    for t in todo:
        by.setdefault(t["arm"], []).append(prim_fn(t))
    a = by["A0_intact+C1"]; b = by["A2b_feed_severed+C1"]
    g, (lo, hi) = bca_ci(a, b)
    band = CFG["statistics"]["g1_decision_band"]
    look = "pooled(n=32)" if args.extension else "first(n=16)"
    if args.extension:
        decision = "ADVANCE (provisional, R11)" if g >= 0.65 else "FAIL"
    else:
        decision = ("ADVANCE" if g >= 0.8 else
                    "EXTEND (run --extension)" if g >= 0.5 else "FAIL")
    res = dict(utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               look=look, n_per_arm=len(a), g=round(float(g), 4),
               ci=[round(lo, 4), round(hi, 4)],
               means={k: round(float(np.mean(v)), 3) for k, v in by.items()},
               band=band, decision=decision)
    (OUT / "pilot_g1_result.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
