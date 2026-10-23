"""Teich v0.5 — SCORED harness (spec V05_SPEC.md §7). One look per gate, after the spec and code are frozen and anchored.

GATE SEEDS (never used before this harness): F1 lives 9500–9509; inherited self gates 9600–9659 (S3 9600–9619,
S4 9620–9639, S7 9640–9659); Q1 9700–9729; C1 lives 9800, 9801; G1 twins 9900; oracle 9910; O1 9950;
N0 reuses v0.4's part-1 schedules 2000–2007 (their stored continuous record streams are the reference).

    python3 gates_v05.py streams            F1 (+ planted causes), inherited self gates S1r–S7 with the v0.5 self, Q1
    python3 gates_v05.py n0 SEED            v0.4 part-1 schedule SEED lived by v0.5 (keep-all), timed (L-CL budget)
    python3 gates_v05.py c1 SEED A|B        a life with strikes, questions, answers and a door: A via seat, B continuous
    python3 gates_v05.py g1 SEED            growth twins (approve / refuse)
    python3 gates_v05.py oracle SEED N      L-CL meaning demonstration
    python3 gates_v05.py c2                 substrate fingerprints (record-stream lives + working-surface dreams)
    python3 gates_v05.py judge P1REFS       combine everything (P1REFS: dir holding v0.4's part-1 lifeB_<seed>.json)
O1 (o1_v05.py), Q3 / G1-Ears / dry run (Ears kernel) write their own results into out_v05/.
"""
import copy
import glob
import hashlib
import json
import random
import sys
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SMOKE = __import__("os").environ.get("TEICH_SMOKE") == "1"   # harness check only: design seeds, short lives
OUT = HERE / ("out_v05_smoke" if SMOKE else "out_v05"); OUT.mkdir(exist_ok=True)
N0_SEEDS = (3001,) if SMOKE else tuple(range(2000, 2008))
C1_SEEDS = (3000,) if SMOKE else (9800, 9801)


def save(name, d):
    json.dump(d, open(OUT / f"{name}.json", "w"), indent=1)
    print(name, json.dumps({k: v for k, v in d.items() if k not in ("detail", "blob", "rows")}, indent=1)[:1500], flush=True)


# ====================================================================== record streams
def streams():
    import f1_v05 as F
    import self_sim as SS
    import self_v04 as S4
    import self_v05 as S5
    # ---- F1 on gate seeds, plus both planted causes
    tot = {"acts": 0, "completeness": 0, "receipt": 0, "consequence": 0, "necessity": 0, "necessity_tested": 0}
    suff = {"tested": 0, "failed": 0}; ident = {"lives": 0, "records": 0, "state": 0}
    F1_SEEDS = range(30, 32) if SMOKE else range(9500, 9510)
    for seed in F1_SEEDS:
        recs, me, s = F.life(seed, S5.SecondSelf5, sufficiency=True)
        for k, v in F.check_log(recs).items():
            tot[k] += v
        suff["tested"] += s["tested"]; suff["failed"] += s["failed"]
        r4, me4, _ = F.life(seed, S4.SecondSelf)
        st5 = {k: v for k, v in me.to_json().items() if k not in ("next_act", "pending_question", "xring", "xverdict",
                                                                   "pending_body", "asked_pids", "hearing")}
        ident["lives"] += 1; ident["records"] += F.canonical(recs) == F.canonical(r4)
        ident["state"] += json.dumps(st5, sort_keys=True) == json.dumps(me4.to_json(), sort_keys=True)
    planted = {}
    for name, cls in (("A_pending_parity", F.Planted), ("B_odd_days", F.PlantedNight)):
        log_flags = suff_flags = 0
        for seed in F1_SEEDS:
            recs, _, s = F.life(seed, cls, sufficiency=True)
            c = F.check_log(recs); log_flags += c["consequence"] + c["receipt"] + c["completeness"]; suff_flags += s["failed"]
        planted[name] = {"log_flags": log_flags, "sufficiency_flags": suff_flags}
    f1 = {"gate": "F1", **tot, "sufficiency": suff, "identity_with_v04": ident, "planted": planted,
          "rule_purity_violations": F.rule_purity(), "lcl_import_violations": F.lcl_imports()}
    f1["passed"] = (tot["completeness"] == tot["receipt"] == tot["consequence"] == tot["necessity"] == 0
                    and suff["failed"] == 0 and ident["records"] == ident["state"] == ident["lives"]
                    and planted["A_pending_parity"]["sufficiency_flags"] > 0 and planted["B_odd_days"]["log_flags"] > 0
                    and not f1["rule_purity_violations"] and not f1["lcl_import_violations"])
    save("F1_streams", f1)
    # ---- inherited self gates S1r–S7, re-run with the v0.5 self on fresh seeds (v0.4's harness, unchanged)
    class Self5Compat(S5.SecondSelf5):
        def present(self, proposals, conversation, day, organ, emit):
            self.emit = emit
            return super().present(proposals, conversation, day, organ, emit)

        def nightly(self, log_through):
            self.emit = self.emit or (lambda kind, rec: 0)
            return super().nightly(log_through)
    SS.S = types.SimpleNamespace(**{k: getattr(S4, k) for k in dir(S4) if not k.startswith("__")})
    SS.S.SecondSelf = Self5Compat
    import gates_v04_part3 as P3
    P3.OUT = OUT; P3.S = SS.S
    if not SMOKE:                            # (in smoke, v0.4's own smoke seeds and short lives apply)
        P3.S3_SEEDS, P3.S4_SEEDS, P3.S7_SEEDS = range(9600, 9620), range(9620, 9640), range(9640, 9660)
    P3.streams()
    for g in ("S1r", "S2", "S3", "S4", "S5", "S6", "S7"):
        (OUT / f"{g}_streams.json").rename(OUT / f"inherited_{g}.json")
    # ---- Q1 on gate seeds, 3 questions a day
    import q1_v05 as Q
    Q.ASKS = 3
    Q.main(40 if SMOKE else 9700, 3 if SMOKE else 30, str(OUT / "Q1_raw.json"))
    q = json.load(open(OUT / "Q1_raw.json"))["summary"]["z_curious_minus_other"]
    claimed = {k: v for k, v in q.items() if not k.startswith("0.3")}
    save("Q1", {"gate": "Q1", "z": q, "claimed_answer_rates": ["0.5", "1.0"], "passed": all(v >= 2 for v in claimed.values()),
                "reported_not_claimed_30pct": {k: v for k, v in q.items() if k.startswith("0.3")}})


