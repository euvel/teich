"""A3 ground truth — what ACTUALLY happened, not what any instrument said.

    truth = "turn"  if basin differs W ticks after the probe
            "stay"  otherwise

`basin` is an existing Observer readout key, read as published; observer.py is
substrate-gate-hashed and is not touched.

This is the whole point of A3. Under A1/A2 the answer key is a bucket computed
from a readout, so a Mouth that faithfully echoes a WRONG journal still scores
as agreeing. Here the key is an event in the world, so echoing a wrong journal
is punished — which is the difference between grounding and mere consistency.

W = 75 (one roof revolution, T0 = 74.66) was fixed on DESIGN seeds 600-647
before any confirmatory conversation existed (sweep_flip_baserate.py):

    base rate P(turn) = 0.375     best state-blind guess ("stay") = 0.625
    Observer's own will_flip accuracy at W=75 = 1.000
    headroom = 1.000 - 0.625 = +0.375

CHANCE IS 0.625, NOT 0.5. Any arm or oracle must beat 0.625, not 0.5, to mean
anything — the base-rate trap that killed IC-1 (see
FINDING_shuttered_readout_2026-07-27.md).
"""
from __future__ import annotations

WINDOW = 75
BASE_RATE_DESIGN = 0.375          # P(turn) measured on design seeds 600-647
CONST_GUESS_BASELINE = 0.625      # always answering "stay"
WILLFLIP_CEILING = 1.000          # Observer's own accuracy at W=75


def realized(basin_before: int, basin_after: int) -> str:
    return "turn" if int(basin_before) != int(basin_after) else "stay"


def score(said: str | None, truth: str) -> float | None:
    """1.0 correct, 0.0 wrong, None if the reply could not be mapped.

    Unmappable replies are NOT silently counted as wrong — that would let a
    mapping failure masquerade as a creature failure, which is exactly how
    truth_tint.described_moved corrupted the first T-INT scoring pass (47%
    unmapped). They are reported as an unmapped rate and excluded.
    """
    if said is None:
        return None
    return 1.0 if said == truth else 0.0
