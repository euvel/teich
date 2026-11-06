"""Teich v0.7.0 creature (LAB BUILD, draft spec SKY_AMENDMENT v0): v0.6's creature, unchanged except the declared changes:
  1. the Sky: at tick DAY - SKY_LEAD of every day it lives, its body's particle 0 is touched by the day's beacon number
     b (sky_v07.b_of): P[0,1] += SKY_EPS * (2b - 1), then P[0] back onto the hyperboloid and V[0] back to its tangent
     plane, in the certified + - * / sqrt order of a tick. Every day, tie or not (founder decision S-C);
  2. a day it must touch without its beacon is refused (SkyMissing): no fallback (founder decision S-D);
  3. versions read v0.7.k; blob v7 / species teich-v0.7; migrate() from v0.6, a typed genome-amendment link.
Everything else (deliberation, read-out u, every rule and untied act, dials, heart, Ears, door, laws): v0.6's code."""
from __future__ import annotations

import hashlib
import json
import math

import creature_v06 as C6
import genome_v04 as GN
import sky_v07 as SKY

BLOB_VERSION = 7
SPECIES = "teich-v0.7"
BASE = "0.7"
SKY_LEAD = 900                       # ticks before its midnight
SKY_EPS = 1e-6


class SkyMissing(RuntimeError):
    pass


def touch(P, V, b):
    """The Sky's touch on particle 0. Pure function of (P, V, b); arrays are copied."""
    P = P.copy(); V = V.copy()
    x1 = P[0, 1] + SKY_EPS * (2.0 * b - 1.0); x2 = P[0, 2]
    x0 = math.sqrt(1.0 + x1 * x1 + x2 * x2)
    P[0] = (x0, x1, x2)
    v0, v1, v2 = V[0]
    c = -v0 * x0 + v1 * x1 + v2 * x2                               # <V, P> (Minkowski)
    v0 = v0 + c * x0; v1 = v1 + c * x1; v2 = v2 + c * x2
    r = math.sqrt(-v0 * v0 + v1 * v1 + v2 * v2)
    V[0] = (v0 / r, v1 / r, v2 / r)
    return P, V


def round_of(t0, day):
    """The Seal's law: day d's beacon is the latest drand round at its midnight (wall time t0 + (d+1)·DAY, t0 its
    public birth time). Fixed by its own clock: nobody chooses it, and it is published after that day's seal."""
    return SKY.round_at(t0 + (day + 1) * GN.DAY)


def touch_ticks(n, owed):
    """The life days whose touch tick lies in [n, n + owed) — the touches an advance from n by owed crosses."""
    out = []
    d = n // GN.DAY
    while d * GN.DAY + GN.DAY - SKY_LEAD < n + owed:
        if d * GN.DAY + GN.DAY - SKY_LEAD >= n:
            out.append(d)
        d += 1
    return out


class Creature7(C6.Creature6):

    def advance(self, ticks: int):
        """As v0.6, split at each touch tick; day d's touch needs day d's beacon among those given to this advance
        (self.sky_beacons: {str(day): beacon}; one per day, so an advance may cross several touches)."""
        entries = []
        while ticks > 0:
            to_touch = (GN.DAY - SKY_LEAD - self.n % GN.DAY) % GN.DAY
            day = self.n // GN.DAY
            if to_touch == 0 and self.sky["touched_day"] < day:
                bc = (getattr(self, "sky_beacons", None) or {}).get(str(day))
                if bc is None:
                    raise SkyMissing(f"day {day} must be touched by the Sky and no beacon was given")
                b = SKY.b_of(bc["randomness"], day)
                self.P, self.V = touch(self.P, self.V, b)
                self.sky["touched_day"] = day
                self._emit("sky", {"day": day, "round": int(bc["round"]), "b": float(b).hex(), "tick": int(self.n)})
                to_touch = GN.DAY
            chunk = min(ticks, to_touch if to_touch > 0 else GN.DAY)
            entries += super().advance(chunk)
            ticks -= chunk
        return entries


def _as7(c, sky=None):
    c.__class__ = Creature7
    c.sky = sky if sky is not None else {"touched_day": -1}
    return c


def birth(seed: int, t0: float, identity: str = "lab") -> Creature7:
    """LAB ONLY (twin lives for the gates). The real creature is never born as v0.7: it is migrated (migrate)."""
    c = _as7(C6.birth(seed, t0, identity))
    c.growth.update(version=f"{BASE}.0", base=BASE)
    return c


def dump_state(c: Creature7, with_outbox=True) -> str:
    d = json.loads(C6.dump_state(c, with_outbox))
    d["v"], d["species"], d["sky"] = BLOB_VERSION, SPECIES, c.sky
    return json.dumps(d, sort_keys=True)


def load_state(blob: str) -> Creature7:
    d = json.loads(blob)
    if d.get("v") != BLOB_VERSION or d.get("species") != SPECIES:
        raise ValueError(f"blob {d.get('species')} v{d.get('v')} is not {SPECIES} v{BLOB_VERSION}; refusing to load")
    sky = d.pop("sky")
    d["v"], d["species"] = C6.BLOB_VERSION, C6.SPECIES
    return _as7(C6.load_state(json.dumps(d, sort_keys=True)), sky)


def migrate(blob_v06: str, change: dict) -> str:
    """The one lawful way v0.6 becomes v0.7 (contract §3). change = {"spec_sha256", "anchor", "verdict_sha256"}.
    Refuses while a growth proposal is pending. Every state field is carried unchanged; the identity chain gains a
    typed link; days already lived are never touched (touched_day = the current day if its touch tick has passed)."""
    c = C6.load_state(blob_v06)
    g = c.growth
    if g["proposal"] is not None:
        raise ValueError("a growth proposal is pending: no amendment until the founder has decided it")
    if not g["version"].startswith("0.6."):
        raise ValueError(f"migrate() takes a v0.6 creature, not v{g['version']}")
    doc = {"type": "genome-amendment", "from_version": g["version"], "to_version": f"{BASE}.0",
           "state_before_sha256": hashlib.sha256(blob_v06.encode()).hexdigest(), **change}
    a_sha = hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()
    prev = g["identity"]; ident = hashlib.sha256((prev + a_sha).encode()).hexdigest()
    day = c.n // GN.DAY
    c = _as7(c, {"touched_day": day if c.n % GN.DAY > GN.DAY - SKY_LEAD else day - 1})
    g.update(version=f"{BASE}.0", base=BASE, identity=ident)
    g.setdefault("amendments", []).append({"version": f"{BASE}.0", "amendment_sha": a_sha, "identity": ident})
    c._emit("genome-amendment", {"amendment": doc, "amendment_sha": a_sha, "prev_identity": prev, "identity": ident})
    return dump_state(c)
