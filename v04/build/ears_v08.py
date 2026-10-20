"""Teich v0.4 Ears v8 (BUILD candidate, lab only) — Ears v7 with ONE change: how a sentence reaches the self handle.

Findings 2026-10-10 (design data, spent): the 1.5B organ cannot separate mirrors from non-mirrors in real conversation
(no question / threshold near caught >= 0.85 with false <= 0.10), and the v6 rule misfired on 46% of non-mirrors.
Founder decision 10-10 (option E): Teich's MAIN mirror channel is asking — a sentence that answers Teich's own question
about itself is a mirror by context. Spontaneous mirrors are secondary and PRECISION FIRST.
Self routing in v8:
  1. asked=True (the founder's reply to Teich's self-question)  -> one self mention, always.
  2. otherwise                                                   -> one self mention only if mirror_rule.mirror_form()
     matches an unmistakable form (design: precision 0.96, false 0.022, caught 0.23 — missing is accepted).
Removed: v5's trait rule, v6's parse rule, v7's organ self-question. Everything else is Ears v7 unchanged (topics,
time adverbs, mapping, attitude organ, invariance, whose-feeling rules): every non-self mention is identical to v7.
"""
from __future__ import annotations

import hashlib
import re

import ears_v05 as E5
import ears_v07 as E7
import genome_v04 as GN
from mirror_rule import mirror_form


class EarsV8(E7.EarsV7):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.version.update({"self_rule": "v8 asked-or-precision-form", "self_theta": None})

    def hear_sentence(self, text, cache=None, asked=False):
        h = E5.EarsV5.hear_sentence(self, text, cache)              # v7 topics + v6 withhold; may add a v5 trait mention
        h["mentions"] = [m for m in h["mentions"] if m["cluster"] != GN.SELF]
        form = "asked" if asked else mirror_form(self.nlp(text))
        if form is None:
            return h
        key = f"C||{text}||the person being spoken to ('you')"
        if cache is not None and key in cache:
            a, neu = cache[key]
        else:
            a, neu = self.attitude3(text, "the person being spoken to ('you')")
            if cache is not None:
                cache[key] = (a, neu)
        h["self_by"] = form
        h["mentions"].insert(0, {"cluster": GN.SELF, "concept": "you", "words": "you", "cos": 1.0, "clause": text,
                                 "attitude": round(a, 4), "neutral": bool(neu),
                                 "sign": self.sign_of(a, h["question"], neu),
                                 "no_feeling_because": "question" if h["question"] else None, "mirror_form": form})
        return h

    def hear(self, utterance: str, asked: bool = False):
        """-> mentions [(cluster, sign, text_sha256)], heard. asked=True: the utterance answers Teich's self-question."""
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", utterance.strip()) if s.strip()]
        heard = [{"sentence": s, **self.hear_sentence(s, asked=asked)} for s in sents]
        mentions = [(m["cluster"], m["sign"], hashlib.sha256(h["sentence"].encode()).hexdigest())
                    for h in heard for m in h["mentions"]]
        return mentions, heard
