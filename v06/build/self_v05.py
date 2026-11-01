"""Teich v0.5 — the second self with the act loop (spec V05_SPEC.md §2), step 1.

v0.4's second self (self_v04.SecondSelf) is inherited UNCHANGED and still executes its two choices — whether to probe,
and how much caution — exactly as gated in v0.4. Before each choice, the act loop writes the choice's reason (the
facts) and the act its pure rule computes from those facts alone (acts_v05). The harness then checks every logged act
against what the creature actually did: faithfulness is verified against behaviour, not assumed from the code.
New in v0.5: after each night it decides tomorrow's question (ask@1) or silence; delivering it comes in step 3.
"""
from __future__ import annotations

import acts_v05 as A
from self_v04 import N_G, N_KINDS, PROBE_NEED, PROBES_PER_DAY, RHO_G, RING, SecondSelf, _empty_night, verdict_of, \
    window_counts
from fractions import Fraction

XKINDS = ("BODY-MEMORY", "BODY-PATH", "THINK")      # v0.5: what in itself is knowable, given, emergent
MIN_NIGHTS = 3                                      # a reading is "settled" after this many quiet nights (v0.4)
DOOR_MIN = 2                                        # a word must be heard this many times before it may be asked about


def xverdict(n, miss):
    """No lever on these kinds, so like v0.4's readings: FINE (foreseeable) or GIVEN (not), once N_G predictions."""
    if n < N_G:
        return "UNRESOLVED"
    return "FINE" if Fraction(miss, n) < RHO_G else "GIVEN"


def body_outcomes(pending, tonight, lengths, moved):
    """-> {kind: (n, miss)} for last night's body predictions against tonight's readings (pure; receipts call it)."""
    mm = pm = mn = pn = 0
    for j, pred in pending["memory"].items():
        j = int(j)
        if j in moved or tonight[j] < 0:
            continue
        mn += 1; mm += tonight[j] != pred
    for j, (settled_hex, side) in pending["path"].items():
        j = int(j)
        if j in moved or lengths[j] is None:
            continue
        now = float.fromhex(lengths[j]) - float.fromhex(settled_hex)
        if now == 0.0:
            continue
        pn += 1; pm += (1 if now > 0 else -1) != side
    return {"BODY-MEMORY": (mn, mm), "BODY-PATH": (pn, pm)}


