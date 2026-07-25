"""Pilot v2 arms — INTERIOR_SPEC v0.3 §3a, §7.2.

A2b_feed_severed: the clean decoupling contrast. It IS arms.A5Deaf — hear()
returns (0,0) and schedules no forcing, so the same seeded synthetic core
free-runs on the same tick schedule with conversational coupling as the only
severed variable. v1.5 already validated this code path across a full campaign;
here it changes role (protocol control, not "deaf" test arm) and name.

C1Journal: wraps any core-running arm. The inner arm's readout never reaches
the Mouth; instead a deterministic Ply R journal (journal.py) accretes entries
and the Mouth receives only its tail. The readout still lands in `meta` so the
transcript records `obs` for offline scoring — published data, not conversation
context; C-EXPOSE governs what the *partner* can see and push against.
"""
from __future__ import annotations

from arms import A5Deaf
from journal import JournalWriter

JOURNAL_TAIL_K = 6      # entries shown to the Mouth; part of the freeze


class A2bFeedSevered(A5Deaf):
    name = "A2b_feed_severed"


class C1Journal:
    """Coupling wrapper: state -> Ply R -> Mouth. Never state -> Mouth."""

    def __init__(self, inner):
        self.inner = inner
        self.name = inner.name + "+C1"

    def start(self, seed):
        self.inner.start(seed)
        self.j = JournalWriter()
        r0 = getattr(self.inner, "e", None)
        if r0 is not None:                    # core-running arms: wake entry
            first = self.inner.e.advance(0)
            self.inner.e.prev_r, self.inner.e.prev_tick = first, self.inner.e.n
            self.j.wake_entry(first)

    def step(self, text, ticks):
        _ro, _ev, forcing, meta = self.inner.step(text, ticks)
        if "readout" in meta:
            self.j.entry(meta["readout"])
        # journal tail replaces the readout channel; events channel is closed
        # entirely (flip counts are category-(b) leaks, spec §1 R10).
        return self.j.tail(JOURNAL_TAIL_K), "none observed", forcing, meta
