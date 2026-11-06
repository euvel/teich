"""Teich v0.7 twin lives (PREREG_V07 §1: K2, S, F1, T1'', K4). One lab life is lived twice from the same birth seed,
under the same founder policy (twin_v06's policy, unchanged): by v0.6.0 through seat_v06.apply and by v0.7.0 through
seat_v07.apply. The one schedule change, applied to BOTH twins identically: a conversation that would land in the
v0.7 quiet quarter-hour is moved to 1 tick after that midnight (the founder waits).
Beacons: real historical drand rounds from a verified store. Each life is born at a past wall time T0 = lab_t0(seed),
so day d's beacon is round_of(T0, d) (the Seal's law), long published.
    python3 twin_v07.py SEED DAYS BEACONS.json OUT.json [--side 6|7]
    python3 twin_v07.py rounds SEED DAYS        (the rounds its life needs)
    python3 twin_v07.py merge SIDE6.json SIDE7.json OUT.json
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time

import creature_v06 as C6
import creature_v07 as C7
import gates_v04 as G1
import genome_v04 as GN
import seat_v06 as S6
import seat_v07 as S7
import self_sim as SS

WORDS = ["duduk", "frisson"]


def quiet_shift(tm, t0):
    """The founder waits out its quiet quarter-hour: a conversation in it moves to 1 tick after midnight."""
    k = int(tm - t0)
    return tm + (GN.DAY - k % GN.DAY + 1 if k % GN.DAY >= GN.DAY - C7.SKY_LEAD else 0)


def lab_t0(seed):
    """A past wall-clock birth for each lab life (28 May to 22 Sep 2026), so every day's round is long published."""
    return 1_780_000_000.0 + 3 * GN.DAY * ((seed - 14000) % 40)


def rounds_needed(seed, days):
    return [C7.round_of(lab_t0(seed), d) for d in range(days + 2)]


def life(c, seed, days, v7=False, beacons=None):
    """gates_v04's schedule for `seed`, `days` long, through the twin's seat apply. -> number of ops."""
    G1.DAYS, G1.SMOKE, G1.T0 = days, days < 13, c.t0
    Sch, _, END = G1.schedule(seed)
    ops = 0

    def ap(op, owed, inputs):
        if not v7:
            return S6.apply(c, op, owed, inputs)
        ds = C7.touch_ticks(c.n, owed)
        sky = None if not ds else {"beacons": {str(d): beacons[str(C7.round_of(c.t0, d))] for d in ds}}
        return S7.apply(c, op, owed, inputs, sky)
    for i, (tm, kind, p) in enumerate(Sch):
        if kind == "commit":
            continue
        rng = random.Random(f"{seed}-{i}")
        if kind != "wake":
            tm = quiet_shift(tm, c.t0)
        owed = int(tm - c.t0) - c.n
        if owed < 0:
            owed = 0
        if kind == "wake":
            ap("wake", owed, {}); ops += 1
            continue
        d = int((tm - G1.T0) // 86400)
        q = ap("ask", owed, {}); prop = c.growth["proposal"]
        props = [{"cluster": j, "sign": s, "text_sha256": h, "cn": 1 + SS._pick(rng, SS.CW_P), "cf": 5} for j, s, h in p[1]]
        if q and q["q"][0] == "region":
            for pr in props:
                if int(GN.REGION_OF[pr["cluster"]]) == q["q"][1]:
                    pr["asked"] = q["act_id"]
        strike = [rng.random() < 0.12 for _ in props]
        door = [WORDS[d % 2]] if d < 20 else []
        items = ap("present", 0, {"proposals": props, "conversation": p[0], "organ": "twin-organ", "door": door})
        ans = None
        if q:
            landed = (60 if q["q"] == ["word", "duduk"] else 22) if q["q"][0] == "word" else None
            ans = {"act_id": q["act_id"], "answered": rng.random() < 0.7, "landed": landed}
        struck = sorted(it["pid"] for it, s in zip(items, strike) if it["shown"] and s)
        ap("decide", 0, {"conversation": p[0], "struck": struck, "speaker": "founder", "answer": ans})
        ops += 3
        if prop:
            ap("growth", 0, {"act_id": prop["act_id"], "approved": True, "note": "twin gate"}); ops += 1
    ap("wake", int(END - c.t0) - c.n, {}); ops += 1
    return ops


def side(seed, days, v, beacons):
    """One twin: v = 6 or 7. The two sides are independent processes; merge() joins them."""
    t0 = time.time()
    M = C6 if v == 6 else C7
    start = M.dump_state(M.birth(seed=seed, t0=lab_t0(seed), identity="twin-gate"))
    c = M.load_state(start)
    ops = life(c, seed, days, v7=(v == 7), beacons=beacons)
    return {"seed": seed, "days": days, "t0": lab_t0(seed), f"ops{v}": ops, f"seconds{v}": round(time.time() - t0, 1),
            f"start{v}": start, f"records{v}": c.outbox, f"blob{v}": M.dump_state(c, with_outbox=False),
            f"blob{v}_sha256": hashlib.sha256(M.dump_state(c).encode()).hexdigest()}


def merge(a, b):
    assert (a["seed"], a["days"], a["t0"]) == (b["seed"], b["days"], b["t0"])
    return {**a, **b}


def twins(seed, days, beacons):
    return merge(side(seed, days, 6, beacons), side(seed, days, 7, beacons))


if __name__ == "__main__":
    if sys.argv[1] == "rounds":                    # python3 twin_v07.py rounds SEED DAYS
        print(json.dumps(rounds_needed(int(sys.argv[2]), int(sys.argv[3])))); raise SystemExit
    if sys.argv[1] == "merge":                     # python3 twin_v07.py merge SIDE6.json SIDE7.json OUT.json
        json.dump(merge(json.load(open(sys.argv[2])), json.load(open(sys.argv[3]))), open(sys.argv[4], "w"))
        raise SystemExit
    argv = sys.argv[1:]
    which = [6, 7]
    if "--side" in argv:
        i = argv.index("--side"); which = [int(argv[i + 1])]; argv = argv[:i] + argv[i + 2:]
    a = argv
    seed, days, bpath, out = int(a[0]), int(a[1]), a[2], a[3]
    r = {}
    for v in which:
        r = merge(r, side(seed, days, v, json.load(open(bpath)))) if r else side(seed, days, v, json.load(open(bpath)))
    json.dump(r, open(out, "w"))
    print(json.dumps({k: r[k] for k in r if k.startswith(("seed", "ops", "seconds"))}), flush=True)
