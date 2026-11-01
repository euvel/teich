"""Teich v0.5 creature (BUILD): v0.4's creature with its self running the act loop (step 1), and thinking on a
working-memory surface (step 2).

Thinking: after each conversation it rehearses the regions of what it kept, in the order heard (at most MAX_THOUGHTS-1
a day); at its midnight it chooses one thought (act loop, think@1), writes its order-blind prediction of what its
working memory will read (think_model_v05), dreams the day's thoughts on the working surface (work_v05), records the
reading and whether its prediction held, and resets. Long-term memory (the 98 dials) is never touched by thinking.
Blob v5 = blob v3 (creature_v04s) + the self's act-loop fields + "work" (working particles, today's thoughts, counts).
"""
from __future__ import annotations

import hashlib
import json

import creature_v04 as CR
import creature_v04s as CS
import genome_v04 as GN
import think_model_v05 as TM
from acts_v05 import choose
from self_v05 import SecondSelf5

BLOB_VERSION = 5
SPECIES = "teich-v0.5"
NPW = 256                      # working thoughts
DREAM_TICKS = 40_000           # design D2: one dream's noise ~0.35% of the reading at this length


class Creature5(CS.CreatureS):
    work = None                # {"pc", "P", "V", "today": [[region, source], ...], "life": [9 ints]}
    door = None                # {word: {"count": n, "answers": [[day, cluster], ...], "bound": cluster | None}}
    growth = None              # {"version", "identity", "applied": [...], "proposal": {...} | None, "refused": [words]}
    thinking = True            # gate O2's twin turns this off; the creature itself never does
    _wb = None

    def _workbody(self):
        if Creature5._wb is None:
            import work_v05 as W
            Creature5._wb = W.WorkBody()
        return Creature5._wb

    # ------------------------------------------------------------------ rehearsal: what it kept, in the order heard
    def decide(self, conversation, struck, speaker):
        before = self.seq
        out = super().decide(conversation, struck, speaker)
        if self.thinking:
            for r in [r for r in self.outbox if r["seq"] > before and r["kind"] == "heard"]:
                if len(self.work["today"]) < TM_MAX_REHEARSAL:
                    region = int(GN.REGION_OF[r["cluster"]])
                    self.work["today"].append([region, "rehearsal"])
                    self._emit("thought", {"night": self.me.night, "region": region, "source": "rehearsal",
                                           "conversation": conversation})
        return out

    # ------------------------------------------------------------------ the door and its questions
    def door_heard(self, words):
        """Unheard nouns from the Ears — single lemmas only, never sentences (founder decision D2)."""
        for w in words:
            d = self.door.setdefault(w, {"count": 0, "answers": [], "bound": None})
            d["count"] += 1
            self._emit("door", {"word": w, "count": d["count"]})

    def deliver_question(self):
        """-> its chosen question {"act_id", "q"} or None. The same question may be asked in up to QUESTIONS_PER_DAY
        conversations a day (founder D3: at most 3; design Q1 10-22: 1 a day is too few to matter), until its night.
        Every delivery is recorded so live verify can check it against the ask act."""
        pq = self.me.pending_question
        if not pq or pq["q"][0] == "silence":
            return None
        day = self.n // GN.DAY
        if pq.get("day") != day:
            pq["day"], pq["delivered"] = day, 0
        if pq["delivered"] >= QUESTIONS_PER_DAY:
            return None
        pq["delivered"] += 1
        self._emit("ask-delivered", {"act_id": pq["act_id"], "q": pq["q"], "night": self.me.night, "nth": pq["delivered"]})
        return {"act_id": pq["act_id"], "q": pq["q"]}

    def answer(self, act_id, answered, landed_cluster=None):
        """The founder's reply to its question. For a door word, where the answer landed is a candidate binding;
        two answers on different days that agree bind the word (step 4 turns bindings into growth proposals)."""
        pq = self.me.pending_question
        if not pq or pq["act_id"] != act_id:
            raise ValueError("an answer must belong to the question it was asked")
        self._emit("answer", {"act_id": act_id, "answered": bool(answered), "landed": landed_cluster})
        q = pq["q"]
        if answered and q[0] == "word" and landed_cluster is not None:
            d = self.door[q[1]]; day = self.n // GN.DAY
            d["answers"].append([day, int(landed_cluster)])
            agree = {dd for dd, c in d["answers"] if c == int(landed_cluster)}
            if len(agree) >= 2 and d["bound"] is None:
                d["bound"] = int(landed_cluster)
                self._emit("binding", {"word": q[1], "cluster": int(landed_cluster), "days": sorted(agree)})

    # ------------------------------------------------------------------ growth as numbered versions (v0.5.x)
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
        """The founder approves or refuses its proposal. Approved: the Ears' map gains the bound words, the version
        steps (0.5.k) and the identity chains: new = sha256(previous + sha256(amendment)). Nothing else changes."""
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

    def ears_map(self):
        """The organ's map additions from every applied growth: {word: cluster}."""
        return {w: c for a in self.growth["applied"] for w, c in a["bindings"]}

    # ------------------------------------------------------------------ the night: choose, predict, dream, reset
    def _close_window(self):
        self.me.emit = self._emit
        self.me.door_view = [[w, d["count"], len({x for x, _ in d["answers"]})]
                             for w, d in sorted(self.door.items()) if d["bound"] is None]
        if self.thinking:
            self.me.think_held = self._dream()
        # the first self hands its own readings to the record; its second self judges last night's predictions on them
        self._propose_growth()
        lh_t, n_t = GN.self_read(self.win_counts, self.win_occ)
        moved = [int(j) for j in CR.np.nonzero(self.win_changed)[0]]
        hexes = lambda a: [None if not CR.np.isfinite(x) else float(x).hex() for x in a]  # noqa: E731
        tonight = [int(x) for x in n_t]; lengths = hexes(lh_t)
        self._emit("night-reading", {"night": self.me.night, "tonight": tonight, "lengths": lengths, "moved": moved})
        self.me.tonight = (tonight, lengths, moved)
        night = self.me.night
        entry = super()._close_window()
        lh_s, n_s = GN.self_read(self.set_counts, self.set_occ)
        self.me.body_predict(night + 1, [int(x) for x in n_s], [int(x) for x in self.set_windows], lengths, hexes(lh_s),
                             set(moved), self._emit)
        return entry

    def _dream(self):
        import work_v05 as W
        w = self.work; night = self.me.night
        aid, r = choose(self.me, "think", "think@1", {"life_counts": list(w["life"])}, self._emit, night=night)
        w["today"].append([r, "chosen"])
        self._emit("thought", {"night": night, "region": r, "source": "chosen", "act_id": aid})
        thoughts = [t[0] for t in w["today"]]
        pred = TM.predict(thoughts)
        self._emit("think-predict", {"night": night, "thoughts": thoughts, "predicted": pred.hex(), "tol": TM.TOL})
        pc, P, V = (CR._unb64(w["pc"], "<i8", (NPW,)), CR._unb64(w["P"], "<f8", (NPW, 3)), CR._unb64(w["V"], "<f8", (NPW, 3)))
        (pc, P, V), lh, counts, occ, applied = W.dream(self._workbody(), pc, P, V, thoughts, DREAM_TICKS)
        if len(applied) < len(thoughts):              # the law: a too-stretched day refuses its last thoughts
            self._emit("thought-refused", {"night": night, "refused": thoughts[len(applied):],
                                           "why": "working memory too stretched for its surface"})
            thoughts = applied
        w["pc"], w["P"], w["V"] = CR._b64(pc, "<i8"), CR._b64(P, "<f8"), CR._b64(V, "<f8")
        self._emit("dream", {"night": night, "thoughts": thoughts, "ticks": DREAM_TICKS,
                             "read": [float(x).hex() for x in lh], "counts": [int(x) for x in counts],
                             "occ": [int(x) for x in occ], "predicted": pred.hex(), "held": TM.holds(pred, float(lh[0]))})
        for t in thoughts:
            w["life"][t] += 1
        w["today"] = []
        return TM.holds(pred, float(lh[0]))


