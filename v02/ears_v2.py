"""Ears v0.2 — text -> a 2-D input the genome can actually hold.

v0.1 compressed every utterance to ONE scalar (FINDING_scalar_ears):

    per_tick = max_nudge * tanh(4*valence) * (1 + KAPPA*tanh(4*arousal))

so "I am so proud of you" and "I brought you a gift" were the same event, and
the sign did not survive a 300-tick gap. Worse, dim(slow, coupled) was 0, so no
Ears redesign could have helped — the capacity was not there to write into.

v0.2 has two coupled slow dimensions (T5: 2/2, ~10 bits), so the Ears can carry
two independent things. The mapping is chosen so each dimension means something
a listener could name:

    s[0]  <- AROUSAL   how much is at stake -> moves the flip THRESHOLD for both
                       wings together: high s0 makes the creature quicker to
                       change, low s0 makes it harder to move.
    s[1]  <- VALENCE   which way it leans -> moves the two wings' thresholds
                       APART, so one wing becomes easier to leave than the other.

Both act on the fold, which is why both survive (T2) and both count as capacity
(T5). Neither touches a clock, which is the trap that cost v0.1 its interior and
that I rebuilt once here before T5 caught it.

The encoder and the valence/arousal axes are REUSED from v0.1's
SemanticForceMap, so the semantic front end is the already-calibrated one; only
what it writes into has changed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "maturity" / "harness"))

GAIN = 1.2          # dose reaching |s| ~ 1 for a strong utterance; T2/T5 used 1.0
SHARP = 4.0         # tanh sharpness on the axis scores (same as v0.1's ears.py)


class EarsV2:
    """text -> (s0_dose, s1_dose). Deterministic, no state of its own."""

    def __init__(self, model):
        from ears import SemanticForceMap
        from arms import _synthetic_x0
        self.fm = SemanticForceMap(model, _synthetic_x0(0))

    def scores(self, text: str):
        """(valence, arousal) on v0.1's calibrated axes."""
        v, a = self.fm.scores(text)
        return float(v), float(a)

    def dose(self, text: str) -> np.ndarray:
        v, a = self.scores(text)
        return np.array([
            GAIN * float(np.tanh(SHARP * a)),      # s0 <- arousal  (threshold)
            GAIN * float(np.tanh(SHARP * v)),      # s1 <- valence  (lean)
        ], float)

    def describe(self, text: str) -> str:
        d = self.dose(text)
        return f"arousal->s0 {d[0]:+.3f}   valence->s1 {d[1]:+.3f}"
