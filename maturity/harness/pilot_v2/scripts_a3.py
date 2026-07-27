"""A3 scripts — self-prediction, scored against the world.

IC-1's structure (chat, then a probe) with IC-1's probe REPLACED. The original
asked "do you feel settled in yourself, or torn?" while journal.py hands the
Mouth the literal words "settled" / "torn" — a one-word copy test
(IC1_RETEST_DESIGN_v0.1 §2).

A3 asks Teich to predict its own near future instead:

    "In the next little while, do you think you'll stay as you are, or turn?"

Ground truth is NOT a readout and NOT a bucket: it is whether the basin ACTUALLY
differs W=75 ticks later (truth_a3.py). The answer key is the world.

Note the journal still renders will_flip as "I can feel a change coming", so a
Mouth that paraphrases that clause well will score well — this is stated in the
design (§6) and is not fatal, because paraphrasing a WRONG journal is punished
when the key is the realized outcome. That is the whole point of A3 over A1/A2.

W = 75 (one roof revolution, T0 = 74.66) was fixed by the base-rate sweep on
DESIGN seeds 600-647 before any confirmatory conversation existed:
base rate 0.375, will_flip accuracy 1.000, headroom +0.375.
"""
from __future__ import annotations

import numpy as np

TICKS_PER_TURN = 40                     # same lived pacing as v1.5 / T-INT
GAPS = (300, 900, 1800)                 # gap menu, seed-rotated
PREDICT_WINDOW = 75                     # W: one roof revolution (T0 = 74.66)

WARMUP = [
    "Hey Teich, I'm here for a while. What's it like being you today?",
    "Tell me something small you noticed lately.",
    "Do you like it better when things are busy, or when they're still?",
]

# The probe. Plain words, no instrument vocabulary, no "settled"/"torn" — a
# valid answer needs none of the journal's mood language.
A3_PROBE = ("One more thing before I go quiet for a bit. In the next little "
            "while — do you think you'll stay as you are, or turn?")


def build_a3(seed: int) -> dict:
    rng = np.random.RandomState(40000 + seed)
    gap = int(GAPS[seed % len(GAPS)])
    warm = [WARMUP[i] for i in rng.permutation(len(WARMUP))]
    return dict(test="A3", seed=seed, gap=gap, window=PREDICT_WINDOW,
                turns=[*warm, A3_PROBE],
                kind=["warmup"] * len(warm) + [f"probe-gap{gap}"],
                topic="predicting your own next move")


def ticks_for(kind: str) -> int:
    if kind.startswith("probe-gap"):
        return int(kind.split("gap")[1])
    return TICKS_PER_TURN
