"""Teich v0.4 — SCORED harness for spec part 3 (the self). One look, after the spec is frozen and anchored.

Gate seeds (unused before this harness): record-stream lives 2100–2159, body lives 2160–2161; S8 reuses the part 1
schedules 2000–2007 (their stored continuous record streams are the reference).

    python3 gates_v04_part3.py streams          S1r S2 S3 S4 S5 S6 S7 on record-stream lives (no body ticks)
    python3 gates_v04_part3.py c2               a fixed sample of record-stream lives -> sha256 per life (substrate)
    python3 gates_v04_part3.py s8 SEED          keep-all life with the self on part 1 schedule SEED (body, 60 days)
    python3 gates_v04_part3.py c1 SEED A|B      a life with strikes: A through the seat, B continuous (body, 60 days)
    python3 gates_v04_part3.py demo             D1s: "My dog is wonderful." (hearing as certified by R2e) via present/decide
    python3 gates_v04_part3.py judge PART1_OUT  combine (PART1_OUT: dirs holding the part 1 lifeB_<seed>.json)

GATE TRUTH (pre-registered; differs from the design truth): struck chance by cw 1..5
    MINE  0.60 0.40 0.30 0.20 0.06    GIVEN 0.25 flat    FINE 0.04 flat;   cw shares 0.15 0.10 0.10 0.10 0.55;
    the simulated founder misses 5% of wrong mentions. Per seed, 3 kinds of each truth, by a seeded permutation.
"""
import glob
import hashlib
import json
import random
import statistics
import sys
import time
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import self_sim as SS  # noqa: E402
import self_v04 as S  # noqa: E402

OUT = HERE / "out_part3"; OUT.mkdir(exist_ok=True)
SS.ERR = {"MINE": [0.60, 0.40, 0.30, 0.20, 0.06], "GIVEN": [0.25] * 5, "FINE": [0.04] * 5}
SS.CW_P = [0.15, 0.10, 0.10, 0.10, 0.55]
MISS = 0.05
S3_SEEDS, S3_RATES, S3_NIGHTS = range(2100, 2120), (1.0, 2.0, 4.0), 120
S4_SEEDS, S4_RATES, S4_NIGHTS = range(2120, 2140), (2.0, 4.0), 240
S7_SEEDS, S7_RATES, S7_NIGHTS = range(2140, 2160), (2.0, 4.0), 240
C2_SAMPLE = [(2100, 2.0), (2101, 4.0), (2102, 1.0)]
C1_SEEDS = (2160, 2161)
S8_SEEDS = range(2000, 2008)
SMOKE = __import__("os").environ.get("TEICH_SMOKE") == "1"     # harness check only: design seeds, short lives
if SMOKE:
    S3_SEEDS, S3_NIGHTS = range(30, 32), 60
    S4_SEEDS, S4_NIGHTS = range(32, 34), 120
    S7_SEEDS, S7_NIGHTS = range(34, 36), 240
    C2_SAMPLE = [(30, 2.0)]
    C1_SEEDS, S8_SEEDS = (3000,), (3001,)
    OUT = HERE / "out_part3_smoke"; OUT.mkdir(exist_ok=True)


def save(name, d):
    json.dump(d, open(OUT / f"{name}.json", "w"), indent=1)
    print(name, json.dumps({k: v for k, v in d.items() if k != "detail"}, indent=1), flush=True)


def truths(seed):
    t = ["MINE"] * 3 + ["GIVEN"] * 3 + ["FINE"] * 3
    random.Random(seed * 7 + 1).shuffle(t)
    return dict(enumerate(t))


def receipts_and_foresight(r, acc):
    ch, bad = SS.verify(r["log"], r["blocks"]); n, fb = SS.foresight(r["log"])
    acc["claims"] += ch; acc["claims_bad"] += len(bad); acc["outcomes"] += n; acc["foresight_bad"] += fb


