"""Teich v0.5 — gate F1 (faithful reasons) and law L-CL checks, step 1. Also the core of the public live verify.

LOG CHECKS (need only the record log — anyone can run them on the published life):
  completeness  every `act` has an earlier `reason` with the same act_id, and every reason has its act
  receipt       RULES[rule](inputs) == act
  consequence   the act is what the creature then actually did (probe flags on the shown records; caution changes in
                that night's self block)
  necessity     moving an input across the rule's documented boundary changes the act as documented
STATIC CHECKS: rule purity (names used by rule functions) and L-CL import whitelist for the self's modules.
LIFE CHECKS (simulated lives; design seeds here, gate seeds at freeze):
  sufficiency   at decision time, scramble state outside the reason; the reason, the act and what the creature
                then does must not change
  planted cause a mutant whose execution secretly depends on state outside the reason must be caught
  identity      v0.5 behaves exactly as v0.4: every record other than reason/act, and the final state, identical
    python3 f1_v05.py
"""
from __future__ import annotations

import ast
import copy
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import acts_v05 as A  # noqa: E402
import self_sim as SS  # noqa: E402
import self_v04 as S4  # noqa: E402
import self_v05 as S5  # noqa: E402

LCL_ALLOWED = {"__future__", "fractions", "math", "self_v04", "acts_v05", "think_model_v05"}
LCL_MODULES = ["self_v04.py", "self_v05.py", "acts_v05.py", "think_model_v05.py"]
RULE_NAMES_ALLOWED = {"inp", "h", "k", "lo", "hi", "cand", "need", "min", "max", "will_of", "None", "n", "r", "enumerate", "w", "count", "days", "best", "c", "sorted", "_"}


# ====================================================================== log checks (live verify)
def check_log(recs):
    f = {"acts": 0, "completeness": 0, "receipt": 0, "consequence": 0, "necessity": 0, "necessity_tested": 0}
    reasons = {}
    by_seq = sorted(recs, key=lambda r: r["seq"])
    for i, r in enumerate(by_seq):
        if r["kind"] == "reason":
            reasons[r["act_id"]] = r
        elif r["kind"] == "act":
            f["acts"] += 1
            rs = reasons.get(r["act_id"])
            if rs is None or rs["seq"] > r["seq"] or rs["act_type"] != r["act_type"]:
                f["completeness"] += 1; continue
            act = A.RULES[rs["rule"]](rs["inputs"])
            f["receipt"] += act != r["act"]
            f["consequence"] += not consequence_ok(r, rs, by_seq, i)
            ok, tested = necessity_ok(rs["rule"], rs["inputs"], r["act"])
            f["necessity"] += not ok; f["necessity_tested"] += tested
    acts_ids = {r["act_id"] for r in recs if r["kind"] == "act"}
    f["completeness"] += sum(1 for a in reasons if a not in acts_ids)
    return f


def consequence_ok(act, reason, by_seq, i):
    if act["act_type"] == "probe":
        pids = set(range(act["pid_base"], act["pid_base"] + act["n"]))
        probed = {r["pid"] for r in by_seq[i + 1:] if r["kind"] == "shown" and r["pid"] in pids and r["probe"]}
        return probed == ({act["pid_base"] + act["act"]} if act["act"] is not None else set())
    if act["act_type"] == "caution":
        k, c = reason["inputs"]["kind"], reason["inputs"]["c"]
        diary = next((r for r in by_seq[i + 1:] if r["kind"] == "diary"), None)
        if diary is None:
            return True                                 # the night has not closed in this log yet
        will = [w for w in diary["entry"]["self"]["will"] if w["kind"] == k]
        return will == [] if act["act"] == c else (len(will) == 1 and will[0]["caution"] == [c, act["act"]])
    if act["act_type"] == "think":                      # the chosen region is the next 'chosen' thought recorded
        nxt = next((r for r in by_seq[i + 1:] if r["kind"] == "thought" and r["source"] == "chosen"), None)
        return nxt is not None and nxt["region"] == act["act"] and nxt["act_id"] == act["act_id"]
    if act["act_type"] == "grow":                       # a proposal is recorded exactly as chosen, or none is
        pr = [r for r in by_seq[i + 1:] if r["kind"] == "growth-proposal" and r["act_id"] == act["act_id"]]
        return (pr == []) if act["act"] == ["none"] else (len(pr) == 1 and pr[0]["bindings"] == act["act"][1])
    if act["act_type"] == "ask":                        # a question is delivered at most once, exactly as chosen;
        dl = [r for r in by_seq[i + 1:] if r["kind"] == "ask-delivered" and r["act_id"] == act["act_id"]]
        if act["act"] == ["silence"]:                   # silence is never delivered
            return dl == []
        return len(dl) <= 3 and all(r["q"] == act["act"] for r in dl)       # chosen at night, asked <= 3 times next day
    return True


