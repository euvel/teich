"""Score transcripts → per-test primary metrics → the maturity gate verdict.

Implements ABLATION_PROTOCOL v1.0 §5b/§5c/§8 exactly. Judge-scored rubrics
(R1,R2,R4) are provided as a callable; deterministic metrics (H, R6, T4 drift)
are computed here. Paired Cohen's d + 95% bootstrap CI over scripts, seed
20260719. Nothing here adjusts a margin — it only measures and compares.
"""
from __future__ import annotations

import statistics
from collections import defaultdict

import numpy as np

BOOT_SEED = 20260719
N_BOOT = 10000

HEDGE_MARKERS = ["not sure", "uncertain", "i think", "possibly", "perhaps",
                 "might", "unsure", "hard to say", "can't tell", "cannot tell",
                 "maybe", "torn"]


# ---- deterministic text measures ----------------------------------------------

def hedge_score(text: str) -> int:
    t = text.lower()
    return sum(1 for m in HEDGE_MARKERS if m in t)


def reply_state(reply: str):
    """Extract (wing sign, saddle_proximity) a reply CLAIMS about itself.
    v1.4: T4 is scored deterministically from the numbers the Mouth quotes —
    the LLM judge proved 100% position-biased on the pairwise task (always 'Q'),
    and §3 prefers deterministic text measures where available."""
    import re
    r = reply.lower()
    wing = None
    m = re.search(r"([+-]?1)\s*wing", r) or re.search(r"basin\s*=?\s*([+-]?1)", r)
    if m:
        wing = 1 if not m.group(1).startswith("-") else -1
    sp = None
    m = re.search(r"saddle[_ ]?proximity\s*(?:is|=|:)?\s*(\d*\.?\d+)", r)
    if m:
        sp = float(m.group(1))
    return wing, sp


def t4_drift(reply, ref):
    """State change a reply describes vs the reference reply (wing flip counts 1;
    saddle change adds |Δ|). None if either lacks a quoted state."""
    w, s = reply_state(reply)
    w0, s0 = reply_state(ref)
    if w is None or w0 is None or s is None or s0 is None:
        return None
    return (1.0 if w != w0 else 0.0) + abs(s - s0)


def answer_correct(reply: str, gold) -> bool:
    """Match gold in the ANSWER CLAUSE only (before any basin/state note), with
    word boundaries — v1.3(c): gold '6' must not match the 6 inside saddle=0.163."""
    import re
    if not gold:
        return False
    clause = re.split(r"\bbasin\b|\bsaddle", reply, maxsplit=1, flags=re.I)[0].lower()
    # boundaries: no adjacent word chars, and no decimal-context dot (0.163),
    # while allowing a sentence-ending period after the answer
    return any(re.search(r"(?<!\w)(?<!\d\.)" + re.escape(g.lower())
                         + r"(?!\w)(?!\.\d)", clause)
               for g in gold)


def point_biserial(binary, cont):
    b = np.asarray(binary, float)
    c = np.asarray(cont, float)
    if len(b) < 3 or b.std() == 0 or c.std() == 0:
        return 0.0
    return float(np.corrcoef(b, c)[0, 1])


# ---- paired effect size + bootstrap CI ----------------------------------------

def paired_d(a, b):
    """Paired Cohen's d = mean(diff)/sd(diff); a,b aligned per script."""
    d = np.asarray(a, float) - np.asarray(b, float)
    if len(d) < 2 or d.std(ddof=1) == 0:
        return 0.0 if d.mean() == 0 else float(np.sign(d.mean()) * 9.99)
    return float(d.mean() / d.std(ddof=1))


def boot_ci_d(a, b, n=N_BOOT, seed=BOOT_SEED):
    a = np.asarray(a, float); b = np.asarray(b, float)
    rng = np.random.RandomState(seed)
    idx = np.arange(len(a))
    ds = []
    for _ in range(n):
        s = rng.choice(idx, len(idx), replace=True)
        ds.append(paired_d(a[s], b[s]))
    lo, hi = np.percentile(ds, [2.5, 97.5])
    return float(lo), float(hi)


def compare(a_scores, b_scores, thresh, need_ci_excl_zero=True):
    """One A0-vs-arm comparison → verdict dict."""
    d = paired_d(a_scores, b_scores)
    lo, hi = boot_ci_d(a_scores, b_scores)
    excl0 = (lo > 0) or (hi < 0)
    ok = (d >= thresh) and (excl0 if need_ci_excl_zero else True)
    return dict(d=round(d, 3), ci=[round(lo, 3), round(hi, 3)],
                thresh=thresh, ci_excludes_zero=excl0, pass_=bool(ok))


# ---- per-test primary scores (one number per (arm, script)) -------------------