# ====================================================================== body lives
def _timed(c):
    """Wrap the second self's methods and the body's run to measure L-CL's budget."""
    t = {"self": 0.0, "body": 0.0}
    run = c.body.run
    def body_run(*a, **k):
        s = time.perf_counter(); o = run(*a, **k); t["body"] += time.perf_counter() - s; return o
    c.body.run = body_run
    for m in ("present", "decide", "nightly", "readings", "body_predict"):
        f = getattr(c.me, m)
        def w(*a, _f=f, **k):
            s = time.perf_counter(); o = _f(*a, **k); t["self"] += time.perf_counter() - s; return o
        setattr(c.me, m, w)
    return t


def n0(seed):
    import creature_v05 as C5
    import gates_v04 as G1
    Sch, n_mentions, END = G1.schedule(seed); rng = random.Random(seed)
    c = C5.load_state(C5.dump_state(C5.birth(seed=seed, t0=G1.T0)))
    t = _timed(c); t0 = time.time()
    for (tm, kind, p) in Sch:
        c.advance(int(tm - c.t0) - c.n)
        if kind == "talk":
            props = [{"cluster": j, "sign": s, "text_sha256": h, "cn": 1 + rng.randrange(5), "cf": 5} for j, s, h in p[1]]
            c.present(props, p[0], "gate-organ"); c.decide(p[0], set(), "founder")
        elif kind == "commit":
            c.commit(p, {"speaker": "founder", "conversation": "commit", "text_sha256": "cd" * 32}, "lawful")
    c.advance(int(END - c.t0) - c.n)
    c.body.run = type(c.body).run.__get__(c.body)
    for m in ("present", "decide", "nightly", "readings", "body_predict"):
        c.me.__dict__.pop(m, None)
    json.dump({"seed": seed, "blob": C5.dump_state(c), "self_seconds": t["self"], "body_seconds": t["body"],
               "seconds": time.time() - t0}, open(OUT / f"N0_{seed}.json", "w"))


