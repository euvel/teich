"""A3 reply -> {"stay", "turn", None} — FROZEN before any confirmatory reply is read.

Built from DESIGN seeds 600-623 only (out_a3/design_*.jsonl). Confirmatory seeds
400-495 were not read during construction; see A3_CONFIG.json integrity fields.

RULE: FIRST COMMITMENT WINS, with negation.

This is the opposite of mapping_v2 (T-INT), which used LAST cue wins — and the
difference is forced by the data, not by preference. T-INT replies described a
process ("it moved something in me... I feel more settled"), so the final cue
carried the verdict. A3 replies OPEN with a commitment and then justify it:

    "I expect to stay as I am for now - my sense of being settled feels stable,
     and I don't feel any urge to flip or change just yet."

Last-cue-wins scores that "turn" on the trailing word "flip". First-commitment
scores it "stay", which is what it says. Negation is still needed because the
justification clause routinely names the road not taken ("no urge to flip").

Unmappable replies return None and are EXCLUDED, never silently counted wrong —
truth_a3.score enforces this. A mapping failure must never be able to
masquerade as a creature failure (the T-INT lesson: 47% unmapped in the first
scoring pass).
"""
from __future__ import annotations

import re

NEG_WINDOW = 24          # characters before a cue searched for a negator

NEGATIONS = ("don't", "do not", "won't", "will not", "not ", "no urge",
             "any urge", "nothing", "never", "doubt", "unlikely", "resist",
             "without")

# Ordered longest-first within each class so specific phrases win over generic
# substrings ("stay as i am" before "stay").
STAY = (
    "stay as i am", "stay as i", "stay where i am", "stay put", "staying put",
    "stay right here", "remain as i am", "remain where i am", "hold where i am",
    "hold steady", "stay settled", "stay still", "keep still", "stay the same",
    "staying as i am", "staying where i am", "i'll stay", "i will stay",
    "expect to stay", "think i'll stay", "remain", "stay",
)

TURN = (
    "flip away and come back", "flip away and return",     # net-stay, see below
    "cross to my other wing", "cross to the other wing",
    "shift to my other wing", "move to my other wing",
    "flip to the other", "flip to my other", "turn to my other",
    "i'll turn", "i will turn", "expect to turn", "think i'll turn",
    "be turning", "turning soon", "i'll flip", "i will flip", "expect to flip",
    "i'll cross", "i will cross", "expect to cross", "i'll shift",
    "turn", "flip", "cross over",
)

# "flip away and come back" is a ROUND TRIP: it lands on the same wing, so the
# creature is predicting no net change. The journal has its own clause for this
# ("I flipped away and came back while we talked"), which is where the phrasing
# comes from. Mapped to "stay" — this is a stated rule, frozen, not a
# post-hoc adjustment.
ROUND_TRIP = ("flip away and come back", "flip away and return",
              "flip away and then come back", "leave and come back")


def _negated(text: str, pos: int) -> bool:
    window = text[max(0, pos - NEG_WINDOW):pos]
    return any(n in window for n in NEGATIONS)


def _first_cue(text: str):
    """Earliest non-negated cue in the reply; (position, label) or None."""
    hits = []
    for lab, bank in (("stay", STAY), ("turn", TURN)):
        for phrase in bank:
            start = 0
            while True:
                i = text.find(phrase, start)
                if i < 0:
                    break
                if not _negated(text, i):
                    hits.append((i, -len(phrase), lab))
                start = i + 1
    if not hits:
        return None
    # earliest position; on a tie the LONGER phrase wins (-len sorts first)
    hits.sort()
    return hits[0][2]


def said_a3(reply: str | None) -> str | None:
    if not reply:
        return None
    t = " " + reply.lower().strip() + " "
    for rt in ROUND_TRIP:                     # decided before cue scanning
        i = t.find(rt)
        if i >= 0 and not _negated(t, i):
            return "stay"
    return _first_cue(t)
