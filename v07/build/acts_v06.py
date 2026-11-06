"""Teich v0.6 — the act loop's rules: v0.5's rules unchanged, plus think@2 (spec V06 §2). Pure functions: each rule sees
ONLY its logged inputs. think@2 = think@1 except that an EXACT tie (several regions with the least life count) is
broken by its deliberation (delib_cert, certified arithmetic) from the logged read-out u, not by the lowest index.

Allowed imports here (law L-CL): fractions, v0.4's self constants/functions, v0.5's rules, and delib_cert (pure
arithmetic on frozen constants: no body, no randomness, no clock)."""
import delib_cert as DC
from acts_v05 import ask_1, ask_2, caution_1, grow_1, probe_1, think_1


def think_2(inp):
    """Its one chosen thought a day: the region (or itself) it has thought about least in its life. If several are tied,
    its deliberation decides among them (in region order), starting from u, the read-out of its body's particle 0 at
    that midnight (logged as float.hex). Undecided deliberation (measure zero) falls back to the lowest region.
    inputs: life_counts (9 integers), u (hex float in [0, 1)).   act: the region index."""
    lc = inp["life_counts"]
    tied = [r for r, n in enumerate(lc) if n == min(lc)]
    if len(tied) == 1:
        return tied[0]
    return tied[DC.deliberate(len(tied), float.fromhex(inp["u"]))[0]]


RULES = {"probe@1": probe_1, "caution@1": caution_1, "ask@1": ask_1, "think@1": think_1, "ask@2": ask_2,
         "grow@1": grow_1, "think@2": think_2}


def choose(state, act_type, rule, inputs, emit, **extra):
    """Write the reason, compute the act from the reason alone, write the act. -> (act_id, act)."""
    aid = state.next_act
    state.next_act += 1
    emit("reason", {"act_id": aid, "act_type": act_type, "rule": rule, "inputs": inputs})
    act = RULES[rule](inputs)
    emit("act", {"act_id": aid, "act_type": act_type, "act": act, **extra})
    return aid, act
