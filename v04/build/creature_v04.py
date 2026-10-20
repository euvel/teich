"""Teich v0.4 creature and blob (BUILD candidate, lab only).

One definition of what a v0.4 commit contains, used by the birth, the wake, the conversation path and the gate:

    dials        98 integers in 0..N_MAX: its mind's memory (attention per cluster). Geometry is derived from them.
    pc, P, V     its 2,048 thoughts (piece, position, velocity), raw little-endian bytes, base64 — exact
    heart        v0.3's ledger (9 integers in 0..6) + today's bounds
    mind         committed dials + today's bounds and speed count
    win          crossings and ticks per handle in the current day window (integers)
    settled      the same, pooled over complete windows since that dial last changed — its settled self-reading
    today        what it heard today (cluster, outcome) — for tonight's diary entry, cleared at its midnight
    last_entry   the last attention-diary entry it wrote
    outbox, seq  closed records not yet acknowledged by the seat's log (every heard mention, every diary entry);
                 the seat acknowledges a sequence number and the creature drops what it has handed over, so the blob
                 keeps a constant size however long it lives
    n, t0        its own clock (ticks lived) and the wall-clock second it is counted from

Laws (each request is logged with its reason; text is never stored, only its sha256):
  mind (founder decision 10-04: a dial means ATTENTION): every mention the Ears route to a cluster asks for +1 on that
  dial; refused if the dial is committed, if that cluster already moved in this conversation today, if the day's speed
  limit (CAP steps, all speakers) is used up, or at the edge (N_MAX).
  heart (v0.3's law + founder decision 10-05): one step per region per conversation, at most one step per region per
  day, refusals at the edges.
  Bounds are kept for the current day of its life only; at its midnight every conversation's bounds close.
"""
from __future__ import annotations

import base64
import hashlib
import json

import numpy as np

import genome_v04 as GN

BLOB_VERSION = 2
SPECIES = "teich-v0.4"
CAP = 12                     # speed limit: accepted dial steps per day of its life, all speakers combined
TOP = 5                      # diary: clusters named as "attending most to"
MIN_NIGHTS = 3               # diary: a reading is spoken after this many quiet nights since the dial moved


def _b64(a, dt):
    return base64.b64encode(np.ascontiguousarray(a).astype(dt).tobytes()).decode()


def _unb64(s, dt, shape):
    return np.frombuffer(base64.b64decode(s), dtype=dt).reshape(shape).astype(np.float64 if dt == "<f8" else np.int64)


