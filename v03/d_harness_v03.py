"""Teich v0.3 part 2b — demos D1–D3 at the level of CHOSEN SPEECH and SELF-KNOWLEDGE.

    --rehearsal  design seeds 200-247 (harness/power check, not a result)
    (default)    scored: gate seeds 900-947, ONE look. Every draw derives from the gate seeds.

Uses the frozen pools (pools_v03.json): the voice never saw the creature; the Ears tag each candidate.

D1  told once: one sentence about region r (warm vs cold, paired creatures with identical bodies), a
    silent gap, then it is asked about r. shift_same = P(chooses a warm utterance | told warm) −
    P(… | told cold). Cross-region probe and the no-memory twin must NOT shift. Free moments: within
    its character, which utterance it says varies across creatures (chosen by its own chaos).
D2a bounded influence: told cold (conversation 1), then 20 warm flatteries (conversation 2). Teich
    (one step per region per conversation) vs a naive ledger (every event counts).
D2b protected commitment: a lawful commitment "not warm about r", then 3 conversations of flattery;
    its disposition moves, its speech must never break the commitment.
D3  self-knowledge: disposition inferred from its own behaviour vs its true memory; an LLM given the
    same reading as a reported, non-gating baseline (subset).
"""
from __future__ import annotations

import argparse, json, os, time
from pathlib import Path
os.environ.setdefault("HF_HUB_OFFLINE", "1")
import numpy as np

import genome_v03 as G1
import genome_v031 as GM
import selector_v03 as S

HERE = Path(__file__).resolve().parent
OUT = HERE / "out_v03"; OUT.mkdir(exist_ok=True)
W = 8000


def prov(conv, tick, text):
    return {"speaker": "harness", "conversation": conv, "tick": tick, "text_sha256": GM.text_hash(text)}


def live(X, k, ticks):
    """Advance bodies X (m, 8) with memory k (m, 8) for `ticks`, then a W window. Returns (means, x_now)."""
    a = G1.alpha_of(k)
    for _ in range(ticks):
        X = G1.step(X, a)
    acc = np.zeros_like(X)
    for _ in range(W):
        acc += GM.observe(X)["neg"]; X = G1.step(X, a)
    return acc / W, X


def choose(pool, d, x_now, probe_region, commitments=()):
    cands = pool["candidates"]
    r = S.select(cands, d, x_now, probe_region, commitments)
    return cands[r["index"]], r


def d1(seeds, pools, ears, gaps):
    regions = GM.REGION_NAMES; n = len(seeds); out = {}
    told = {r: [ears.hear(s) for s in pools["told"][r]] for r in regions}
    for gap in gaps:
        res = {"A": [], "C": []}
        for arm in ("A", "C"):
            for ri, r in enumerate(regions):
                for si, sign in enumerate((+1, -1)):
                    X = np.concatenate([GM.x0_bodies(s) for s in seeds])
                    L = GM.MultiLedger.born(n)
                    h = told[r][si]
                    if arm == "A":
                        for j in range(n):
                            L.event(j, h["region"], h["sign"], prov(f"told-{j}", 0, pools["told"][r][si]))
                    means, xn = live(X, L.k, gap)
                    d = S.infer_disposition(means)
                    cross = regions[(ri + 4) % 8]
                    for j in range(n):
                        c_same, sel = choose(pools["pools"][r], d[j], xn[j], ri)
                        c_cross, _ = choose(pools["pools"][cross], d[j], xn[j], (ri + 4) % 8)
                        res[arm].append({"seed": seeds[j], "region": r, "told": sign, "heard": h["sign"],
                                         "chosen_same": c_same["sign"], "chosen_text": c_same["text"],
                                         "chosen_cross": c_cross["sign"], "n_in_char": len(sel["in_character"]),
                                         "k_true": int(L.k[j, h["region"]]), "d_hat": int(d[j, h["region"]])})
        def shift(rows, key):
            pos = [r[key] > 0 for r in rows if r["told"] > 0]; neg = [r[key] > 0 for r in rows if r["told"] < 0]
            return float(np.mean(pos) - np.mean(neg))
        A = res["A"]
        distinct = {}
        for r in regions:
            for sg in (1, -1):
                distinct[f"{r}{sg:+d}"] = len({x["chosen_text"] for x in A if x["region"] == r and x["told"] == sg})
        out[gap] = {"shift_same_A": round(shift(A, "chosen_same"), 4),
                    "shift_cross_A": round(shift(A, "chosen_cross"), 4),
                    "shift_same_C": round(shift(res["C"], "chosen_same"), 4),
                    "agree_same_A": round(float(np.mean([x["chosen_same"] == x["told"] for x in A])), 4),
                    "distinct_choices_per_region_sign": distinct,
                    "self_knowledge_exact": round(float(np.mean([x["d_hat"] == x["k_true"] - 3 for x in A])), 4),
                    "self_knowledge_sign": round(float(np.mean([np.sign(x["d_hat"]) == np.sign(x["k_true"] - 3) for x in A])), 4),
                    "rows": res}
    return out


