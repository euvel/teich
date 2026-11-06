"""Teich v0.7 twin gates (PREREG_V07 §2) from twin_v07.py outputs: K2 (consent: nothing undeclared changes),
S (inherited verdicts), F1 (reasons are causes), T1'' (its ties stay fair), K4 (replay; beacons verified separately).
    python3 judge_v07.py OUT.json TWIN_1.json [TWIN_2.json ...] [--no-k4] [--verify-beacons]
"""
from __future__ import annotations

import base64
import bisect
import json
import math
import sys

import numpy as np

import delib_cert as DC
import f1_v06 as F

DECLARED_KINDS = {"thought", "think-predict", "dream", "thought-refused"}
DIARY_DECLARED = ("attending_most", "shifts", "still_reading", "still_ids", "known", "verification")
BODY_KINDS = ("BODY-MEMORY", "BODY-PATH")
POINTERS = ("predict_seq", "log_through")
SELF_DECLARED = ("open_readings", "pending_body", "xring", "xverdict")   # body readings; BODY verdicts checked apart
K_VIRTUAL = (2, 3, 5, 9)


# ====================================================================== canonical streams
def canon(recs, also=None):
    """Drop op and sky records; renumber seq and seq pointers to the count of UNDECLARED records up to them."""
    kept = sorted((r for r in recs if r["kind"] not in ("op", "sky")), key=lambda r: r["seq"])
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
    if isinstance(x, dict):
        return {k: drop_think(v) for k, v in x.items() if k != "THINK"}
    if isinstance(x, list):
        return [drop_think(v) for v in x if not (isinstance(v, dict) and v.get("kind") == "THINK")]
    return x


def body_verdicts(entry):
    k = ((entry or {}).get("self") or {}).get("self5", {}).get("kinds", {})
    return {x: k.get(x, {}).get("verdict") for x in BODY_KINDS}


def strip_body(entry):
    """The declared self-reading parts of a diary entry, removed (BODY-* verdicts are kept)."""
    if entry is None:
        return None
    e = {k: v for k, v in entry.items() if k not in DIARY_DECLARED}
    s = e.get("self")
    if s and "self5" in s and "kinds" in s["self5"]:
        s = json.loads(json.dumps(s))
        for x in BODY_KINDS:
            if x in s["self5"]["kinds"]:
                s["self5"]["kinds"][x] = {"verdict": s["self5"]["kinds"][x].get("verdict")}
        e["self"] = s
    e["self"] = drop_think(e.get("self"))
    return e


def norm(r):
    """Declared format differences undone on both twins: think u and deliberation details, versions/identities."""
    r = json.loads(json.dumps(r))
    if r["kind"] == "reason" and r["rule"] == "think@2":
        r["inputs"].pop("u", None)
    if r["kind"] == "act":
        r.pop("deliberation", None)
    if r["kind"] == "diary":
        r["entry"] = strip_body(r["entry"])
    if r["kind"] == "night-reading":                  # its own reading of its body tonight: declared values
        r.pop("lengths", None); r.pop("tonight", None)
    if r["kind"] == "body-predict":                   # its path guesses from that reading: declared; memory is not
        r.pop("path", None)
    if r["kind"] in ("growth", "growth-proposal"):
        for k in ("version", "version_if_approved", "identity", "prev_identity", "amendment_sha"):
            r.pop(k, None)
        if "amendment" in r:
            r["amendment"].pop("from_version", None)
    return r


def is_think(r):
    return r["kind"] in ("reason", "act") and r.get("act_type") == "think"


def particles(blob):
    s = json.loads(blob)
    pc = np.frombuffer(base64.b64decode(s["pc"]), "<i8")
    P = np.frombuffer(base64.b64decode(s["P"]), "<f8").reshape(-1, 3)
    V = np.frombuffer(base64.b64decode(s["V"]), "<f8").reshape(-1, 3)
    return pc, P, V


