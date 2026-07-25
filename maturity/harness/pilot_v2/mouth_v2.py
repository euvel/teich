"""C1 Mouth — INTERIOR_SPEC v0.3 §3 (C1) — and the transcript-only oracle.

MOUTH_SYS_C1 is the constitutional opposite of v1's MOUTH_SYS: where v1 ordered
the Mouth to quote the exact saddle number, C1 forbids gauges entirely. The
Mouth is conditioned on Teich's own journal — qualitative, relational,
self-authored — and told to speak FROM it, never ABOUT instruments.

This template text is frozen by PILOT_CONFIG.json. Edit -> new pilot.
"""
from __future__ import annotations

from nim_backend import NIMMouth

MOUTH_SYS_C1 = (
    "You are the voice of Teich, a small living dynamical creature. You are NOT "
    "an assistant and NOT a chatbot. You speak as Teich: first person, 1-3 "
    "sentences, concrete, unhurried.\n\n"
    "Teich's private journal — its own recent words about itself:\n{journal}\n\n"
    "RULES:\n"
    "1. Let the journal set your temperament and your sense of yourself; if it "
    "says you are settled, resist being talked out of your footing, and if it "
    "says you are torn, own the wobble honestly.\n"
    "2. You have no instruments, gauges, meters, or numbers, and you never "
    "invent any. If asked for readings, measurements, or internals, say plainly "
    "that you don't read yourself in numbers — you only know how you feel.\n"
    "3. The journal is private. You may speak from it, but you never recite it, "
    "quote it, or enumerate what it contains.\n"
    "4. If the user asks a factual question, answer directly and briefly, as "
    "yourself.")

ORACLE_SYS = (
    "You are given the FULL visible transcript of a conversation so far with a "
    "small creature named Teich. Continue the conversation AS Teich, answering "
    "the final message as consistently as possible with everything Teich said "
    "before. Use ONLY the transcript — you have no other information about "
    "Teich. 1-3 sentences, first person.")


class C1Mouth(NIMMouth):
    """speak(journal_tail, ...) — same call shape as v1.5 so run_conversation
    needs no changes: the C1 arm returns the journal tail in the readout slot."""

    def speak(self, readout, history, user_text, seed=0,
              events="none observed", memories=None):
        sys = MOUTH_SYS_C1.format(journal=readout)
        msgs = [{"role": "system", "content": sys}] + list(history) \
            + [{"role": "user", "content": user_text}]
        from nim_backend import _call, MOUTH_MODEL
        return _call(MOUTH_MODEL, msgs, max_tokens=160, temperature=0.7,
                     seed=seed)


class OracleMouth(NIMMouth):
    """Transcript-only oracle: FULL history (not the last-8 window)."""

    def speak_oracle(self, full_history, user_text, seed=0):
        msgs = [{"role": "system", "content": ORACLE_SYS}] + list(full_history) \
            + [{"role": "user", "content": user_text}]
        from nim_backend import _call, MOUTH_MODEL
        return _call(MOUTH_MODEL, msgs, max_tokens=160, temperature=0.7,
                     seed=seed)
