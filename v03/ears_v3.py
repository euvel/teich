"""Ears v3 — text -> (concept, region, valence sign, strength). Deterministic, stateless.

v0.1 heard one scalar; v0.2 two numbers. v0.3 hears WHAT a sentence is about (its nearest birth
concept, hence its region of the concept tree) and HOW it leans (valence sign on v0.1's calibrated
axis — the anchor sentences are imported verbatim, not re-chosen).

An utterance becomes a memory event only if its valence is clear: |valence score| >= V_MIN.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "teich_repo" / "maturity" / "harness"))
import genome_v031 as GM

V_MIN = 0.05          # design value (WordSim-free; set on the design utterances in ears_design.py)


def _anchors():
    """POS/NEG anchor sentences from v0.1's ears.py, read as constants (no torch import)."""
    import ast
    src = open(HERE.parent / "teich_repo" / "maturity" / "harness" / "ears.py").read()
    vals = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in ("POS_ANCHORS", "NEG_ANCHORS"):
            vals[node.targets[0].id] = ast.literal_eval(node.value)
    return vals["POS_ANCHORS"], vals["NEG_ANCHORS"]


class EarsV3:
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.enc = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
        pos, neg = _anchors()
        v = self._emb(pos).mean(0) - self._emb(neg).mean(0)
        self.v_axis = v / np.linalg.norm(v)
        self.C, self.region = GM.load_concepts()
        self.words = sorted(self.region)
        self.W = self._emb(self.words)

    def _emb(self, texts):
        return np.asarray(self.enc.encode(list(texts), normalize_embeddings=True,
                                          show_progress_bar=False), dtype=np.float64)

    def hear(self, text: str) -> dict:
        e = self._emb([text])[0]
        sims = self.W @ e
        i = int(np.argmax(sims)); concept = self.words[i]
        val = float(e @ self.v_axis)
        sign = int(np.sign(val)) if abs(val) >= V_MIN else 0
        return {"concept": concept, "region": self.region[concept],
                "region_name": GM.REGION_LABELS[GM.REGION_NAMES[self.region[concept]]],
                "valence": round(val, 4), "sign": sign, "concept_sim": round(float(sims[i]), 4)}
