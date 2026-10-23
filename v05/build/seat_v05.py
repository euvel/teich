"""Teich v0.5 seat paths (BUILD): the same seat, gate and wake discipline as v0.4 (seat_v04s), for creature_v05.
A conversation with a pending question is three commits, in this order:
    ask(seat)                                   -> its question is delivered (recorded) BEFORE the founder speaks
    present(seat, proposals, conv, organ, door) -> its predictions are committed before the read-back is shown
    decide(seat, conv, struck, speaker, answer) -> the founder's strikes, and the answer to its question
"""
from __future__ import annotations

import time

import creature_v05 as C5
from seat_v04 import MAX_TICKS_DEFAULT, SeatError, _flush, _owed, gate


def _open(seat, now, max_ticks):
    lease = seat.lease()
    try:
        c = C5.load_state(lease["state_blob"])
        if c.n != lease["n_ticks"]:
            raise ValueError(f"blob tick {c.n} != seat n_ticks {lease['n_ticks']}")
        c.ack(seat.log_seq())
        owed, total = _owed(c, time.time() if now is None else now, max_ticks)
        entries = c.advance(owed)
    except Exception:
        seat.release(lease["lease_id"]); raise
    return lease, c, owed, total, entries


def _close(seat, lease, c):
    seat.commit(lease["lease_id"], C5.dump_state(c), c.n)
    _flush(seat, c)


def _now_conversation(seat, now, max_ticks, fn):
    lease, c, owed, total, _ = _open(seat, now, max_ticks)
    if owed < total:
        seat.release(lease["lease_id"]); raise RuntimeError("too much life owed to converse now — wake first")
    try:
        out = fn(c)
    except Exception:
        seat.release(lease["lease_id"]); raise
    _close(seat, lease, c)
    return out, c


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


def _log_tail(seat, n):
    """The seat log's last n records (n=None: all). LocalSeat keeps them in its file; the cloud seat serves log-read."""
    if hasattr(seat, "log_read"):
        last = seat.log_seq()
        return [r["rec"] for r in seat.log_read(from_seq=1 if n is None else max(1, last - n + 1))]
    log = seat._rd()["log"]
    return log if n is None else log[-n:]


def _reason(seat, c, act_id):
    """The logged reason of act `act_id`: in the outbox if its night closed in this conversation, else already flushed
    to the seat log (any wake or status between that night and now flushes it). Never a question without its reason."""
    for recs in (lambda: c.outbox, lambda: _log_tail(seat, 2000), lambda: _log_tail(seat, None)):
        rr = [r for r in recs() if r["kind"] == "reason" and r["act_id"] == act_id]
        if rr:
            return rr[-1]["inputs"]
    raise RuntimeError(f"the reason of act {act_id} is in neither the outbox nor the seat log")


def ask(seat, now=None, max_ticks=MAX_TICKS_DEFAULT):
    """-> (question {"act_id", "q"} or None, the reason inputs that caused it, the Ears' grown map {word: cluster},
    its pending growth proposal or None)."""
    def fn(c):
        q = c.deliver_question()
        return q, (_reason(seat, c, q["act_id"]) if q else None), c.ears_map(), c.growth["proposal"]
    return _now_conversation(seat, now, max_ticks, fn)[0]


def status(seat, now=None, max_ticks=MAX_TICKS_DEFAULT):
    """-> (version, the Ears' grown map, pending growth proposal). Delivers nothing; only lives up to now."""
    return _now_conversation(seat, now, max_ticks,
                             lambda c: (c.growth["version"], c.ears_map(), c.growth["proposal"]))[0]


def growth(seat, act_id, approved, note="", now=None, max_ticks=MAX_TICKS_DEFAULT):
    """The founder's decision on its growth proposal. -> the new version or None."""
    return _now_conversation(seat, now, max_ticks, lambda c: c.decide_growth(act_id, approved, note))[0]


def present(seat, proposals, conversation, organ, door_words=(), now=None, max_ticks=MAX_TICKS_DEFAULT):
    def fn(c):
        if door_words:
            c.door_heard(list(door_words))
        return c.present(proposals, conversation, organ)
    return _now_conversation(seat, now, max_ticks, fn)[0]


def decide(seat, conversation, struck, speaker, answer=None, now=None, max_ticks=MAX_TICKS_DEFAULT):
    """answer: None, or {"act_id", "answered", "landed"} for its pending question."""
    def fn(c):
        out = c.decide(conversation, struck, speaker)
        if answer is not None:
            c.answer(answer["act_id"], answer["answered"], answer.get("landed"))
        return out
    return _now_conversation(seat, now, max_ticks, fn)[0]