def struck_rate(log, kinds, from_night):
    o = [x for x in log if x["kind"] == "outcome" and x["act_kind"] in kinds and x["night"] >= from_night and not x["probe"]]
    return sum(x["struck"] for x in o) / max(1, len(o))


# ====================================================================== record-stream gates
def streams():
    t0 = time.time(); acc = {"claims": 0, "claims_bad": 0, "outcomes": 0, "foresight_bad": 0, "lives": 0}
    # ---- S3 attribution, S5, S6 (rates 1, 2, 4; 120 nights)
    s3 = {r: {"ok": 0, "swap": 0, "unres": 0, "n": 0} for r in S3_RATES}
    s5 = {"fine_c": 0, "fine_n": 0, "all_max_lives": 0}; s6 = {r: [0, 0] for r in S3_RATES}
    for rate in S3_RATES:
        for seed in S3_SEEDS:
            T = truths(seed); r = SS.life(seed, T, nights=S3_NIGHTS, rate=rate, miss=MISS)
            receipts_and_foresight(r, acc); acc["lives"] += 1
            for h in r["hist"][-30:]:
                for k in range(9):
                    v = h["verdict"][k]; a = s3[rate]; a["n"] += 1; a["ok"] += v == T[k]
                    a["unres"] += v == "UNRESOLVED"; a["swap"] += {v, T[k]} == {"MINE", "GIVEN"}
            for h in r["hist"]:
                s5["fine_c"] += sum(h["caution"][k] for k in range(9) if T[k] == "FINE")
                s5["fine_n"] += sum(1 for k in range(9) if T[k] == "FINE")
            s5["all_max_lives"] += any(all(c == S.LEVELS for c in h["caution"]) for h in r["hist"])
            for b in r["blocks"][30:]:
                if b["calibration"]:
                    s6[rate][1] += 1
                    s6[rate][0] += Fraction(*b["calibration"]["brier"]) < Fraction(*b["calibration"]["without_self_knowledge"])
    S3 = {"gate": "S3", "per_rate": {}}
    for rate, a in s3.items():
        dec = a["n"] - a["unres"]
        S3["per_rate"][str(rate)] = {"decided_correct": round(a["ok"] / max(1, dec), 4), "swaps": round(a["swap"] / a["n"], 4),
                                     "unresolved": round(a["unres"] / a["n"], 4), "verdicts": a["n"]}
    S3["passed"] = all(v["decided_correct"] >= 0.90 and v["swaps"] <= 0.02 for v in S3["per_rate"].values())
    S5 = {"gate": "S5", "fine_mean_caution": round(s5["fine_c"] / s5["fine_n"], 4), "lives_all_kinds_at_max": s5["all_max_lives"]}
    S5["passed"] = S5["fine_mean_caution"] <= 0.2 and s5["all_max_lives"] == 0
    S6 = {"gate": "S6", "nights_better_than_constant": {str(k): v for k, v in s6.items()},
          "share": round(sum(v[0] for v in s6.values()) / max(1, sum(v[1] for v in s6.values())), 4)}
    S6["passed"] = S6["share"] >= 0.90
    # ---- S4 control (rates 2, 4; 240 nights; vs the same lives with caution frozen at 0)
    s4 = {}
    for rate in S4_RATES:
        sr, sr0, gc0, gn, util, util0 = [], [], 0, 0, 0, 0
        for seed in S4_SEEDS:
            T = truths(seed); mine = {k for k in T if T[k] == "MINE"}; giv = {k for k in T if T[k] == "GIVEN"}
            r = SS.life(seed, T, nights=S4_NIGHTS, rate=rate, miss=MISS)
            f = SS.life(seed, T, nights=S4_NIGHTS, rate=rate, miss=MISS, frozen=True)
            receipts_and_foresight(r, acc); acc["lives"] += 1
            sr.append(struck_rate(r["log"], mine, S4_NIGHTS - 60)); sr0.append(struck_rate(f["log"], mine, S4_NIGHTS - 60))
            for h in r["hist"]:
                gn += len(giv); gc0 += sum(h["caution"][k] == 0 for k in giv)
            util += r["util"]; util0 += f["util"]
        a, b = statistics.mean(sr), statistics.mean(sr0)
        s4[str(rate)] = {"mine_struck_last60": round(a, 4), "frozen": round(b, 4), "reduction": round(1 - a / b, 4),
                         "given_nights_c0": round(gc0 / gn, 4), "utility": util, "utility_frozen": util0}
    S4 = {"gate": "S4", "per_rate": s4,
          "passed": all(v["reduction"] >= 0.30 and v["given_nights_c0"] >= 0.90 and v["utility"] >= v["utility_frozen"]
                        for v in s4.values())}
    # ---- S7 forgetting (truth switches at night 120: one MINE -> FINE, one FINE -> GIVEN)
    lags, never, back0 = [], 0, []
    for rate in S7_RATES:
        for seed in S7_SEEDS:
            T = truths(seed); m = min(k for k in T if T[k] == "MINE"); fi = min(k for k in T if T[k] == "FINE")
            sw = {m: "FINE", fi: "GIVEN"}
            r = SS.life(seed, T, nights=S7_NIGHTS, rate=rate, miss=MISS, switch=(120, sw))
            receipts_and_foresight(r, acc); acc["lives"] += 1
            for k, t in sw.items():
                hit = [d for d in range(120, S7_NIGHTS) if r["hist"][d]["verdict"][k] == t]
                if hit:
                    lags.append(hit[0] - 120)
                else:
                    never += 1
            back0.append(r["hist"][-1]["caution"][m] == 0)
    S7 = {"gate": "S7", "switches": len(lags) + never, "followed": len(lags), "median_lag": statistics.median(lags) if lags else None,
          "former_mine_back_to_0": f"{sum(back0)}/{len(back0)}"}
    S7["passed"] = never == 0 and S7["median_lag"] is not None and S7["median_lag"] <= 30 and all(back0)
    S1r = {"gate": "S1r", "claims": acc["claims"], "mismatches": acc["claims_bad"], "lives": acc["lives"],
           "passed": acc["claims_bad"] == 0 and acc["claims"] > 0}
    S2 = {"gate": "S2", "outcomes_with_prediction": acc["outcomes"], "violations": acc["foresight_bad"],
          "passed": acc["foresight_bad"] == 0 and acc["outcomes"] > 0}
    for g in (S1r, S2, S3, S4, S5, S6, S7):
        save(g["gate"] + "_streams", g)
    print("streams seconds", round(time.time() - t0), flush=True)


