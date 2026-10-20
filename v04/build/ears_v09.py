"""Teich v0.4 Ears v9 (S1b candidate, lab only) — Ears v7 with ONE change: how a sentence reaches the self handle.

Founder reading 2026-10-19 (S1 audit): a sentence MIRRORS the listener when some you-word in it is the listener
personally, whatever else it is about. Design (spent data, v9_design_labels.json): the 1.5B organ cannot tell generic
"you" from the listener (generic odds -0.8..3.6, inside the mirror range), so v9 uses NO organ for self routing:
  1. asked=True (the founder's reply to Teich's self-question)        -> one self mention, always.
  2. otherwise one self mention when generic_you.listener_you() holds  (some you-word that is not the "you know" filler).
Design: caught 0.98, precision 0.92 at 11% generic; known limit: generic "you" is routed to self (disclosed).
Everything else is Ears v7 unchanged: every non-self mention is identical to v7 (regression R-v9).
"""
from __future__ import annotations

import hashlib
import re

import ears_v05 as E5
import ears_v07 as E7
import genome_v04 as GN
from generic_you import listener_you


class EarsV9(E7.EarsV7):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.version.update({"self_rule": "v9 asked-or-listener-you", "self_theta": None})

    def hear_sentence(self, text, cache=None, asked=False):
        h = E5.EarsV5.hear_sentence(self, text, cache)              # v7 topics + v6 withhold; may add a v5 trait mention
        h["mentions"] = [m for m in h["mentions"] if m["cluster"] != GN.SELF]
        form = "asked" if asked else ("listener-you" if listener_you(self.nlp(text)) else None)
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
