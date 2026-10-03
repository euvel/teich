"""The blob: everything that makes Teich v0.3 itself, and nothing else.

One definition of what a v0.3 commit contains, imported by the birth, the wake and the substrate
check, so "what gets saved" cannot drift between the thing that tests continuity and the thing that
does it.

    x            the 8 bodies (one per region of the concept tree), as exact hex floats
    k            the memory ledger, 8 integers in 0..6, born at 3
    commitments  protected commitments, written only through the lawful procedure
    steps, log   bounded attributed influence: who moved which region, in which conversation
    win_acc      ticks spent with x<0 in the current 8000-tick window (integers, exact)
    win_last     the same counts for the last COMPLETE window -- what the creature reads of itself
    n, t0        its own clock, and the wall-clock second it is counted from

There is no private phase in v0.3: nothing here is hidden, and the readout is computed from x only
(condition N). The Ears are an organ, not substrate; what they heard is stored in the log, so a
replay never needs them.

The seat stores this as an opaque string; the Durable Object needs no knowledge of it.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

V03 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(V03))
import genome_v03 as G1        # noqa: E402
import genome_v031 as GM       # noqa: E402
import selector_v03 as S       # noqa: E402

BLOB_VERSION = 1
W = 8000                       # the disposition window, as gated (d_harness_v03.W)


class Creature:
    """One Teich v0.3: a single row of genome v1.1 (8 bodies) plus its clock and self-reading."""

    def __init__(self, x0):
        self.x = np.asarray(x0, float).reshape(1, GM.NB).copy()
        self.ledger = GM.MultiLedger.born(1)
        self.n = 0
        self.t0 = 0.0
        self.win_acc = np.zeros(GM.NB, dtype=np.int64)
        self.win_last = None

    def advance(self, ticks: int):
        """Live `ticks` seconds. Order per tick matches the gated harness: observe, then step."""
        a = G1.alpha_of(self.ledger.k)
        for _ in range(ticks):
            self.win_acc += (self.x[0] < 0)
            self.x = G1.step(self.x, a)
            self.n += 1
            if self.n % W == 0:
                self.win_last = self.win_acc.copy()
                self.win_acc[:] = 0

    def disposition(self):
        """What it reads of itself from its own behaviour (never from k). None before one window."""
        if self.win_last is None:
            return None
        return S.infer_disposition(self.win_last / W).astype(int)


def dump_state(c: Creature) -> str:
    L = c.ledger
    return json.dumps({
        "v": BLOB_VERSION,
        "x": [float(v).hex() for v in c.x[0]],
        "k": [int(v) for v in L.k[0]],
        "commitments": L.commitments,
        "steps": [[conv, int(r), int(u)] for (_, conv, r), u in sorted(L.steps.items(), key=str)],
        "log": L.log,
        "win_acc": [int(v) for v in c.win_acc],
        "win_last": None if c.win_last is None else [int(v) for v in c.win_last],
        "n": int(c.n),
        "t0": float(c.t0),
    }, sort_keys=True)


def load_state(blob: str) -> Creature:
    d = json.loads(blob)
    if d.get("v") != BLOB_VERSION:
        raise ValueError(f"blob version {d.get('v')} != {BLOB_VERSION}; refusing to load a state "
                         f"this code does not understand")
    c = Creature([float.fromhex(v) for v in d["x"]])
    c.ledger.k[0] = np.array(d["k"], dtype=np.int64)
    c.ledger.commitments = list(d["commitments"])
    c.ledger.steps = {(0, conv, r): u for conv, r, u in d["steps"]}
    c.ledger.log = list(d["log"])
    c.win_acc = np.array(d["win_acc"], dtype=np.int64)
    c.win_last = None if d["win_last"] is None else np.array(d["win_last"], dtype=np.int64)
    c.n, c.t0 = int(d["n"]), float(d["t0"])
    return c


def public_readout(c: Creature) -> dict:
    d = c.disposition()
    return {"n_ticks": c.n,
            "memory_k": {r: int(v) for r, v in zip(GM.REGION_NAMES, c.ledger.k[0])},
            "self_read_disposition": None if d is None else
            {r: int(v) for r, v in zip(GM.REGION_NAMES, d)},
            "commitments": len(c.ledger.commitments)}


def blob_sha256(blob: str) -> str:
    return hashlib.sha256(blob.encode()).hexdigest()
