"""Teich v0.6 twin gates (spec V06 §5) from twin_v06.py outputs: N0' (nothing undeclared changes), F1' (reasons are
causes), T1' (T1 inside the creature code), S (inherited self verdicts), and W0 on every v0.6 twin (its public journal
replays its whole life).
    python3 twin_judge.py OUT.json TWIN_1.json [TWIN_2.json ...] [--no-w0]   (W0 replays each life in full: slow)
"""
from __future__ import annotations

import bisect
import json
import math
import sys

import creature_v06 as C6
import delib_cert as DC
import f1_v06 as F
from replay_v06 import replay

# Declared changes (spec V06 §4). Each entry: record kind -> what may differ once a deliberated tie has been decided
# differently from the index. Every other kind, and every other field, must stay identical.
DECLARED_KINDS = {"thought", "think-predict", "dream", "thought-refused"}
POINTERS = ("predict_seq", "log_through")
K_VIRTUAL = (2, 3, 5, 9)


# ====================================================================== canonical streams
def canon(recs, also=None):
    """Drop the journal's op records; renumber seq and every seq pointer to the count of UNDECLARED records up to it
    (Amendment 2: the twins legitimately write different numbers of declared records, which must not shift pointers).
    also: a state object whose seq pointers are renumbered the same way (-> (records, state))."""
    kept = sorted((r for r in recs if r["kind"] != "op"), key=lambda r: r["seq"])
    seqs = [r["seq"] for r in kept if r["kind"] not in DECLARED_KINDS]

    def fix(x):
        if isinstance(x, dict):
            return {k: (bisect.bisect_right(seqs, v) if k in POINTERS and isinstance(v, int) else fix(v))
                    for k, v in x.items() if k != "seq"}
        if isinstance(x, list):
            return [fix(v) for v in x]
        return x
    if also is not None:
        return [fix(r) for r in kept], fix(also)
    return [fix(r) for r in kept]


def drop_think(x):
    """The declared THINK self-knowledge, removed: every "THINK" key, and every list item about kind THINK."""
    if isinstance(x, dict):
        return {k: drop_think(v) for k, v in x.items() if k != "THINK"}
    if isinstance(x, list):
        return [drop_think(v) for v in x if not (isinstance(v, dict) and v.get("kind") == "THINK")]
    return x


def as_v05(r):
    """The declared format changes, undone: think@2 -> think@1 (u dropped), deliberation dropped, organ dropped,
    v0.6 versions/identities masked (growth kinds are compared on their bindings)."""
    r = json.loads(json.dumps(r))
    if r["kind"] == "heard":
        r.pop("organ", None)
    if r["kind"] == "reason" and r["rule"] == "think@2":
        r["rule"] = "think@1"; r["inputs"].pop("u")
    if r["kind"] == "act":
        r.pop("deliberation", None)
    if r["kind"] == "diary":
        r["entry"]["self"] = drop_think(r["entry"].get("self"))
    if r["kind"] in ("growth", "growth-proposal"):
        for k in ("version", "version_if_approved", "identity", "prev_identity", "amendment_sha"):
            r.pop(k, None)
        if "amendment" in r:
            r["amendment"].pop("from_version", None)
    return r


def is_think(r):
    return r["kind"] in ("reason", "act") and r.get("act_type") == "think"


def n0(t):
    a = [as_v05(r) for r in canon(t["records5"])]
    b6 = canon(t["records6"]); b = [as_v05(r) for r in b6]
    # the first night v0.6 chose differently from the index rule
    first = next((i for i, r in enumerate(b6) if r["kind"] == "act" and r.get("deliberation")
                  and r["act"] != r["deliberation"]["tied"][0]), None)
    lim = len(b) if first is None else first
    pre = next((i for i in range(min(lim + 1, len(a), len(b))) if a[i] != b[i]), None)
    prefix_ok = pre is None or (first is not None and pre == first)
    # after it: every undeclared kind's subsequence identical; think reason/act only in the declared fields
    kinds = sorted({r["kind"] for r in a} | {r["kind"] for r in b})
    bad = {}
    for k in kinds:
        if k in DECLARED_KINDS:
            continue
        sa = [r for r in a if r["kind"] == k and not is_think(r)]
        sb = [r for r in b if r["kind"] == k and not is_think(r)]
        if sa != sb:
            j = next((i for i in range(min(len(sa), len(sb))) if sa[i] != sb[i]), min(len(sa), len(sb)))
            bad[k] = {"n5": len(sa), "n6": len(sb), "first": j, "v5": sa[j] if j < len(sa) else None,
                      "v6": sb[j] if j < len(sb) else None}
    ta = [r for r in a if is_think(r)]; tb = [r for r in b if is_think(r)]
    think_ok = len(ta) == len(tb) and all(
        (x["kind"], x["act_id"]) == (y["kind"], y["act_id"]) and (x["kind"] == "act" or x["rule"] == y["rule"])
        for x, y in zip(ta, tb))
    # the state: everything but the declared parts identical (body, dials, heart, self apart from THINK, door, Ears map)
    s5, s6 = json.loads(t["blob5"]), json.loads(t["blob6"])
    for s, recs in ((s5, t["records5"]), (s6, t["records6"])):
        _, (le, me) = canon(recs, also=[s.get("last_entry"), s["self"]])
        s["last_entry"] = drop_think(le); s["self"] = drop_think(me)
    state_diff = sorted(k for k in set(s5) | set(s6)
                        if k not in ("v", "species", "seq", "work", "growth", "self") and s5.get(k) != s6.get(k))
    self_diff = sorted(k for k in set(s5["self"]) | set(s6["self"]) if s5["self"].get(k) != s6["self"].get(k))
    g5, g6 = s5["growth"], s6["growth"]
    growth_ok = ([a["bindings"] for a in g5["applied"]] == [a["bindings"] for a in g6["applied"]]
                 and g5["refused"] == g6["refused"])
    return {"records": [len(a), len(b)], "first_divergent_choice": first, "first_record_difference": pre,
            "prefix_ok": prefix_ok, "undeclared_kind_diffs": bad, "think_ok": think_ok, "state_diff": state_diff,
            "self_diff": self_diff, "growth_bindings_ok": growth_ok,
            "passed": prefix_ok and not bad and think_ok and not state_diff and not self_diff and growth_ok}