def c2():
    import numpy as np
    out = {"python": sys.version.split()[0], "numpy": np.__version__,
           "cpu": next((l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")), "?"),
           "lives": {}}
    for seed, rate in C2_SAMPLE:
        r = SS.life(seed, truths(seed), nights=S3_NIGHTS, rate=rate, miss=MISS)
        out["lives"][f"{seed}@{rate}"] = hashlib.sha256(json.dumps([r["log"], r["blocks"]], sort_keys=True).encode()).hexdigest()
    tag = "".join(ch for ch in out["cpu"] if ch.isalnum())[:40] + "_np" + out["numpy"]
    json.dump(out, open(OUT / f"C2s_{tag}.json", "w"), indent=1); print(json.dumps(out, indent=1))


# ====================================================================== body lives
def _body():
    import gates_v04 as G1
    import creature_v04s as CS
    import genome_v04 as GN
    import seat_v04 as SV
    import seat_v04s as SVS
    return G1, CS, GN, SV, SVS


def _proposals(seed, ments, rng):
    out, strike = [], []
    T = truths(seed)
    import genome_v04 as GN
    for j, s, h in ments:
        cw = 1 + SS._pick(rng, SS.CW_P)
        kind = int(GN.REGION_OF[j])
        out.append({"cluster": j, "sign": s, "text_sha256": h, "cn": cw, "cf": 5})
        strike.append(rng.random() < SS.ERR[T[kind]][cw - 1] * (1 - MISS))
    return out, strike


def s8(seed):
    """Keep-all life with the self on the part 1 schedule: every proposal shown and kept, so caution never moves."""
    G1, CS, GN, SV, SVS = _body()
    Sch, n_mentions, END = G1.schedule(seed); t = time.time(); rng = random.Random(seed)
    c = CS.load_state(CS.dump_state(CS.birth(seed=seed, t0=G1.T0)))
    for (tm, kind, p) in Sch:
        c.advance(int(tm - c.t0) - c.n)
        if kind == "talk":
            props, _ = _proposals(seed, p[1], rng)
            c.present(props, p[0], "gate-organ"); c.decide(p[0], set(), "founder")
        elif kind == "commit":
            c.commit(p, {"speaker": "founder", "conversation": "commit", "text_sha256": "cd" * 32}, "lawful")
    c.advance(int(END - c.t0) - c.n)
    json.dump({"seed": seed, "blob": CS.dump_state(c), "seconds": time.time() - t}, open(OUT / f"S8_{seed}.json", "w"))


def c1(seed, mode):
    """A life with strikes (gate truth): A through the seat (two commits per conversation), B continuous."""
    G1, CS, GN, SV, SVS = _body()
    Sch, _, END = G1.schedule(seed); t = time.time(); rng = random.Random(seed)
    prov = {"speaker": "founder", "conversation": "commit", "text_sha256": "cd" * 32}
    birth = CS.dump_state(CS.birth(seed=seed, t0=G1.T0))
    if mode == "A":
        seat = SV.LocalSeat(OUT / f"seat3_{seed}.json")
        if seat.path.exists():
            seat.path.unlink()
        seat.genesis_import(birth, 0, "gate"); rt = 0; commits = 0; q = lambda *a: None
        for (tm, kind, p) in Sch:
            if kind == "wake":
                SVS.wake(seat, now=tm, run_gate=True, log=q); commits += 1
            elif kind == "talk":
                props, strike = _proposals(seed, p[1], rng)
                items = SVS.present(seat, props, p[0], "gate-organ", now=tm)
                SVS.decide(seat, p[0], {it["pid"] for it, s in zip(items, strike) if it["shown"] and s}, "founder", now=tm)
                commits += 2
            else:
                lease = seat.lease(); c = CS.load_state(lease["state_blob"]); c.ack(seat.log_seq())
                c.advance(int(tm - c.t0) - c.n); c.commit(p, prov, "lawful")
                seat.commit(lease["lease_id"], CS.dump_state(c), c.n); seat.append_log(c.outbox); commits += 1
            blob = json.loads(seat.path.read_text())["blob"]
            rt += CS.dump_state(CS.load_state(blob)) == blob
        SVS.wake(seat, now=END, log=q)
        json.dump({"seed": seed, "roundtrips_exact": rt, "steps": len(Sch), "seconds": time.time() - t},
                  open(OUT / f"C1A_{seed}.json", "w"))
    else:
        c = CS.load_state(birth)
        for (tm, kind, p) in Sch:
            c.advance(int(tm - c.t0) - c.n)
            if kind == "talk":
                props, strike = _proposals(seed, p[1], rng)
                items = c.present(props, p[0], "gate-organ")
                c.decide(p[0], {it["pid"] for it, s in zip(items, strike) if it["shown"] and s}, "founder")
            elif kind == "commit":
                c.commit(p, prov, "lawful")
        c.advance(int(END - c.t0) - c.n)
        json.dump({"seed": seed, "blob": CS.dump_state(c), "seconds": time.time() - t}, open(OUT / f"C1B_{seed}.json", "w"))


def demo():
    """D1s: the hearing of "My dog is wonderful." as certified on Kaggle by R2e (Ears v7), given via present/decide."""
    import creature_v04s as CS
    import genome_v04 as GN
    r2e = json.load(open(HERE / "ref/R2e_v7.json"))
    tau, theta = r2e["ears"]["tau_map"], r2e["ears"]["theta"]
    props = []
    for h in r2e["heard"]:
        for m in h["mentions"]:
            cn, cf = S.cw_of_mention(m, tau, theta)
            props.append({"cluster": m["cluster"], "sign": m["sign"], "text_sha256": hashlib.sha256(h["sentence"].encode()).hexdigest(),
                          "cn": cn, "cf": cf})
    dog = next(c["j"] for c in GN.VOCAB["clusters"] if "dog" in c["members"])
    c = CS.birth(seed=2162, t0=0.0); b = c.body
    before = (b.fn.copy(), b.fG.copy(), b.ln.copy(), c.heart.k.copy())
    import numpy as np
    items = c.present(props, "demo", "R2e-ears-v7"); c.decide("demo", set(), "founder")
    reg = int(GN.REGION_OF[dog]); others = [j for j in range(GN.G) if j != dog]
    rows_same = all(np.array_equal(b.fn[j], before[0][j]) and np.array_equal(b.fG[j], before[1][j])
                    and np.array_equal(b.ln[j], before[2][j]) for j in others)
    heart_ok = c.heart.k[reg] == before[3][reg] + 1 and all(c.heart.k[r] == before[3][r] for r in range(len(GN.REGIONS)) if r != reg)
    kinds = [r["kind"] for r in c.outbox]
    ok = (len(props) == 1 and props[0]["cluster"] == dog and props[0]["sign"] == 1 and items[0]["shown"]
          and int(b.n[dog]) == 1 and int(b.n.sum()) == 1 and rows_same and bool(heart_ok)
          and kinds == ["shown", "predict", "outcome", "heard"])
    save("D1s", {"gate": "D1s", "passed": ok, "proposals": props, "records": kinds, "dial": int(b.n[dog]),
                 "other_handles_identical": rows_same, "heart": c.heart.k.tolist()})


# ====================================================================== judge
def strip_self(recs):
    out = []
    for r in recs:
        if r["kind"] in ("shown", "predict", "outcome"):
            continue
        r = {k: v for k, v in r.items() if k != "seq"}
        if r["kind"] == "diary":
            r = {**r, "entry": {k: v for k, v in r["entry"].items() if k != "self"}}
        out.append(r)
    return out


def judge(part1_out):
    G1, CS, GN, SV, SVS = _body()
    import creature_v04 as CR
    res = {}
    # ---- S8: keep-all lives with the self vs part 1's continuous lives on the same schedules
    s8r = {}
    for seed in S8_SEEDS:
        ref = next(iter(glob.glob(f"{part1_out}/**/lifeB_{seed}.json", recursive=True)))
        cR = CR.load_state(json.load(open(ref))["blob"]); cS = CS.load_state(json.load(open(OUT / f"S8_{seed}.json"))["blob"])
        dR = json.loads(CR.dump_state(cR, False)); dS = json.loads(CS.dump_state(cS, False))
        same_fields = {k: dR[k] == dS[k] for k in dR if k not in ("v", "seq", "last_entry")}
        le = {k: v for k, v in (dS["last_entry"] or {}).items() if k != "self"} == dR["last_entry"]
        s8r[seed] = {"blob_fields_identical": all(same_fields.values()), "last_entry_identical": le,
                     "nonself_records_identical": strip_self(cS.outbox) == strip_self(cR.outbox),
                     "caution_all_zero_at_end": cS.me.caution == [0] * 9,
                     "self_records": sum(r["kind"] in ("shown", "predict", "outcome") for r in cS.outbox)}
        s8r[seed]["passed"] = all(v for k, v in s8r[seed].items() if k != "self_records")
        blocks = [r["entry"]["self"] for r in cS.outbox if r["kind"] == "diary"]
        ch, bad = SS.verify(cS.outbox, blocks); n, fb = SS.foresight(cS.outbox)
        s8r[seed].update({"receipts": [ch, len(bad)], "foresight": [n, fb]})
    res["S8"] = {"gate": "S8", "lives": s8r, "passed": all(v["passed"] and v["receipts"][1] == 0 and v["foresight"][1] == 0
                                                         for v in s8r.values())}
    # ---- C1s, L1s, S9 on the lives with strikes
    c1r, l1r, s9 = {}, {}, {"predictions": 0, "outcomes": 0, "verdicts": []}
    for seed in C1_SEEDS:
        a = json.load(open(OUT / f"C1A_{seed}.json")); b = json.load(open(OUT / f"C1B_{seed}.json"))
        seat = json.loads((OUT / f"seat3_{seed}.json").read_text())
        cA, cB = CS.load_state(seat["blob"]), CS.load_state(b["blob"])
        last = seat["log"][-1]["seq"] if seat["log"] else 0
        sA = seat["log"] + [r for r in cA.outbox if r["seq"] > last]; sB = cB.outbox
        blocks = [r["entry"]["self"] for r in sB if r["kind"] == "diary"]
        ch, bad = SS.verify(sB, blocks); n, fb = SS.foresight(sB)
        c1r[seed] = {"final_state_identical": CS.dump_state(cA, False) == CS.dump_state(cB, False),
                     "record_stream_identical": sA == sB, "roundtrips_exact": f'{a["roundtrips_exact"]}/{a["steps"]}',
                     "receipts": [ch, len(bad)], "foresight": [n, fb], "caution_end": cB.me.caution, "verdict_end": cB.me.verdict}
        c1r[seed]["passed"] = (c1r[seed]["final_state_identical"] and c1r[seed]["record_stream_identical"]
                               and a["roundtrips_exact"] == a["steps"] and not bad and fb == 0)
        kept = sum(1 for r in sB if r["kind"] == "outcome" and r["act_kind"] < S.READINGS and not r["struck"])
        ok, v = G1.check_laws(sB, kept, cB); l1r[seed] = {"passed": ok, **v}
        s9["predictions"] += sum(1 for r in sB if r["kind"] == "predict" and r["act_kind"] == S.READINGS)
        s9["outcomes"] += sum(1 for r in sB if r["kind"] == "outcome" and r["act_kind"] == S.READINGS)
        s9["verdicts"].append(cB.me.verdict[S.READINGS])
    res["C1s"] = {"gate": "C1s", "lives": c1r, "passed": all(v["passed"] for v in c1r.values())}
    res["L1s"] = {"gate": "L1s", "lives": l1r, "passed": all(v["passed"] for v in l1r.values())}
    res["S9"] = {"gate": "S9", **s9, "passed": s9["predictions"] > 0 and "MINE" not in s9["verdicts"]}
    # ---- C2s: identical record-stream lives on every machine that ran `c2`
    c2s = [json.load(open(f)) for f in sorted(glob.glob(str(OUT / "C2s_*.json")))]
    res["C2s"] = {"gate": "C2s", "machines": [{"cpu": x["cpu"], "numpy": x["numpy"]} for x in c2s],
                  "passed": len(c2s) >= 2 and len({json.dumps(x["lives"], sort_keys=True) for x in c2s}) == 1
                  and len({x["numpy"].split(".")[0] for x in c2s}) >= 2}
    for g in ("S1r", "S2", "S3", "S4", "S5", "S6", "S7"):
        res[g] = json.load(open(OUT / f"{g}_streams.json"))
    res["D1s"] = json.load(open(OUT / "D1s.json"))
    hard = ("S1r", "S2", "S8", "C1s", "C2s")
    verdict = {"all_passed": all(res[g]["passed"] for g in res), "hard_failed": [g for g in hard if not res[g]["passed"]],
               "gates": {g: res[g]["passed"] for g in res}}
    save("judge_part3", {**verdict, "detail": res})


if __name__ == "__main__":
    cmd = sys.argv[1]
    {"streams": streams, "c2": c2, "demo": demo}.get(cmd, lambda: None)()
    if cmd == "s8":
        s8(int(sys.argv[2]))
    elif cmd == "c1":
        c1(int(sys.argv[2]), sys.argv[3])
    elif cmd == "judge":
        judge(sys.argv[2])
