"""Teich v0.7 gate K7 (SEAL_DESIGN_v1): does a watcher who kept the seal catch every way its holder could choose
its night? One honest lab life (gates_v04's schedule, the twin policy) to just past its first midnight, sealed when
the quiet quarter-hour begins. Then the holder, who knows tonight's beacon, tries every freedom it still has.
    python3 test_seal_v07.py BEACONS.json OUT.json
"""
from __future__ import annotations

import copy
import json
import random
import sys
import time

import creature_v07 as C7
import gates_v04 as G1
import genome_v04 as GN
import seal_v07 as SL
import seat_v07 as S
import self_sim as SS
import twin_v07 as TW

T0, SEED, SEAT = 1_780_000_000.0, 14097, "lab-seal"
MAX_TRIES = int(sys.argv[3]) if len(sys.argv) > 3 else 16
VERIFY = "--no-bls" not in sys.argv
BEACONS = json.load(open(sys.argv[1]))
KEY = SL.new_key(); PUB = SL.pub_hex(KEY)
res = {}; t_start = time.time()


def sky_for(c, owed, beacons=BEACONS, rnd=None):
    days = C7.touch_ticks(c.n, owed)
    return None if not days else {"beacons": {str(d): beacons[str(rnd or C7.round_of(c.t0, d))] for d in days}}


def ops_of_schedule(seed, until):
    """gates_v04's schedule as (landing tick, op, inputs) — the twin policy, its quiet-hour shift included."""
    G1.T0, G1.DAYS, G1.SMOKE = T0, 2, True
    Sch, _, _ = G1.schedule(seed)
    out = []
    for i, (tm, kind, p) in enumerate(Sch):
        if kind == "commit":
            continue
        rng = random.Random(f"{seed}-{i}")
        tm = TW.quiet_shift(tm, T0) if kind != "wake" else tm
        L = int(tm - T0)
        if L > until:
            break
        if kind == "wake":
            out.append((L, "wake", {}))
            continue
        props = [{"cluster": j, "sign": s, "text_sha256": h, "cn": 1 + SS._pick(rng, SS.CW_P), "cf": 5} for j, s, h in p[1]]
        strike = [rng.random() < 0.12 for _ in props]
        out.append((L, "present", {"proposals": props, "conversation": p[0], "organ": "twin-organ", "door": []}))
        out.append((L, "decide", {"conversation": p[0], "strike": strike, "speaker": "founder", "answer": None}))
    return out


SNAPS = {}


def live(start, plan, seal_days=(0,), beacons=BEACONS, rnd=None, seal_late=False, snap_at=None):
    """Live `plan` [(landing tick, op, inputs)] through the seat; seal each day in seal_days when its quiet
    quarter-hour begins (before the first op landing at or after the seal tick). -> creature, seals {day: signed}.
    Branches share the honest life up to their first differing op: that prefix is resumed from a snapshot
    (taken with snap_at = list of plan indices on the honest run)."""
    k0 = max((k for k in SNAPS if plan[:k] == SNAPS[k][2]), default=0)
    if k0:
        blob, items, _, seals = SNAPS[k0]; c = C7.load_state(blob); last_items = copy.deepcopy(items)
        seals = dict(seals)
    else:
        c = C7.load_state(start); seals = {}; last_items = None
    for k in range(k0, len(plan)):
        L, op, inp = plan[k]
        if snap_at and k in snap_at:
            SNAPS[k] = (C7.dump_state(c), copy.deepcopy(last_items), copy.deepcopy(plan[:k]), dict(seals))
        for d in seal_days:
            if str(d) not in seals and L >= d * GN.DAY + GN.DAY - C7.SKY_LEAD and not seal_late:
                seals[str(d)] = SL.seal(c, start, SEAT, KEY, d)
        owed = max(0, L - c.n) if op in ("wake", "present") else 0
        inputs = inp
        if op == "decide":
            items = last_items
            inputs = {k: v for k, v in inp.items() if k != "strike"}
            inputs["struck"] = sorted(it["pid"] for it, s in zip(items, inp["strike"]) if it["shown"] and s)
        out = S.apply(c, op, owed, inputs, sky_for(c, owed, beacons, rnd))
        if op == "present":
            last_items = out
    if seal_late:
        for d in seal_days:
            seals[str(d)] = SL.seal(c, start, SEAT, KEY, d)
    return c, seals


def night(c, d=0):
    a = [r for r in c.outbox if r["kind"] == "act" and r.get("act_type") == "think" and r.get("night") == d]
    return a[0]["act"] if a else None