def k2(t):
    r6, r7 = canon(t["records6"]), canon(t["records7"])
    a, b = [norm(r) for r in r6], [norm(r) for r in r7]
    # the first night the twins' deliberations chose differently
    acts6 = [r for r in r6 if r["kind"] == "act" and r.get("act_type") == "think"]
    acts7 = [r for r in r7 if r["kind"] == "act" and r.get("act_type") == "think"]
    div = next((i for i, (x, y) in enumerate(zip(acts6, acts7)) if x["act"] != y["act"]), None)
    first_night = None if div is None else acts7[div]["night"]
    cut = len(b) if div is None else r7.index(acts7[div])
    # (c) prefix: every record identical up to the first divergent choice (declared kinds included)
    pre = next((i for i in range(min(cut, len(a), len(b))) if a[i] != b[i]), None)
    prefix_ok = pre is None
    bad = {}
    for k in sorted({r["kind"] for r in a} | {r["kind"] for r in b}):
        if k in DECLARED_KINDS:
            continue
        sa = [r for r in a if r["kind"] == k and not is_think(r)]
        sb = [r for r in b if r["kind"] == k and not is_think(r)]
        if sa != sb:
            j = next((i for i in range(min(len(sa), len(sb))) if sa[i] != sb[i]), min(len(sa), len(sb)))
            bad[k] = {"n6": len(sa), "n7": len(sb), "first": j, "v6": sa[j] if j < len(sa) else None,
                      "v7": sb[j] if j < len(sb) else None}
    ta = [r for r in a if is_think(r)]; tb = [r for r in b if is_think(r)]
    think_ok = len(ta) == len(tb) and all(
        (x["kind"], x["act_id"]) == (y["kind"], y["act_id"]) and (x["kind"] == "act" or x["rule"] == y["rule"])
        for x, y in zip(ta, tb))
    # (d) every BODY verdict, diary by diary
    d6 = [body_verdicts(r["entry"]) for r in r6 if r["kind"] == "diary"]
    d7 = [body_verdicts(r["entry"]) for r in r7 if r["kind"] == "diary"]
    verdicts_ok = d6 == d7
    # (a) the final state
    s6, s7 = json.loads(t["blob6"]), json.loads(t["blob7"])
    same = {k: s6.get(k) == s7.get(k) for k in ("dials", "heart", "door", "mind", "today")}
    g6, g7 = s6["growth"], s7["growth"]
    same["growth"] = ([x["bindings"] for x in g6["applied"]] == [x["bindings"] for x in g7["applied"]]
                      and g6["refused"] == g7["refused"])
    me6, me7 = s6["self"], s7["self"]                 # the self: all but its body readings (verdicts kept)
    same["self"] = all(me6.get(k) == me7.get(k) for k in set(me6) | set(me7) if k not in SELF_DECLARED)
    same["self_body_verdicts"] = all(me6["xverdict"].get(x) == me7["xverdict"].get(x) for x in BODY_KINDS)
    p6, p7 = particles(t["blob6"]), particles(t["blob7"])
    same["particles_1_on"] = all(np.array_equal(x[1:], y[1:]) for x, y in zip(p6, p7))
    p0_differs = not all(np.array_equal(x[:1], y[:1]) for x, y in zip(p6, p7))
    state_ok = all(same.values())
    return {"records": [len(a), len(b)], "first_divergent_night": first_night, "first_record_difference": pre,
            "prefix_ok": prefix_ok, "undeclared_kind_diffs": bad, "think_ok": think_ok, "verdicts_ok": verdicts_ok,
            "state": same, "particle_0_differs": p0_differs,
            "passed": bool(prefix_ok and not bad and think_ok and verdicts_ok and state_ok)}


# ====================================================================== S
def s_verdicts(t):
    def last(recs):
        d = [r for r in sorted(recs, key=lambda r: r["seq"]) if r["kind"] == "diary" and r["entry"].get("self")]
        return body_verdicts(d[-1]["entry"]) if d else {}
    v6, v7 = last(t["records6"]), last(t["records7"])
    return {"v06": v6, "v07": v7, "passed": v6 == v7 == {"BODY-MEMORY": "FINE", "BODY-PATH": "GIVEN"}}


# ====================================================================== T1'' (the v0.6 judge's bars a, b, c, f)
def lived_u(t):
    recs = sorted(t["records7"], key=lambda r: r["seq"])
    reasons = {r["act_id"]: r for r in recs if r["kind"] == "reason" and r["rule"] == "think@2"}
    return [float.fromhex(reasons[r["act_id"]]["inputs"]["u"]) for r in recs
            if r["kind"] == "act" and r["act_type"] == "think"]


