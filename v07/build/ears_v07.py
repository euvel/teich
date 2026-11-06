"""Teich v0.4 Ears v7 (BUILD candidate, lab only) — Ears v6 + the organ for talk about the creature + time adverbs.

A2c (Ears v6, founder set 2) failed self routing (0.58) and precision (0.63). Post-hoc: the v6 self rule was shaped on
set 1's short sentences and missed richer talk about the creature ("you are the one who is going to change the world",
"a creature like you helps humans…"); and nouns used as time adverbs ("today", "this week", "one day") became topics.
  1. SELF = RULE OR ORGAN. A sentence that addresses the creature ("you", "your", "Teich") reaches the self cluster when
     the v5/v6 rules fire (a self trait word; "you" an object or the subject of a clause naming no other thing), OR
     when the pinned organ, asked whether the sentence is mainly about the listener (A) or something else (B), gives
     log P(A) - log P(B) > SELF_THETA. Design (e7_probe, both spent founder sets + MAMS val): the rule alone 18/25,
     the organ alone at best 20/25; together 24/25 with 4 false routes on 24 founder non-self sentences. SELF_THETA was
     chosen on that design data (25 self sentences) — the A2d look is its test.
  2. A time expression used as an adverb is not a topic: spaCy dep npadvmod AND (tagged DATE / TIME, or a time-unit
     lemma: TIME_UNITS) — "today", "this week", "one day", "these days", "10 minutes into". Other adverb-nouns stay
     topics ("not worth the prices").
Everything else is Ears v6 unchanged: topics, mapping (TAU_MAP 0.60), attitude organ, invariance, whose-feeling rules.
"""
from __future__ import annotations

import ears_v04 as E4
import ears_v06 as E6
import genome_v04 as GN

SELF_THETA = 4.0
TIME_UNITS = {"time", "day", "week", "month", "year", "hour", "minute", "second", "moment", "night", "evening", "morning",
              "afternoon", "while", "today", "tonight", "yesterday", "tomorrow"}
SELF_Q = ("You classify sentences. Answer with one letter.",
          'Sentence said to "you": "{text}"\nWhat is this sentence mainly about?\n'
          'A) the listener "you" (their nature, abilities, behaviour, or how the speaker sees them)\n'
          "B) something else\nAnswer A or B.")


class EarsV7(E6.EarsV6):
    def __init__(self, *a, self_theta=SELF_THETA, **k):
        super().__init__(*a, **k)
        t = self.tok
        self.A = [t.encode(" A")[0], t.encode("A")[0]]
        self.B = [t.encode(" B")[0], t.encode("B")[0]]
        self.self_theta = self_theta
        self.version.update({"self_rule": "v7 rule-or-organ", "self_theta": self_theta, "time_adverb_not_topic": True})

    def self_odds(self, text):
        lp = self._ask(SELF_Q[0], SELF_Q[1].format(text=text))
        T = self.torch
        return float(T.logsumexp(lp[self.A], 0) - T.logsumexp(lp[self.B], 0))

    def topics(self, text):
        cands, unheard, addressed, trait, question = super().topics(text)
        doc = self.nlp(text)
        adv = {t.i for t in doc if t.dep_ == "npadvmod" and t.pos_ in ("NOUN", "PROPN")
               and (t.ent_type_ in ("DATE", "TIME") or t.lemma_.lower() in TIME_UNITS)}
        advw = {doc[i].text for i in adv}; advl = {doc[i].lemma_.lower() for i in adv}
        cands = [c for c in cands if c[1].split()[-1] not in advw]
        unheard = [u for u in unheard if u[0] not in advl]
        return cands, unheard, addressed, trait, question

    def hear_sentence(self, text, cache=None):
        h = super().hear_sentence(text, cache)                      # v6: trait rule, v6 rule, whose-feeling fix
        if any(m["cluster"] == GN.SELF for m in h["mentions"]):
            h["self_by"] = "rule"
            return h
        if not any(t.lower_ in E4.ADDRESS for t in self.nlp(text)):
            return h
        key = f"SELF||{text}"
        if cache is not None and key in cache:
            s = cache[key]
        else:
            s = self.self_odds(text)
            if cache is not None:
                cache[key] = s
        h["self_odds"] = round(s, 4)
        if s <= self.self_theta:
            return h
        key = f"C||{text}||the person being spoken to ('you')"
        if cache is not None and key in cache:
            a, neu = cache[key]
        else:
            a, neu = self.attitude3(text, "the person being spoken to ('you')")
            if cache is not None:
                cache[key] = (a, neu)
        h["self_by"] = "organ"
        h["mentions"].insert(0, {"cluster": GN.SELF, "concept": "you", "words": "you", "cos": 1.0, "clause": text,
                                 "attitude": round(a, 4), "neutral": bool(neu),
                                 "sign": self.sign_of(a, h["question"], neu),
                                 "no_feeling_because": "question" if h["question"] else None})
        return h