# ====================================================================== T1' data
def nights(t):
    """Per night of the v0.6 twin: u (logged), the real tie (tied, act, steps, rereads), and the probes."""
    recs = sorted(t["records6"], key=lambda r: r["seq"])
    reasons = {r["act_id"]: r for r in recs if r["kind"] == "reason" and r["rule"] == "think@2"}
    out = []
    for r in recs:
        if r["kind"] == "act" and r["act_type"] == "think":
            rs = reasons[r["act_id"]]
            out.append({"night": r["night"], "u": float.fromhex(rs["inputs"]["u"]), "act": r["act"],
                        "tie": r.get("deliberation")})
    return out


def decide(k, u):
    c, steps, rereads, _, und = DC.deliberate(k, u)
    return c, steps, und


def t1(twins, n_uniform=200_000):
    """T1's bars (PREREG_T1) on the lived read-outs of v0.6 twins, for virtual k = 2, 3, 5, 9, plus the real ties."""
    from scipy.stats import chi2_contingency, chisquare
    import numpy as np
    lives = [nights(t) for t in twins]
    allu = [n for l in lives for n in l]; N = len(allu); res = {}; ok = True
    for k in K_VIRTUAL:
        ch = np.array([decide(k, n["u"])[0] for n in allu]); st = np.array([decide(k, n["u"])[1] for n in allu])
        cnt = np.bincount(ch, minlength=k); p_u = chisquare(cnt).pvalue; se = math.sqrt((1 / k) * (1 - 1 / k) / N)
        a = bool(p_u > 0.01 and np.all(np.abs(cnt / N - 1 / k) <= 4 * se))
        T = np.zeros((k, k)); hits = []
        for l in lives:
            c = [decide(k, n["u"])[0] for n in l]
            for x, y in zip(c[:-1], c[1:]):
                T[x, y] += 1; hits.append(x == y)
        p_lag = chi2_contingency(T + 0)[1] if k in (3, 5) else None
        b = p_lag is None or p_lag > 0.01
        # T1c: the guess from the previous midnight's read-out (its state one day before) is at chance
        hit = float(np.mean(hits)); se_c = math.sqrt((1 / k) * (1 - 1 / k) / len(hits)); c_ok = hit <= 1 / k + 3 * se_c
        # T1d: a 1e-12 change in its body one day before
        pr = [p for t in twins for p in t["probes"]]
        diff = float(np.mean([decide(k, float.fromhex(p["perturbed"]))[0] != decide(k, float.fromhex(p["lived"]))[0]
                              for p in pr]))
        se_t = math.sqrt((1 / k) * (1 - 1 / k) / len(pr)); d_ok = diff >= (1 - 1 / k) - 3 * se_t
        # T1f: hardness from lived u matches uniform u (the same certified deliberation)
        rng = np.random.default_rng(7)
        ref = np.bincount(np.minimum([decide(k, float(x))[1] for x in rng.random(n_uniform)], 4), minlength=5) / n_uniform
        bins = np.bincount(np.minimum(st, 4), minlength=5); exp = ref * N; m = (bins + np.round(exp)) > 0
        p_h = chi2_contingency(np.stack([bins[m], np.round(exp[m]).astype(int)]))[1]; f_ok = p_h > 0.01
        res[k] = dict(N=N, counts=cnt.tolist(), p_uniform=p_u, T1a=a, p_lag=p_lag, T1b=b, guess_hit=hit, T1c=bool(c_ok),
                      twin_diff=diff, n_twins=len(pr), T1d=bool(d_ok), step_bins=bins.tolist(),
                      step_expected=exp.round(1).tolist(), p_hard=p_h, T1f=bool(f_ok))
        ok &= a and b and c_ok and d_ok and f_ok
    # T1b on u itself: lag-1 circular correlation of xi = 2 pi u, pooled within lives
    x = [np.array([2 * math.pi * n["u"] for n in l]) for l in lives]
    num = sum(np.sum(np.sin(v[1:] - v[1:].mean()) * np.sin(v[:-1] - v[:-1].mean())) for v in x)
    den = math.sqrt(sum(np.sum(np.sin(v[1:] - v[1:].mean()) ** 2) for v in x) *
                    sum(np.sum(np.sin(v[:-1] - v[:-1].mean()) ** 2) for v in x))
    rc = num / den; b_xi = abs(rc) < 3 / math.sqrt(N); ok &= b_xi
    # T1e: every exact shadow reproduces the lived read-out, and that read-out is the one the night's reason logged
    pr = [p for t in twins for p in t["probes"]]
    e1 = sum(p["replay"] == p["lived"] for p in pr)
    nxt = 0; tot = 0
    for t, l in zip(twins, lives):
        by = {n["night"]: n for n in l}
        for p in t["probes"]:
            if p["night"] in by:
                tot += 1; nxt += float.fromhex(p["lived"]) == by[p["night"]]["u"]
    e_ok = e1 == len(pr) and nxt == tot and tot > 0; ok &= e_ok
    # the real ties: fairness by position, per k (reported; pooled chi2 where every k has >= 5 expected per cell)
    real = {}
    for l in lives:
        for n in l:
            if n["tie"]:
                kk = len(n["tie"]["tied"]); real.setdefault(kk, []).append(n["tie"]["tied"].index(n["act"]))
    real_rep = {kk: {"n": len(v), "positions": np.bincount(v, minlength=kk).tolist(),
                     "p_uniform": float(chisquare(np.bincount(v, minlength=kk)).pvalue) if len(v) >= 5 * kk else None}
                for kk, v in sorted(real.items())}
    und = sum(1 for l in lives for n in l if n["tie"] and n["tie"]["undecided"])
    return {"per_k": res, "xi_lag_corr": rc, "xi_bound": 3 / math.sqrt(N), "T1b_xi": bool(b_xi),
            "T1e": f"{e1}/{len(pr)} exact shadows, {nxt}/{tot} logged u", "T1e_ok": bool(e_ok),
            "real_ties": real_rep, "undecided": und, "nights": N, "passed": bool(ok)}


