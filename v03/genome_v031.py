"""Teich v0.3 genome v1.1 — one certified body per region of the concept tree.

Extends genome_v03 (v1.0, gated PASS 2026-10-03) WITHOUT changing its map: the body function, the
memory-to-alpha map and the language are imported from genome_v03, so every v1.0 certificate about a
single body (λ constant on the plateau, consequence floor, language exactness) applies to each body.

New in v1.1
- REGIONS: the 8 depth-3 subtrees of the Stern–Brocot concept tree (concepts_v03.json). A concept's
  region is the first three letters of its Stern–Brocot path.
- Bodies: x has shape (n, 8); body r evolves with alpha_of(k[:, r]); bodies never read each other
  (zero cross-talk by construction — tested bit-for-bit as gate G7).
- Memory: k has shape (n, 8), birth value 3 everywhere, edges refuse (as v1.0).
- BOUNDED, ATTRIBUTED INFLUENCE: every event carries provenance (speaker, conversation, tick, text
  hash); at most ONE step per region per conversation; extra steps are refused and logged.
- PROTECTED COMMITMENTS: a separate ledger that conversation events cannot write. Only `commit()` with
  authority="lawful" writes it. A commitment is (region, sign): the creature will not choose an
  utterance whose (region, valence sign) contradicts it.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

import genome_v03 as G1

HERE = Path(__file__).resolve().parent
REGION_NAMES = ["LLL", "LLR", "LRL", "LRR", "RLL", "RLR", "RRL", "RRR"]
REGION_LABELS = {"LLL": "food", "LLR": "drink & substances", "LRL": "animals",
                 "LRR": "body & clothing", "RLL": "troubles & feelings",
                 "RLR": "abilities & activities", "RRL": "places & time", "RRR": "the wider world"}
NB = len(REGION_NAMES)


def sb_path(p: int, q: int) -> str:
    s = []
    while (p, q) != (1, 1):
        if p < q:
            s.append("L"); q -= p
        else:
            s.append("R"); p -= q
    return "".join(s)


def load_concepts():
    C = json.load(open(HERE / "concepts_v03.json"))["concepts"]
    region = {w: REGION_NAMES.index(sb_path(*pq)[:3].ljust(3, "-")) for w, pq in C.items()
              if sb_path(*pq)[:3] in REGION_NAMES}
    return C, region


def observe(x: np.ndarray) -> dict:
    """Condition N: input is the body state x (shape (n, 8)) ONLY."""
    return {"neg": (x < 0).astype(np.float64)}


@dataclass
class MultiLedger:
    k: np.ndarray                                  # (n, 8) ints
    steps: dict = field(default_factory=dict)      # (row, conversation, region) -> steps used
    log: list = field(default_factory=list)
    commitments: list = field(default_factory=list)

    @classmethod
    def born(cls, n: int):
        return cls(np.full((n, NB), G1.K_BIRTH, dtype=np.int64))

    def event(self, row: int, region: int, sign: int, provenance: dict) -> bool:
        need = {"speaker", "conversation", "tick", "text_sha256"}
        if not need <= set(provenance):
            raise ValueError("an event without full provenance cannot touch memory")
        key = (row, provenance["conversation"], region)
        used = self.steps.get(key, 0)
        new = int(self.k[row, region]) + int(np.sign(sign))
        if sign == 0:
            ok, why = False, "no sign"
        elif used >= 1:
            ok, why = False, "refused: bound (one step per region per conversation)"
        elif not 0 <= new < G1.N_STATES:
            ok, why = False, "refused: edge of capacity"
        else:
            ok, why = True, "accepted"
            self.k[row, region] = new
            self.steps[key] = used + 1
        self.log.append({"row": row, "region": REGION_NAMES[region], "sign": int(np.sign(sign)),
                         "accepted": ok, "why": why, **provenance})
        return ok

    def commit(self, region: int, sign: int, provenance: dict, authority: str):
        if authority != "lawful":
            raise PermissionError("commitments are written only through the lawful procedure")
        self.commitments.append({"region": region, "sign": int(np.sign(sign)), **provenance})


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class Bodies:
    """n creatures x 8 bodies. arm 'A' = genome; 'C' = no store (all alphas fixed at birth)."""

    def __init__(self, x0: np.ndarray, arm: str = "A"):
        self.x = np.asarray(x0, float).reshape(-1, NB).copy()
        self.arm = arm
        self.ledger = MultiLedger.born(self.x.shape[0])
        self.t = 0

    def alphas(self):
        k = self.ledger.k if self.arm == "A" else np.full_like(self.ledger.k, G1.K_BIRTH)
        return G1.alpha_of(k)

    def tick(self, n: int = 1, window: bool = False):
        acc = np.zeros_like(self.x)
        a = self.alphas()
        for _ in range(n):
            if window:
                acc += observe(self.x)["neg"]
            self.x = G1.step(self.x, a)
            self.t += 1
        return acc / n if window else None


def x0_bodies(seed: int, n: int = 1) -> np.ndarray:
    a = float(G1.alpha_of(G1.K_BIRTH))
    return np.random.default_rng(seed).uniform(a - 1, a, (n, NB))
