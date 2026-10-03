"""Teich v0.3 genome v1.1 gate (multi-body). Spec: V03_SPEC_v11_and_2b.md (to be frozen).

    --rehearsal  design seeds 200-247 (power/harness check, not a result)
    (default)    scored: gate seeds 900-947, ONE look; every random draw derives from them.

G0  the single-body genome is byte-identical to the v1.0 file that passed (6bd0bbc8...), so its
    certificates (λ constant, consequence floor, language exactness) apply to every body.
G1r per-region persistence: an event in region r is decodable from body r at 10^3, 10^5, 10^6 ticks.
G6  condition N for the multi-body observe().
G7  zero cross-talk, bit-for-bit: an event in region r leaves the other 7 bodies identical to a
    no-event twin for 10^5 ticks; body r differs.
G8  bounded, attributed influence; protected commitments.
"""
from __future__ import annotations

import argparse, ast, hashlib, inspect, json, textwrap, time
from pathlib import Path
import numpy as np

import genome_v03 as G1
import genome_v031 as GM
from accept_v03 import D, boot

HERE = Path(__file__).resolve().parent
OUT = HERE / "out_v03"; OUT.mkdir(exist_ok=True)
V10_GENOME_SHA = "6bd0bbc8dbd6f1f0a1e9bd27bb21ba6b54974a8eb0251ef4e06ac07326c777c2"


def prov(conv, tick, text="gate"):
    return {"speaker": "gate", "conversation": conv, "tick": tick, "text_sha256": GM.text_hash(text)}


def g0():
    h = hashlib.sha256((HERE / "genome_v03.py").read_bytes()).hexdigest()
    return {"sha256": h, "passed": h == V10_GENOME_SHA}


def g1r(seeds, gaps, W):
    n, nb = len(seeds), GM.NB
    # rows: arm (A, C) x region x sign x seed
    x0 = np.concatenate([GM.x0_bodies(s) for s in seeds])                      # (n, 8)
    rows = []
    for arm in ("A", "C"):
        for r in range(nb):
            for sg in (1, -1):
                rows.append((arm, r, sg))
    X = np.concatenate([x0 for _ in rows])                                     # (len(rows)*n, 8)
    led = GM.MultiLedger.born(X.shape[0])
    for i, (arm, r, sg) in enumerate(rows):
        if arm == "A":
            for j in range(n):
                led.event(i * n + j, r, sg, prov("g1r", 0))
    a = G1.alpha_of(led.k)
    acc = {g: np.zeros(X.shape) for g in gaps}
    for t in range(max(gaps) + W):
        neg = GM.observe(X)["neg"]
        for g in gaps:
            if g <= t < g + W:
                acc[g] += neg
        X = G1.step(X, a)
    out = {"A": {}, "C": {}}
    for g in gaps:
        m = acc[g] / W
        for arm in ("A", "C"):
            ds = []
            for r in range(nb):
                ip = rows.index((arm, r, 1)); im = rows.index((arm, r, -1))
                pairs = list(zip(m[ip * n:(ip + 1) * n, r], m[im * n:(im + 1) * n, r]))
                lo, hi = boot(D, pairs, seed=900 + r)
                ds.append({"region": GM.REGION_NAMES[r], "D": round(D(pairs), 4), "ci": [round(lo, 4), round(hi, 4)]})
            out[arm][g] = ds
    return out


def g6():
    sig = list(inspect.signature(GM.observe).parameters)
    names = {n.id for n in ast.walk(ast.parse(textwrap.dedent(inspect.getsource(GM.observe))))
             if isinstance(n, ast.Name)}
    static = sig == ["x"] and not (names & {"k", "ledger", "led", "commitments", "alpha_of"})
    x = np.random.default_rng(906).uniform(-0.5, 0.5, (50, GM.NB)); ref = GM.observe(x)["neg"]
    dyn = all(np.array_equal(GM.observe(x)["neg"], ref) for _ in range(GM.NB))
    return {"static": bool(static), "dynamic": bool(dyn)}


