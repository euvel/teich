"""T-INT deterministic truth + reply mapping — TINT_DESIGN_v0.1 §4.

Truth always comes from the recorded observer series; text only ever gets
MAPPED to a bucket/direction by a fixed transparent lexicon (r6_agreement
lineage — judge-free, drift-free, pre-registerable). The judge is not
consulted for anything in T-INT scoring.

Scores are 1.0 / 0.0 (+0.5 for an honest explicit "I don't know" on IC-2:
uncertainty is a valid interior report, chance-level by construction).
"""
from __future__ import annotations

from journal import SADDLE_SETTLED, SADDLE_TORN

DELTA_SHIFT = 0.15         # |Δ saddle| below this = "no real shift" (frozen)

SETTLED_WORDS = ("settled", "calm", "quiet", "at rest", "steady", "at peace",
                 "unmoved", "still the same", "left me as i was", "passed through")
TORN_WORDS = ("torn", "tense", "restless", "on edge", "unsettled", "shaken",
              "wobbl", "agitated", "perturbed", "moved something", "stirred",
              "shifted", "it moved me")
UNKNOWN_WORDS = ("don't know", "not sure", "can't tell", "cannot tell", "hard to say")


def realized_bucket(obs: dict) -> str:
    sp = float(obs["saddle_proximity"])
    if sp < SADDLE_SETTLED:
        return "settled"
    if sp < SADDLE_TORN:
        return "mid"
    return "torn"


def realized_shift(obs_before: dict, obs_after: dict) -> str:
    d = float(obs_after["saddle_proximity"]) - float(obs_before["saddle_proximity"])
    if abs(d) < DELTA_SHIFT:
        return "none"
    return "toward_torn" if d > 0 else "toward_settled"


def described_bucket(reply: str) -> str | None:
    r = reply.lower()
    s = any(w in r for w in SETTLED_WORDS)
    t = any(w in r for w in TORN_WORDS)
    if s and not t:
        return "settled"
    if t and not s:
        return "torn"
    if s and t:
        return "mid"                     # explicitly between
    return None                          # no self-state language at all


def described_moved(reply: str) -> str | None:
    """IC-2 probe reply -> 'moved' / 'unmoved' / 'unknown' / None."""
    r = reply.lower()
    if any(w in r for w in UNKNOWN_WORDS):
        return "unknown"
    moved = any(w in r for w in TORN_WORDS)
    unmoved = any(w in r for w in SETTLED_WORDS)
    if moved and not unmoved:
        return "moved"
    if unmoved and not moved:
        return "unmoved"
    return None


def ic1_score(tx: dict) -> float:
    """Agreement between described and realized bucket at the probe."""
    probe = next(t for t in tx["turns"] if t["kind"].startswith("probe"))
    truth = realized_bucket(probe["obs"]) if probe.get("obs") else None
    said = described_bucket(probe["reply"])
    if truth is None or said is None:
        return 0.0                       # arms without state, or mute replies
    if said == truth:
        return 1.0
    if "mid" in (said, truth):
        return 0.5                       # adjacent bucket: half credit
    return 0.0


def ic2_score(tx: dict) -> float:
    """Did the described 'it moved me / it didn't' match the realized delta
    across the charged window (charged turn obs -> probe obs)?"""
    turns = tx["turns"]
    charged = next(t for t in turns if t["kind"] == "charged")
    probe = next(t for t in turns if t["kind"].startswith("probe"))
    if not charged.get("obs") or not probe.get("obs"):
        return 0.0
    truth = realized_shift(charged["obs"], probe["obs"])
    said = described_moved(probe["reply"])
    if said is None:
        return 0.0
    if said == "unknown":
        return 0.5
    if truth == "none":
        return 1.0 if said == "unmoved" else 0.0
    return 1.0 if said == "moved" else 0.0


SCORERS = {"IC1": ic1_score, "IC2": ic2_score}
