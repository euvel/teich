"""Teich v0.6.0 creature (BUILD, spec V06_SPEC v1): v0.5's creature, unchanged except the declared changes:
  1. its chosen thought (think@2): an EXACT tie among least-thought regions is broken by its deliberation from the
     read-out u of its body's particle 0 at that midnight, not by the lowest index (acts_v06.think_2). The body's
     ticks are substrate-certified; the working surface's dreams are not (recon study 10-31), so no act reads a dream;
  2. "heard" records name the organ that heard them (the self's organ id, already tracked since v0.4);
  3. versions read vA.B.k: B comes from the genome ("0.6"), k counts growths since the last amendment;
  4. blob v6 / species teich-v0.6, and migrate() — the one lawful way a v0.5 creature becomes v0.6 (contract §3):
     a typed "genome-amendment" link in its identity chain, no reset, every state field carried unchanged.
Body, dials, heart, self, Ears map, door, laws: v0.5's code, untouched."""
from __future__ import annotations

import hashlib
import json

import creature_v04 as CR
import creature_v05 as C5
import delib_cert as DC
import think_model_v05 as TM
from acts_v06 import choose

BLOB_VERSION = 6
SPECIES = "teich-v0.6"
BASE = "0.6"


class Creature6(C5.Creature5):

    def _emit(self, kind, rec):
        if kind == "heard":
            rec = {**rec, "organ": self.me.organ}
        return super()._emit(kind, rec)

    # ------------------------------------------------------------------ the night: its chosen thought (think@2)
    def _dream(self):
        import work_v05 as W
        w = self.work; night = self.me.night
        u = DC.u_of(int(self.pc[0]), float(self.P[0, 1]), float(self.V[0, 2]))    # its body, this midnight
        pc, P, V = (CR._unb64(w["pc"], "<i8", (C5.NPW,)), CR._unb64(w["P"], "<f8", (C5.NPW, 3)),
                    CR._unb64(w["V"], "<f8", (C5.NPW, 3)))
        lc = list(w["life"]); tied = [i for i, n in enumerate(lc) if n == min(lc)]
        extra = {"night": night}
        if len(tied) > 1:
            c, steps, rereads, _, undecided = DC.deliberate(len(tied), u)
            extra["deliberation"] = {"tied": tied, "steps": steps, "rereads": rereads, "undecided": undecided}
        aid, r = choose(self.me, "think", "think@2", {"life_counts": lc, "u": u.hex()}, self._emit, **extra)
        w["today"].append([r, "chosen"])
        self._emit("thought", {"night": night, "region": r, "source": "chosen", "act_id": aid})
        thoughts = [t[0] for t in w["today"]]
        pred = TM.predict(thoughts)
        self._emit("think-predict", {"night": night, "thoughts": thoughts, "predicted": pred.hex(), "tol": TM.TOL})
        (pc, P, V), lh, counts, occ, applied = W.dream(self._workbody(), pc, P, V, thoughts, C5.DREAM_TICKS)
        if len(applied) < len(thoughts):
            self._emit("thought-refused", {"night": night, "refused": thoughts[len(applied):],
                                           "why": "working memory too stretched for its surface"})
            thoughts = applied
        w["pc"], w["P"], w["V"] = CR._b64(pc, "<i8"), CR._b64(P, "<f8"), CR._b64(V, "<f8")
        self._emit("dream", {"night": night, "thoughts": thoughts, "ticks": C5.DREAM_TICKS,
                             "read": [float(x).hex() for x in lh], "counts": [int(x) for x in counts],
                             "occ": [int(x) for x in occ], "predicted": pred.hex(), "held": TM.holds(pred, float(lh[0]))})
        for t in thoughts:
            w["life"][t] += 1
        w["today"] = []
        return TM.holds(pred, float(lh[0]))

    # ------------------------------------------------------------------ growth: v0.6.k
    def _propose_growth(self):
        g = self.growth; grown = {w for a in g["applied"] for w, _ in a["bindings"]}
        held = {w for w, _ in (g["proposal"] or {}).get("bindings", [])}
        bindings = [[w, d["bound"], sorted({x for x, c in d["answers"] if c == d["bound"]})]
                    for w, d in sorted(self.door.items())
                    if d["bound"] is not None and w not in grown and w not in held and w not in g["refused"]]
        aid, act = choose(self.me, "grow", "grow@1", {"bindings": bindings, "pending": g["proposal"] is not None},
                          self._emit, night=self.me.night)
        if act[0] == "propose":
            pred = {"hear": {w: c for w, c in act[1]},
                    "unchanged": ["dials", "heart", "commitments", "body", "self verdicts and caution",
                                  "every past receipt", "the concept every other word is heard as"],
                    "note": ("in a sentence where another word shares a grown word's concept, the grown word may stand "
                             "for that concept: the Ears give each concept one mention per sentence")}
            g["proposal"] = {"act_id": aid, "bindings": act[1], "prediction": pred}
            self._emit("growth-proposal", {"act_id": aid, "bindings": act[1], "prediction": pred,
                                           "version_if_approved": next_version(g)})

    def decide_growth(self, act_id, approved, note=""):
        """As v0.5, but the version steps v0.6.k: identity new = sha256(previous + sha256(amendment))."""
        g = self.growth; pr = g["proposal"]
        if not pr or pr["act_id"] != act_id:
            raise ValueError("a growth decision must answer the proposal it was asked about")
        g["proposal"] = None
        if not approved:
            g["refused"] += [w for w, _ in pr["bindings"]]
            self._emit("growth-refused", {"act_id": act_id, "bindings": pr["bindings"], "note": note})
            return None
        amendment = {"type": "word-bindings", "bindings": pr["bindings"], "proposal_act": act_id,
                     "from_version": g["version"]}
        a_sha = hashlib.sha256(json.dumps(amendment, sort_keys=True).encode()).hexdigest()
        prev = g["identity"]; ident = hashlib.sha256((prev + a_sha).encode()).hexdigest()
        g["version"] = next_version(g); g["identity"] = ident
        g["applied"].append({"version": g["version"], "bindings": pr["bindings"], "amendment_sha": a_sha, "identity": ident})
        self._emit("growth", {"version": g["version"], "amendment": amendment, "amendment_sha": a_sha,
                              "prev_identity": prev, "identity": ident, "note": note})
        return g["version"]