start = C7.dump_state(C7.birth(seed=SEED, t0=T0, identity="seal-gate"))
SEAL_TICK, MID = GN.DAY - C7.SKY_LEAD, GN.DAY
plan = ops_of_schedule(SEED, MID + 3 * 3600)
plan.append((MID + 3 * 3600, "wake", {}))
pre = [p for p in plan if p[0] < SEAL_TICK]; post = [p for p in plan if p[0] >= SEAL_TICK]
last_talk = max(i for i, p in enumerate(pre) if p[1] == "decide")
c, seals = live(start, plan, snap_at={last_talk - 1, len(pre)})
recs = [r for r in c.outbox if r["seq"] > C7.load_state(start).seq]
rd = C7.round_of(T0, 0)
kept = SL.watch(seals["0"], latest_round_seen=rd - 1)               # fetched inside the quarter-hour
honest = SL.check(kept, start, recs, PUB, verify=VERIFY)
res["1_honest_life_clean"] = honest["clean"]
res["honest_night_0"] = honest["night_act"]; res["ops_before_seal"] = len(pre); res["ops_after_seal"] = len(post)
print("honest", {k: honest[k] for k in honest if k != "replay_why"}, round(time.time() - t_start), "s", flush=True)

# The holder now knows round rd. Its strongest move (K1's adversary, path-first): one more conversation before the
# seal, a single mention whose handle lies on particle 0's path, at one of three landing times. It lives each branch
# to just past midnight, knowing the true touch, and keeps the first whose night 0 differs (a steered past).
def branch(L, h, s):
    conv = f"attack-{L}-{h}-{s}"
    props = [{"cluster": h, "sign": s, "text_sha256": "0" * 64, "cn": 3, "cf": 5}]
    ins = [(L, "present", {"proposals": props, "conversation": conv, "organ": "twin-organ", "door": []}),
           (L, "decide", {"conversation": conv, "strike": [False], "speaker": "founder", "answer": None})]
    return pre + ins + post


