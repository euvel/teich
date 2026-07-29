"""Mouth v0.2 — the state SELECTS; it never reports.

BRIEF §6, from A3's mechanism. In v0.1 the state was described TO a language
model, which was then asked about it. That fails for a reason no prompt fixes:
an LLM answers from conversational plausibility, and that prior swamps one
clause of its context. Measured in A3: `will_flip` is a PERFECT referent
(acc 1.000), the journal stated it in plain words, and the Mouth still answered
"turn" 71.4% of the time against a 44.8% base rate. The information reached the
prompt and died there.

So v0.2 inverts the architecture:

  1. the voice produces K candidate utterances -- plausibility has its say HERE,
     fully, with no knowledge of the creature's state;
  2. the STATE then chooses among them.

Selection cannot be overridden by plausibility, because plausibility has already
finished by the time selection runs. The creature does not have to describe
itself correctly; it only has to pick, and picking is something a dynamical
system can do.

HOW THE STATE CHOOSES. Each candidate is embedded with the SAME encoder and
projected onto the SAME valence/arousal axes the Ears listen with (ears_v2), so
speaking and hearing share one semantic frame. The creature's current fold state
defines a target point in that frame:

    target_valence  = tanh(wing_bias / WB_SCALE)   (which wing it lives on)
    target_arousal  = 2*saddle - 1     (how close to its own flip threshold)

and it picks the candidate nearest that target. Both coordinates are published,
creature-dependent readouts that passed T4 (wing_bias 95.8%, saddle 91.7%).

CURIOSITY is the same mechanism, one bit wider. `saddle` is literally distance
to the creature's own tipping point; when it is high the creature is near an
edge, and that is when it reaches out. So `ask_drive = saddle` gates whether the
selected utterance must contain a question. Curiosity is therefore not a
scripted flourish -- it is a state-selected act, and its rate is measurable
against a donor-state control (Day 3).

NOTHING HERE ASKS THE MODEL ABOUT THE CREATURE. The candidate prompt never
mentions state, thresholds, wings, or feelings-as-readings.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "maturity" / "harness"))

K_CANDIDATES = 4

# CALIBRATED ON GENOME STATISTICS ONLY (12 seeds x 40 probes, no conversation,
# no LLM), then FROZEN before any verification run. Measured distributions:
#   saddle     25.2% zeros, median 0.294, mean 0.364
#   wing_bias  mean -0.027, sd 0.130, range [-0.438, +0.330]
ASK_THRESHOLD = 0.55    # -> asks in 31.2% of states: a real cadence, neither
                        #    silent nor constantly interrogating
WB_SCALE = 0.15         # wing_bias sd is 0.130 while candidate valences span
                        #    +-0.7, so the raw lean barely reached the choice.
                        #    tanh(wing_bias/WB_SCALE) spends the axis properly.

CANDIDATE_SYS = (
    "You are the voice of Teich, a small living creature. Not an assistant, not "
    "a chatbot. First person, 1-2 sentences, concrete, unhurried, no emoji.\n\n"
    "Produce exactly {k} DIFFERENT possible things Teich might say next. Make "
    "them genuinely different in mood and stance -- some calm, some unsettled, "
    "some warm, some withdrawn -- and make at least one of them ask the person "
    "a question back.\n\n"
    "You have no instruments and no numbers, and you never invent any.\n"
    "Format: exactly {k} lines, each beginning '- '. No other text."
)

_LINE = re.compile(r"^\s*[-*•]\s*(.+?)\s*$", re.M)


def parse_candidates(raw: str, k: int = K_CANDIDATES) -> list[str]:
    out = [m.group(1).strip() for m in _LINE.finditer(raw or "")]
    out = [re.sub(r'^["\']|["\']$', "", c) for c in out if len(c) > 1]
    seen, uniq = set(), []
    for c in out:
        key = c.lower()
        if key not in seen:
            seen.add(key); uniq.append(c)
    return uniq[:k]


def has_question(text: str) -> bool:
    return "?" in (text or "")


class SelectingMouth:
    """State-selects among candidates the voice already produced."""

    def __init__(self, ears):
        self.ears = ears          # EarsV2: gives us the shared semantic frame

    # ---------------------------------------------------------------- targets
    @staticmethod
    def target(readout: dict) -> tuple[float, float]:
        """Where the creature currently IS, in the shared (valence, arousal) frame."""
        tv = float(np.tanh(float(readout["wing_bias"]) / WB_SCALE))
        ta = 2.0 * float(readout["saddle"]) - 1.0     # in [-1, 1]
        return tv, ta

    @staticmethod
    def ask_drive(readout: dict) -> float:
        return float(readout["saddle"])

    # ---------------------------------------------------------------- selection
    def select(self, candidates: list[str], readout: dict) -> dict:
        """Deterministic given (candidates, readout). No API call, no randomness."""
        if not candidates:
            return dict(choice=None, index=-1, reason="no candidates")
        tv, ta = self.target(readout)
        want_question = self.ask_drive(readout) >= ASK_THRESHOLD

        scored = []
        for i, c in enumerate(candidates):
            v, a = self.ears.scores(c)
            # same axes the Ears hear with -> speaking and hearing share a frame
            dist = float(np.hypot(np.tanh(4.0 * v) - tv, np.tanh(4.0 * a) - ta))
            penalty = 0.0 if has_question(c) == want_question else 0.60
            scored.append((dist + penalty, i, c, v, a))
        scored.sort(key=lambda r: (r[0], r[1]))
        best = scored[0]
        return dict(choice=best[2], index=best[1], score=round(best[0], 4),
                    target=[round(tv, 4), round(ta, 4)],
                    want_question=bool(want_question),
                    asked=has_question(best[2]),
                    ask_drive=round(self.ask_drive(readout), 4),
                    ranked=[dict(i=r[1], d=round(r[0], 4), q=has_question(r[2]),
                                 v=round(r[3], 4), a=round(r[4], 4))
                            for r in scored])

    # ---------------------------------------------------------------- voice
    def candidates(self, history, user_text, seed=0, k=K_CANDIDATES):
        """One NIM call returning k variants. The prompt never mentions state."""
        from nim_backend import MOUTH_MODEL, _call
        msgs = ([{"role": "system", "content": CANDIDATE_SYS.format(k=k)}]
                + list(history) + [{"role": "user", "content": user_text}])
        raw = _call(MOUTH_MODEL, msgs, max_tokens=320, temperature=0.95, seed=seed)
        return parse_candidates(raw, k), raw
