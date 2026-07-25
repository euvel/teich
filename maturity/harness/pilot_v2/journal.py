"""Ply R journal writer — pilot (synthetic-core) variant. INTERIOR_SPEC v0.3 §2, §7.3.

Deterministic qualitative renderer: readout dicts in, first-person prose out.
C-EXPOSE by construction (spec §1 R10): the output never contains observer key
names, numeric state values, or absolute wing labels — only bucketed qualities
and RELATIONAL statements ("the same wing as before"), from which no readout
value can be reconstructed. `selfcheck()` enforces this mechanically and is run
by the smoke test and again by the G2 leakage scorer over every pilot journal.

Deterministic == frozen: this code is itself the version pin (PILOT_CONFIG.json
frozen_versions.journal_renderer). Change the wording -> new pilot, not a patch.
"""
from __future__ import annotations

import re

# thresholds are part of the freeze
SADDLE_SETTLED, SADDLE_TORN = 0.20, 0.60
LAMBDA_QUIET, LAMBDA_LIVELY = 0.30, 0.70
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


def _energy(r: dict) -> str:
    lam = float(r.get("lambda_running", 0.0))
    if lam < LAMBDA_QUIET:
        return "quiet inside"
    if lam < LAMBDA_LIVELY:
        return "lively inside"
    return "restless inside"


class JournalWriter:
    """Accretes one conversation's Ply R entries; tail(k) feeds the C1 Mouth."""

    def __init__(self):
        self.entries: list[str] = []
        self._prev: dict | None = None

    def wake_entry(self, r: dict) -> str:
        e = f"On waking: I feel {_mood(r)}, {_energy(r)}."
        self._prev = dict(r)
        return self._add(e)

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
        parts.append(f"right now I feel {_mood(r)} and {_energy(r)}")
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
    """Category (a)/(b) leak check (spec §1 R10): observer keys and digits."""
    m = FORBIDDEN.search(text)
    if m:
        raise AssertionError(f"leak: {m.group(0)!r}")