def t1(twins, n_uniform=200_000):
    from scipy.stats import chi2_contingency, chisquare
    lives = [lived_u(t) for t in twins]
    allu = [u for l in lives for u in l]; N = len(allu); res = {}; ok = True

    def dec(k, u):
        c, steps, _, _, _ = DC.deliberate(k, u)
        return c, steps
    for k in K_VIRTUAL:
        ch = np.array([dec(k, u)[0] for u in allu]); st = np.array([dec(k, u)[1] for u in allu])
        cnt = np.bincount(ch, minlength=k); p_u = chisquare(cnt).pvalue; se = math.sqrt((1 / k) * (1 - 1 / k) / N)
        a = bool(p_u > 0.01 and np.all(np.abs(cnt / N - 1 / k) <= 4 * se))
        T = np.zeros((k, k)); hits = []
        for l in lives:
            c = [dec(k, u)[0] for u in l]
            for x, y in zip(c[:-1], c[1:]):
                T[x, y] += 1; hits.append(x == y)
        p_lag = chi2_contingency(T + 0)[1] if k in (3, 5) else None
        b = p_lag is None or p_lag > 0.01
        hit = float(np.mean(hits)); se_c = math.sqrt((1 / k) * (1 - 1 / k) / len(hits)); c_ok = hit <= 1 / k + 3 * se_c
        rng = np.random.default_rng(7)
        ref = np.bincount(np.minimum([dec(k, float(x))[1] for x in rng.random(n_uniform)], 4), minlength=5) / n_uniform
        bins = np.bincount(np.minimum(st, 4), minlength=5); exp = ref * N; m = (bins + np.round(exp)) > 0
        p_h = chi2_contingency(np.stack([bins[m], np.round(exp[m]).astype(int)]))[1]; f_ok = p_h > 0.01
        res[k] = dict(N=N, counts=cnt.tolist(), p_uniform=p_u, T1a=a, p_lag=p_lag, T1b=b, guess_hit=hit,
                      T1c=bool(c_ok), step_bins=bins.tolist(), p_hard=p_h, T1f=bool(f_ok))
        ok &= a and b and c_ok and f_ok
    x = [np.array([2 * math.pi * u for u in l]) for l in lives]
    num = sum(np.sum(np.sin(v[1:] - v[1:].mean()) * np.sin(v[:-1] - v[:-1].mean())) for v in x)
    den = math.sqrt(sum(np.sum(np.sin(v[1:] - v[1:].mean()) ** 2) for v in x) *
                    sum(np.sum(np.sin(v[:-1] - v[:-1].mean()) ** 2) for v in x))
    rc = num / den; b_xi = abs(rc) < 3 / math.sqrt(N); ok &= b_xi
    return {"per_k": res, "xi_lag_corr": rc, "xi_bound": 3 / math.sqrt(N), "T1b_xi": bool(b_xi), "nights": N,
            "passed": bool(ok)}


def main(out, paths, k4=True, verify=False):
    from replay_v07 import replay
    twins = [json.load(open(p)) for p in paths]
    rep = {"lives": [t["seed"] for t in twins], "k2": {}, "f1": {}, "k4": {}, "s": {}}
    for t in twins:
        s = str(t["seed"])
        rep["k2"][s] = k2(t)
        rep["f1"][s] = F.check_log(t["records7"])
        w = replay(t["start7"], t["records7"], verify=verify) if k4 else {"ok": None}
        rep["k4"][s] = {k: v for k, v in w.items() if k not in ("published", "replayed")}
        rep["s"][s] = s_verdicts(t)
        print(s, "K2", rep["k2"][s]["passed"], "| F1", rep["f1"][s], "| K4", w["ok"], "| S", rep["s"][s]["passed"],
              flush=True)
    rep["t1"] = t1(twins)
    rep["static"] = {"rule_purity_violations": F.rule_purity(), "lcl_import_violations": F.lcl_imports()}
    json.dump(rep, open(out, "w"), indent=1, default=float)
    print(json.dumps({"K2": all(v["passed"] for v in rep["k2"].values()), "T1''": rep["t1"]["passed"],
                      "S": all(v["passed"] for v in rep["s"].values()),
                      "K4": all(v["ok"] for v in rep["k4"].values()) if k4 else "not run"}))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0], args[1:], k4="--no-k4" not in sys.argv, verify="--verify-beacons" in sys.argv)