def necessity_ok(rule, inp, act):
    """-> (ok, tested). Documented semantics, not the rule's code: each perturbation states what the act must become."""
    R = A.RULES[rule]
    if rule == "probe@1":
        if act is not None:                             # make the chosen mention ineligible: it must not be probed
            h2 = [[*h[:3], "GIVEN"] if h[2] == act else h for h in inp["hidden"]]
            return R({**inp, "hidden": h2}) != act, 1
        if inp["hidden"]:                               # make one eligible, with budget: it must be probed
            h = inp["hidden"][0]
            return R({**inp, "budget_left": 1, "hidden": [[0, h[1], h[2], "UNRESOLVED"]]}) == h[2], 1
        return True, 0
    if rule == "caution@1":
        c = inp["c"]; up = [[10, 10] if L == c else [0, 0] for L in range(5)]
        ok = True
        if c < 4:                                       # MINE with every next-level act struck: caution must rise
            ok &= R({**inp, "verdict": "MINE", "lv": up}) == c + 1
        if c > 0:                                       # FINE: caution cannot help, it must fall
            ok &= R({**inp, "verdict": "FINE"}) == c - 1
        return ok, 1
    if rule == "think@1":                               # make the chosen region the most thought-about: choice moves
        lc = list(inp["life_counts"]); lc[act] = max(lc) + 1
        return (R({"life_counts": lc}) != act) if len(lc) > 1 else True, 1
    if rule == "grow@1":
        if act[0] == "none" and not inp["pending"] and not inp["bindings"]:   # a binding appears: it must propose
            return R({**inp, "bindings": [["zz", 1, [0, 1]]]}) == ["propose", [["zz", 1]]], 1
        if act[0] == "propose":                         # a proposal already awaiting: it must not propose again
            return R({**inp, "pending": True}) == ["none"], 1
        return True, 0
    if rule == "ask@2":
        if act[0] == "silence":                         # a word heard often, never answered: it must ask
            return R({**inp, "door": [["zz", inp["door_min"], 0]]}) == ["word", "zz"], 1
        if act[0] == "word":                            # once the word has its two answers it must not ask it again
            d2 = [[w, c, 2] if w == act[1] else [w, c, d] for w, c, d in inp["door"]]
            return R({**inp, "door": d2}) != act, 1
        k = act[1]; others = [u for u in inp["unresolved"] if u[0] != k]
        if not others or inp["door"]:
            return True, 0
        o = others[0][0]
        u2 = [[k, 0, 0] if u[0] == k else ([o, inp["n_g"], inp["n_g"]] if u[0] == o else u) for u in inp["unresolved"]]
        return R({**inp, "unresolved": u2}) == ["region", o], 1
    if rule == "ask@1":
        if act[0] == "silence":                         # one unresolved region appears: it must ask about it
            return R({**inp, "unresolved": [[3, 0, 0]]}) == ["region", 3], 1
        k = act[1]; others = [u for u in inp["unresolved"] if u[0] != k]
        if not others:
            return True, 0
        o = others[0][0]                                # make k need everything and another need nothing
        u2 = [[k, 0, 0] if u[0] == k else ([o, inp["n_g"], inp["n_g"]] if u[0] == o else u) for u in inp["unresolved"]]
        return R({**inp, "unresolved": u2}) == ["region", o], 1
    return False, 0


# ====================================================================== static checks
def rule_purity():
    tree = ast.parse((HERE / "acts_v05.py").read_text()); bad = {}
    for fn in [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("probe_1", "caution_1", "ask_1", "think_1", "ask_2", "grow_1")]:
        names = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)} | {a.arg for a in fn.args.args}
        extra = names - RULE_NAMES_ALLOWED
        if extra:
            bad[fn.name] = sorted(extra)
    return bad


def lcl_imports():
    bad = {}
    for m in LCL_MODULES:
        tree = ast.parse((HERE / m).read_text()); mods = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom):
                mods.add((n.module or "").split(".")[0])
        if mods - LCL_ALLOWED:
            bad[m] = sorted(mods - LCL_ALLOWED)
    return bad


# ====================================================================== simulated lives
class Planted(S5.SecondSelf5):
    """MUTANT A: its execution skips probing whenever it holds an odd number of pending mentions — a hidden cause that
    never fires in these lives (each conversation is decided before the next), so only sufficiency can catch it."""
    def blocked_now(self, day):
        return len(self.pending) % 2 == 1

    def present(self, proposals, conversation, day, organ, emit):
        if self.blocked_now(day):
            real = S4.SecondSelf.present
            def blocked(me, *a):
                saved = me.probes_used; me.probes_used = S4.PROBES_PER_DAY
                try:
                    return real(me, *a)
                finally:
                    me.probes_used = saved
            S5.SecondSelf.present = blocked
            try:
                return super().present(proposals, conversation, day, organ, emit)
            finally:
                S5.SecondSelf.present = real
        return super().present(proposals, conversation, day, organ, emit)


