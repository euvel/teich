"""The real seat for v0.4: TeichSeat Durable Object at teich.euvvel.xyz, adapted to the seat_v04/seat_v04s interface.

Record log (worker change 2026-10-21): after each commit the creature's closed records (heard, shown, predict,
outcome, diary with its self block, commitment) are appended to the seat's log — append-only, contiguous seq,
hash-chained from the genesis anchor — and on the next lease the creature drops what the log holds, so the blob keeps a
constant size. Before that worker change is deployed the log endpoints answer 404; then nothing is acknowledged
(log_seq() = 0) and every record stays in the blob's outbox: lossless either way.
release(): the seat has no release endpoint; an abandoned lease expires after 15 minutes (lawful).
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

_R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_R / "body") if (_R / "body" / "seat_client.py").exists() else str(_R / "teich_repo" / "body"))
from seat_client import Seat, SeatError, _call  # noqa: E402,F401

CHUNK = 400


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

    def _log_live(self):
        try:
            return _call(self.name, "log-seq", {})
        except SeatError as e:
            if e.status == 404 and "unknown endpoint" in str(e.payload):
                return None                       # worker without the log yet: keep everything in the outbox
            raise

    def log_seq(self):
        r = self._log_live()
        return 0 if r is None else int(r["seq"])

    def append_log(self, records):
        r = self._log_live()
        if r is None:
            return None
        fresh = [x for x in records if x["seq"] > int(r["seq"])]
        for i in range(0, len(fresh), CHUNK):
            _call(self.name, "log-append", {"records": fresh[i:i + CHUNK]})
        return len(fresh)

    def log_read(self, from_seq=1, limit=2000):
        """-> every log row from from_seq on: {"seq", "ts", "h", "raw", "rec"}."""
        out = []
        while True:
            rows = _call(self.name, "log-read", {"from_seq": from_seq, "limit": limit})["records"]
            out += rows
            if len(rows) < limit:
                return out
            from_seq = rows[-1]["seq"] + 1


def verify_log(rows, genesis_anchor):
    """Recompute the hash chain: h(seq) = sha256(h(seq-1) + raw), h(0) = the genesis anchor; seqs contiguous from 1.
    -> (ok, n, head)."""
    h = genesis_anchor
    for k, r in enumerate(rows, 1):
        if r["seq"] != k:
            return False, k - 1, h
        h = hashlib.sha256((h + r["raw"]).encode()).hexdigest()
        if h != r["h"]:
            return False, k - 1, h
    return True, len(rows), h
