"""Teich v0.7 seat paths (LAB BUILD): v0.6's seat paths and public journal for creature_v07, plus the Sky and the Seal.

The op record gains "sky": {"beacons": {str(day): beacon}} for every touch day d the life it owes crosses, or null.
Day d's beacon must be round creature_v07.round_of(t0, d), the latest drand round at its midnight, fixed by its own
public clock (nobody chooses it). Laws, all checked before anything is journaled:
  - an advance that crosses a touch without that day's beacon, or with another round, is refused (no fallback);
  - the quiet quarter-hour: an operation other than "wake" that would land its inputs in the last SKY_LEAD ticks
    before its midnight is refused. Day d's SEAL (seal_v07) is published when that quarter-hour begins: it commits
    the journal through its last record, so nothing that decides tonight can change after it.
"""
from __future__ import annotations

import time

import creature_v07 as C7
import genome_v04 as GN
import sky_v07 as SKY


class QuietWindow(RuntimeError):
    pass


def check(c, op, owed, sky):
    """The Sky's laws, before journaling. Raises; returns nothing."""
    if op != "wake" and (c.n + owed) % GN.DAY >= GN.DAY - C7.SKY_LEAD:
        raise QuietWindow("its quiet quarter-hour before midnight: inputs wait until its midnight has passed")
    days = C7.touch_ticks(c.n, owed)
    given = (sky or {}).get("beacons") or {}
    if sorted(given, key=int) != [str(d) for d in days]:
        raise C7.SkyMissing(f"this life crosses the touches of days {days}; beacons were given for {sorted(given)}")
    for d in days:
        if int(given[str(d)]["round"]) != C7.round_of(c.t0, d):
            raise C7.SkyMissing(f"day {d}'s beacon must be round {C7.round_of(c.t0, d)}, not {given[str(d)]['round']}")


def apply(c, op, owed, inputs, sky=None):
    """Journal, live what is owed (touched by the Sky), then perform the operation. ONE code path for seat and replay.
    sky: None or {"beacons": {str(day): beacon}}."""
    check(c, op, owed, sky)
    c._emit("op", {"op": op, "n": c.n, "owed": owed, "inputs": inputs, "sky": sky})
    c.sky_beacons = None if sky is None else sky["beacons"]
    try:
        entries = c.advance(owed)
    finally:
        c.sky_beacons = None
    if op == "wake":
        return entries
    return _perform(c, op, inputs)


def _perform(c, op, inputs):
    """v0.6's operations after the advance (seat_v06.apply without its journal and advance)."""
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


def assign_sky(c, owed, fetch=SKY.fetch, verify=True, wait=True, poll=2.0, max_wait=600, **kw):
    """The seat's step: for each touch day the owed life crosses, fetch round_of(t0, day), waiting for it to be
    published (no fallback), and verify it. -> sky dict or None."""
    days = C7.touch_ticks(c.n, owed)
    if not days:
        return None
    out = {}; t0 = time.time()
    for d in days:
        target = C7.round_of(c.t0, d)
        while True:
            try:
                b = fetch(target, **kw)
                break
            except Exception:
                if not wait or time.time() - t0 > max_wait:
                    raise C7.SkyMissing(f"beacon round {target} not available; nothing lived, nothing journaled")
                time.sleep(poll)
        if int(b["round"]) != target or (verify and not SKY.verify(b)):
            raise C7.SkyMissing(f"beacon round {target} failed verification")
        out[str(d)] = b
    return {"beacons": out}