class PlantedNight(Planted):
    """MUTANT B: its execution skips probing on odd days — a hidden cause that fires in real life, so the LOG
    (consequence) must catch it."""
    def blocked_now(self, day):
        return day % 2 == 1


def scramble(me, rng):
    """Change only state that no reason may depend on: other conversations' pending mentions, open readings and the
    readings kind's ring."""
    m = copy.deepcopy(me)
    for j in range(rng.randrange(1, 4)):
        m.pending[10_000_000 + j] = {"conversation": f"zz{j}", "act_kind": 0, "cw": 5, "altered": False, "probe": False,
                                     "p": [1, 2], "p0": [1, 2], "predict_seq": 0, "pid": 10_000_000 + j}
    m.open_readings = {7: {"seq": 1, "night": 0, "p": [1, 3]}}
    m.ring[S4.READINGS] = [{**S4._empty_night(), "lv": [[0, 0]] * 4 + [[rng.randrange(9), 0]]} for _ in range(S4.RING)]
    return m


def life(seed, cls, nights=90, rate=3.0, sufficiency=False):
    rng = random.Random(seed); srng = random.Random(seed + 99_000)   # scrambling has its own stream
    me = cls(); log = SS.Log(); T = {k: ("MINE", "GIVEN", "FINE")[k % 3] for k in range(9)}
    suff = {"tested": 0, "failed": 0}
    for d in range(nights):
        props, wrong = [], []
        for k, t in T.items():
            for _ in range(SS._pois(rng, rate)):
                cw = 1 + SS._pick(rng, SS.CW_P)
                props.append({"cluster": k, "kind": k, "sign": 1, "text_sha256": "x", "cn": cw, "cf": 5})
                wrong.append(rng.random() < SS.ERR[t][cw - 1])
        if sufficiency:
            ref = copy.deepcopy(me); scr = scramble(me, srng); a, b = SS.Log(), SS.Log()
            ia = ref.present(props, f"c{d}", d, "o", a.emit); ib = scr.present(props, f"c{d}", d, "o", b.emit)
            ra = [(r["kind"], r.get("inputs"), r.get("act")) for r in a.recs if r["kind"] in ("reason", "act")]
            rb = [(r["kind"], r.get("inputs"), r.get("act")) for r in b.recs if r["kind"] in ("reason", "act")]
            if ra:
                suff["tested"] += 1
                suff["failed"] += ra != rb or [x["probe"] for x in ia] != [x["probe"] for x in ib]
        items = me.present(props, f"c{d}", d, "o", log.emit)
        me.decide(f"c{d}", {it["pid"] for it, w in zip(items, wrong) if it["shown"] and w}, log.emit)
        me.emit = log.emit
        if sufficiency and isinstance(me, S5.SecondSelf5):
            ref = copy.deepcopy(me); scr = scramble(me, srng)
            la, lb = SS.Log(), SS.Log(); ref.emit, scr.emit = la.emit, lb.emit
            ref.nightly(log.seq); scr.nightly(log.seq)
            ra = [(r["kind"], r.get("inputs"), r.get("act")) for r in la.recs]
            rb = [(r["kind"], r.get("inputs"), r.get("act")) for r in lb.recs]
            suff["tested"] += 1; suff["failed"] += ra != rb or ref.caution != scr.caution
        block = me.nightly(log.seq)
        log.emit("diary", {"entry": {"self": block}})
    return log.recs, me, suff


def canonical(rs):
    """Records other than reason/act, with every seq pointer (predict_seq, log_through) translated to the ordinal of
    the record it points to among those records — so v0.4 and v0.5 logs compare by meaning, not by numbering."""
    kept = [r for r in rs if r["kind"] not in ("reason", "act")]
    ordinal = {r["seq"]: i for i, r in enumerate(kept)}
    seqs = sorted(ordinal)
    import bisect
    def through(t):                     # number of kept records with seq <= t
        return bisect.bisect_right(seqs, t)
    out = []
    for r in kept:
        r = {k: v for k, v in r.items() if k != "seq"}
        if r.get("predict_seq") is not None:
            r["predict_seq"] = ordinal[r["predict_seq"]]
        if r["kind"] == "diary":
            e = json.loads(json.dumps(r["entry"])); blk = e.get("self")
            if blk:
                blk.pop("self5", None)          # v0.5's own kinds are not part of v0.4's record
                blk["log_through"] = through(blk["log_through"])
                for part in ("verdicts", "will", "comparisons", "facts", "curiosity"):
                    for x in blk.get(part) or []:
                        x["receipt"]["log_through"] = through(x["receipt"]["log_through"])
                if blk.get("calibration"):
                    blk["calibration"]["receipt"]["log_through"] = through(blk["calibration"]["receipt"]["log_through"])
            r = {**r, "entry": e}
        out.append(r)
    return out