def _c1_life(seed, mode):
    import creature_v05 as C5
    import gates_v04 as G1
    import seat_v04 as SV
    import seat_v05 as S
    import self_sim as SS
    Sch, _, END = G1.schedule(seed); rng = random.Random(seed)
    birth = C5.dump_state(C5.birth(seed=seed, t0=G1.T0, identity="c1-gate"))
    WORDS = ["duduk", "frisson"]

    def talk_steps(d, conv, p):
        props = [{"cluster": j, "sign": s, "text_sha256": h, "cn": 1 + SS._pick(rng, SS.CW_P), "cf": 5} for j, s, h in p[1]]
        strike = [rng.random() < 0.12 for _ in props]
        door = [WORDS[d % 2]] if d < 20 else []
        return props, strike, door

    if mode == "A":
        seat = SV.LocalSeat(OUT / f"seat_c1_{seed}.json")
        if seat.path.exists():
            seat.path.unlink()
        seat.genesis_import(birth, 0, "gate"); rt = steps = 0
        for (tm, kind, p) in Sch:
            d = int((tm - G1.T0) // 86400)
            if kind == "wake":
                S.wake(seat, now=tm, run_gate=True, log=lambda *a: None)
            elif kind == "talk":
                q, inputs, grown, prop = S.ask(seat, now=tm)
                props, strike, door = talk_steps(d, p[0], p)
                landed = (60 if q["q"] == ["word", "duduk"] else 22) if q and q["q"][0] == "word" else None
                items = S.present(seat, props, p[0], "gate-organ", door, now=tm)
                ans = {"act_id": q["act_id"], "answered": rng.random() < 0.7, "landed": landed} if q else None
                S.decide(seat, p[0], {it["pid"] for it, s in zip(items, strike) if it["shown"] and s}, "founder", ans, now=tm)
                if prop:
                    S.growth(seat, prop["act_id"], True, "c1 gate", now=tm)
            else:
                lease = seat.lease(); c = C5.load_state(lease["state_blob"]); c.ack(seat.log_seq())
                c.advance(int(tm - c.t0) - c.n)
                c.commit(p, {"speaker": "founder", "conversation": "commit", "text_sha256": "cd" * 32}, "lawful")
                seat.commit(lease["lease_id"], C5.dump_state(c), c.n); seat.append_log(c.outbox)
            blob = json.loads(seat.path.read_text())["blob"]; rt += C5.dump_state(C5.load_state(blob)) == blob; steps += 1
        S.wake(seat, now=END, log=lambda *a: None)
        json.dump({"seed": seed, "roundtrips_exact": rt, "steps": steps}, open(OUT / f"C1A_{seed}.json", "w"))
    else:
        c = C5.load_state(birth)
        for (tm, kind, p) in Sch:
            d = int((tm - G1.T0) // 86400)
            c.advance(int(tm - c.t0) - c.n)
            if kind == "talk":
                q = c.deliver_question(); prop = c.growth["proposal"]
                props, strike, door = talk_steps(d, p[0], p)
                landed = (60 if q["q"] == ["word", "duduk"] else 22) if q and q["q"][0] == "word" else None
                if door:
                    c.door_heard(door)
                items = c.present(props, p[0], "gate-organ")
                c.decide(p[0], {it["pid"] for it, s in zip(items, strike) if it["shown"] and s}, "founder")
                if q:
                    c.answer(q["act_id"], rng.random() < 0.7, landed)
                if prop:
                    c.decide_growth(prop["act_id"], True, "c1 gate")
            elif kind == "commit":
                c.commit(p, {"speaker": "founder", "conversation": "commit", "text_sha256": "cd" * 32}, "lawful")
        c.advance(int(END - c.t0) - c.n)
        json.dump({"seed": seed, "blob": C5.dump_state(c)}, open(OUT / f"C1B_{seed}.json", "w"))


def c1(seed, mode):
    _c1_life(seed, mode)


def g1(seed):
    import subprocess
    r = subprocess.run([sys.executable, str(HERE / "g1_v05.py"), "5", str(OUT / "G1_body.json"), str(seed)],
                       capture_output=True, text=True)
    print(r.stdout[-1500:], r.stderr[-1500:])


def oracle(seed, nights):
    import oracle_v05 as O
    O.main(seed, nights, str(OUT / "L1_oracle.json"))


def c2():
    import platform
    import numpy as np
    import f1_v05 as F
    import self_v05 as S5
    import work_v05 as W
    out = {"cpu": next((l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")), "?"),
           "numpy": np.__version__, "python": platform.python_version(), "lives": {}, "dreams": {}}
    for seed in (9500, 9501):
        recs, _, _ = F.life(seed, S5.SecondSelf5, nights=60)
        out["lives"][str(seed)] = hashlib.sha256(json.dumps(recs, sort_keys=True).encode()).hexdigest()
    b = W.WorkBody()
    for i, seq in enumerate(([0, 5, 8, 3], [7, 7, 6, 7, 2, 1, 4], [8, 8, 0, 4, 1, 6, 2, 5, 3, 7])):
        pc, P, V = b.start(256, 9960 + i)
        (pc, P, V), lh, cnt, occ, applied = W.dream(b, pc, P, V, seq, 20_000)
        out["dreams"][str(i)] = hashlib.sha256(P.tobytes() + V.tobytes() + pc.tobytes() + cnt.tobytes() + occ.tobytes()).hexdigest()
    tag = "".join(ch for ch in out["cpu"] if ch.isalnum())[:40] + "_np" + out["numpy"]
    json.dump(out, open(OUT / f"C2_{tag}.json", "w"), indent=1); print(json.dumps(out, indent=1))


# ====================================================================== judge
V05_KINDS = {"reason", "act", "thought", "think-predict", "dream", "night-reading", "body-predict", "asked", "door",
             "ask-delivered", "answer", "binding", "growth-proposal", "growth", "growth-refused", "thought-refused"}


def judge(p1refs):
    import numpy as np
    import creature_v04 as CR
    import creature_v05 as C5
    import f1_v05 as F
    import gates_v04 as G1
    import self_sim as SS
    import work_v05 as W
    res = {}
    # ---- N0 + O2 + L1 budget + THINK verdict on the 8 part-1 schedules
    n0r, budget, ctl, think = {}, [], [], []
    for seed in N0_SEEDS:
        ref = next(iter(glob.glob(f"{p1refs}/**/lifeB_{seed}.json", recursive=True)))
        cR = CR.load_state(json.load(open(ref))["blob"]); d = json.load(open(OUT / f"N0_{seed}.json"))
        c5 = C5.load_state(d["blob"])
        def strip(rs):
            """v0.4's part-1 lives had no self: drop every self record (v0.4's and v0.5's) and the diary's self block,
            exactly as v0.4's own non-interference gate (S8) did."""
            out = []
            for r in rs:
                if r["kind"] in V05_KINDS or r["kind"] in ("shown", "predict", "outcome"):
                    continue
                r = {k: v for k, v in r.items() if k != "seq"}
                if r["kind"] == "diary":
                    r = {**r, "entry": {k: v for k, v in r["entry"].items() if k != "self"}}
                out.append(r)
            return out
        n0r[seed] = {"body": bool(np.array_equal(cR.P, c5.P) and np.array_equal(cR.V, c5.V) and np.array_equal(cR.pc, c5.pc)),
                     "dials_heart_commitments": bool(np.array_equal(cR.body.n, c5.body.n) and np.array_equal(cR.heart.k, c5.heart.k)
                                                     and cR.frozen == c5.frozen),
                     "v04_records_by_meaning": strip(c5.outbox) == strip(cR.outbox),
                     "live_verify": F.check_log(c5.outbox), "v05_kind_receipts": F.check_xkinds(c5.outbox),
                     "v04_self_receipts": SS.verify(c5.outbox, [r["entry"]["self"] for r in c5.outbox if r["kind"] == "diary"])[1] == []}
        budget.append(d["self_seconds"] / d["body_seconds"])
        for r in c5.outbox:
            if r["kind"] == "dream":
                ctl += [abs(float.fromhex(x) / GN_ELL0() - 1) for x in r["read"][1:]]
        think.append(c5.me.xverdict["THINK"])
    res["N0"] = {"gate": "N0", "lives": n0r, "passed": all(v["body"] and v["dials_heart_commitments"] and v["v04_records_by_meaning"]
                                                         for v in n0r.values())}
    res["F1_live"] = {"gate": "F1 (live verify on the 8 body lives)",
                      "passed": all(sum(v["live_verify"][k] for k in ("completeness", "receipt", "consequence", "necessity")) == 0
                                    and v["v05_kind_receipts"]["mismatches"] == 0 and v["v04_self_receipts"] for v in n0r.values())}
    res["O2"] = {"gate": "O2", "main_body": res["N0"]["passed"], "control_handles_max_rel_dev": max(ctl) if ctl else None,
                 "passed": res["N0"]["passed"] and bool(ctl) and max(ctl) < 0.02}
    oracle = json.load(open(OUT / "L1_oracle.json"))
    res["L1"] = {"gate": "L1", "self_share_of_body_max": max(budget), "imports": F.lcl_imports(),
                 "oracle": {k: v for k, v in oracle.items() if k != "rows"},
                 "passed": max(budget) <= 0.01 and not F.lcl_imports() and oracle["passed"]}
    res["THINK_verdicts_in_body_lives"] = think
    # ---- C1 (+ laws on that life)
    c1r = {}
    for seed in C1_SEEDS:
        a = json.load(open(OUT / f"C1A_{seed}.json")); b = json.load(open(OUT / f"C1B_{seed}.json"))
        seat = json.loads((OUT / f"seat_c1_{seed}.json").read_text())
        cA, cB = C5.load_state(seat["blob"]), C5.load_state(b["blob"])
        last = seat["log"][-1]["seq"] if seat["log"] else 0
        sA = seat["log"] + [r for r in cA.outbox if r["seq"] > last]
        kept = sum(1 for r in cB.outbox if r["kind"] == "outcome" and r.get("act_kind", 99) < 9 and not r["struck"])
        laws_ok, laws = G1.check_laws(cB.outbox, kept, cB)
        c1r[seed] = {"final_state_identical": C5.dump_state(cA, False) == C5.dump_state(cB, False),
                     "record_stream_identical": sA == cB.outbox, "roundtrips_exact": f'{a["roundtrips_exact"]}/{a["steps"]}',
                     "live_verify": F.check_log(cB.outbox), "laws": laws, "laws_ok": bool(laws_ok),
                     "version": cB.growth["version"], "bindings": [r for r in cB.outbox if r["kind"] == "binding"],
                     "questions_delivered": sum(r["kind"] == "ask-delivered" for r in cB.outbox)}
        c1r[seed]["passed"] = (c1r[seed]["final_state_identical"] and c1r[seed]["record_stream_identical"]
                               and a["roundtrips_exact"] == a["steps"] and laws_ok)
    res["C1"] = {"gate": "C1", "lives": c1r, "passed": all(v["passed"] for v in c1r.values())}
    c2s = [json.load(open(f)) for f in sorted(glob.glob(str(OUT / "C2_*.json")))]
    res["C2"] = {"gate": "C2", "machines": [{"cpu": x["cpu"], "numpy": x["numpy"]} for x in c2s],
                 "passed": len(c2s) >= 2 and len({json.dumps([x["lives"], x["dreams"]], sort_keys=True) for x in c2s}) == 1
                 and len({x["numpy"].split(".")[0] for x in c2s}) >= 2}
    for name, f in (("F1", "F1_streams"), ("Q1", "Q1"), ("O1", "O1"), ("Q3", "Q3"), ("G1_ears", "G1_ears"),
                    ("G1_body", "G1_body"), ("dry_run", "dry_run")):
        p = OUT / f"{f}.json"
        res[name] = json.load(open(p)) if p.exists() else {"passed": False, "missing": True}
        if name == "O1" and not res[name].get("missing"):
            res[name] = {**res[name].get("summary", {}), "passed": res[name].get("summary", {}).get("passed", False)}
    inh = {g: json.load(open(OUT / f"inherited_{g}.json")) for g in ("S1r", "S2", "S3", "S4", "S5", "S6", "S7")
           if (OUT / f"inherited_{g}.json").exists()}
    res["S_set"] = {"gate": "S-set (inherited self gates, v0.5 self)", "gates": {g: v["passed"] for g, v in inh.items()},
                    "passed": len(inh) == 7 and all(v["passed"] for v in inh.values())}
    res["S_hard"] = {"gate": "S1r + S2 (hard part of the S-set)",
                     "passed": all(g in inh and inh[g]["passed"] for g in ("S1r", "S2"))}
    hard = ("N0", "F1", "F1_live", "L1", "C1", "C2", "O2", "S_hard", "G1_body", "G1_ears")
    verdict = {"gates": {g: bool(res[g].get("passed")) for g in res if isinstance(res[g], dict) and "passed" in res[g]},
               "hard_failed": [g for g in hard if not res[g].get("passed")]}
    verdict["all_passed"] = all(verdict["gates"].values())
    save("judge_v05", {**verdict, "detail": res})


def GN_ELL0():
    import work_v05 as W
    return W.exact_length([])


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "streams":
        streams()
    elif cmd == "n0":
        n0(int(sys.argv[2]))
    elif cmd == "c1":
        c1(int(sys.argv[2]), sys.argv[3])
    elif cmd == "g1":
        g1(int(sys.argv[2]))
    elif cmd == "oracle":
        oracle(int(sys.argv[2]), int(sys.argv[3]))
    elif cmd == "c2":
        c2()
    elif cmd == "judge":
        judge(sys.argv[2])