class SecondSelf5(SecondSelf):
    def __init__(self):
        super().__init__()
        self.next_act = 0
        self.pending_question = None        # ["region", k] | ["silence"] — delivered from step 3 on
        self.emit = None                    # set by the creature before nightly(); never stored
        self.xring = {k: [[0, 0] for _ in range(RING)] for k in XKINDS}     # per night: [predictions, misses]
        self.xverdict = {k: "UNRESOLVED" for k in XKINDS}
        self.pending_body = None            # last night's body predictions, judged tonight
        self.tonight = None                 # transient: (tonight readings, lengths, moved) handed over by the first self
        self.think_held = None              # transient: did tonight's thinking prediction hold
        self.door_view = []                 # transient: [[word, count, answer_days]] handed over by the first self
        self.asked_pids = []                # mentions heard in answer to its own question (tagged "asked")
        self.hearing = {"asked": [0, 0], "free": [0, 0]}   # [shown and decided, struck]: asked vs free hearing

    def to_json(self):
        return {**super().to_json(), "next_act": self.next_act, "pending_question": self.pending_question,
                "xring": self.xring, "xverdict": self.xverdict, "pending_body": self.pending_body,
                "asked_pids": self.asked_pids, "hearing": self.hearing}

    @classmethod
    def from_json(cls, d):
        d = dict(d)
        na, pq = d.pop("next_act"), d.pop("pending_question")
        xr, xv, pb = d.pop("xring"), d.pop("xverdict"), d.pop("pending_body")
        ap, hg = d.pop("asked_pids"), d.pop("hearing")
        s = cls(); base = SecondSelf.from_json(d)
        s.__dict__.update(base.__dict__); s.next_act, s.pending_question, s.emit = na, pq, None
        s.xring, s.xverdict, s.pending_body, s.tonight, s.think_held = xr, xv, pb, None, None
        s.door_view, s.asked_pids, s.hearing = [], ap, hg
        return s

    # ---------------------------------------------------------------- probe: reason first, v0.4 executes
    def present(self, proposals, conversation, day, organ, emit):
        if organ != self.organ:                 # identical pre-steps to v0.4 (idempotent when v0.4 repeats them)
            if self.organ is not None:
                for k in range(N_KINDS):
                    self.ring[k] = [_empty_night() for _ in range(RING)]; self.W[k] = RING
                    self.verdict[k] = "UNRESOLVED"; self.caution[k] = 0
            self.organ = organ
        if day != self.probe_day:
            self.probe_day, self.probes_used = day, 0
        ws = self._windows()
        hidden = [[ws[p["kind"]]["lv"][self.caution[p["kind"]] - 1][0], p["kind"], i, self.verdict[p["kind"]]]
                  for i, p in enumerate(proposals) if min(p["cn"], p["cf"]) <= self.caution[p["kind"]]]
        if hidden:
            A.choose(self, "probe", "probe@1",
                     {"budget_left": PROBES_PER_DAY - self.probes_used, "probe_need": PROBE_NEED, "hidden": hidden},
                     emit, pid_base=self.next_pid, n=len(proposals), conversation=conversation)
        base = self.next_pid
        items = super().present(proposals, conversation, day, organ, emit)
        for i, p in enumerate(proposals):
            if p.get("asked") and items[i]["shown"]:
                self.asked_pids.append(base + i)
                emit("asked", {"pid": base + i, "act_id": p["asked"]})
        return items

    def decide(self, conversation, struck, emit):
        mine = {k for k, v in self.pending.items() if v["conversation"] == conversation}
        kept = super().decide(conversation, struck, emit)
        for pid in sorted(mine):
            side = "asked" if pid in self.asked_pids else "free"
            self.hearing[side][0] += 1; self.hearing[side][1] += pid in struck
        self.asked_pids = [p for p in self.asked_pids if p not in mine]
        return kept

    # ---------------------------------------------------------------- caution: reason first, v0.4 executes; then ask
    def nightly(self, log_through):
        emit = self.emit
        d = self.night
        for k in range(N_KINDS):
            w = window_counts(self._window(k, d)); v = verdict_of(w, k); c = self.caution[k]
            if v == "MINE" or c > 0:            # will_of can only change caution in these states
                A.choose(self, "caution", "caution@1", {"kind": k, "lv": w["lv"], "verdict": v, "c": c}, emit, night=d)
        x = self._xnight(d, log_through)
        block = super().nightly(log_through)
        block["self5"] = x
        ws = self._windows()
        aid, q = A.choose(self, "ask", "ask@2",
                          {"n_g": N_G, "door_min": DOOR_MIN,
                           "unresolved": [[k, ws[k]["n_lo"], ws[k]["n_hi"]]
                                          for k in range(N_KINDS) if self.verdict[k] == "UNRESOLVED"],
                           "door": [list(x) for x in self.door_view]},
                          emit, night=d)
        self.pending_question = {"act_id": aid, "q": q}
        block["self5"]["hearing"] = {k: list(v) for k, v in self.hearing.items()}
        return block

    # ---------------------------------------------------------------- v0.5 kinds: knowable, given, emergent
    def _xnight(self, d, log_through):
        slot = d % RING
        for k in XKINDS:
            self.xring[k][slot] = [0, 0]
        if self.pending_body is not None and self.tonight is not None:
            tonight, lengths, moved = self.tonight
            for k, (n, m) in body_outcomes(self.pending_body, tonight, lengths, set(moved)).items():
                self.xring[k][slot] = [n, m]
        if self.think_held is not None:
            self.xring["THINK"][slot] = [1, 0 if self.think_held else 1]
        out = {"night": d, "kinds": {}, "changes": []}
        a = max(0, d - RING + 1)
        for k in XKINDS:
            n = sum(self.xring[k][x % RING][0] for x in range(a, d + 1))
            m = sum(self.xring[k][x % RING][1] for x in range(a, d + 1))
            v = xverdict(n, m)
            out["kinds"][k] = {"verdict": v, "n": n, "miss": m,
                               "receipt": {"log_through": log_through, "select": {"kind": k, "nights": [a, d]},
                                           "fn": "self_v5.xverdict", "out": {"n": n, "miss": m, "verdict": v}}}
            if v != self.xverdict[k]:
                out["changes"].append({"kind": k, "from": self.xverdict[k], "to": v,
                                       "wrong_about_myself": self.xverdict[k] != "UNRESOLVED"})
            self.xverdict[k] = v
        self.tonight = self.think_held = None
        return out

    def body_predict(self, night, n_set, windows, lengths_tonight, lengths_set, moved, emit):
        """After the night: predict the NEXT night's readings from records the first self handed over.
        memory: tonight-of-next-night rounded reading = the settled reading;  path: the side of the settled length the
        next single night falls on = the side it fell on tonight (the best a cheap model can do if paths had memory)."""
        mem, path = {}, {}
        for j in range(len(n_set)):
            if windows[j] >= MIN_NIGHTS and n_set[j] >= 0 and j not in moved:
                mem[str(j)] = int(n_set[j])
                if lengths_tonight[j] is not None and lengths_set[j] is not None:
                    side = float.fromhex(lengths_tonight[j]) - float.fromhex(lengths_set[j])
                    if side != 0.0:
                        path[str(j)] = [lengths_set[j], 1 if side > 0 else -1]
        self.pending_body = {"for_night": night, "memory": mem, "path": path}
        emit("body-predict", self.pending_body)