class Creature:
    def __init__(self, body: GN.Body, pc, P, V):
        g = body.g
        self.body, self.pc, self.P, self.V = body, pc, P, V
        self.heart = GN.Heart()
        self.frozen = []                                 # [{"cluster": j, **provenance}]
        self.mind_steps = set()                          # (conversation, cluster), today
        self.speed_day, self.speed_used = 0, 0
        self.today = []                                  # [{"cluster": j, "why": ...}], today
        self.win_counts = np.zeros(g, np.int64); self.win_occ = np.zeros(g, np.int64)
        self.win_changed = np.zeros(g, bool)
        self.set_counts = np.zeros(g, np.int64); self.set_occ = np.zeros(g, np.int64)
        self.set_windows = np.zeros(g, np.int64)
        self.last_entry = None
        self.outbox, self.seq = [], 0
        self.n, self.t0 = 0, 0.0

    def _emit(self, kind, rec):
        self.seq += 1
        self.outbox.append({"seq": self.seq, "kind": kind, **rec})

    def ack(self, seq_through: int):
        """The seat's log holds every record up to seq_through: drop them from the blob."""
        self.outbox = [e for e in self.outbox if e["seq"] > seq_through]

    # ------------------------------------------------------------------ living
    def advance(self, ticks: int):
        """Live `ticks` seconds. Day windows are aligned to its own clock; each closed window yields a diary entry."""
        entries = []
        while ticks > 0:
            chunk = min(ticks, GN.DAY - self.n % GN.DAY)
            (self.pc, self.P, self.V), c, o, _ = self.body.run(self.pc, self.P, self.V, chunk)
            self.win_counts += c; self.win_occ += o
            self.n += chunk; ticks -= chunk
            if self.n % GN.DAY == 0:
                entries.append(self._close_window())
        return entries

    def _close_window(self):
        moved = self.win_changed
        keep = ~moved
        self.set_counts = np.where(keep, self.set_counts + self.win_counts, 0)
        self.set_occ = np.where(keep, self.set_occ + self.win_occ, 0)
        self.set_windows = np.where(keep, self.set_windows + 1, 0)
        _, n_tonight = GN.self_read(self.win_counts, self.win_occ)
        lh, n_set = GN.self_read(self.set_counts, self.set_occ)
        day = self.n // GN.DAY - 1
        entry = diary_entry(day, self.n, lh, n_set, self.set_windows, n_tonight, moved, self.heart.k, self.today,
                            self.last_entry, self.body.n)
        self.last_entry = entry
        self._emit("diary", {"entry": entry})
        self.win_counts[:] = 0; self.win_occ[:] = 0; self.win_changed[:] = False
        self.today = []
        return entry

    def _new_day(self, day):
        if day != self.speed_day:
            self.speed_day, self.speed_used, self.mind_steps = day, 0, set()

    # ------------------------------------------------------------------ hearing (the Ears' output, one mention)
    def hear(self, cluster: int, sign: int, provenance: dict):
        prov = {**provenance, "tick": int(self.n)}
        need = {"speaker", "conversation", "text_sha256"}
        if not need <= set(prov):
            raise ValueError("a mention without full provenance cannot touch memory")
        day = self.n // GN.DAY
        self._new_day(day)
        j = int(cluster); region = int(GN.REGION_OF[j])
        heart_ok, heart_why = self.heart.event(region, sign, prov["conversation"], day)
        key = (prov["conversation"], j)
        if any(f["cluster"] == j for f in self.frozen):
            why = "refused: committed"
        elif key in self.mind_steps:
            why = "refused: one step per cluster per conversation"
        elif self.speed_used >= CAP:
            why = "refused: daily speed limit"
        elif self.body.n[j] + 1 > GN.N_MAX:
            why = "refused: edge"
        else:
            why = "accepted"
            self.body.set_dial(j, int(self.body.n[j]) + 1)
            self.mind_steps.add(key); self.speed_used += 1; self.win_changed[j] = True
        self.today.append({"cluster": j, "why": why})
        self._emit("heard", {"cluster": j, "mind": why, "region": GN.REGIONS[region], "sign": int(np.sign(sign)),
                             "heart": heart_why, **prov})
        return heart_ok, why == "accepted"

    def commit(self, cluster: int, provenance: dict, authority: str):
        if authority != "lawful":
            raise PermissionError("commitments are written only through the lawful procedure")
        rec = {"cluster": int(cluster), **provenance, "tick": int(self.n)}
        self.frozen.append(rec)
        self._emit("commitment", rec)


def birth(seed: int, t0: float) -> Creature:
    body = GN.Body()
    pc, P, V = body.start(GN.NP, seed)
    c = Creature(body, pc, P, V)
    c.t0 = float(t0)
    return c


def dump_state(c: Creature, with_outbox=True) -> str:
    H = c.heart
    d = {
        "v": BLOB_VERSION, "species": SPECIES, "table_sha256": GN.TABLE_SHA, "vocab_sha256": GN.VOCAB_SHA,
        "dials": [int(v) for v in c.body.n],
        "pc": _b64(c.pc, "<i8"), "P": _b64(c.P, "<f8"), "V": _b64(c.V, "<f8"),
        "heart": {"k": [int(v) for v in H.k], "day": int(H.day), "day_used": sorted(int(r) for r in H.day_used),
                  "steps": [[conv, int(r), int(u)] for (conv, r), u in sorted(H.steps.items(), key=str)]},
        "mind": {"frozen": c.frozen, "steps": sorted([[conv, int(j)] for conv, j in c.mind_steps], key=str),
                 "speed_day": int(c.speed_day), "speed_used": int(c.speed_used)},
        "today": c.today,
        "win": {"counts": c.win_counts.tolist(), "occ": c.win_occ.tolist(), "changed": c.win_changed.astype(int).tolist()},
        "settled": {"counts": c.set_counts.tolist(), "occ": c.set_occ.tolist(), "windows": c.set_windows.tolist()},
        "last_entry": c.last_entry, "seq": int(c.seq),
        "n": int(c.n), "t0": float(c.t0),
    }
    if with_outbox:
        d["outbox"] = c.outbox
    return json.dumps(d, sort_keys=True)


