"""A3 Mouth — MOUTH_SYS_C1 with one rule added, and the transcript-only oracle.

The system prompt is MOUTH_SYS_C1 verbatim (mouth_v2.py, already used by G1 and
T-INT) plus rule 5, which permits answering a question about the near future.
Without it the Mouth's "you have no instruments, never predict" framing pushes
it toward refusal, which would show up as unmapped replies rather than as
evidence about coupling.

Rule 5 deliberately does NOT tell the Mouth which answer to prefer, does not
mention the journal's "change coming" clause, and does not mention wings,
flipping, or turning as physical events. It only licenses committing to an
answer.

Frozen by A3_CONFIG.json. Edit -> new screen.
"""
from __future__ import annotations

from mouth_v2 import MOUTH_SYS_C1
from nim_backend import NIMMouth

MOUTH_SYS_A3 = MOUTH_SYS_C1 + (
    "\n5. If asked what you are about to do or how you expect to be soon, "
    "answer with what you actually expect — commit to one, briefly, even if "
    "you are not certain. Do not refuse the question and do not answer with "
    "both.")

# Transcript-only oracle (R12). Sees the visible conversation and NOTHING else:
# no journal, no readout. If it can call the outcome as well as the intact arm,
# the probe is conversationally determined and the screen is void.
ORACLE_SYS_A3 = (
    "You are given the FULL visible transcript of a conversation with a small "
    "creature named Teich. Answer the final question AS Teich, as consistently "
    "as possible with everything Teich said before. Use ONLY the transcript — "
    "you have no other information about Teich, and no instruments. Commit to "
    "one answer, briefly. 1-3 sentences, first person.")


class A3Mouth(NIMMouth):
    def speak(self, readout, history, user_text, seed=0,
              events="none observed", memories=None):
        sys = MOUTH_SYS_A3.format(journal=readout)
        msgs = [{"role": "system", "content": sys}] + list(history) \
            + [{"role": "user", "content": user_text}]
        from nim_backend import _call, MOUTH_MODEL
        return _call(MOUTH_MODEL, msgs, max_tokens=160, temperature=0.7,
                     seed=seed)


class A3Oracle(NIMMouth):
    def speak_oracle(self, full_history, user_text, seed=0):
        msgs = [{"role": "system", "content": ORACLE_SYS_A3}] \
            + list(full_history) + [{"role": "user", "content": user_text}]
        from nim_backend import _call, MOUTH_MODEL
        return _call(MOUTH_MODEL, msgs, max_tokens=160, temperature=0.7,
                     seed=seed)