TM_MAX_REHEARSAL = 11          # one slot of the day's 12 is kept for its own chosen thought
QUESTIONS_PER_DAY = 3          # founder D3 (at most 3); design Q1 10-22


def next_version(g):
    return f"0.5.{len(g['applied']) + 1}"


def _adopt(c0, me, work, door=None, growth=None):
    c = Creature5.__new__(Creature5)
    c.__dict__.update(c0.__dict__)
    c.me, c.work, c.door = me, work, ({} if door is None else door)
    c.growth = growth
    return c


def birth(seed: int, t0: float, identity: str = "lab") -> Creature5:
    import work_v05 as W
    pc, P, V = W.WorkBody().start(NPW, seed + 1)
    work = {"pc": CR._b64(pc, "<i8"), "P": CR._b64(P, "<f8"), "V": CR._b64(V, "<f8"), "today": [], "life": [0] * 9}
    growth = {"version": "0.5.0", "identity": identity, "applied": [], "proposal": None, "refused": []}
    return _adopt(CR.birth(seed, t0), SecondSelf5(), work, None, growth)


def dump_state(c: Creature5, with_outbox=True) -> str:
    d = json.loads(CR.dump_state(c, with_outbox))
    d["v"], d["species"], d["self"], d["work"], d["door"] = BLOB_VERSION, SPECIES, c.me.to_json(), c.work, c.door
    d["growth"] = c.growth
    return json.dumps(d, sort_keys=True)


def load_state(blob: str) -> Creature5:
    d = json.loads(blob)
    if d.get("v") != BLOB_VERSION or d.get("species") != SPECIES:
        raise ValueError(f"blob {d.get('species')} v{d.get('v')} is not {SPECIES} v{BLOB_VERSION}; refusing to load")
    me = SecondSelf5.from_json(d.pop("self")); work = d.pop("work"); door = d.pop("door"); growth = d.pop("growth")
    d["v"], d["species"] = CR.BLOB_VERSION, CR.SPECIES
    return _adopt(CR.load_state(json.dumps(d, sort_keys=True)), me, work, door, growth)
