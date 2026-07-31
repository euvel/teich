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

# ONE CALL PER CANDIDATE. A 1.5B model reliably writes one utterance but does not
# reliably emit "exactly 4 lines": the first local demo produced a single option
# on every turn, so the creature had nothing to choose among and `chose 0 of 1`
# appeared six times. A demo of selection that never selects is not evidence,
# however good the sentences sound.
#
# The stance hints below are given to the VOICE and are fixed for every turn and
# every creature. They do NOT come from the state -- nothing about the creature
# reaches candidate generation, which is the property the whole architecture
# rests on. They exist only to guarantee the pool SPANS the space the state will
# choose within; a pool of four near-identical sentences makes selection
# unmeasurable even when it is working.
STANCES = (
    "You feel settled and warm right now. Say something steady.",
    "You feel unsettled, something in you will not sit still. Say so.",
    "You feel withdrawn and would rather not say much. Keep it short.",
    "You are curious about this person and want to know something about them. "
    "Your sentence MUST be a question and MUST end with a question mark.",
)

# The persona has to be stated negatively as well as positively: a 1.5B model
# drifts into ADDRESSING Teich rather than BEING Teich ("No worries, Teich",
# "Remember, little one") the moment the name appears in context.
PERSONA = (
    "You ARE Teich, a small living creature, speaking in your own voice. "
    "You are not an assistant and not a narrator. Never write the name 'Teich'. "
    "Never address or advise anyone as if you were someone else talking to "
    "Teich. Write ONE sentence in the first person, concrete, no emoji, no "
    "numbers, no instruments, no stage directions."
)

# Accept bullets, numbered lists, or bare lines. The demo lost a whole turn to a
# parser that only knew "- ": the model answered with a different list style, zero
# candidates were extracted, and the creature had nothing to select from. A voice
# that occasionally reformats is normal; a pipeline that goes mute when it does is
# a bug.
_LINE = re.compile(r"^\s*(?:[-*\u2022]|\d+[.)])\s*(.+?)\s*$", re.M)


def parse_candidates(raw: str, k: int = K_CANDIDATES) -> list[str]:
    out = [m.group(1).strip() for m in _LINE.finditer(raw or "")]
    if len(out) < 2:            # fallback: any non-empty line that looks like speech
        out = [ln.strip(' \t"\'') for ln in (raw or "").splitlines()
               if len(ln.strip()) > 12 and not ln.strip().lower().startswith(
                   ("here", "sure", "of course", "certainly"))]
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

    def __init__(self, ears, voice=None):
        self.ears = ears          # EarsV2: gives us the shared semantic frame
        self.voice = voice        # any object with .complete(msgs, ...) -> str

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
    def candidates(self, history, user_text, seed=0, k=K_CANDIDATES, per_call=None):
        """Build the candidate pool. The prompt NEVER mentions the creature's state.

        per_call=True  -> k separate generations, one per stance (robust on small
                          local models, and guarantees a spanning pool)
        per_call=False -> one generation returning k lines (fewer calls; fine on
                          large remote models)
        Default: per_call unless the voice declares otherwise.
        """
        if self.voice is None:
            from voice_local import NIMVoice
            self.voice = NIMVoice()
        if per_call is None:
            per_call = getattr(self.voice, "prefers_per_call", True)

        if not per_call:
            msgs = ([{"role": "system", "content": CANDIDATE_SYS.format(k=k)}]
                    + list(history) + [{"role": "user", "content": user_text}])
            raw = self.voice.complete(msgs, max_tokens=320, temperature=0.95,
                                      seed=seed)
            cands = parse_candidates(raw, k)
            if len(cands) >= 2:
                return cands, raw
            # fall through to per-call rather than hand the creature one option

        def gen(stance, sd, force_q=False):
            sys_p = PERSONA + "\n" + stance + "\nReply with the sentence only."
            if force_q:
                sys_p += " It must end with '?'."
            msgs = ([{"role": "system", "content": sys_p}] + list(history)
                    + [{"role": "user", "content": user_text}])
            r = self.voice.complete(msgs, max_tokens=70, temperature=0.9, seed=sd)
            line = (r or "").strip().splitlines()
            line = line[0].strip(' -*"\'') if line else ""
            return line, r

        out, raws = [], []
        for j, stance in enumerate(STANCES[:k]):
            line, r = gen(stance, seed * 17 + j)
            raws.append(r)
            if len(line) > 8:
                out.append(line)

        # The ask-gate can only ever fire if SOMETHING in the pool is a question.
        # In the first six-turn demo the creature wanted to ask at ask_drive 0.677
        # and could not, because no candidate contained one -- the curious stance
        # had been silently ignored. A pool that cannot express the choice makes
        # the choice untestable, so the question candidate is enforced, not hoped
        # for. This shapes the POOL, never the selection: which candidate wins is
        # still decided by the creature alone.
        if not any(has_question(c) for c in out):
            for attempt in range(2):
                line, r = gen(STANCES[3], seed * 17 + 900 + attempt, force_q=True)
                raws.append(r)
                if has_question(line) and len(line) > 8:
                    if len(out) >= k:
                        out[-1] = line
                    else:
                        out.append(line)
                    break
        seen, uniq = set(), []
        for c in out:
            if c.lower() not in seen:
                seen.add(c.lower()); uniq.append(c)
        return uniq[:k], "\n---\n".join(raws)