def load_state(blob: str) -> Creature:
    d = json.loads(blob)
    if d.get("v") != BLOB_VERSION or d.get("species") != SPECIES:
        raise ValueError(f"blob {d.get('species')} v{d.get('v')} is not {SPECIES} v{BLOB_VERSION}; refusing to load")
    if d["table_sha256"] != GN.TABLE_SHA or d["vocab_sha256"] != GN.VOCAB_SHA:
        raise ValueError("blob was lived under a different genome (geometry table or vocabulary); refusing to load")
    body = GN.Body()
    for j, n in enumerate(d["dials"]):
        if n:
            body.set_dial(j, int(n))
    m = GN.NP
    c = Creature(body, _unb64(d["pc"], "<i8", (m,)), _unb64(d["P"], "<f8", (m, 3)), _unb64(d["V"], "<f8", (m, 3)))
    c.heart.k = np.array(d["heart"]["k"], dtype=np.int64)
    c.heart.day, c.heart.day_used = int(d["heart"]["day"]), set(d["heart"]["day_used"])
    c.heart.steps = {(conv, r): u for conv, r, u in d["heart"]["steps"]}
    c.frozen = list(d["mind"]["frozen"])
    c.mind_steps = {(conv, j) for conv, j in d["mind"]["steps"]}
    c.speed_day, c.speed_used = int(d["mind"]["speed_day"]), int(d["mind"]["speed_used"])
    c.today = list(d["today"])
    c.win_counts = np.array(d["win"]["counts"], np.int64); c.win_occ = np.array(d["win"]["occ"], np.int64)
    c.win_changed = np.array(d["win"]["changed"], bool)
    c.set_counts = np.array(d["settled"]["counts"], np.int64); c.set_occ = np.array(d["settled"]["occ"], np.int64)
    c.set_windows = np.array(d["settled"]["windows"], np.int64)
    c.last_entry = d["last_entry"]; c.seq = int(d["seq"]); c.outbox = list(d.get("outbox", []))
    c.n, c.t0 = int(d["n"]), float(d["t0"])
    return c


def blob_sha256(blob: str) -> str:
    return hashlib.sha256(blob.encode()).hexdigest()


# ---------------------------------------------------------------------- the attention diary
def _name(j):
    return " · ".join(GN.VOCAB["clusters"][j]["label"])


def diary_entry(day, tick, lh, n_set, windows, n_tonight, moved, heart_k, heard, last, dials_true):
    """Written from its own reading only. A cluster's reading is SPOKEN only once it has MIN_NIGHTS quiet nights since
    its dial last moved; until then the cluster is "still reading" and keeps its last spoken value in `known`. The
    `verification` block compares readings with its ledger for the public; the creature never uses it. Nothing in the
    entry comes from a language model."""
    spoke = (windows >= MIN_NIGHTS) & (n_set >= 0)
    known = {int(k): v for k, v in (last or {}).get("known", {}).items()}
    told = {e["cluster"] for e in heard if e["why"] == "accepted"} | set(np.nonzero(moved)[0].tolist())
    still = sorted(j for j in range(len(n_set)) if not spoke[j] and (j in known or j in told
                                                                     or (last or {}).get("still_ids", []).count(j)))
    shifts = []
    for j in np.nonzero(spoke)[0]:
        j = int(j); r = int(n_set[j]); before = known.get(j, 0)
        if r != before:
            shifts.append({"cluster": j, "name": _name(j), "from": before, "to": r})
        if r > 0:
            known[j] = r
        else:
            known.pop(j, None)
    ranked = sorted((j for j in np.nonzero(spoke)[0] if n_set[j] >= 1), key=lambda j: (-lh[j], j))
    acc = [e for e in heard if e["why"] == "accepted"]
    have = spoke
    return {
        "day": int(day), "tick": int(tick),
        "attending_most": [{"cluster": int(j), "name": _name(j), "read": int(n_set[j]), "nights": int(windows[j]),
                            "length_vs_birth": round(float(lh[j] / GN.ELL0), 4)} for j in ranked[:TOP]],
        "shifts": shifts,
        "still_reading": [{"cluster": int(j), "name": _name(j)} for j in still],
        "still_ids": still,
        "known": {str(j): v for j, v in sorted(known.items())},
        "heart": {r: int(k) for r, k in zip(GN.REGIONS, heart_k)},
        "heard": {"mentions": len(heard), "accepted": len(acc),
                  "clusters": sorted({_name(e["cluster"]) for e in acc})},
        "verification": {"clusters_spoken": int(have.sum()),
                         "spoken_read_equals_ledger": int(((n_set == dials_true) & have).sum()),
                         "tonight_read_equals_ledger": int((n_tonight == dials_true).sum())},
    }


def public_readout(c: Creature) -> dict:
    return {"n_ticks": c.n, "dials_nonzero": int((c.body.n > 0).sum()), "attention_steps": int(c.body.n.sum()),
            "heart": {r: int(k) for r, k in zip(GN.REGIONS, c.heart.k)}, "committed": len(c.frozen),
            "last_entry_day": None if c.last_entry is None else c.last_entry["day"]}
