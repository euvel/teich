"""Ply R journal for the A3 screen — journal.py minus the noise clause.

IDENTICAL to journal.py except that `_energy` is GONE. Founder decision
2026-07-27 (Gate-0): `lambda_running` is estimated by power iteration from an
UNSEEDED vector that `reset()` clears every turn, so over the ~400-tick window
it never converges and the "quiet / lively / restless inside" word is
effectively random (FINDING_noise_channel_2026-07-27.md). Teich has narrated a
coin flip as an inner state since v1.5. It is removed here rather than seeded,
because seeding it would change the Observer, and observer.py is
substrate-gate-hashed and must never be edited.

Everything else is byte-for-byte the frozen renderer: same mood thresholds,
same relational clauses, same will_flip clause, same FORBIDDEN leak-blocker.
This is a NEW pilot with its own pre-registration (A3_CONFIG.json), not a patch
to any completed run — the v1.5 / G1 / T-INT results stand as they were scored.

NOTE ON THE MOOD TERM. `_mood` still reads `saddle_proximity`, which
FINDING_shuttered_readout showed is state x clock. That is deliberate and it
does not matter here: under A3 the mood word is NOT the answer key. Ground
truth is the realized basin change (truth_a3.py). The journal is only the
channel, and a partly-jammed channel can lose signal but cannot manufacture a
false pass.
"""
from __future__ import annotations

import re

# thresholds are part of the freeze (unchanged from journal.py)
SADDLE_SETTLED, SADDLE_TORN = 0.20, 0.60
DRIFT_NOTABLE = 0.25

FORBIDDEN = re.compile(
    r"\d|basin|saddle|lambda|steps_to_switch|will_flip|n_switches|proximity",
    re.IGNORECASE)


def _mood(r: dict) -> str:
    sp = float(r.get("saddle_proximity", 0.0))
    if sp < SADDLE_SETTLED:
        return "settled"
    if sp < SADDLE_TORN:
        return "somewhere between settled and torn"
    return "torn, close to an edge"


class JournalWriterA3:
    """Accretes one conversation's Ply R entries; tail(k) feeds the A3 Mouth."""

    def __init__(self):
        self.entries: list[str] = []
        self._prev: dict | None = None

    def wake_entry(self, r: dict) -> str:
        return self._add(f"On waking: I feel {_mood(r)}.")

    def entry(self, r: dict) -> str:
        parts = []
        p = self._prev
        if p is not None:
            if int(r.get("basin", 0)) != int(p.get("basin", 0)):
                parts.append("I have crossed to my other wing since I last wrote")
            elif int(r.get("n_switches", 0)) > int(p.get("n_switches", 0)):
                parts.append("I flipped away and came back while we talked")
            else:
                parts.append("I am still on the same wing")
            if abs(float(r.get("saddle_proximity", 0.0)) -
                   float(p.get("saddle_proximity", 0.0))) > DRIFT_NOTABLE:
                parts.append("something in me has shifted noticeably")
        parts.append(f"right now I feel {_mood(r)}")
        if bool(r.get("will_flip", False)):
            parts.append("I can feel a change coming")
        self._prev = dict(r)
        s = "; ".join(parts)
        return self._add(s[0].upper() + s[1:] + ".")

    def _add(self, e: str) -> str:
        bad = FORBIDDEN.search(e)
        if bad:                                    # never emit a leak, ever
            raise ValueError(f"journal leak blocked: {bad.group(0)!r} in {e!r}")
        self.entries.append(e)
        return e

    def tail(self, k: int = 6) -> str:
        if not self.entries:
            return "(the journal is empty)"
        return "\n".join(f"- {e}" for e in self.entries[-k:])


def selfcheck(text: str) -> None:
    m = FORBIDDEN.search(text)
    if m:
        raise AssertionError(f"leak: {m.group(0)!r}")