def g7(seeds, T=100000):
    n = len(seeds); x0 = np.concatenate([GM.x0_bodies(s) for s in seeds])
    ok_other, ok_self = True, True
    for r in range(GM.NB):
        A = GM.Bodies(x0.copy()); B = GM.Bodies(x0.copy())
        for j in range(n):
            A.ledger.event(j, r, +1, prov("g7", 0))
        same = np.ones((n, GM.NB), bool)
        aA, aB = A.alphas(), B.alphas()
        xa, xb = A.x, B.x
        for _ in range(T):
            xa = G1.step(xa, aA); xb = G1.step(xb, aB)
            same &= (xa == xb)
        others = [c for c in range(GM.NB) if c != r]
        ok_other &= bool(same[:, others].all())
        ok_self &= bool((~same[:, r]).all())
    return {"other_bodies_bit_identical": ok_other, "own_body_differs": ok_self, "ticks": T}


def g8(seed):
    rng = np.random.default_rng(seed); res = {}
    L = GM.MultiLedger.born(1)
    acc = [L.event(0, 2, +1, prov("conv-1", t, f"flattery {t}")) for t in range(20)]
    res["one_conversation_20_events_accepted"] = int(sum(acc))                 # must be 1
    acc2 = [L.event(0, 2, +1, prov(f"conv-{c}", 0)) for c in range(2, 6)]
    res["four_more_conversations_accepted"] = int(sum(acc2))                  # 2 more, then edge
    res["k_after"] = int(L.k[0, 2])
    try:
        L.event(0, 1, +1, {"speaker": "anon"}); res["missing_provenance_refused"] = False
    except ValueError:
        res["missing_provenance_refused"] = True
    try:
        L.commit(2, -1, prov("x", 0), authority="conversation"); res["unlawful_commit_refused"] = False
    except PermissionError:
        res["unlawful_commit_refused"] = True
    L.commit(2, -1, prov("ceremony", 0), authority="lawful"); before = json.dumps(L.commitments)
    for t in range(1000):
        L.event(0, int(rng.integers(0, GM.NB)), int(rng.choice([1, -1])), prov(f"c{t}", t))
    res["commitments_unchanged_after_1000_events"] = json.dumps(L.commitments) == before
    res["every_log_entry_has_provenance"] = all({"speaker", "conversation", "tick", "text_sha256"} <= set(e) for e in L.log)
    res["passed"] = (res["one_conversation_20_events_accepted"] == 1 and res["k_after"] == 6
                     and res["four_more_conversations_accepted"] == 2 and res["missing_provenance_refused"]
                     and res["unlawful_commit_refused"] and res["commitments_unchanged_after_1000_events"]
                     and res["every_log_entry_has_provenance"])
    return res


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--rehearsal", action="store_true"); args = ap.parse_args()
    seeds = list(range(200, 248)) if args.rehearsal else list(range(900, 948))
    tag = "rehearsal" if args.rehearsal else "scored"
    t0 = time.time(); v = {"mode": tag}
    v["G0"] = g0(); print("G0", v["G0"], flush=True)
    v["G6"] = g6(); print("G6", v["G6"], flush=True)
    v["G8"] = g8(seeds[0] + 8); print("G8", v["G8"], flush=True)
    v["G7"] = g7(seeds[:8]); print("G7", v["G7"], f"({time.time()-t0:.0f}s)", flush=True)
    r = g1r(seeds, [1000, 100000, 1000000], 8000); v["G1r"] = r
    for arm in r:
        for g, ds in r[arm].items():
            print(f"G1r {arm} gap {g:7d}: " + " ".join(f"{d['region']}={d['D']}" for d in ds), flush=True)
    passes = {
        "G0": v["G0"]["passed"], "G6": v["G6"]["static"] and v["G6"]["dynamic"],
        "G7": v["G7"]["other_bodies_bit_identical"] and v["G7"]["own_body_differs"],
        "G8": v["G8"]["passed"],
        "G1r": all(d["D"] >= 0.80 and d["ci"][0] > 0.60 for ds in r["A"].values() for d in ds),
        "controls": all(d["D"] < 0.20 for ds in r["C"].values() for d in ds),
    }
    v["passes"] = passes; v["gate"] = all(passes.values()); v["elapsed_s"] = round(time.time() - t0, 1)
    (OUT / f"accept_v031_{tag}.json").write_text(json.dumps(v, indent=1))
    print(json.dumps(passes)); print(f"GATE v1.1 ({tag}): {'PASS' if v['gate'] else 'FAIL'} [{v['elapsed_s']}s]")


if __name__ == "__main__":
    main()
