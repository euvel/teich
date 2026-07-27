"""A3 screen — can Teich predict its own next move?

Founder Gate-0, 2026-07-27: variant A3, n=96 per arm, bar 0.20 with CI
excluding 0, journal energy clause dropped.

  A0_intact       own journal      -> scored against its own realized future
  A0_shufjournal  a donor's journal -> scored against its own realized future

Ground truth = did `basin` actually differ W=75 ticks after the probe. Chance
is 0.625 (always answering "stay"), NOT 0.5.

  python pilot_a3.py --design            # design seeds 600-623, dump replies
                                         #   (for building the mapping ONLY)
  python pilot_a3.py --smoke             # 1 confirmatory-shaped seed, no score
  python pilot_a3.py --shard K --nshards 8
  python pilot_a3.py --finalize          # merge, score, one look, decide
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
import truth_a3 as ta  # noqa: E402
from journal_a3 import selfcheck  # noqa: E402
from pilot_g1 import _phi, _z, hedges_g  # noqa: E402

OUT = HERE / "out_a3"
OUT.mkdir(exist_ok=True)
TX = OUT / "a3_transcripts.jsonl"
DESIGN_TX = OUT / "a3_design.jsonl"

ARMS = ("A0_intact", "A0_shufjournal")
SEEDS = list(range(400, 496))            # confirmatory, n=96 — never run before freeze
DESIGN_SEEDS = list(range(600, 624))     # mapping construction ONLY
BAR = 0.20


def cells(seeds=None):
    seeds = SEEDS if seeds is None else seeds
    return [(a, s) for s in seeds for a in ARMS]


def paired_bootstrap(per_seed, n_boot=10000, seed=0, alpha=0.05):
    """BCa CI for the mean per-seed accuracy difference (resamples seeds)."""
    rng = np.random.RandomState(seed)
    x = np.asarray(per_seed, float)
    theta = x.mean()
    boots = np.array([x[rng.randint(0, len(x), len(x))].mean()
                      for _ in range(n_boot)])
    z0 = _z(np.mean(boots < theta))
    jack = np.array([np.delete(x, i).mean() for i in range(len(x))])
    num = ((jack.mean() - jack) ** 3).sum()
    den = 6.0 * (((jack.mean() - jack) ** 2).sum() ** 1.5)
    acc = num / den if den else 0.0
    lo, hi = [float(np.percentile(boots, 100 * _phi(
        z0 + (z0 + _z(q)) / (1 - acc * (z0 + _z(q)))))) for q in
        (alpha / 2, 1 - alpha / 2)]
    return float(theta), (lo, hi)


def generate(tasks, tx_path, workers=1, seeds_all=None, seed0=400):
    import compat
    from campaign import seed_fn
    from arms_a3 import A3Intact, A3ShufJournal, donor_seed
    from mouth_a3 import A3Mouth, A3Oracle

    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)
    mouth, oracle = A3Mouth(), A3Oracle()
    n_seeds = len(seeds_all) if seeds_all else len(SEEDS)

    # Resume from EVERY banked ledger, not just this shard's, so a conversation
    # generated anywhere is never paid for twice and the partition may change
    # between dispatches without orphaning work (the T-INT fix).
    done = set()
    for p in sorted(OUT.glob("shard_*.jsonl")) + sorted(OUT.glob("design_*.jsonl")) \
            + ([tx_path] if tx_path.exists() else []):
        for line in p.open():
            t = json.loads(line)
            done.add((t["arm"], t["seed"]))
    print(f"resume: {len(done)} conversations already banked (all ledgers)")

    import threading
    from concurrent.futures import ThreadPoolExecutor
    cpu_lock, write_lock = threading.Lock(), threading.Lock()

    def one(task):
        arm_name, seed = task
        if (arm_name, seed) in done:
            return None
        t0 = time.time()
        script = sa.build_a3(seed)
        with cpu_lock:
            if arm_name == "A0_intact":
                arm = A3Intact(model)
            else:
                arm = A3ShufJournal(model, donor_seed(seed, n_seeds, seed0))
            arm.start(seed)
        history, records, oracle_reply = [], [], None
        for i, (text, kind) in enumerate(zip(script["turns"], script["kind"])):
            with cpu_lock:
                jt, ev, _f, meta = arm.step(text, sa.ticks_for(kind))
            selfcheck(jt)
            s = seed_fn("a3", "A3", seed, i)
            reply = mouth.speak(jt, history[-8:], text, seed=s, events=ev)
            is_probe = kind.startswith("probe-gap")
            if is_probe and arm_name == "A0_intact":
                # R12 oracle: same visible transcript, no journal, no readout.
                # Costs one extra call, no extra conversation.
                oracle_reply = oracle.speak_oracle(list(history), text, seed=s)
            history += [{"role": "user", "content": text},
                        {"role": "assistant", "content": reply}]
            rec = dict(i=i, kind=kind, user=text, reply=reply, journal=jt)
            if "readout" in meta:
                r = meta["readout"]
                rec["obs"] = {k: r.get(k) for k in
                              ("basin", "lobe_coord", "saddle_proximity",
                               "will_flip", "steps_to_switch", "n_switches")}
            records.append(rec)
        # live the prediction window and record WHAT ACTUALLY HAPPENED
        with cpu_lock:
            b_before, b_after = arm.realized(sa.PREDICT_WINDOW)
        tx = dict(arm=arm_name, test="A3", seed=seed, gap=script["gap"],
                  window=sa.PREDICT_WINDOW, basin_before=b_before,
                  basin_after=b_after, truth=ta.realized(b_before, b_after),
                  oracle_reply=oracle_reply, turns=records)
        with write_lock:
            with tx_path.open("a") as f:
                f.write(json.dumps(tx) + "\n")
        print(f"  {arm_name} s{seed}: truth={tx['truth']} ({time.time()-t0:.0f}s)",
              flush=True)
        return tx

    with ThreadPoolExecutor(max_workers=workers) as ex:
        return [t for t in ex.map(one, tasks) if t is not None]


def merge():
    best = {}
    files = ([TX] if TX.exists() else []) + sorted(OUT.glob("shard_*.jsonl"))
    for p in files:
        for line in p.open():
            t = json.loads(line)
            best[(t["arm"], t["seed"])] = t
    txs = list(best.values())
    TX.write_text("".join(json.dumps(t) + "\n" for t in txs))
    print(f"merged {len(files)} files -> {len(txs)} conversations")
    return txs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--shard", type=int, default=None)
    ap.add_argument("--nshards", type=int, default=8)
    ap.add_argument("--finalize", action="store_true")
    args = ap.parse_args()

    if args.design:
        # DESIGN SEEDS ONLY. Confirmatory seeds 400-495 are not touched.
        banked = set()
        for p in sorted(OUT.glob("design_*.jsonl")) + \
                ([DESIGN_TX] if DESIGN_TX.exists() else []):
            for line in p.open():
                t = json.loads(line)
                banked.add((t["arm"], t["seed"]))
        missing = [c for c in cells(DESIGN_SEEDS) if c not in banked]
        if args.shard is not None:
            tasks = missing[args.shard::args.nshards]
            path = OUT / f"design_{args.shard}.jsonl"
        else:
            tasks, path = missing, DESIGN_TX
        print(f"{len(banked)}/{len(cells(DESIGN_SEEDS))} banked; "
              f"{len(missing)} missing; this run takes {len(tasks)}")
        txs = generate(tasks, path, workers=1,
                       seeds_all=DESIGN_SEEDS, seed0=600)
        print(f"\n=== {len(txs)} design conversations -> {path}")
        print("Build the reply->{stay,turn} mapping from THESE ONLY, freeze it,")
        print("and commit before any confirmatory generation.")
        return

    if args.smoke:
        # seeds_all has 2 entries so donor_seed has somewhere to land; only
        # seed 900 is actually run. Both are outside every scored range.
        txs = generate([(a, 900) for a in ARMS], OUT / "smoke.jsonl",
                       seeds_all=[900, 901], seed0=900)
        for t in txs:
            p = t["turns"][-1]
            print(f"--- {t['arm']} truth={t['truth']}")
            print(f"    journal: {p['journal'][-200:]!r}")
            print(f"    reply  : {p['reply']!r}")
        print("\nSMOKE ONLY — no decision, seed 900 is outside every scored range.")
        return

    if args.shard is not None:
        banked = set()
        for p in sorted(OUT.glob("shard_*.jsonl")) + ([TX] if TX.exists() else []):
            for line in p.open():
                t = json.loads(line)
                banked.add((t["arm"], t["seed"]))
        missing = [c for c in cells() if c not in banked]
        tasks = missing[args.shard::args.nshards]
        print(f"{len(banked)}/{len(cells())} banked; {len(missing)} missing; "
              f"this shard takes {len(tasks)}")
        generate(tasks, OUT / f"shard_{args.shard}.jsonl", workers=1)
        print(f"shard {args.shard}/{args.nshards} complete")
        return

    if not args.finalize:
        sys.exit("use --design, --smoke, --shard K, or --finalize")

    from mapping_a3 import said_a3
    txs = merge()
    have = {(t["arm"], t["seed"]) for t in txs}
    missing = [c for c in cells() if c not in have]
    if missing:
        sys.exit(f"finalize refused: {len(missing)} conversations missing "
                 f"(e.g. {missing[:3]}) — re-dispatch shards first.")

    idx, unmapped = {}, {a: 0 for a in ARMS}
    for t in txs:
        said = said_a3(t["turns"][-1]["reply"])
        if said is None:
            unmapped[t["arm"]] += 1
        idx[(t["arm"], t["seed"])] = ta.score(said, t["truth"])

    # per-seed paired difference; a seed is dropped only if EITHER arm is unmapped
    per_seed, used = [], []
    for s in SEEDS:
        a, b = idx[(ARMS[0], s)], idx[(ARMS[1], s)]
        if a is None or b is None:
            continue
        per_seed.append(a - b)
        used.append(s)
    diff, (lo, hi) = paired_bootstrap(per_seed)

    def acc(arm):
        v = [idx[(arm, s)] for s in used]
        return float(np.mean(v))

    truths = [t["truth"] for t in txs if t["arm"] == ARMS[0]]
    base = float(np.mean([x == "turn" for x in truths]))
    const_guess = max(base, 1 - base)

    # R12 oracle: transcript-only, must not beat the constant-guess baseline
    o_scored = [(said_a3(t["oracle_reply"]), t["truth"]) for t in txs
                if t["arm"] == ARMS[0] and t.get("oracle_reply")]
    o_ok = [1.0 if s == tr else 0.0 for s, tr in o_scored if s is not None]
    oracle_acc = float(np.mean(o_ok)) if o_ok else None

    ceiling = "OK" if 0.35 <= base <= 0.65 else "CEILING-LIMITED"
    voided = (oracle_acc is not None and oracle_acc > const_guess)
    decision = "PASS" if (diff >= BAR and lo > 0 and not voided) else "FAIL"
    if voided:
        decision = "VOID-R12"

    res = dict(utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               n_conversations=len(txs), n_seeds_used=len(used),
               acc_intact=round(acc(ARMS[0]), 4),
               acc_shufjournal=round(acc(ARMS[1]), 4),
               diff=round(diff, 4), ci=[round(lo, 4), round(hi, 4)],
               hedges_g=round(float(hedges_g(per_seed, [0.0] * len(per_seed))), 4),
               base_rate_turn=round(base, 4),
               const_guess_baseline=round(const_guess, 4),
               oracle_acc=(round(oracle_acc, 4) if oracle_acc is not None else None),
               unmapped=unmapped, label_balance=ceiling,
               bar=f"diff >= {BAR} AND ci_low > 0 AND oracle <= {const_guess:.3f}",
               decision=decision)
    (OUT / "a3_result.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
