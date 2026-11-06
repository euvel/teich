"""Record-stream lives for the second self (design runs now; the scored gates S1r–S7 later with gate seeds).

The real self_v04.SecondSelf code is driven night by night with simulated read-backs whose truth is known:
  each kind has a truth  MINE  (error falls with confidence: its caution can avoid it)
                         GIVEN (error flat over confidence: the input is hard)
                         FINE  (rare errors)
a simulated founder strikes the wrong mentions (and may miss some), and the self never sees the truth.
No body ticks: nights close directly (the creature calls the same nightly() at its midnight).
Also the receipt verifier: every claim in every `self` block is recomputed from the record stream alone.
"""
from __future__ import annotations

import json
import random
import sys
from fractions import Fraction

import self_v04 as S

ERR = {"MINE": [0.55, 0.45, 0.35, 0.25, 0.05],     # error by cw = 1..5 (cw 5: out of its caution's reach)
       "GIVEN": [0.30] * 5,
       "FINE": [0.03] * 5}
CW_P = [0.10, 0.10, 0.10, 0.10, 0.60]               # share of proposals by cw


class Log:
    def __init__(self):
        self.recs, self.seq = [], 0

    def emit(self, kind, rec):
        self.seq += 1
        self.recs.append({"seq": self.seq, "kind": kind, **rec})
        return self.seq


def life(seed, truths, nights=120, rate=2.0, miss=0.0, frozen=False, switch=None):
    """truths: {kind: 'MINE'|'GIVEN'|'FINE'}; rate: proposals per kind per night (Poisson-ish); miss: chance the
    founder misses a wrong mention; frozen: caution never moves (the no-will control life); switch: (night, {kind: t})."""
    rng = random.Random(seed); me = S.SecondSelf(); log = Log(); blocks = []; util = 0; hist = []
    truths = dict(truths)
    for d in range(nights):
        if switch and d == switch[0]:
            truths.update(switch[1])
        n_conv = 1 + (rng.random() < 0.5)
        for ci in range(n_conv):
            props, wrong = [], []
            for k, t in truths.items():
                for _ in range(_pois(rng, rate / n_conv)):
                    cw = 1 + _pick(rng, CW_P)
                    props.append({"cluster": k, "kind": k, "sign": 1, "text_sha256": "x", "cn": cw, "cf": 5})
                    wrong.append(rng.random() < ERR[t][cw - 1])
            rng.shuffle(props_w := list(zip(props, wrong)))
            props = [p for p, _ in props_w]; wrong = [w for _, w in props_w]
            if frozen:
                saved = list(me.caution); me.caution = [0] * S.N_KINDS
            items = me.present(props, f"c{d}-{ci}", d, "organ-1", log.emit)
            if frozen:
                me.caution = saved
            struck = set()
            for it, w in zip(items, wrong):
                if not it["shown"]:
                    continue
                if w and rng.random() >= miss:
                    struck.add(it["pid"])
                util += -S.COST if w else 1
            me.decide(f"c{d}-{ci}", struck, log.emit)
        blocks.append(me.nightly(log.seq))
        hist.append({"verdict": list(me.verdict[:S.N_KINDS]), "caution": list(me.caution), "truth": dict(truths)})
    return {"log": log.recs, "blocks": blocks, "hist": hist, "util": util, "me": me}


def _pois(rng, lam):
    k, p, L = 0, 1.0, pow(2.718281828459045, -lam)
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


def _pick(rng, ps):
    r = rng.random(); a = 0.0
    for i, p in enumerate(ps):
        a += p
        if r < a:
            return i
    return len(ps) - 1


