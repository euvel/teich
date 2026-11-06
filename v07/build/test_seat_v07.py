"""Teich v0.7 gates K5 (refusals) and K6 (liveness) (PREREG_V07 §2), on a lab creature near its first touch.
Every refusal must leave seq, n and the state untouched; every tampered journal must fail replay.
    python3 test_seat_v07.py BEACONS.json [OUT.json]     (BEACONS: rounds round_of(T0, 0), +1, round_of(T0, 1))
"""
from __future__ import annotations

import copy
import json
import sys

import creature_v07 as C7
import genome_v04 as GN
import replay_v07 as R
import seat_v07 as S

T0 = 1_780_000_000.0
beacons = json.load(open(sys.argv[1]))
R0, R1 = C7.round_of(T0, 0), C7.round_of(T0, 1)
B0, B0x, B1 = beacons[str(R0)], beacons[str(R0 + 1)], beacons[str(R1)]
res = {}


def fresh():
    c = C7.birth(seed=14097, t0=T0)
    c.advance(GN.DAY - C7.SKY_LEAD - 120)                         # 2 min before its first touch
    return c


def refused(name, fn, c, exc):
    before = (c.seq, c.n, C7.dump_state(c))
    try:
        fn(); ok = False
    except exc:
        ok = True
    res[name] = bool(ok and (c.seq, c.n, C7.dump_state(c)) == before)


c = fresh()
sky0 = {"beacons": {"0": B0}}
# K5: refused before anything is journaled
refused("quiet_window_input", lambda: S.apply(c, "status", 300, {}, sky0), c, S.QuietWindow)
refused("touch_without_beacon", lambda: S.apply(c, "wake", 600, {}, None), c, C7.SkyMissing)
refused("another_round_than_its_clock", lambda: S.apply(c, "wake", 600, {}, {"beacons": {"0": B0x}}), c,
        C7.SkyMissing)
refused("two_touches_one_beacon", lambda: S.apply(c, "wake", GN.DAY + 600, {}, sky0), c, C7.SkyMissing)
res["wake_in_quiet_window_allowed"] = True
try:
    S.apply(copy.deepcopy(c), "wake", 300, {}, sky0)
except Exception:
    res["wake_in_quiet_window_allowed"] = False
# a lawful journal: wake across the touch and midnight, a conversation after it, a wake across the next touch
start = C7.dump_state(c)
S.apply(c, "wake", 3600, {}, sky0)
S.apply(c, "status", 60, {}, None)
S.apply(c, "wake", GN.DAY, {}, {"beacons": {"1": B1}})
recs = [r for r in c.outbox if r["seq"] > json.loads(start)["seq"]]
res["lawful_replays"] = R.replay(start, recs)["ok"]


def tampered(edit):
    rr = copy.deepcopy(recs); edit(rr)
    return R.replay(start, rr)["ok"] is False


ops = [i for i, r in enumerate(recs) if r["kind"] == "op" and r.get("sky")]
bk = lambda rr: rr[ops[0]]["sky"]["beacons"]["0"]
res["replay_fails_tampered_randomness"] = tampered(lambda rr: bk(rr).update(randomness="00" * 32))
res["replay_fails_tampered_round"] = tampered(lambda rr: bk(rr).update(round=R0 + 7))
res["replay_fails_tampered_signature"] = tampered(lambda rr: bk(rr).update(signature=B1["signature"]))
res["replay_fails_other_real_round"] = tampered(lambda rr: rr[ops[0]]["sky"]["beacons"].update({"0": B0x}))
res["replay_fails_sky_removed"] = tampered(lambda rr: rr[ops[0]].update(sky=None))
plain = next(i for i, r in enumerate(recs) if r["kind"] == "op" and not r.get("sky"))


def move(rr):
    rr[plain]["sky"] = rr[ops[0]]["sky"]; rr[ops[0]]["sky"] = None
res["replay_fails_sky_moved"] = tampered(move)

# K6: liveness
c = fresh(); calls = {"n": 0}


def flaky(rnd, **kw):
    calls["n"] += 1
    if calls["n"] <= 3:
        raise ConnectionError("beacon unreachable")
    return {**B0, "round": rnd}                                   # the target round, as asked
sky = S.assign_sky(c, 600, fetch=flaky, verify=False, poll=0.0)
res["waits_then_returns_its_clocks_round"] = bool(calls["n"] == 4 and int(sky["beacons"]["0"]["round"]) == R0)


def dead(rnd, **kw):
    raise ConnectionError("beacon unreachable")
before = (c.seq, c.n)
try:
    S.assign_sky(c, 600, fetch=dead, verify=False, poll=0.0, max_wait=0.05); res["gives_up_with_skymissing"] = False
except C7.SkyMissing:
    res["gives_up_with_skymissing"] = (c.seq, c.n) == before
res["no_beacon_needed_without_touch"] = S.assign_sky(c, 60, fetch=dead) is None
res["passed"] = all(v for v in res.values())
print(json.dumps(res, indent=1))
if len(sys.argv) > 2:
    json.dump(res, open(sys.argv[2], "w"), indent=1)