def main():
    out = {"rule_purity_violations": rule_purity(), "lcl_import_violations": lcl_imports()}
    tot = {"acts": 0, "completeness": 0, "receipt": 0, "consequence": 0, "necessity": 0, "necessity_tested": 0}
    suff = {"tested": 0, "failed": 0}; ident = {"lives": 0, "records_identical": 0, "state_identical": 0}
    kinds = {}
    for seed in range(8000, 8010):
        recs, me, s = life(seed, S5.SecondSelf5, sufficiency=True)
        for k, v in check_log(recs).items():
            tot[k] += v
        for r in recs:
            if r["kind"] == "act":
                kinds[r["act_type"]] = kinds.get(r["act_type"], 0) + 1
        suff["tested"] += s["tested"]; suff["failed"] += s["failed"]
        r4, me4, _ = life(seed, S4.SecondSelf)
        strip = canonical
        st5 = {k: v for k, v in me.to_json().items() if k not in ("next_act", "pending_question", "xring", "xverdict",
                                                                 "pending_body", "asked_pids", "hearing")}
        ident["lives"] += 1; ident["records_identical"] += strip(recs) == strip(r4)
        ident["state_identical"] += json.dumps(st5, sort_keys=True) == json.dumps(me4.to_json(), sort_keys=True)
    out["honest"] = {**tot, "acts_by_type": kinds}
    out["sufficiency"] = suff
    out["identity_with_v04"] = ident
    for name, cls in (("planted_A_pending_parity", Planted), ("planted_B_odd_days", PlantedNight)):
        pl = {"acts": 0, "completeness": 0, "receipt": 0, "consequence": 0, "necessity": 0, "necessity_tested": 0}
        psuff = {"tested": 0, "failed": 0}
        for seed in range(8000, 8010):
            recs, _, s = life(seed, cls, sufficiency=True)
            for k, v in check_log(recs).items():
                pl[k] += v
            psuff["tested"] += s["tested"]; psuff["failed"] += s["failed"]
        out[name] = {"log_flags": pl["consequence"] + pl["receipt"] + pl["completeness"], "sufficiency_flags": psuff["failed"],
                     "caught": pl["consequence"] + pl["receipt"] + pl["completeness"] + psuff["failed"] > 0}
    out["F1_pass"] = (not out["rule_purity_violations"] and not out["lcl_import_violations"]
                      and tot["completeness"] == tot["receipt"] == tot["consequence"] == tot["necessity"] == 0
                      and suff["failed"] == 0 and ident["records_identical"] == ident["state_identical"] == ident["lives"]
                      and out["planted_A_pending_parity"]["caught"] and out["planted_B_odd_days"]["log_flags"] > 0)
    print(json.dumps(out, indent=1))
    (HERE / "f1_design.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()


def check_xkinds(recs):
    """Recompute every v0.5 self-kind claim (BODY-MEMORY, BODY-PATH, THINK) from the records alone."""
    import self_v05 as S5x
    preds = {r["for_night"]: r for r in recs if r["kind"] == "body-predict"}
    reads = {r["night"]: r for r in recs if r["kind"] == "night-reading"}
    dreams = {r["night"]: r for r in recs if r["kind"] == "dream"}

    def night(k, x):
        if k == "THINK":
            return (1, 0 if dreams[x]["held"] else 1) if x in dreams else (0, 0)
        if x not in preds or x not in reads:
            return (0, 0)
        rd = reads[x]
        return S5x.body_outcomes(preds[x], rd["tonight"], rd["lengths"], set(rd["moved"]))[k]

    checked = bad = 0
    for r in recs:
        if r["kind"] != "diary" or "self5" not in (r["entry"].get("self") or {}):
            continue
        for k, v in r["entry"]["self"]["self5"]["kinds"].items():
            a, d = v["receipt"]["select"]["nights"]
            n = sum(night(k, x)[0] for x in range(a, d + 1)); m = sum(night(k, x)[1] for x in range(a, d + 1))
            checked += 1; bad += (n, m, S5x.xverdict(n, m)) != (v["n"], v["miss"], v["verdict"])
    return {"claims": checked, "mismatches": bad}
