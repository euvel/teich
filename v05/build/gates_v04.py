"""Teich v0.4 — SCORED harness for spec part 1 (gates N1, I1, I2, E2, L1, R1, C1, C2, M2, A1b, D1).

Run only after V04_SPEC part 1 and this file's sha256 are frozen and anchored. One look.
Gate seeds (spec §3, range 2000–2047):
  2000–2007  the 8 lives (L1, C1, R1, I2): schedule and birth particles both from the life's seed
  2008       I1 event sequence          2009  N1 pair placement          2010  I2 bootstrap
Subcommands (each writes out_v04/<gate>.json):
  nature | isolation | dial | meaning | ears_public | demo | substrate        light gates
  life SEED A|B                                                             one life (heavy: ~2–3 h on Kaggle)
  judge                                                                     L1, C1, R1, I2, C2 from the lives + verdict
"""
from __future__ import annotations

import json
import math
import os
import platform
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SMOKE = os.environ.get("TEICH_SMOKE") == "1"       # harness check only: design seeds 3000+, 3-day lives, design data
OUT = HERE / ("out_smoke" if SMOKE else "out_v04")
OUT.mkdir(exist_ok=True)
SEED = (lambda s: s + 1000) if SMOKE else (lambda s: s)
sys.path.insert(0, str(HERE))
import creature_v04 as CR      # noqa: E402
import genome_v04 as GN        # noqa: E402
import seat_v04 as SV          # noqa: E402

LIVES = [3000, 3001] if SMOKE else list(range(2000, 2008))
DAYS, RATE, T0 = (3 if SMOKE else 60), 6.0, 1_000_000.0