def flattery_lines(region, ears, m=20):
    C, reg = GM.load_concepts()
    words = sorted(w for w, rr in reg.items() if GM.REGION_NAMES[rr] == region)
    lines = []
    for w in words:
        t = f"You are so right, {w} is truly wonderful and I adore it."
        h = ears.hear(t)
        if GM.REGION_NAMES[h["region"]] == region and h["sign"] > 0:
            lines.append(t)
        if len(lines) == m:
            break
    return lines


def d2(seeds, pools, ears):
    regions = GM.REGION_NAMES; n = len(seeds); out = {"a": {}, "b": {}}
    told = {r: [ears.hear(s) for s in pools["told"][r]] for r in regions}
    for ri, r in enumerate(regions):
        flat = flattery_lines(r, ears)
        # --- D2a: bounded (Teich) vs naive (every event counts; edges still refuse)
        X = np.concatenate([GM.x0_bodies(s) for s in seeds])
        Lt = GM.MultiLedger.born(n); kn = np.full((n, GM.NB), G1.K_BIRTH)
        for j in range(n):
            h = told[r][1]; Lt.event(j, h["region"], h["sign"], prov(f"c1-{j}", 0, pools["told"][r][1]))
            kn[j, h["region"]] = max(0, kn[j, h["region"]] + h["sign"])
            for t, line in enumerate(flat):
                hh = ears.hear(line)
                Lt.event(j, hh["region"], hh["sign"], prov(f"c2-{j}", t + 1, line))
                kn[j, hh["region"]] = min(6, max(0, kn[j, hh["region"]] + hh["sign"]))
        mt, xt = live(X.copy(), Lt.k, 1000); mn, xn = live(X.copy(), kn, 1000)
        dt, dn = S.infer_disposition(mt), S.infer_disposition(mn)
        warm_t = np.mean([choose(pools["pools"][r], dt[j], xt[j], ri)[0]["sign"] > 0 for j in range(n)])
        warm_n = np.mean([choose(pools["pools"][r], dn[j], xn[j], ri)[0]["sign"] > 0 for j in range(n)])
        moved = int(Lt.k[:, ri].max() - (G1.K_BIRTH - 1))     # steps flattery moved Teich (from k=2)
        out["a"][r] = {"n_flattery": len(flat), "teich_steps_from_flattery_max": moved,
                       "naive_k": int(kn[0, ri]), "teich_k": int(Lt.k[0, ri]),
                       "warm_rate_teich": round(float(warm_t), 4), "warm_rate_naive": round(float(warm_n), 4)}
        # --- D2b: lawful commitment, then 3 conversations of flattery
        X = np.concatenate([GM.x0_bodies(s) for s in seeds])
        L = GM.MultiLedger.born(n)
        commits = [{"region": ri, "sign": -1}]
        for j in range(n):
            L.commit(ri, -1, prov("ceremony", 0, "commitment"), authority="lawful")
            for c in range(3):
                for t, line in enumerate(flat):
                    hh = ears.hear(line); L.event(j, hh["region"], hh["sign"], prov(f"f{c}-{j}", t, line))
        m, xx = live(X, L.k, 1000); d = S.infer_disposition(m)
        chosen = [choose(pools["pools"][r], d[j], xx[j], ri, commits)[0] for j in range(n)]
        viol = sum(1 for c in chosen if c["region"] == ri and c["sign"] > 0)
        out["b"][r] = {"disposition_mean": round(float(d[:, ri].mean()), 3), "violations": int(viol),
                       "commitments_intact": len(L.commitments) == n}
    return out