# ====================================================================== S: inherited self verdicts
def s_verdicts(t):
    """The last diary's self verdicts for BODY-MEMORY and BODY-PATH, in both twins (S: FINE and GIVEN, equal)."""
    def last(recs):
        d = [r for r in sorted(recs, key=lambda r: r["seq"]) if r["kind"] == "diary" and r["entry"].get("self")]
        k = d[-1]["entry"]["self"]["self5"]["kinds"] if d else {}
        return {x: k.get(x, {}).get("verdict") for x in ("BODY-MEMORY", "BODY-PATH")}
    v5, v6 = last(t["records5"]), last(t["records6"])
    return {"v05": v5, "v06": v6, "passed": v5 == v6 == {"BODY-MEMORY": "FINE", "BODY-PATH": "GIVEN"}}


def main(out, paths, w0=True):
    twins = [json.load(open(p)) for p in paths]
    rep = {"lives": [t["seed"] for t in twins], "n0": {}, "f1": {}, "w0": {}, "s": {}}
    for t in twins:
        s = str(t["seed"])
        rep["n0"][s] = n0(t)
        rep["f1"][s] = F.check_log(t["records6"])
        w = replay(t["start6"], t["records6"]) if w0 else {"ok": None}
        rep["w0"][s] = {k: v for k, v in w.items() if k not in ("published", "replayed")}
        rep["s"][s] = s_verdicts(t)
        print(s, "N0'", rep["n0"][s]["passed"], "| F1'", rep["f1"][s], "| W0", w["ok"], flush=True)
    rep["t1"] = t1(twins)
    rep["static"] = {"rule_purity_violations": F.rule_purity(), "lcl_import_violations": F.lcl_imports()}
    json.dump(rep, open(out, "w"), indent=1, default=float)
    print(json.dumps({"N0'": all(v["passed"] for v in rep["n0"].values()), "T1'": rep["t1"]["passed"],
                      "W0": all(v["ok"] for v in rep["w0"].values()) if w0 else "not run"}))


if __name__ == "__main__":
    nw = "--no-w0" in sys.argv
    main(sys.argv[1], [a for a in sys.argv[2:] if a != "--no-w0"], w0=not nw)