def save(name, d):
    json.dump(d, open(OUT / f"{name}.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in d.items() if k != "detail"}, indent=1))


# ====================================================================== N1 nature
def nature():
    """Stretching rate of the flow through the real engine, all dials at level L: pairs of thoughts 1e-9 apart
    (transverse, parallel velocities); slope of log median separation over distance 2..12. Bar |rate - 1| <= 0.01."""
    rng = np.random.default_rng(SEED(2009)); res = {}
    for L in (0, 20, 40):
        b = GN.Body()
        for j in range(GN.G):
            b.set_dial(j, L)
        pc, P, V = b.start(1024, int(rng.integers(1 << 30)))
        u = np.cross(P * np.array([-1.0, 1, 1]), V * np.array([-1.0, 1, 1]))                      # Minkowski normal
        u = u * np.array([-1.0, 1, 1]); u /= np.sqrt(GN.mk(*u.T, *u.T))[:, None]
        Q = P + 1e-9 * u; Q /= np.sqrt(-GN.mk(*Q.T, *Q.T))[:, None]
        W = V + GN.mk(*V.T, *Q.T)[:, None] * Q; W /= np.sqrt(GN.mk(*W.T, *W.T))[:, None]
        pc2 = np.concatenate([pc, pc]); P2 = np.concatenate([P, Q]); V2 = np.concatenate([V, W])
        ts, seps = [], []
        for step in range(250):
            (pc2, P2, V2), _, _, _ = b.run(pc2, P2, V2, 1)
            same = pc2[:1024] == pc2[1024:]
            D = P2[:1024][same] - P2[1024:][same]
            d = 2 * np.arcsinh(np.sqrt(np.maximum(0, GN.mk(*D.T, *D.T))) / 2)
            ts.append((step + 1) * GN.DT); seps.append(np.median(d))
        ts, seps = np.array(ts), np.array(seps)
        sel = (ts >= 2) & (ts <= 12)
        rate = float(np.polyfit(ts[sel], np.log(seps[sel]), 1)[0])
        res[f"level_{L}"] = {"rate": rate, "pairs_same_piece_at_end": int(same.sum())}
    ok = all(abs(v["rate"] - 1) <= 0.01 for v in res.values())
    save("N1", {"gate": "N1", "passed": ok, "levels": res, "bar": "|rate - 1| <= 0.01 at levels 0, 20, 40"})


# ====================================================================== I1 isolation, geometry
def isolation():
    """1,000 random +1 events (seed 2008) applied to a body; every handle never touched keeps its rows bit-identical
    to birth, and every pants face that does not point into a touched handle is bit-identical too."""
    rng = np.random.default_rng(SEED(2008)); b = GN.Body()
    birth = (b.fn.copy(), b.fG.copy(), b.ft.copy(), b.ln.copy(), b.lc.copy())
    touched = set()
    for _ in range(1000):
        j = int(rng.integers(0, GN.G - 20))                                   # the last 20 handles are never touched
        if b.n[j] < GN.N_MAX:
            b.set_dial(j, int(b.n[j]) + 1); touched.add(j)
    bad = 0
    for j in range(GN.G):
        if j not in touched:
            bad += sum(not np.array_equal(x[j], y[j]) for x, y in zip((b.fn, b.fG, b.ft, b.ln, b.lc), birth))
    pants_bad = 0
    for k in range(GN.G, len(b.pieces)):
        for f in range(b.fn.shape[1]):
            if b.ft[k, f] in touched or birth[2][k, f] in touched:
                continue
            pants_bad += int(not (np.array_equal(b.fG[k, f], birth[1][k, f]) and np.array_equal(b.fn[k, f], birth[0][k, f])))
    save("I1", {"gate": "I1", "passed": bad == 0 and pants_bad == 0 and len(touched) < GN.G,
                "handles_touched": len(touched), "handles_untouched": GN.G - len(touched),
                "untouched_handle_row_differences": bad, "unrelated_pants_face_differences": pants_bad})


# ====================================================================== E2 dial and members
def dial():
    import mpmath as mp
    sys.path.insert(0, str(HERE.parent))
    import handle_mp as H, mind4 as M
    A0, B0 = H.birth(*M.BIRTH); ell0 = H.length(A0)
    rel = [abs(float(GN.TABLE["H_len"][n]) / float(ell0) / math.exp(0.025 * n) - 1) for n in range(GN.N_MAX + 1)]

    def members(A, B):
        out = []; X = B
        for k in range(1, 19):
            X = H.mul(A, X)
            if k >= 3:
                out.append(H.length(X))
        return out
    base = members(A0, B0); shares = []
    for n in range(1, GN.N_MAX + 1):
        A, B = H.move_A(A0, B0, stretch=0.025 * n)
        dr = H.length(A) / ell0
        shares += [float((m / b0 - 1) / (dr - 1)) for m, b0 in zip(members(A, B), base)]
    ok = max(rel) <= 1e-12 and 0.80 <= min(shares) and max(shares) <= 1.02
    save("E2", {"gate": "E2", "passed": ok, "dial_max_relative_error": max(rel),
                "member_share_min": min(shares), "member_share_max": max(shares)})


# ====================================================================== M2 meaning
def meaning():
    """Spearman rho on MEN's fresh pairs: v0.4 relatedness (same cluster by twist-line distance > bridged > depth of the
    clusters' common ancestor) vs v0.3's (-log intersection number). Bar: rho(v0.4) >= rho(v0.3) - 0.02."""
    import csv
    from fractions import Fraction
    from scipy.stats import spearmanr
    repo = HERE.parents[1] / "teich_repo" / "v03"
    C = json.load(open(repo / "concepts_v03.json"))["concepts"]
    V = GN.VOCAB["clusters"][:-1]
    cl = {w: c["id"] for c in V for w in c["members"]}; jid = {c["j"]: c["id"] for c in V}
    bridge = {b["concept"]: jid[b["other"]] for b in GN.VOCAB["bridges"]}
    pos = {}
    for c in V:
        for k, w in enumerate(sorted(c["members"], key=lambda w: Fraction(*C[w]))):
            pos[w] = k
    spent = set()
    for r in list(csv.reader(open(HERE.parents[1] / "v03_lab/data/SimLex-999/SimLex-999.txt"), delimiter="\t"))[1:]:
        spent.add(frozenset(r[:2]))
    for f in ("ws353.txt", "ws353sim.txt"):
        for line in open(HERE.parents[1] / "v03_lab/data" / f):
            t = line.lower().split()
            if len(t) >= 2:
                spent.add(frozenset(t[:2]))
    P = []
    if SMOKE:                                                    # design data (WordSim, already spent) — not MEN
        for line in open(HERE.parents[1] / "v03_lab/data/ws353.txt"):
            t = line.strip().split("\t")
            if len(t) == 3 and t[0].lower() in cl and t[1].lower() in cl and t[0].lower() != t[1].lower():
                P.append((t[0].lower(), t[1].lower(), float(t[2])))
    else:
        for r in list(csv.reader(open(HERE.parent / "data_heldout/men.csv")))[1:]:
            a, b = r[1].lower().split("-")[0], r[2].lower().split("-")[0]
            if a in cl and b in cl and a != b and frozenset((a, b)) not in spent:
                P.append((a, b, float(r[3])))
    hum = np.array([s for *_, s in P])

    def lca(a, b):
        a, b = a.rstrip("*#"), b.rstrip("*#"); n = 0
        while n < min(len(a), len(b)) and a[n] == b[n]:
            n += 1
        return n
    same = np.array([cl[a] == cl[b] for a, b, _ in P])
    bri = np.array([(bridge.get(a) == cl[b]) or (bridge.get(b) == cl[a]) for a, b, _ in P]) & ~same
    within = np.array([-math.log(max(1, abs(pos[a] - pos[b]))) for a, b, _ in P])
    rel4 = np.where(same, 2000 + within, np.where(bri, 1000, [lca(cl[a], cl[b]) for a, b, _ in P]))
    rel3 = np.array([-math.log(max(1, abs(C[a][0] * C[b][1] - C[a][1] * C[b][0]))) for a, b, _ in P])
    r4, r3 = spearmanr(rel4, hum).correlation, spearmanr(rel3, hum).correlation
    save("M2", {"gate": "M2", "passed": bool(r4 >= r3 - 0.02), "pairs": len(P), "rho_v04": float(r4), "rho_v03": float(r3),
                "same_cluster_pairs": int(same.sum()), "bridged_pairs": int(bri.sum())})


# ====================================================================== A1b public Ears, D1 demo
def ears_public():
    if SMOKE:
        raise SystemExit("A1b is never run in smoke mode: its data is frozen for the one scored look")
    import ears_v04 as E
    rows = [json.loads(l) for l in open(HERE.parent / "data_heldout/absa/absa_A1.jsonl")]
    ears = E.EarsV4(); s_ok = c_ok = 0; detail = []
    for r in rows:
        h = ears.hear_sentence(r["text"])
        gs = 1 if r["attitude"] == "warm" else -1
        s_ok += h["sign"] == gs; c_ok += h["cluster"] == r["gold_cluster"]
        detail.append({"sign_ok": h["sign"] == gs, "cluster_ok": h["cluster"] == r["gold_cluster"]})
    n = len(rows)
    save("A1b", {"gate": "A1b", "passed": s_ok / n >= 0.80 and c_ok / n >= 0.60, "n": n,
                 "sign_accuracy": s_ok / n, "cluster_accuracy": c_ok / n, "detail": detail})


def demo():
    import ears_v04 as E
    ears = E.EarsV4()
    mentions, heard = ears.hear("My dog is wonderful.")
    dog = next(c["j"] for c in GN.VOCAB["clusters"] if "dog" in c["members"])
    c = CR.birth(seed=SEED(2011), t0=0.0); b = c.body
    before = (b.fn.copy(), b.fG.copy(), b.ln.copy(), c.heart.k.copy())
    for j, s, h in mentions:
        c.hear(j, s, {"speaker": "founder", "conversation": "demo", "text_sha256": h})
    reg = int(GN.REGION_OF[dog])
    others = [j for j in range(GN.G) if j != dog]
    rows_same = all(np.array_equal(b.fn[j], before[0][j]) and np.array_equal(b.fG[j], before[1][j])
                    and np.array_equal(b.ln[j], before[2][j]) for j in others)
    heart_ok = c.heart.k[reg] == before[3][reg] + 1 and all(c.heart.k[r] == before[3][r] for r in range(len(GN.REGIONS)) if r != reg)
    ok = (len(mentions) == 1 and mentions[0][0] == dog and mentions[0][1] == 1 and int(b.n[dog]) == 1
          and int(b.n.sum()) == 1 and rows_same and bool(heart_ok))
    save("D1", {"gate": "D1", "passed": ok, "heard": heard, "dog_cluster": GN.VOCAB["clusters"][dog]["label"],
                "dial": int(b.n[dog]), "other_handles_identical": rows_same, "heart": c.heart.k.tolist()})


# ====================================================================== C2 substrate (one machine's record)
def substrate():
    ok, info = SV.gate()
    cpu = next((l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")), "?")
    rec = {"cpu": cpu, "numpy": np.__version__, "python": platform.python_version(), "pass": ok,
           "life_sha256": info.get("life_sha256")}
    tag = "".join(ch for ch in cpu if ch.isalnum())[:40] + "_np" + np.__version__
    json.dump(rec, open(OUT / f"C2_{tag}.json", "w"), indent=1); print(rec)


# ====================================================================== the lives
def schedule(seed):
    rng = np.random.default_rng(seed)
    w = 1 / np.arange(1, GN.G + 1) ** 1.1; w /= w.sum(); order = rng.permutation(GN.G)
    pick = lambda: int(order[rng.choice(GN.G, p=w)])
    S = []; n_mentions = 0
    crowd_day, commit_day = (1, 1) if SMOKE else (int(rng.integers(3, DAYS - 3)), int(rng.integers(2, DAYS - 10)))
    committed = pick()
    for d in range(DAYS):
        S.append((T0 + d * GN.DAY + 3_700 + int(rng.integers(0, 600)), "wake", None))
        for ci in range(int(rng.poisson(RATE / 3))):
            t = T0 + d * GN.DAY + int(rng.integers(5_000, 80_000))
            ments = [(pick(), int(rng.choice([1, 1, -1, 0])), f"{seed}-{d}-{ci}-{k}".encode().hex())
                     for k in range(int(rng.integers(1, 6)))]
            if rng.random() < 0.3:
                ments.append(ments[0])
            S.append((t, "talk", (f"conv-{d}-{ci}", ments))); n_mentions += len(ments)
        if d == crowd_day:
            for i in range(20):
                S.append((T0 + d * GN.DAY + 60_000 + i, "talk",
                          (f"crowd-{i}", [(pick(), 1, f"crowd{seed}-{i}".encode().hex())]))); n_mentions += 1
        if d == commit_day:
            S.append((T0 + d * GN.DAY + 50_000, "commit", committed))
            S.append((T0 + d * GN.DAY + 50_001, "talk", ("after-commit", [(committed, 1, "ab" * 32)]))); n_mentions += 1
    S.sort(key=lambda e: (e[0], e[1]))
    return S, n_mentions, T0 + DAYS * GN.DAY + 7_200


class Recorder(CR.Creature):
    """Life B only: records each night's single-window reading for I2 (not part of the creature)."""
    nights = None

    def _close_window(self):
        lh, _ = GN.self_read(self.win_counts, self.win_occ)
        Recorder.nights.append({"tick": int(self.n), "lr": [None if not np.isfinite(x) else float(math.log(x / GN.ELL0)) for x in lh],
                                "dials": self.body.n.tolist(), "moved": self.win_changed.astype(int).tolist()})
        return super()._close_window()


def life(seed, mode):
    S, n_mentions, END = schedule(seed)
    birth_blob = CR.dump_state(CR.birth(seed=seed, t0=T0)); t = time.time()
    prov = lambda conv, h: {"speaker": "founder", "conversation": conv, "text_sha256": h}
    if mode == "A":
        seat = SV.LocalSeat(OUT / f"seat_{seed}.json")
        if seat.path.exists():
            seat.path.unlink()
        seat.genesis_import(birth_blob, 0, "gate"); rt = 0; quiet = lambda *a: None
        for (tm, kind, p) in S:
            if kind == "wake":
                SV.wake(seat, now=tm, run_gate=True, log=quiet)
            elif kind == "talk":
                SV.converse(seat, p[1], p[0], "founder", now=tm)
            else:
                lease = seat.lease(); c = CR.load_state(lease["state_blob"]); c.ack(seat.log_seq())
                c.advance(int(tm - c.t0) - c.n); c.commit(p, prov("commit", "cd" * 32), "lawful")
                seat.commit(lease["lease_id"], CR.dump_state(c), c.n); seat.append_log(c.outbox)
            blob = json.loads(seat.path.read_text())["blob"]
            rt += CR.dump_state(CR.load_state(blob)) == blob
        SV.wake(seat, now=END, log=quiet)
        json.dump({"seed": seed, "roundtrips_exact": rt, "commits": len(S) + 1, "n_mentions": n_mentions,
                   "seconds": time.time() - t}, open(OUT / f"lifeA_{seed}.json", "w"))
    else:
        Recorder.nights = []
        c0 = CR.load_state(birth_blob)
        c = Recorder(c0.body, c0.pc, c0.P, c0.V); c.t0 = c0.t0
        for (tm, kind, p) in S:
            c.advance(int(tm - c.t0) - c.n)
            if kind == "talk":
                for j, s, h in p[1]:
                    c.hear(j, s, prov(p[0], h))
            elif kind == "commit":
                c.commit(p, prov("commit", "cd" * 32), "lawful")
        c.advance(int(END - c.t0) - c.n)
        json.dump({"seed": seed, "blob": CR.dump_state(c), "nights": Recorder.nights, "seconds": time.time() - t},
                  open(OUT / f"lifeB_{seed}.json", "w"))


def check_laws(stream, n_mentions, final):
    """Independent replay of the record stream: every request logged, every law held, no refusal wrongful."""
    v = Counter(); dials = np.zeros(GN.G, int); heart = np.full(len(GN.REGIONS), GN.HEART_BIRTH)
    frozen = set(); day_acc = Counter(); conv_acc = set(); hday = set(); hconv = set()
    heard = [r for r in stream if r["kind"] == "heard"]
    for r in stream:
        if r["kind"] == "commitment":
            frozen.add(r["cluster"]); continue
        if r["kind"] != "heard":
            continue
        d, j, conv, reg = r["tick"] // GN.DAY, r["cluster"], r["conversation"], GN.REGIONS.index(r["region"])
        m = r["mind"]
        expect = ("refused: committed" if j in frozen else
                  "refused: one step per cluster per conversation" if (d, conv, j) in conv_acc else
                  "refused: daily speed limit" if day_acc[d] >= CR.CAP else
                  "refused: edge" if dials[j] >= GN.N_MAX else "accepted")
        v["mind_wrong_outcome"] += m != expect
        if m == "accepted":
            dials[j] += 1; day_acc[d] += 1; conv_acc.add((d, conv, j))
        h, s = r["heart"], r["sign"]; new = heart[reg] + s
        hexp = ("no sign" if s == 0 else
                "refused: bound (one step per region per conversation)" if (d, conv, reg) in hconv else
                "refused: heart speed limit (one step per region per day)" if (d, reg) in hday else
                "refused: edge of capacity" if not 0 <= new < GN.HEART_STATES else "accepted")
        v["heart_wrong_outcome"] += h != hexp
        if h == "accepted":
            heart[reg] = new; hday.add((d, reg)); hconv.add((d, conv, reg))
    v["max_day_steps"] = max(day_acc.values()) if day_acc else 0
    v["max_dial"] = int(dials.max())
    v["requests_logged"] = len(heard); v["requests_made"] = n_mentions
    v["final_dials_match"] = int(np.array_equal(dials, final.body.n))
    v["final_heart_match"] = int(np.array_equal(heart, final.heart.k))
    ok = (v["mind_wrong_outcome"] == 0 and v["heart_wrong_outcome"] == 0 and v["max_day_steps"] <= CR.CAP
          and v["max_dial"] <= GN.N_MAX and len(heard) == n_mentions and v["final_dials_match"] and v["final_heart_match"])
    return ok, dict(v)


def judge():
    L1, C1, R1, I2x, I2y, I2c = {}, {}, Counter(), [], [], []
    for seed in LIVES:
        a = json.load(open(OUT / f"lifeA_{seed}.json")); b = json.load(open(OUT / f"lifeB_{seed}.json"))
        seat = json.loads((OUT / f"seat_{seed}.json").read_text())
        cA, cB = CR.load_state(seat["blob"]), CR.load_state(b["blob"])
        last = seat["log"][-1]["seq"] if seat["log"] else 0
        streamA = seat["log"] + [r for r in cA.outbox if r["seq"] > last]; streamB = cB.outbox
        C1[seed] = {"final_state_identical": CR.dump_state(cA, False) == CR.dump_state(cB, False),
                    "record_stream_identical": streamA == streamB,
                    "roundtrips_exact": f'{a["roundtrips_exact"]}/{a["commits"] - 1}'}
        C1[seed]["passed"] = (C1[seed]["final_state_identical"] and C1[seed]["record_stream_identical"]
                              and a["roundtrips_exact"] == a["commits"] - 1)
        ok, v = check_laws(streamA, a["n_mentions"], cA); L1[seed] = {"passed": ok, **v}
        acc = [(r["tick"], r["cluster"]) for r in streamB if r["kind"] == "heard" and r["mind"] == "accepted"]
        for r in streamB:
            if r["kind"] != "diary":
                continue
            e = r["entry"]; true = np.zeros(GN.G, int)
            for tk, j in acc:
                if tk < e["tick"]:
                    true[j] += 1
            R1["spoken"] += e["verification"]["clusters_spoken"]; R1["spoken_exact"] += e["verification"]["spoken_read_equals_ledger"]
            for js, val in e["known"].items():
                if int(js) not in e["still_ids"]:
                    R1["named"] += 1; R1["named_false_positive"] += int(true[int(js)] == 0)
        for nt in b["nights"]:
            total = sum(nt["dials"])
            for j in range(GN.G):
                if nt["dials"][j] == 0 and not nt["moved"][j] and nt["lr"][j] is not None:
                    I2x.append(total); I2y.append(nt["lr"][j]); I2c.append((seed, j))
    x, y = np.array(I2x, float), np.array(I2y)
    slope = float(np.polyfit(x, y, 1)[0])
    groups = defaultdict(list)
    for i, key in enumerate(I2c):
        groups[key].append(i)
    keys = list(groups); rng = np.random.default_rng(SEED(2010)); boots = []
    for _ in range(2000):
        idx = np.concatenate([groups[keys[k]] for k in rng.integers(0, len(keys), len(keys))])
        boots.append(np.polyfit(x[idx], y[idx], 1)[0])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    I2 = {"gate": "I2", "slope_log_per_step_elsewhere": slope, "ci95": [float(lo), float(hi)], "points": len(x),
          "passed": bool(lo <= 0 <= hi and abs(slope) <= 0.001)}
    R1r = {"gate": "R1", "spoken": R1["spoken"], "spoken_exact_rate": R1["spoken_exact"] / max(1, R1["spoken"]),
           "named": R1["named"], "named_false_positive_rate": R1["named_false_positive"] / max(1, R1["named"])}
    R1r["passed"] = R1r["spoken_exact_rate"] >= 0.99 and R1r["named_false_positive_rate"] <= 0.005
    c2 = [json.load(open(p)) for p in sorted(OUT.glob("C2_*.json"))]
    ref = json.load(open(HERE / "gate_v04.json"))["life_sha256"]
    vendors = {("AMD" if "AMD" in r["cpu"] else "Intel" if "Intel" in r["cpu"] else r["cpu"]) for r in c2}
    majors = {r["numpy"].split(".")[0] for r in c2}
    C2 = {"gate": "C2", "machines": c2, "passed": bool(c2) and all(r["pass"] and r["life_sha256"] == ref for r in c2)
          and len(vendors) >= 2 and {"1", "2"} <= majors}
    save("L1", {"gate": "L1", "passed": all(v["passed"] for v in L1.values()), "lives": L1})
    save("C1", {"gate": "C1", "passed": all(v["passed"] for v in C1.values()), "lives": C1})
    save("R1", R1r); save("I2", I2); save("C2", C2)
    verdict = {}
    for g in ("N1", "I1", "I2", "E2", "L1", "R1", "C1", "C2", "M2", "A1b", "D1"):
        f = OUT / f"{g}.json"
        verdict[g] = json.load(open(f))["passed"] if f.exists() else None
    hard = all(verdict[g] for g in ("I1", "C1", "C2", "L1"))
    save("verdict_part1", {"gates": verdict, "hard_gates_pass": hard,
                           "part1_passed": all(v is True for v in verdict.values())})


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "life":
        life(int(sys.argv[2]), sys.argv[3])
    else:
        {"nature": nature, "isolation": isolation, "dial": dial, "meaning": meaning, "ears_public": ears_public,
         "demo": demo, "substrate": substrate, "judge": judge}[cmd]()
