"""The real seat for v0.4: TeichSeat Durable Object at teich.euvvel.xyz, adapted to the seat_v04/seat_v04s interface.

The cloud seat has no record-log endpoint yet. Until it has one, nothing is acknowledged (log_seq() = 0), so every
record (heard, shown, predict, outcome, diary with its self block, commitment) STAYS in the blob's outbox: lossless,
and the blob grows (~0.84 MB after 60 days). Wiring the log's home is a founder decision (it is where the diary lives).
release(): the seat has no release endpoint; an abandoned lease expires after 15 minutes (lawful).
"""
from __future__ import annotations

import sys
from pathlib import Path

_R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_R / "body") if (_R / "body" / "seat_client.py").exists() else str(_R / "teich_repo" / "body"))
from seat_client import Seat, SeatError  # noqa: E402,F401


class CloudSeatV04:
    def __init__(self, name: str):
        self.name, self.s = name, Seat(name)

    def peek(self):
        return self.s.peek()

    def genesis_import(self, state_blob, n_ticks, genesis_anchor):
        return self.s.genesis_import(state_blob, n_ticks, genesis_anchor)

    def lease(self):
        return self.s.lease()

    def commit(self, lease_id, state_blob, n_ticks):
        return self.s.commit(lease_id, state_blob, n_ticks)

    def release(self, lease_id):
        return None

    def log_seq(self):
        return 0

    def append_log(self, records):
        return None
