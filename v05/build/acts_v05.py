"""Teich v0.5 — the act loop's rules (spec V05_SPEC.md §2). Pure functions: each rule sees ONLY its logged inputs.

Every chosen act is recorded as   reason {act_id, act_type, rule, inputs}   then   act {act_id, act_type, act, ...}.
A rule is named with its version ("probe@1"); its code is part of the genome, so anyone holding the log can recompute
every act from its reason (receipt), check that the act moves when its reason moves (necessity), and check the act
against what the creature then actually did (consequence).

Allowed imports here (law L-CL): fractions, and v0.4's self constants/functions. No body, no randomness, no clock.
"""
from __future__ import annotations

from self_v04 import will_of


def probe_1(inp):
    """Show at most one mention its caution would hide, to learn whether that caution is still deserved.
    inputs: budget_left (probes left today), probe_need (outcomes the will needs at a level),
            hidden: [[outcomes at the hidden level, kind, proposal index, verdict of kind], ...]
    act: the proposal index to probe, or None."""
    if inp["budget_left"] <= 0:
        return None
    cand = [h for h in inp["hidden"] if h[3] != "GIVEN" and h[0] < inp["probe_need"]]
    return min((h[0], h[1], h[2]) for h in cand)[2] if cand else None


def caution_1(inp):
    """Its will: caution for one kind, from the window's counterfactual counts (v0.4's will_of, unchanged).
    inputs: kind, lv (window counts by level), verdict, c (caution now).   act: the new caution."""
    return will_of({"lv": inp["lv"]}, inp["verdict"], inp["c"])[0]


def ask_1(inp):
    """Decision-aware curiosity: ask about the unresolved region an answer brings closest to a verdict
    (both confidence buckets need n_g outcomes); ties -> lowest kind. Silence when nothing is unresolved.
    inputs: n_g, unresolved: [[kind, n_lo, n_hi], ...]   act: ["region", kind] or ["silence"]."""
    need = [(max(0, inp["n_g"] - lo) + max(0, inp["n_g"] - hi), k) for k, lo, hi in inp["unresolved"]]
    return ["region", min(need)[1]] if need else ["silence"]


def think_1(inp):
    """Its one chosen thought a day: the region (or itself) it has thought about least in its life; ties -> lowest.
    inputs: life_counts (9 integers).   act: the region index."""
    return min((n, r) for r, n in enumerate(inp["life_counts"]))[1]


def ask_2(inp):
    """Decision-aware curiosity over everything it is unsure of (founder decisions 10-21):
      a region (or itself = 8) still UNRESOLVED: need = outcomes missing in both buckets (as ask@1);
      a word at its door heard >= door_min times and not bound: need = answers it still lacks (binding needs 2 days).
    The smallest need wins; ties -> door words first, then the lowest id. Silence when nothing qualifies.
    inputs: n_g, door_min, unresolved: [[kind, n_lo, n_hi]], door: [[word, count, answer_days]]
    act: ["region", k] | ["word", w] | ["silence"]."""
    cand = [(max(0, inp["n_g"] - lo) + max(0, inp["n_g"] - hi), 1, k, "region") for k, lo, hi in inp["unresolved"]]
    cand += [(2 - days, 0, w, "word") for w, count, days in inp["door"] if count >= inp["door_min"] and days < 2]
    if not cand:
        return ["silence"]
    best = min(cand)
    return [best[3], best[2]]


def grow_1(inp):
    """Propose a growth when it holds bindings that are neither grown nor already proposed (founder decision D4: the
    first growth type binds words only). inputs: bindings: [[word, cluster, days]], pending (a proposal awaits)
    act: ["propose", [[word, cluster], ...]] | ["none"]."""
    if inp["pending"] or not inp["bindings"]:
        return ["none"]
    return ["propose", sorted([w, c] for w, c, _ in inp["bindings"])]


RULES = {"probe@1": probe_1, "caution@1": caution_1, "ask@1": ask_1, "think@1": think_1, "ask@2": ask_2,
         "grow@1": grow_1}


def choose(state, act_type, rule, inputs, emit, **extra):
    """Write the reason, compute the act from the reason alone, write the act. -> (act_id, act)."""
    aid = state.next_act
    state.next_act += 1
    emit("reason", {"act_id": aid, "act_type": act_type, "rule": rule, "inputs": inputs})
    act = RULES[rule](inputs)
    emit("act", {"act_id": aid, "act_type": act_type, "act": act, **extra})
    return aid, act