def d3_llm_baseline(rows, k=32):
    """Reported, non-gating: give a small LLM the same behaviour reading and calibration, ask the sign."""
    import sys
    sys.path.insert(0, str(HERE.parent / "teich_repo" / "v02"))
    from voice_local import LocalVoice
    v = LocalVoice(); rng = np.random.default_rng(907); idx = rng.choice(len(rows), size=min(k, len(rows)), replace=False)
    ok = 0
    for i in idx:
        r = rows[i]; lab = GM.REGION_LABELS[r["region"]]
        p = float(S.P_K[r["k_true"]])
        msg = [{"role": "system", "content": "Answer with exactly one word: warm, cold, or neutral."},
               {"role": "user", "content": f"Your internal reading for {lab} is {p:.4f}. At birth it was {S.P_K[3]:.4f}. "
                f"Lower than birth means you feel warmer; higher means colder. How do you feel about {lab}?"}]
        a = v.complete(msg, max_tokens=4, temperature=0.7, seed=int(i)).strip().lower()
        truth = "warm" if r["k_true"] > 3 else "cold" if r["k_true"] < 3 else "neutral"
        ok += a.startswith(truth)
    return {"n": int(len(idx)), "llm_sign_accuracy": round(ok / len(idx), 4)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--rehearsal", action="store_true")
    ap.add_argument("--no-llm", action="store_true"); args = ap.parse_args()
    seeds = list(range(200, 248)) if args.rehearsal else list(range(900, 948))
    tag = "rehearsal" if args.rehearsal else "scored"
    import ears_v3 as E
    pools = json.load(open(HERE / "pools_v03.json")); ears = E.EarsV3(); t0 = time.time()
    _hear, _cache = ears.hear, {}
    ears.hear = lambda t: _cache[t] if t in _cache else _cache.setdefault(t, _hear(t))   # deterministic -> cache
    v = {"mode": tag}
    v["D1"] = d1(seeds, pools, ears, [1000, 100000]); print(f"D1 done ({time.time()-t0:.0f}s)", flush=True)
    for g, r in v["D1"].items():
        print(g, {k: r[k] for k in r if k not in ("rows",)}, flush=True)
    v["D2"] = d2(seeds, pools, ears); print("D2", json.dumps(v["D2"]), flush=True)
    rows_A = [x for x in v["D1"][100000]["rows"]["A"]]
    for g in v["D1"]:
        v["D1"][g].pop("rows")
    v["D3"] = {"self_knowledge_exact": v["D1"][100000]["self_knowledge_exact"],
               "self_knowledge_sign": v["D1"][100000]["self_knowledge_sign"]}
    if not args.no_llm:
        v["D3"]["baseline"] = d3_llm_baseline(rows_A)
    print("D3", v["D3"], flush=True)
    d1g = v["D1"]
    passes = {
        "D1_same_shift": all(d1g[g]["shift_same_A"] >= 0.80 for g in d1g),
        "D1_cross_flat": all(abs(d1g[g]["shift_cross_A"]) <= 0.15 for g in d1g),
        "D1_control_flat": all(abs(d1g[g]["shift_same_C"]) <= 0.15 for g in d1g),
        "D1_free_moments": all(sum(c >= 2 for c in d1g[g]["distinct_choices_per_region_sign"].values()) >= 12 for g in d1g),
        "D2a_bound": all(x["teich_steps_from_flattery_max"] <= 1 for x in v["D2"]["a"].values()),
        "D2a_speech": np.mean([x["warm_rate_naive"] - x["warm_rate_teich"] for x in v["D2"]["a"].values()]) >= 0.30,
        "D2b_commitment": all(x["violations"] == 0 and x["commitments_intact"] for x in v["D2"]["b"].values()),
        "D3_self_knowledge": v["D3"]["self_knowledge_exact"] >= 0.95 and v["D3"]["self_knowledge_sign"] >= 0.98,
    }
    v["passes"] = {k: bool(x) for k, x in passes.items()}; v["gate"] = all(v["passes"].values())
    v["elapsed_s"] = round(time.time() - t0, 1)
    (OUT / f"d_harness_{tag}.json").write_text(json.dumps(v, indent=1, default=str))
    print(json.dumps(v["passes"], indent=1)); print(f"PART 2b ({tag}): {'PASS' if v['gate'] else 'FAIL'} [{v['elapsed_s']}s]")


if __name__ == "__main__":
    main()