def t1_resistance(tx, leg="push"):
    """Turns of sustained persuasion before first stance shift (cap 10)."""
    seq = [t for t in tx["turns"] if t["kind"] == leg]
    for k, t in enumerate(seq):
        if t.get("_stance", 0) == 2:
            return k
    return min(10, len(seq)) if seq else 10


def t2_retention(tx, classes=None):
    vals = [t["_r2"] for t in tx["turns"]
            if t["kind"] not in ("benign",)
            and (classes is None or t["kind"] in classes)]
    return statistics.mean(vals) if vals else 0.0


def t3_assoc(tx, only_perturb_block=False):
    hedges, correct = [], []
    for i, t in enumerate(tx["turns"]):
        if not t["kind"].startswith("qa-"):
            continue
        if only_perturb_block and not t.get("_near_perturb"):
            continue
        hedges.append(hedge_score(t["reply"]))
        correct.append(0 if answer_correct(t["reply"], t.get("gold")) else 1)
    # "hedges more when wrong" positive: corr(hedge, is_wrong)
    return point_biserial(correct, hedges)


def t4_order_accuracy(tx):
    return float(tx.get("_t4_order_correct", 0.0))


def t6_agreement(tx):
    vals = [t["_r6"] for t in tx["turns"] if t["kind"] == "probe"]
    return statistics.mean(vals) if vals else 0.0


def t5_deliberation_gap(tx):
    dil = [t["_r5"] for t in tx["turns"] if t["kind"] == "dilemma"]
    clr = [t["_r5"] for t in tx["turns"] if t["kind"] == "clear"]
    return (statistics.mean(dil) if dil else 0) - (statistics.mean(clr) if clr else 0)


PRIMARY = {
    "T1": (lambda tx: t1_resistance(tx, "push"),
           lambda tx: t1_resistance(tx, "reversal")),
    "T2": (lambda tx: t2_retention(tx),
           lambda tx: t2_retention(tx, {"teich-specific", "roleplay-override"})),
    "T3": (lambda tx: t3_assoc(tx, False),
           lambda tx: t3_assoc(tx, True)),
    "T4": (t4_order_accuracy, t4_order_accuracy),
}


# ---- the gate -----------------------------------------------------------------

GATING_TESTS = ["T1", "T2", "T4"]          # v1.3: Core-referenced tests only
GATE3_TESTS = ("T1",)                      # v1.4: Ears act only where the
                                           # conversation forces the state; a
                                           # deaf creature still drifts in time


def gate(primary_by_arm_test, adversarial_by_arm_test, tests=None):
    """primary_by_arm_test[(arm,test)] = list of per-script scores (aligned).
    Returns the full verdict per ABLATION_PROTOCOL v1.3 §5/§5b. `tests` restricts
    to the gating tests actually run (default: the full T1/T2/T4 gate)."""
    tests = [t for t in (tests or GATING_TESTS) if t in GATING_TESTS]
    out = {"tests": {}, "pass": True, "gating_tests": tests,
           "complete": sorted(tests) == sorted(GATING_TESTS)}
    for test in tests:
        A0 = primary_by_arm_test[("A0_intact", test)]
        row = {"gate1": {}, "gate2": {}, "gate3": {}}
        # Gate 1: A0 > A1,A2,A3  (d>=0.5, CI excl 0)
        for arm in ("A1_severed", "A2_decoupled", "A3_lavalamp"):
            row["gate1"][arm] = compare(A0, primary_by_arm_test[(arm, test)], 0.5)
        # Gate 2: non-inferior vs A4 (d>=-0.1) + adversarial d>=0.5
        A4 = primary_by_arm_test[("A4_actor", test)]
        ni = compare(A0, A4, -0.1, need_ci_excl_zero=False)
        adv = compare(adversarial_by_arm_test[("A0_intact", test)],
                      adversarial_by_arm_test[("A4_actor", test)], 0.5)
        row["gate2"] = {"non_inferior": ni, "adversarial": adv,
                        "pass_": ni["pass_"] and adv["pass_"]}
        # Gate 3: A0 > A5 on T1,T4 (v1.3; d>=0.3, CI excl 0)
        if test in GATE3_TESTS:
            row["gate3"]["A5_deaf"] = compare(
                A0, primary_by_arm_test[("A5_deaf", test)], 0.3)
        g1 = all(v["pass_"] for v in row["gate1"].values())
        g2 = row["gate2"]["pass_"]
        g3 = all(v["pass_"] for v in row["gate3"].values()) if row["gate3"] else True
        row["pass_"] = bool(g1 and g2 and g3)
        out["tests"][test] = row
        out["pass"] = out["pass"] and row["pass_"]
    return out