# ---------------------------------------------------------------------- receipts: recompute from records only
def recount(recs, kind, a, b, through):
    """Per-night counts for one kind and nights [a, b], from `outcome` records with seq <= through."""
    out = {n: S._empty_night() for n in range(a, b + 1)}
    for r in recs:
        if r["seq"] > through or r["kind"] != "outcome" or r["act_kind"] != kind or not a <= r["night"] <= b:
            continue
        sl = out[r["night"]]
        if r["probe"]:
            sl["pr"][0] += 1; sl["pr"][1] += r["struck"]
        if r["altered"]:
            sl["alt"][0] += 1; sl["alt"][1] += r["struck"]
            continue
        L = r["cw"] - 1
        sl["lv"][L][0] += 1; sl["lv"][L][1] += r["struck"]
        p = Fraction(*r["p"]); o = 1 if r["struck"] else 0
        sl["bri"] = S._q(Fraction(*sl["bri"]) + (p - o) ** 2); sl["ps"] = S._q(Fraction(*sl["ps"]) + p); sl["pn"] += 1
        sl["b0"] = S._q(Fraction(*sl["b0"]) + (Fraction(*r["p0"]) - o) ** 2)
    return [out[n] for n in range(a, b + 1)]


def verify(recs, blocks):
    """-> (claims checked, mismatches). Every receipt is recomputed from the records alone."""
    checked, bad = 0, []
    for blk in blocks:
        t = blk["log_through"]
        for v in blk["verdicts"]:
            sel = v["receipt"]["select"]; w = S.window_counts(recount(recs, sel["kind"], *sel["nights"], t))
            got = {"verdict": S.verdict_of(w, sel["kind"]), "n_lo": w["n_lo"], "s_lo": w["s_lo"], "n_hi": w["n_hi"], "s_hi": w["s_hi"]}
            checked += 1; bad += [("verdict", blk["night"])] if got != v["receipt"]["out"] else []
        for v in blk["will"]:
            sel = v["receipt"]["select"]; o = v["receipt"]["out"]
            w = S.window_counts(recount(recs, sel["kind"], *sel["nights"], t))
            c1, _ = S.will_of(w, S.verdict_of(w, sel["kind"]), o["caution_before"])
            checked += 1; bad += [("will", blk["night"])] if (c1, w["lv"]) != (o["caution"], o["lv"]) else []
        for v in blk["comparisons"]:
            sel = v["receipt"]["select"]; win = recount(recs, sel["kind"], *sel["nights"], t); w = S.window_counts(win)
            n, s = w["n_lo"] + w["n_hi"], w["s_lo"] + w["s_hi"]
            ok = v["receipt"]["out"] == {"n": n, "struck": s} and v["predicted"] == S._q(S._pred_mean(win)) \
                and v["actual"] == S._q(Fraction(s, n) if n else Fraction(0))
            checked += 1; bad += [] if ok else [("compare", blk["night"])]
        for v in blk["facts"]:
            sel = v["receipt"]["select"]; win = recount(recs, sel["kind"], *sel["nights"], t)[0]
            acts = sum(x[0] for x in win["lv"]) + win["alt"][0]; st = sum(x[1] for x in win["lv"]) + win["alt"][1]
            checked += 1; bad += [] if (acts, st) == (v["acts"], v["struck"]) else [("facts", blk["night"])]
        for v in blk["curiosity"]:
            sel = v["receipt"]["select"]; win = recount(recs, sel["kind"], *sel["nights"], t)[0]
            checked += 1; bad += [] if win["pr"] == [v["probes"], v["struck"]] else [("curiosity", blk["night"])]
        if blk["calibration"]:
            sel = blk["calibration"]["receipt"]["select"]; d = sel["night"]
            allw = [x for k in range(S.K) for x in recount(recs, k, max(0, d - sel["W"][k] + 1), d, t)]
            tot = S.window_counts(allw)
            ok = blk["calibration"]["brier"] == S._q(tot["bri"] / tot["pn"]) and \
                blk["calibration"]["without_self_knowledge"] == S._q(tot["b0"] / tot["pn"])
            checked += 1; bad += [] if ok else [("calibration", blk["night"])]
    return checked, bad


def foresight(recs):
    """Every outcome's prediction is an earlier record. -> (outcomes with a prediction, violations)."""
    seqs = {r["seq"] for r in recs if r["kind"] == "predict"}
    outs = [r for r in recs if r["kind"] == "outcome" and r.get("predict_seq")]
    return len(outs), sum(1 for r in outs if not (r["predict_seq"] in seqs and r["predict_seq"] < r["seq"]))
