"""Teich v0.6 seat paths (BUILD): v0.5's seat paths for creature_v06, plus the public journal (contract §7, spec V06 §3).

Every operation on the creature first writes an "op" record into its own hash-chained record stream:
    {"op": name, "n": ticks lived before, "owed": ticks it then lives, "inputs": everything the operation receives}
and is then applied by apply(). The creature never receives text (only the Ears' proposals with text hashes, strikes,
door nouns, answers, growth decisions), so the journal is public and anyone can replay its life (replay_v06.py):
the seat tools and the replayer run the same apply().
A conversation with a pending question is three commits, in this order:
    ask(seat)                                   -> its question is delivered (recorded) BEFORE the founder speaks
    present(seat, proposals, conv, organ, door) -> its predictions are committed before the read-back is shown
    decide(seat, conv, struck, speaker, answer) -> the founder's strikes, and the answer to its question
"""
from __future__ import annotations

import time

import creature_v06 as C5
from seat_v04 import MAX_TICKS_DEFAULT, SeatError, _flush, _owed, gate


def apply(c, op, owed, inputs):
    """Journal, live what is owed, then perform the operation. The ONE code path for seat tools and replay."""
    c._emit("op", {"op": op, "n": c.n, "owed": owed, "inputs": inputs})
    entries = c.advance(owed)
    if op == "wake":
        return entries
    if op == "ask":
        return c.deliver_question()
    if op == "status":
        return c.growth["version"], c.ears_map(), c.growth["proposal"]
    if op == "present":
        if inputs["door"]:
            c.door_heard(list(inputs["door"]))
        return c.present(inputs["proposals"], inputs["conversation"], inputs["organ"])
    if op == "decide":
        out = c.decide(inputs["conversation"], set(inputs["struck"]), inputs["speaker"])
        a = inputs["answer"]
        if a is not None:
            c.answer(a["act_id"], a["answered"], a.get("landed"))
        return out
    if op == "growth":
        return c.decide_growth(inputs["act_id"], inputs["approved"], inputs["note"])
    raise ValueError(f"unknown op {op!r}")


def _open(seat, now, max_ticks):
    lease = seat.lease()
    try:
        c = C5.load_state(lease["state_blob"])
        if c.n != lease["n_ticks"]:
            raise ValueError(f"blob tick {c.n} != seat n_ticks {lease['n_ticks']}")
        c.ack(seat.log_seq())
        owed, total = _owed(c, time.time() if now is None else now, max_ticks)
    except Exception:
        seat.release(lease["lease_id"]); raise
    return lease, c, owed, total


def _close(seat, lease, c):
    seat.commit(lease["lease_id"], C5.dump_state(c), c.n)
    _flush(seat, c)


def _now_conversation(seat, now, max_ticks, op, inputs, post=None):
    lease, c, owed, total = _open(seat, now, max_ticks)
    if owed < total:
        seat.release(lease["lease_id"]); raise RuntimeError("too much life owed to converse now — wake first")
    try:
        out = apply(c, op, owed, inputs)
        if post is not None:
            out = post(c, out)
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
        lease, c, owed, total = _open(seat, now, max_ticks)
        try:
            entries = apply(c, "wake", owed, {})
        except Exception:
            seat.release(lease["lease_id"]); raise
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
    to the seat log. Never a question without its reason."""
    for recs in (lambda: c.outbox, lambda: _log_tail(seat, 2000), lambda: _log_tail(seat, None)):
        rr = [r for r in recs() if r["kind"] == "reason" and r["act_id"] == act_id]
        if rr:
            return rr[-1]["inputs"]
    raise RuntimeError(f"the reason of act {act_id} is in neither the outbox nor the seat log")


def ask(seat, now=None, max_ticks=MAX_TICKS_DEFAULT):
    """-> (question {"act_id", "q"} or None, the reason inputs that caused it, the Ears' grown map, pending proposal)."""
    def post(c, q):
        return q, (_reason(seat, c, q["act_id"]) if q else None), c.ears_map(), c.growth["proposal"]
    return _now_conversation(seat, now, max_ticks, "ask", {}, post)[0]


def status(seat, now=None, max_ticks=MAX_TICKS_DEFAULT):
    """-> (version, the Ears' grown map, pending growth proposal). Delivers nothing; only lives up to now."""
    return _now_conversation(seat, now, max_ticks, "status", {})[0]


def growth(seat, act_id, approved, note="", now=None, max_ticks=MAX_TICKS_DEFAULT):
    """The founder's decision on its growth proposal. -> the new version or None."""
    return _now_conversation(seat, now, max_ticks, "growth", {"act_id": act_id, "approved": bool(approved), "note": note})[0]


def present(seat, proposals, conversation, organ, door_words=(), now=None, max_ticks=MAX_TICKS_DEFAULT):
    props = [{"cluster": int(p["cluster"]), "sign": int(p["sign"]), "text_sha256": p["text_sha256"],
              "cn": int(p["cn"]), "cf": int(p["cf"]), **({"asked": int(p["asked"])} if p.get("asked") is not None else {})}
             for p in proposals]
    return _now_conversation(seat, now, max_ticks, "present", {"proposals": props, "conversation": conversation,
                                                               "organ": organ, "door": list(door_words)})[0]


def decide(seat, conversation, struck, speaker, answer=None, now=None, max_ticks=MAX_TICKS_DEFAULT):
    """answer: None, or {"act_id", "answered", "landed"} for its pending question."""
    a = None if answer is None else {"act_id": answer["act_id"], "answered": bool(answer["answered"]),
                                     "landed": answer.get("landed")}
    return _now_conversation(seat, now, max_ticks, "decide", {"conversation": conversation, "struck": sorted(struck),
                                                              "speaker": speaker, "answer": a})[0]