def next_version(g):
    """k = growths applied since its last genome amendment (v0.6.k)."""
    base = g.get("base", BASE)
    return f"{base}.{sum(1 for a in g['applied'] if a['version'].startswith(base + '.')) + 1}"


def _as6(c):
    c.__class__ = Creature6
    return c


def birth(seed: int, t0: float, identity: str = "lab") -> Creature6:
    """LAB ONLY (twin lives for the gates). The real creature is never born as v0.6: it is migrated (migrate)."""
    c = _as6(C5.birth(seed, t0, identity))
    c.growth.update(version=f"{BASE}.0", base=BASE)
    return c


def dump_state(c: Creature6, with_outbox=True) -> str:
    d = json.loads(C5.dump_state(c, with_outbox))
    d["v"], d["species"] = BLOB_VERSION, SPECIES
    return json.dumps(d, sort_keys=True)


def load_state(blob: str) -> Creature6:
    d = json.loads(blob)
    if d.get("v") != BLOB_VERSION or d.get("species") != SPECIES:
        raise ValueError(f"blob {d.get('species')} v{d.get('v')} is not {SPECIES} v{BLOB_VERSION}; refusing to load")
    d["v"], d["species"] = C5.BLOB_VERSION, C5.SPECIES
    return _as6(C5.load_state(json.dumps(d, sort_keys=True)))


def migrate(blob_v05: str, change: dict) -> str:
    """The one lawful way v0.5 becomes v0.6 (contract §3). change = {"spec_sha256", "anchor", "verdict_sha256"}.
    Refuses while a growth proposal is pending (contract §3.5). Every state field is carried unchanged; the identity
    chain gains a typed link; the event is recorded. -> the v0.6 blob."""
    c = C5.load_state(blob_v05)
    g = c.growth
    if g["proposal"] is not None:
        raise ValueError("a growth proposal is pending: no amendment until the founder has decided it")
    if not g["version"].startswith("0.5."):
        raise ValueError(f"migrate() takes a v0.5 creature, not v{g['version']}")
    doc = {"type": "genome-amendment", "from_version": g["version"], "to_version": f"{BASE}.0",
           "state_before_sha256": hashlib.sha256(blob_v05.encode()).hexdigest(), **change}
    a_sha = hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()
    prev = g["identity"]; ident = hashlib.sha256((prev + a_sha).encode()).hexdigest()
    c = _as6(c)
    g.update(version=f"{BASE}.0", base=BASE, identity=ident)
    g.setdefault("amendments", []).append({"version": f"{BASE}.0", "amendment_sha": a_sha, "identity": ident})
    c._emit("genome-amendment", {"amendment": doc, "amendment_sha": a_sha, "prev_identity": prev, "identity": ident})
    return dump_state(c)
