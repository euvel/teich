"""Teich v0.6 twin lives (spec V06 §5: N0', F1', T1', S). One lab life is lived twice from the same birth, under the same
founder policy: by v0.5 (Creature5) and by v0.6 (Creature6), both through seat_v06.apply (v0.5's twin does not journal).
The founder policy reacts to what the creature delivers (its question, its growth proposal), as the real founder does;
every random draw of the policy is seeded by (seed, event index), so a divergence never desynchronises the twins' worlds.
Commitments have no seat path in v0.5/v0.6 (the founder's tools never commit), so the schedule's commit event is skipped.

v0.6's twin also carries probes for T1' (Probe6: shadow copies of its body's particle 0, never fed back to the life).

    python3 twin_v06.py SEED DAYS OUT.json
    python3 twin_v06.py SEED DAYS OUT.json planted      F1''s planted hidden cause (v0.6 only)
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
import sys
import time

import numpy as np

import creature_v04 as CR
import creature_v05 as C5
import creature_v06 as C6
import delib_cert as DC
import gates_v04 as G1
import genome_v04 as GN
import seat_v06 as S
import self_sim as SS

WORDS = ["duduk", "frisson"]


class Twin5(C5.Creature5):
    """v0.5's creature, unchanged, driven by the same apply(): it does not journal."""

    def _emit(self, kind, rec):
        if kind != "op":
            return super()._emit(kind, rec)


class Probe6(C6.Creature6):
    """v0.6 with T1' probes (never fed back to the life): two shadow copies of its body's particle 0 live every tick
    with it, through the same body (same dials, same moments): one exact (T1e: must equal particle 0 bit for bit) and
    one moved by 1e-12 in P[0,1] at the previous midnight (T1d). At each midnight both are read, then re-seeded."""
    probes = None
    shadow = None

    def _seed(self):
        pc = np.repeat(self.pc[:1], 2); P = np.repeat(self.P[:1], 2, axis=0); V = np.repeat(self.V[:1], 2, axis=0)
        P[1, 1] += 1e-12
        self.shadow = (pc, P, V)

    def advance(self, ticks):
        if self.shadow is None:
            self._seed()
        return super().advance(ticks)

    def _dream(self):
        pc, P, V = self.shadow
        self.probes.append({"night": self.me.night,
                            "lived": DC.u_of(int(self.pc[0]), float(self.P[0, 1]), float(self.V[0, 2])).hex(),
                            "replay": DC.u_of(int(pc[0]), float(P[0, 1]), float(V[0, 2])).hex(),
                            "perturbed": DC.u_of(int(pc[1]), float(P[1, 1]), float(V[1, 2])).hex()})
        self._seed()
        return super()._dream()


def shadowed(c):
    """Run the shadow particles through every body.run the creature makes (the same body object, the same ticks)."""
    run = c.body.run

    def body_run(pc, P, V, ticks):
        out = run(pc, P, V, ticks)
        if c.shadow is not None:
            (spc, sP, sV), *_ = run(*c.shadow, ticks)
            c.shadow = (spc, sP, sV)
        return out
    c.body.run = body_run
    return c


class Hidden6(C6.Creature6):
    """PLANTED CAUSE (F1'): its tie-break secretly reads body particle 1, while the reason logs particle 0's u."""

    def _dream(self):
        import acts_v06 as A
        hidden = DC.u_of(int(self.pc[1]), float(self.P[1, 1]), float(self.V[1, 2])).hex()
        real = A.RULES["think@2"]
        A.RULES["think@2"] = lambda inp: real({**inp, "u": hidden})
        try:
            return super()._dream()
        finally:
            A.RULES["think@2"] = real


def planted(seed, days):
    c = C6.load_state(C6.dump_state(C6.birth(seed=seed, t0=G1.T0, identity="twin-gate"))); c.__class__ = Hidden6
    life(c, seed, days)
    return {"seed": seed, "days": days, "planted": True, "records6": c.outbox}


def life(c, seed, days):
    """Live the lab life (gates_v04's schedule for `seed`, `days` long) through seat_v06.apply. -> number of ops."""
    G1.DAYS, G1.SMOKE = days, days < 13        # short (design) lives: crowd and commit on day 1
    Sch, _, END = G1.schedule(seed)
    ops = 0
    for i, (tm, kind, p) in enumerate(Sch):
        if kind == "commit":
            continue
        rng = random.Random(f"{seed}-{i}")
        owed = int(tm - c.t0) - c.n
        if kind == "wake":
            S.apply(c, "wake", owed, {}); ops += 1
            continue
        d = int((tm - G1.T0) // 86400)
        q = S.apply(c, "ask", owed, {}); prop = c.growth["proposal"]
        props = [{"cluster": j, "sign": s, "text_sha256": h, "cn": 1 + SS._pick(rng, SS.CW_P), "cf": 5} for j, s, h in p[1]]
        if q and q["q"][0] == "region":                # answering its region question tags that region's mentions
            for pr in props:
                if int(GN.REGION_OF[pr["cluster"]]) == q["q"][1]:
                    pr["asked"] = q["act_id"]
        strike = [rng.random() < 0.12 for _ in props]
        door = [WORDS[d % 2]] if d < 20 else []
        items = S.apply(c, "present", 0, {"proposals": props, "conversation": p[0], "organ": "twin-organ", "door": door})
        ans = None
        if q:
            landed = (60 if q["q"] == ["word", "duduk"] else 22) if q["q"][0] == "word" else None
            ans = {"act_id": q["act_id"], "answered": rng.random() < 0.7, "landed": landed}
        struck = sorted(it["pid"] for it, s in zip(items, strike) if it["shown"] and s)
        S.apply(c, "decide", 0, {"conversation": p[0], "struck": struck, "speaker": "founder", "answer": ans})
        ops += 3
        if prop:
            S.apply(c, "growth", 0, {"act_id": prop["act_id"], "approved": True, "note": "twin gate"}); ops += 1
    S.apply(c, "wake", int(END - c.t0) - c.n, {}); ops += 1
    return ops


def twins(seed, days):
    t0 = time.time()
    c5 = C5.load_state(C5.dump_state(C5.birth(seed=seed, t0=G1.T0, identity="twin-gate"))); c5.__class__ = Twin5
    start6 = C6.dump_state(C6.birth(seed=seed, t0=G1.T0, identity="twin-gate"))
    c6 = shadowed(C6.load_state(start6)); c6.__class__ = Probe6; c6.probes = []
    ops5 = life(c5, seed, days); t5 = time.time() - t0
    ops6 = life(c6, seed, days)
    return {"seed": seed, "days": days, "ops": [ops5, ops6], "seconds": [round(t5, 1), round(time.time() - t0 - t5, 1)],
            "start6": start6, "records5": c5.outbox, "records6": c6.outbox, "probes": c6.probes,
            "blob5": C5.dump_state(c5, with_outbox=False), "blob6": C6.dump_state(c6, with_outbox=False),
            "blob6_sha256": hashlib.sha256(C6.dump_state(c6).encode()).hexdigest()}


if __name__ == "__main__":
    seed, days, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    if len(sys.argv) > 4 and sys.argv[4] == "planted":
        json.dump(planted(seed, days), open(out, "w")); print("planted", seed, flush=True); raise SystemExit
    r = twins(seed, days)
    json.dump(r, open(out, "w"))
    print(json.dumps({k: r[k] for k in ("seed", "days", "ops", "seconds")}), len(r["records5"]), len(r["records6"]), flush=True)
