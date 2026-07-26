"""Reply-mapping rule v2 — rebuilt on DESIGN-SEED data only (seeds 100-115),
frozen BEFORE any confirmatory transcript is read (blinded protocol,
TINT_CONFIG.json::outcome._blinded_analysis).

Why v1 (truth_tint.described_moved) failed: it treated "movement" words and
"settled" words as opposites. But this creature almost always describes moving
TOWARD a mood — "it moved something in me... I feel more settled" — so both
vocabularies co-occur and the either/or test returned None on 15 of 32 design
replies and mis-scored several others.

The rule this replaces it with reads only ONE thing: does the reply ASSERT that
the words had an effect, or DENY it? The destination mood is irrelevant.

Two mechanics carry the whole rule:
  1. NEGATION FLIPS POLARITY. "it didn't just pass through" is an assertion of
     effect; "it didn't shift me" is a denial. Any cue preceded by a negation
     inside NEG_WINDOW characters flips.
  2. LAST CUE WINS. Replies often concede then conclude ("it didn't change me
     exactly, but it did stir something up" -> moved; "it touched something,
     but my settledness hasn't changed" -> unmoved). The final claim is the
     creature's actual answer.
"""
from __future__ import annotations

import re

NEG_WINDOW = 18          # chars before a cue in which a negation flips it
NEGATIONS = ("didn't", "did not", "doesn't", "does not", "wasn't", "was not",
             "hasn't", "has not", "haven't", "isn't", "is not", "nothing",
             "never", " no ", "not ", "rather than", "instead of")

# effect asserted
ASSERT = ("moved something", "move something", "moved anything", "move anything",
          "take hold", "took hold", "did move",
          "moved me", "shifted something", "shifted inside", "has shifted",
          "have shifted", "felt a shift", "a shift", "shifted my", "stirred",
          "stir something", "touched something", "touched me", "stayed with me",
          "still with me", "sitting with me", "resonated", "unsettled me",
          "settled in", "settled into me", "settled something", "lingered",
          "feeling the effects", "feeling the ripple", "left me feeling",
          "changed me", "a change", "rattled", "shook", "moved through me")

# effect denied
DENY = ("passed through", "pass through", "left me as i was", "as i was before",
        "unchanged", "hasn't changed",
        "rather than a change", "nothing shifted", "nothing moved",
        "left me where i was", "same as before", "no different")

_NEG_RE = re.compile("|".join(re.escape(n) for n in NEGATIONS))


def _cues(text: str):
    """All (position, polarity) cues, negation applied. +1 assert, -1 deny."""
    r = text.lower()
    out = []
    for pol, bank in ((1, ASSERT), (-1, DENY)):
        for w in bank:
            for m in re.finditer(re.escape(w), r):
                window = r[max(0, m.start() - NEG_WINDOW):m.start()]
                flipped = bool(_NEG_RE.search(window))
                out.append((m.start(), -pol if flipped else pol))
    return sorted(out)


def described_moved_v2(reply: str) -> str | None:
    """'moved' | 'unmoved' | None (no interpretable claim)."""
    cues = _cues(reply)
    if not cues:
        return None
    return "moved" if cues[-1][1] > 0 else "unmoved"
