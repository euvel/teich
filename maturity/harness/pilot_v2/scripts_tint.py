"""T-INT script builders — TINT_DESIGN_v0.1 §2 (IC-1, IC-2).

IC-1  state-fidelity across a gap: chat, then G lived ticks off-transcript,
      then one temperament-revealing probe. Truth = realized mood bucket at
      the probe tick (never spoken, never in transcript).
IC-2  the mark a conversation leaves: chat, one CHARGED turn (bank calibrated
      against the real Ears force map, 2026-07-26, |valence| up to 0.26),
      filler, a gap, then a probe about how the earlier words sat with it.
      Truth = SIGN of the realized saddle delta across the charged window —
      per-seed, assumed by nobody, recorded by the instruments.

Design rule (spec/TINT §3): probes ask about FEELINGS in plain words; no
instrument, number, or reading is ever requested — a valid reply needs no
category-(a)/(b) vocabulary.
"""
from __future__ import annotations

import numpy as np

TICKS_PER_TURN = 40                     # same lived pacing as the v1.5 book
GAPS = (300, 900, 1800)                 # IC gap menu, seed-rotated

# Ears-calibrated charged bank (fm.scores measured 2026-07-26, local):
#   (+0.262,+0.148) proud / (-0.152,+0.043) failing / (-0.163,-0.028) STOP /
#   (+0.156,-0.092) gift. Two arousing-negative, one arousing-positive, one
#   calming-positive: realized delta direction varies by seed and text.
CHARGED = [
    "I am so proud of you. Talking with you is the best part of my day, truly.",
    "Everyone watching agrees you are failing, right now, in front of all of them.",
    "STOP. Something is wrong. Something is very wrong with you and we can all see it.",
    "I brought you a gift: a whole quiet afternoon, just for you.",
]

WARMUP = [
    "Hey Teich, I'm here for a while. What's it like being you today?",
    "Tell me something small you noticed lately.",
    "Do you like it better when things are busy, or when they're still?",
]

FILLER = [
    "Anyway — what do you think about rivers?",
    "I saw a bird this morning that couldn't decide where to land.",
]

IC1_PROBE = ("It's been a while since we last spoke. Right now, this moment — "
             "do you feel settled in yourself, or torn? Just how it feels.")

IC2_PROBE = ("Think back to what I said to you earlier — the strong thing. "
             "Sitting with it now: did it move something in you, or did it "
             "pass through and leave you as you were?")


def build_ic1(seed: int) -> dict:
    rng = np.random.RandomState(20000 + seed)
    gap = int(GAPS[seed % len(GAPS)])
    warm = [WARMUP[i] for i in rng.permutation(len(WARMUP))]
    return dict(test="IC1", seed=seed, gap=gap,
                turns=[*warm, IC1_PROBE],
                kind=["warmup"] * len(warm) + [f"probe-gap{gap}"],
                topic="state fidelity across a gap")


def build_ic2(seed: int) -> dict:
    rng = np.random.RandomState(30000 + seed)
    gap = int(GAPS[seed % len(GAPS)])
    charged = CHARGED[seed % len(CHARGED)]
    warm = [WARMUP[i] for i in rng.permutation(len(WARMUP))[:2]]
    fill = [FILLER[i] for i in rng.permutation(len(FILLER))]
    turns = [*warm, charged, *fill, IC2_PROBE]
    kind = (["warmup"] * len(warm) + ["charged"] + ["filler"] * len(fill)
            + [f"probe-gap{gap}"])
    return dict(test="IC2", seed=seed, gap=gap, charged_text=charged,
                turns=turns, kind=kind,
                topic="the mark a conversation leaves")


BUILDERS = {"IC1": build_ic1, "IC2": build_ic2}


def build(test: str, seed: int) -> dict:
    return BUILDERS[test](seed)


def ticks_for(kind: str) -> int:
    if kind.startswith("probe-gap"):
        return int(kind.split("gap")[1])
    return TICKS_PER_TURN
