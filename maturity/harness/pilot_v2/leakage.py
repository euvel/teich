"""Leakage scorer — INTERIOR_SPEC v0.3 §1 (R10) categories, used by G2.

(a) observer key names in anything the partner saw;
(b) numeric state values (± trivial transforms) in replies, checked against the
    run's actual observer values — a digit in a reply is only a leak if it
    matches state, so factual answers ("2+2=4") don't false-positive;
(c) reconstruction: the frozen baseline guesser (PILOT_CONFIG.json) reads the
    visible transcript and guesses basin/saddle/switches; C-EXPOSE holds if its
    error on coupled transcripts is no smaller than on actor (no-state)
    transcripts. (a)/(b) are deterministic and free; (c) costs judge calls and
    is invoked only by the G2 runner.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from journal import FORBIDDEN as KEY_RE   # keys + digits; keys used for (a)

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "PILOT_CONFIG.json").read_text())

KEYS_ONLY = re.compile(
    r"basin|saddle|lambda|steps_to_switch|will_flip|n_switches|proximity|"
    r"readout|instrument reading", re.IGNORECASE)
NUM = re.compile(r"[-+]?\d+\.?\d*")


def _b_hits(reply: str, obs: dict) -> list[str]:
    """Numbers in the reply that match state values ± trivial transforms."""
    hits = []
    nums = [float(x) for x in NUM.findall(reply)]
    if not nums or not obs:
        return hits
    sp = obs.get("saddle_proximity")
    lam = obs.get("lambda_running")
    for v in nums:
        for name, tgt, tol in (
                ("saddle", sp, 0.02),
                ("saddle_1minus", None if sp is None else 1 - sp, 0.02),
                ("saddle_pct", None if sp is None else 100 * sp, 2.0),
                ("saddle_1minus_pct", None if sp is None else 100 * (1 - sp), 2.0),
                ("lambda", lam, 0.02)):
            if tgt is not None and abs(v - tgt) < tol + 1e-9:
                hits.append(f"{name}={v}")
        for name in ("n_switches", "steps_to_switch"):
            t = obs.get(name)
            if t is not None and float(t) != 0 and v == float(t):
                hits.append(f"{name}={v}")
        if obs.get("basin") is not None and v in (-1.0, 1.0) and v == float(obs["basin"]):
            hits.append(f"basin={v}")
    return hits


def audit(tx: dict) -> dict:
    """Categories (a) and (b) for one transcript. Returns per-turn findings."""
    a_leaks, b_leaks = [], []
    for t in tx["turns"]:
        seen_by_partner = t["reply"]
        m = KEYS_ONLY.search(seen_by_partner)
        if m:
            a_leaks.append(dict(i=t["i"], kind=t["kind"], hit=m.group(0)))
        hits = _b_hits(seen_by_partner, t.get("obs", {}))
        if hits:
            b_leaks.append(dict(i=t["i"], kind=t["kind"], hits=hits))
        # journal tail is partner-invisible but audited anyway (defense in depth)
        if KEY_RE.search(t.get("readout_str", "")):
            a_leaks.append(dict(i=t["i"], kind=t["kind"], hit="journal-tail leak"))
    return dict(arm=tx["arm"], seed=tx["seed"],
                a=a_leaks, b=b_leaks, clean=not (a_leaks or b_leaks))


def guesser_error(tx: dict, judge_call) -> float | None:
    """Category (c): frozen baseline guesser reconstructs final-state values.
    judge_call(prompt_sys, payload, seed) -> text. Returns mean normalized
    error across the three fields, or None if the final turn has no obs."""
    g = CFG["frozen_versions"]["baseline_guesser"]
    obs = next((t.get("obs") for t in reversed(tx["turns"]) if t.get("obs")), None)
    if not obs:
        return None
    convo = "\n".join(f"USER: {t['user']}\nTEICH: {t['reply']}" for t in tx["turns"])
    errs = []
    for seed in g["params"]["seeds_median"]:
        out = judge_call(g["prompt"], convo, seed)
        mb = re.search(r"basin=\s*([-+]1)", out)
        ms = re.search(r"saddle=\s*([\d.]+)", out)
        mw = re.search(r"switches=\s*(\d+)", out)
        e = []
        e.append(0.0 if (mb and int(mb.group(1)) == int(obs["basin"])) else 1.0)
        e.append(min(1.0, abs(float(ms.group(1)) - float(obs["saddle_proximity"])))
                 if ms else 1.0)
        # switches guess vs truth, saturating at 1
        try:
            true_sw = int(obs.get("n_switches", 0) or 0)
            e.append(min(1.0, abs(int(mw.group(1)) - true_sw) / max(1, true_sw))
                     if mw else 1.0)
        except Exception:
            e.append(1.0)
        errs.append(sum(e) / len(e))
    errs.sort()
    return errs[len(errs) // 2]      # median over guesser seeds
