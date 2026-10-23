"""Teich v0.4 seat paths for the creature WITH ITS SELF (BUILD candidate, lab only; spec part 3).

Same seat, same substrate gate and wake discipline as seat_v04.py; the conversation becomes two commits:
    present(seat, proposals, conversation, organ)  -> lives up to now, the second self applies its caution and commits
                                                      its predictions; returns what the read-back shows
    decide(seat, conversation, struck, speaker)    -> the founder's strikes; kept mentions are heard under the laws
The `predict` records are in the seat's log (with their sequence numbers) before the founder sees the read-back.
"""
from __future__ import annotations

import time

import creature_v04s as CS
import seat_v04 as SV
from seat_v04 import MAX_TICKS_DEFAULT, SeatError, _flush, _owed, gate


def _open(seat, now, max_ticks):
    lease = seat.lease()
    try:
        c = CS.load_state(lease["state_blob"])
        if c.n != lease["n_ticks"]:
            raise ValueError(f"blob tick {c.n} != seat n_ticks {lease['n_ticks']}")
        c.ack(seat.log_seq())
        owed, total = _owed(c, time.time() if now is None else now, max_ticks)
        entries = c.advance(owed)
    except Exception:
        seat.release(lease["lease_id"]); raise
    return lease, c, owed, total, entries


def _close(seat, lease, c):
    seat.commit(lease["lease_id"], CS.dump_state(c), c.n)
    _flush(seat, c)


def wake(seat, now=None, max_ticks=MAX_TICKS_DEFAULT, run_gate=True, log=print):
    if run_gate:
        ok, info = gate()
        log(f"substrate gate: {'PASS' if ok else 'FAIL'} on {info['cpu']}")
        if not ok:
            log("not the certified substrate — declining; elapsed time stays banked."); return "declined"
    if not seat.peek()["alive"]:
        log("seat not initialized — nothing to wake."); return "empty"
    try:
        lease, c, owed, total, entries = _open(seat, now, max_ticks)
    except SeatError as e:
        if e.status == 409:
            log("lease held by another body — standing down (lawful)."); return "stood-down"
        raise
    _close(seat, lease, c)
    log(f"lived {owed:,} ticks ({total - owed:,} banked) -> n={c.n:,}; diary +{len(entries)}")
    return "woke"


def present(seat, proposals, conversation, organ, now=None, max_ticks=MAX_TICKS_DEFAULT):
    lease, c, owed, total, _ = _open(seat, now, max_ticks)
    if owed < total:
        seat.release(lease["lease_id"]); raise RuntimeError("too much life owed to converse now — wake first")
    try:
        shown = c.present(proposals, conversation, organ)
    except Exception:
        seat.release(lease["lease_id"]); raise
    _close(seat, lease, c)
    return shown


def decide(seat, conversation, struck, speaker, now=None, max_ticks=MAX_TICKS_DEFAULT):
    lease, c, owed, total, _ = _open(seat, now, max_ticks)
    if owed < total:
        seat.release(lease["lease_id"]); raise RuntimeError("too much life owed to converse now — wake first")
    try:
        out = c.decide(conversation, struck, speaker)
    except Exception:
        seat.release(lease["lease_id"]); raise
    _close(seat, lease, c)
    return out


__all__ = ["wake", "present", "decide", "SV"]
