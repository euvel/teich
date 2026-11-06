"""Teich v0.7 seat paths (PRODUCTION): v0.6's seat tools (wake, ask, status, present, decide, growth) over the anchored
v0.7 build (seat_v07.apply, creature_v07), with the Sky and the Seal's seat-side duties.

What production adds to the lab paths, and why:
  - the Sky: before an advance, each touch day it crosses gets its beacon, round_of(t0, d), fetched from drand and
    BLS-verified (seat_v07.assign_sky). No fallback: if a round is missing or fails, nothing is lived or journaled;
  - it never lives past a touch whose round cannot exist yet (wall time before that day's midnight): those ticks
    stay banked, exactly as v0.6 banks ticks beyond --max-ticks. So a wake that runs inside the quiet quarter-hour
    lives up to its touch and stops there;
  - the journal is appended in canonical form (seal_v07.canonical), so the seat's running seal head equals the head
    any watcher computes from the published log (cloud_v07.append_log).
The laws themselves (the touch, b, round_of, the quiet quarter-hour, refusals) are the anchored code's, unchanged.
"""
from __future__ import annotations

import os
import time

import creature_v07 as C7
import genome_v04 as GN
import seat_v07 as S7
import sky_v07 as SKY
from seat_v04 import MAX_TICKS_DEFAULT, SeatError, gate  # noqa: F401

PUBLISHED_AFTER = 30          # seconds after a day's wall midnight by which its round is surely out
SKY_MAX_WAIT = 300            # how long a wake waits for a round that should be out (then: nothing lived)


def _fetch(rnd):
    return SKY.fetch(rnd, proxy=os.environ.get("TEICH_SKY_PROXY") or None)


def owed(c, now, max_ticks):
    """-> (owed, total). As v0.6 (total = wall seconds since birth minus ticks lived, capped by max_ticks), and never
    across the touch of a day whose round cannot be published yet."""
    total = int(now - c.t0) - c.n
    o = max(0, min(total, max_ticks))
    for d in C7.touch_ticks(c.n, o):
        if now < c.t0 + (d + 1) * GN.DAY + PUBLISHED_AFTER:
            o = d * GN.DAY + GN.DAY - C7.SKY_LEAD - c.n      # live up to the touch, not through it
            break
    return o, total


def apply_live(c, op, o, inputs, fetch=_fetch, verify=True):
    """The seat's step: refuse in the quiet quarter-hour first (cheap), then the beacons, then seat_v07.apply."""
    if op != "wake" and (c.n + o) % GN.DAY >= GN.DAY - C7.SKY_LEAD:
        raise S7.QuietWindow("its quiet quarter-hour before midnight: inputs wait until its midnight has passed")
    sky = S7.assign_sky(c, o, fetch=fetch, verify=verify, wait=True, poll=2.0, max_wait=SKY_MAX_WAIT)
    return S7.apply(c, op, o, inputs, sky)


def _open(seat, now, max_ticks):
    lease = seat.lease()
    try:
        c = C7.load_state(lease["state_blob"])
        if c.n != lease["n_ticks"]:
            raise ValueError(f"blob tick {c.n} != seat n_ticks {lease['n_ticks']}")
        c.ack(seat.log_seq())
        o, total = owed(c, time.time() if now is None else now, max_ticks)
    except Exception:
        seat.release(lease["lease_id"]); raise
    return lease, c, o, total


def _close(seat, lease, c):
    seat.commit(lease["lease_id"], C7.dump_state(c), c.n)
    seat.append_log(c.outbox)


def _now_conversation(seat, now, max_ticks, op, inputs, post=None, fetch=_fetch):
    lease, c, o, total = _open(seat, now, max_ticks)
    if (c.n + total) % GN.DAY >= GN.DAY - C7.SKY_LEAD:          # the true reason first: its quiet quarter-hour
        seat.release(lease["lease_id"])
        raise S7.QuietWindow("its quiet quarter-hour before midnight: inputs wait until its midnight has passed")
    if o < total:
        seat.release(lease["lease_id"])
        raise RuntimeError("too much life owed to converse now (or its touch's round is not out yet) — wake first")
    try:
        out = apply_live(c, op, o, inputs, fetch=fetch)
        if post is not None:
            out = post(c, out)
    except Exception:
        seat.release(lease["lease_id"]); raise
    _close(seat, lease, c)
    return out, c


def wake(seat, now=None, max_ticks=MAX_TICKS_DEFAULT, run_gate=True, log=print, fetch=_fetch):
    if run_gate:
        ok, info = gate()
        log(f"substrate gate: {'PASS' if ok else 'FAIL'} on {info['cpu']}")
        if not ok:
            log("not the certified substrate — declining; elapsed time stays banked."); return "declined"
    if not seat.peek()["alive"]:
        log("seat not initialized — nothing to wake."); return "empty"
    try:
        lease, c, o, total = _open(seat, now, max_ticks)
        try:
            days = C7.touch_ticks(c.n, o)
            entries = apply_live(c, "wake", o, {}, fetch=fetch)
        except Exception:
            seat.release(lease["lease_id"]); raise
    except SeatError as e:
        if e.status == 409:
            log("lease held by another body — standing down (lawful)."); return "stood-down"
        raise
    _close(seat, lease, c)
    log(f"lived {o:,} ticks ({total - o:,} banked) -> n={c.n:,}; diary +{len(entries)}; "
        f"touched by the Sky on days {days} (rounds {[C7.round_of(c.t0, d) for d in days]})")
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
