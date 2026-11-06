"""Teich v0.4 creature WITH ITS SELF (BUILD candidate, lab only; spec V04_SPEC_part3_self.md).

The part 1–2 creature (creature_v04.py, gated and unchanged) plus the second self (self_v04.py):
  - a conversation is two phases, two seat commits: PRESENT (the second self applies its caution to the Ears'
    proposals and commits its predictions BEFORE the founder sees the read-back) and DECIDE (the founder's strikes;
    the kept mentions are heard by the first self under its laws, exactly as before);
  - at each of its midnights the diary entry gains a `self` block (verdicts, will, comparisons, calibration, facts),
    every claim with a receipt.
With every caution at 0 and no probe, every body / mind / heart effect is that of creature_v04 (gate S8).
Blob v3 = blob v2 + "self".
"""
from __future__ import annotations

import json

import creature_v04 as CR
import genome_v04 as GN
from creature_v04 import diary_entry
from self_v04 import SecondSelf

BLOB_VERSION = 3


class CreatureS(CR.Creature):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.me = SecondSelf()

    def _emit(self, kind, rec):
        super()._emit(kind, rec)
        return self.seq

    def _close_window(self):
        moved = self.win_changed
        keep = ~moved
        self.set_counts = CR.np.where(keep, self.set_counts + self.win_counts, 0)
        self.set_occ = CR.np.where(keep, self.set_occ + self.win_occ, 0)
        self.set_windows = CR.np.where(keep, self.set_windows + 1, 0)
        _, n_tonight = GN.self_read(self.win_counts, self.win_occ)
        lh, n_set = GN.self_read(self.set_counts, self.set_occ)
        day = self.n // GN.DAY - 1
        entry = diary_entry(day, self.n, lh, n_set, self.set_windows, n_tonight, moved, self.heart.k, self.today,
                            self.last_entry, self.body.n)
        # the second self: its speaking (readings) and its night (compare, will, forget, integrate)
        self.me.readings(entry, set(CR.np.nonzero(moved)[0].tolist()), self._emit)
        entry["self"] = self.me.nightly(log_through=self.seq)
        self.last_entry = entry
        self._emit("diary", {"entry": entry})
        self.win_counts[:] = 0; self.win_occ[:] = 0; self.win_changed[:] = False
        self.today = []
        return entry

    # ------------------------------------------------------------------ a conversation, in two phases
    def present(self, proposals, conversation: str, organ: str):
        """proposals: [{"cluster", "sign", "text_sha256", "cn", "cf"}] (cn/cf from self_v04.cw_of on the organ side)."""
        props = [{**p, "cluster": int(p["cluster"]), "kind": int(GN.REGION_OF[int(p["cluster"])])} for p in proposals]
        return self.me.present(props, conversation, self.n // GN.DAY, organ, self._emit)

    def decide(self, conversation: str, struck, speaker: str):
        kept = self.me.decide(conversation, set(struck), self._emit)
        return [(r["pid"],) + self.hear(r["cluster"], r["sign"], {"speaker": speaker, "conversation": conversation,
                                                                    "text_sha256": r["text_sha256"]})
                for r in kept]


def birth(seed: int, t0: float) -> CreatureS:
    c0 = CR.birth(seed, t0)
    return _adopt(c0, SecondSelf())


def _adopt(c0, me):
    c = CreatureS.__new__(CreatureS)
    c.__dict__.update(c0.__dict__)
    c.me = me
    return c


def dump_state(c: CreatureS, with_outbox=True) -> str:
    d = json.loads(CR.dump_state(c, with_outbox))
    d["v"] = BLOB_VERSION
    d["self"] = c.me.to_json()
    return json.dumps(d, sort_keys=True)


def load_state(blob: str) -> CreatureS:
    d = json.loads(blob)
    if d.get("v") != BLOB_VERSION or d.get("species") != CR.SPECIES:
        raise ValueError(f"blob {d.get('species')} v{d.get('v')} is not {CR.SPECIES} v{BLOB_VERSION}; refusing to load")
    me = SecondSelf.from_json(d.pop("self"))
    d["v"] = CR.BLOB_VERSION
    return _adopt(CR.load_state(json.dumps(d, sort_keys=True)), me)
