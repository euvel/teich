"""Teich v0.3 selector — certified character, free moments.

CHARACTER (provable, memory-shaped): the creature infers its disposition toward each region ONLY
from its own behaviour — the windowed statistic of each body (condition N) — by matching it to the
calibration table P_K. It never reads its ledger. d_r = k_hat_r - 3 (in memory steps).
It prefers utterances whose valence agrees with its disposition toward the utterance's region.

FREE MOMENT (chaotic, unscripted): among the utterances its character admits, WHICH one it says is
picked by its own chaos — the probe region's body state at the moment of speaking — not by an RNG.

COMMITMENTS (protected): an utterance whose (region, sign) contradicts a lawful commitment is never
chosen, whatever the disposition.
"""
from __future__ import annotations

import numpy as np

# P(x<0) at memory states k = 0..6 (design calibration, seeds 300-306, 40,000 orbits x 3,000 ticks)
P_K = np.array([0.61228, 0.5877, 0.55782, 0.52811, 0.49878, 0.46943, 0.44038])
K_BIRTH = 3
TIE = 0.5          # utterances within half a step of the best score are all "in character"


def infer_disposition(window_means: np.ndarray) -> np.ndarray:
    """(…, 8) windowed P(x<0) per body -> (…, 8) integer disposition in steps, from behaviour only."""
    k_hat = np.argmin(np.abs(window_means[..., None] - P_K), axis=-1)
    return k_hat - K_BIRTH


def select(cands: list[dict], d: np.ndarray, x_now: np.ndarray, probe_region: int,
           commitments: list[dict] = ()) -> dict:
    """cands: [{'region': r, 'sign': s, 'text': ...}]; d: (8,) dispositions; x_now: (8,) body states."""
    allowed = [i for i, c in enumerate(cands)
               if not any(m["region"] == c["region"] and c["sign"] == -m["sign"] for m in commitments)]
    scores = {i: cands[i]["sign"] * float(d[cands[i]["region"]]) for i in allowed}
    best = max(scores.values())
    in_char = [i for i in allowed if scores[i] >= best - TIE]
    u = abs(float(x_now[probe_region]))
    frac = (1.0 / u) % 1.0 if u > 1e-12 else 0.5            # one step of the body's own chaos
    pick = in_char[min(int(frac * len(in_char)), len(in_char) - 1)]
    return {"index": pick, "in_character": in_char, "allowed": allowed, "score": scores[pick]}