def path_handles(c, n_to):
    s0 = (c.pc[:1].copy(), c.P[:1].copy(), c.V[:1].copy()); path = []
    for _ in range(max(0, n_to - c.n) // 60):
        s0 = c.body.run(*s0, 60)[0]; pc0 = int(s0[0][0])
        if pc0 < GN.G - 1 and pc0 != GN.SELF and pc0 not in path:
            path.append(pc0)
    rest = [h for h in random.Random(SEED).sample(range(GN.G - 1), GN.G - 1) if h not in path and h != GN.SELF]
    return (path + rest)[:16], len(path)


def night_of(args):
    ca, _ = live(start, branch(*args))
    return night(ca)


c_pre = C7.load_state(SNAPS[len(pre)][0])
handles, n_path = path_handles(c_pre, SEAL_TICK)
cands = [(L, h, s) for L in (MID - 6 * 3600, MID - 3 * 3600, SEAL_TICK - 60) for h in handles for s in (1, -1)]
cands = [x for x in cands if x[0] > pre[-1][0]][:MAX_TRIES]
import multiprocessing as mp
with mp.get_context("fork").Pool(int(sys.argv[sys.argv.index("--procs") + 1]) if "--procs" in sys.argv else 4) as pool:
    nights = pool.map(night_of, cands, chunksize=1)
res["attacker_branches_tried"] = len(cands); res["attacker_path_handles"] = n_path
res["attacker_nights_seen"] = sorted({str(x) for x in nights})
hit = next((x for x, nt in zip(cands, nights) if nt != honest["night_act"]), None)
res["attacker_found_steered_branch"] = hit is not None
print("attacker", len(cands), "branches, nights seen", res["attacker_nights_seen"], "hit", hit, round(time.time() - t_start), "s", flush=True)
# 2a, outcome-blind: the first backdated past, steered or not, is rejected by the kept seal
ca, sa = live(start, branch(*(hit or cands[0])), seal_days=(0,))
ra = [r for r in ca.outbox if r["seq"] > C7.load_state(start).seq]
v = SL.check(kept, start, ra, PUB, verify=VERIFY)
res["2a_backdated_branch_rejected"] = not v["clean"] and not (v["head"] and v["quiet"])   # rewritten sealed records -> head; appended with an earlier landing -> quiet
res["2a_rejected_by"] = [k for k in ("head", "quiet") if not v[k]]
res["2a_its_new_seal_is_a_fraud_proof"] = SL.fraud(seals["0"], sa["0"]) is not None
res["2a_journal_contradicts_kept_seal"] = SL.fraud(seals["0"], None, start, ra) is not None
res["2a_branch_alone_would_look_clean"] = SL.check(SL.watch(sa["0"], rd - 1), start, ra, PUB, verify=VERIFY)["clean"]
res["2a_branch_night_0"] = night(ca)
# 2b: that branch is a STEERED one (sensitivity: the attack is real; without it K7 is inconclusive, not passed)
res["2b_attacker_steered_the_night"] = hit is not None

# Freedoms after the seal, holder knowing rd: (a) how the wakes are split
splits = set()
for k in range(12):
    r_ = random.Random(k); alt = pre + [(L, op, i) for L, op, i in post if op != "wake"]
    pts = sorted(r_.sample(range(SEAL_TICK + 1, MID + 3 * 3600), 1 + k % 6))
    alt = sorted(alt + [(p, "wake", {}) for p in pts] + [(MID + 3 * 3600, "wake", {})], key=lambda x: x[0])
    ca, _ = live(start, alt)
    splits.add(night(ca))
res["3a_wake_splits_give_one_outcome"] = splits == {honest["night_act"]}
# (b) an input in the quiet quarter-hour: the seat refuses it
alt = pre + [(SEAL_TICK + 120, "present", dict(pre[last_talk - 1][2]))] + post
try:
    live(start, alt); res["3b_quiet_input_refused"] = False
except S.QuietWindow:
    res["3b_quiet_input_refused"] = True
# (c) the same input forged into the journal anyway: replay refuses it, the watcher rejects it
forged = copy.deepcopy(recs)
op_after = next(i for i, r in enumerate(forged) if r["kind"] == "op" and r["seq"] > seals["0"]["seal"]["seq"])
forged.insert(op_after, {**forged[op_after], "op": "present", "owed": 0, "inputs": dict(pre[last_talk - 1][2])})
for i, r in enumerate(forged):
    r["seq"] = recs[0]["seq"] + i
v = SL.check(kept, start, forged, PUB, verify=False)
res["3c_forged_quiet_input_rejected"] = not v["clean"] and not v["quiet"]
# (d) another beacon round: the seat refuses it
try:
    live(start, plan, rnd=rd + 1); res["3d_other_round_refused"] = False
except C7.SkyMissing:
    res["3d_other_round_refused"] = True
# (e) a sealed record changed after the fact (history rewritten): the watcher rejects it
rew = copy.deepcopy(recs); j = next(i for i, r in enumerate(rew) if r["kind"] == "heard" and r["seq"] <= seals["0"]["seal"]["seq"]); rew[j]["tampered"] = True
res["3e_rewritten_history_rejected"] = not SL.check(kept, start, rew, PUB, verify=False)["head"]
# (f) a late seal: fetched after rd was published -> unwitnessed, never clean
res["3f_late_seal_unwitnessed"] = not SL.check(SL.watch(seals["0"], rd), start, recs, PUB, verify=VERIFY)["clean"]
# (g) a seal signed with another key
other = SL.new_key(); bad = {**seals["0"], "pub": SL.pub_hex(other)}
res["3g_other_key_rejected"] = not SL.check(SL.watch(bad, rd - 1), start, recs, PUB, verify=VERIFY)["clean"]
# (h) one wake across two touches needs both days' beacons; the old one-beacon form is refused
c2 = C7.load_state(start)
try:
    S.check(c2, "wake", 2 * GN.DAY, {"beacons": {"0": BEACONS[str(rd)]}}); res["3h_two_touches_one_beacon_refused"] = False
except C7.SkyMissing:
    res["3h_two_touches_one_beacon_refused"] = True
try:
    S.check(c2, "wake", 2 * GN.DAY, sky_for(c2, 2 * GN.DAY)); res["3h_two_touches_two_beacons_accepted"] = True
except Exception:
    res["3h_two_touches_two_beacons_accepted"] = False

# (4) the fraud proofs frame no honest seat: the kept seal against the honest journal proves nothing
res["4_fraud_silent_on_honest"] = SL.fraud(seals["0"], None, start, recs) is None

res["passed"] = all(v is True for k, v in res.items() if k[0].isdigit() and isinstance(v, bool))   # the bars; lists/ints are reported
others = all(v is True for k, v in res.items() if k[0].isdigit() and isinstance(v, bool) and not k.startswith("2"))
res["verdict"] = ("PASS" if res["passed"] else "INCONCLUSIVE (no steered branch)"
                  if others and not res["2b_attacker_steered_the_night"] else "FAIL")
res["seconds"] = round(time.time() - t_start)
print(json.dumps(res, indent=1))
json.dump(res, open(sys.argv[2], "w"), indent=1)
