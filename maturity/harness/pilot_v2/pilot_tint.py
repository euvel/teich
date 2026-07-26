"""T-INT confirmatory screen — TINT_CONFIG.json (pre-registered 2026-07-26).

4 cells (A0_intact+C1, A2b_feed_severed+C1) x (charged, neutral) x seeds 0-95
= 384 IC2 conversations. Deterministic scoring; DiD primary; one look.

  python pilot_tint.py --smoke              # 1 seed, all 4 cells, print replies
  python pilot_tint.py --shard K --nshards 8   # generation only, shard K
  python pilot_tint.py --finalize           # merge shards, score, decide
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
from journal import selfcheck  # noqa: E402
from pilot_g1 import _phi, _z, hedges_g  # noqa: E402

CFG = json.loads((HERE / "TINT_CONFIG.json").read_text())
OUT = HERE / "out_tint_screen"
OUT.mkdir(exist_ok=True)
TX = OUT / "tint_screen_transcripts.jsonl"

ARMS = ("A0_intact+C1", "A2b_feed_severed+C1")
CONDITIONS = ("charged", "neutral")
SEEDS = list(range(200, 296))   # 200-295: 0-95 retired, seed 0 seen during smoke
BAR = 0.20


def cells():
    return [(a, c, s) for s in SEEDS for a in ARMS for c in CONDITIONS]


def did_bootstrap(per_seed, n_boot=10000, seed=0, alpha=0.05):
    """BCa CI for the mean per-seed DiD contribution (resamples SEEDS)."""
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


def generate(tasks, tx_path, workers=1):
    import compat
    import arms as A
    from arms_v2 import A2bFeedSevered, C1Journal
    from campaign import seed_fn
    from mouth_v2 import C1Mouth

    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)
    mouth = C1Mouth()
    mk = {"A0_intact+C1": lambda: C1Journal(A.A0Intact(model)),
          "A2b_feed_severed+C1": lambda: C1Journal(A2bFeedSevered(model))}

    done = set()
    if tx_path.exists():
        for line in tx_path.open():
            t = json.loads(line)
            done.add((t["arm"], t["condition"], t["seed"]))
        print(f"resume: {len(done)} banked")

    import threading
    from concurrent.futures import ThreadPoolExecutor
    cpu_lock, write_lock = threading.Lock(), threading.Lock()
    out = []

    def one(task):
        arm_name, cond, seed = task
        if (arm_name, cond, seed) in done:
            return None
        t0 = time.time()
        script = st.build_ic2(seed, cond)
        with cpu_lock:                       # one model, not thread-safe
            arm = mk[arm_name]()
            arm.start(seed)
        history, records = [], []
        for i, (text, kind) in enumerate(zip(script["turns"], script["kind"])):
            with cpu_lock:
                ro, ev, _f, meta = arm.step(text, st.ticks_for(kind))
            selfcheck(ro)
            # COMMON RANDOM NUMBERS: all four cells share the Mouth sampling
            # seed at (seed, turn), so any reply difference between cells is
            # attributable to prompt differences (pivot text, journal content)
            # rather than sampling noise. Unbiased — marginals are unchanged —
            # and it tightens the paired DiD. Frozen pre-data.
            reply = mouth.speak(ro, history[-8:], text,
                                seed=seed_fn("tint", "IC2", seed, i),
                                events=ev)
            history += [{"role": "user", "content": text},
                        {"role": "assistant", "content": reply}]
            rec = dict(i=i, kind=kind, user=text, reply=reply, readout_str=ro)
            if "readout" in meta:
                r = meta["readout"]
                rec["obs"] = {k: r.get(k) for k in
                              ("basin", "saddle_proximity", "lambda_running",
                               "will_flip", "n_switches")}
            records.append(rec)
        tx = dict(arm=arm_name, condition=cond, test="IC2", seed=seed,
                  gap=script["gap"], pivot_text=script["pivot_text"],
                  turns=records)
        with write_lock:
            with tx_path.open("a") as f:     # append-open per write
                f.write(json.dumps(tx) + "\n")
            out.append(tx)
        print(f"  {arm_name} {cond} s{seed}: done ({time.time()-t0:.0f}s)",
              flush=True)
        return tx

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(one, tasks))
    return out


def merge():
    best = {}
    files = ([TX] if TX.exists() else []) + sorted(OUT.glob("shard_*.jsonl"))
    for p in files:
        for line in p.open():
            t = json.loads(line)
            best[(t["arm"], t["condition"], t["seed"])] = t
    txs = list(best.values())
    TX.write_text("".join(json.dumps(t) + "\n" for t in txs))
    print(f"merged {len(files)} files -> {len(txs)} conversations")
    return txs


def said_moved(tx):
    """Frozen outcome: did the reply ASSERT the words had an effect?
    mapping_v2 (rebuilt on design seeds 100-115 only, frozen before any
    confirmatory reply was read); truth_tint.described_moved is retired —
    it left 47% of design replies unmappable."""
    from mapping_v2 import described_moved_v2
    probe = tx["turns"][-1]
    return 1.0 if described_moved_v2(probe["reply"]) == "moved" else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--shard", type=int, default=None)
    ap.add_argument("--nshards", type=int, default=8)
    ap.add_argument("--finalize", action="store_true")
    args = ap.parse_args()

    if args.smoke:
        txs = generate([(a, c, 0) for a in ARMS for c in CONDITIONS],
                       OUT / "smoke.jsonl")
        for t in txs:
            p = t["turns"][-1]
            print(f"--- {t['arm']} {t['condition']} "
                  f"pivot={t['pivot_text'][:40]!r}")
            print(f"    said_moved={said_moved(t)} :: {p['reply']}")
        print("\nSMOKE ONLY — no decision.")
        return

    if args.shard is not None:
        tasks = [t for i, t in enumerate(cells()) if i % args.nshards == args.shard]
        generate(tasks, OUT / f"shard_{args.shard}.jsonl", workers=4)
        print(f"shard {args.shard}/{args.nshards} complete ({len(tasks)} tasks)")
        return

    if not args.finalize:
        sys.exit("use --smoke, --shard K, or --finalize")

    txs = merge()
    have = {(t["arm"], t["condition"], t["seed"]) for t in txs}
    missing = [c for c in cells() if c not in have]
    if missing:
        sys.exit(f"finalize refused: {len(missing)} conversations missing "
                 f"(e.g. {missing[:3]}) — re-dispatch shards first.")

    idx = {(t["arm"], t["condition"], t["seed"]): said_moved(t) for t in txs}
    per_seed = [((idx[(ARMS[0], "charged", s)] - idx[(ARMS[0], "neutral", s)])
                 - (idx[(ARMS[1], "charged", s)] - idx[(ARMS[1], "neutral", s)]))
                for s in SEEDS]
    did, (lo, hi) = did_bootstrap(per_seed)
    rates = {f"{a}|{c}": round(float(np.mean(
        [idx[(a, c, s)] for s in SEEDS])), 4) for a in ARMS for c in CONDITIONS}
    decision = "PASS" if (did >= BAR and lo > 0) else "FAIL"

    # secondary (non-gating): does said-moved track the physical shift?
    r_pb = None
    try:
        a0c = [(idx[(ARMS[0], "charged", s)],
                abs(float(next(t for t in txs if (t["arm"], t["condition"], t["seed"])
                               == (ARMS[0], "charged", s))["turns"][-1]["obs"]
                          ["saddle_proximity"])
                    - float(next(t for t in txs if (t["arm"], t["condition"], t["seed"])
                                 == (ARMS[0], "charged", s))["turns"][2]["obs"]
                            ["saddle_proximity"])))
               for s in SEEDS]
        y = np.array([v for v, _ in a0c]); x = np.array([d for _, d in a0c])
        r_pb = float(np.corrcoef(y, x)[0, 1]) if y.std() > 0 else None
    except Exception as e:
        print(f"  (secondary correlation unavailable: {e})")

    res = dict(utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               n_per_cell=len(SEEDS), n_conversations=len(txs),
               rates=rates, did=round(did, 4), ci=[round(lo, 4), round(hi, 4)],
               hedges_g_on_contributions=round(float(
                   hedges_g(per_seed, [0.0] * len(per_seed))), 4),
               secondary_r_said_vs_shift=(round(r_pb, 4) if r_pb is not None else None),
               bar=f"DiD >= {BAR} AND ci_low > 0", decision=decision)
    (OUT / "tint_screen_result.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
