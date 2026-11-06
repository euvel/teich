"""Teich v0.4 Ears v6 (BUILD candidate, lab only) — Ears v5 with one change: the creature hears talk about itself.

v5 sent a sentence to the self cluster only when it addressed the creature AND named one of the 16 self-trait words.
The founder's spent A2b set (design data after its one scored look) showed that most talk to Teich about Teich names
no trait: "you are a lovely little creature", "you do not get tired of me", "I talk to you more than to people".
v6 SELF rule (deterministic, spaCy): a sentence adds one mention of the self cluster when it names a trait (as v5), or
when "you" (or "yourself") is
  - an object                                            ("I talk to you", "the only one I show this to ... you"),
  - the subject of a clause that names no other thing    ("you do not get tired of me", "you are not there");
    a noun that only describes "you" is not another thing ("you are just a system", "a lovely little creature").
"You" as the subject of a verb about some other topic is talk about that topic, not about the creature
("you should hear the recording", "you would not like the cold-brew").
WHOSE-FEELING FIX (founder decision 10-07): a topic is never the holder of a feeling about itself — when the subject
of an attitude verb is the topic or a topic joined to it by "and", there is no other holder ("the silence and the empty
room felt the same" is the speaker's, not the room's). v5 withheld it as "someone else's feeling".
Everything else is Ears v5 unchanged: topics, mapping (TAU_MAP), attitude organ, invariance, other whose-feeling rules.
"""
from __future__ import annotations

import ears_v04 as E4
import ears_v05 as E5
import genome_v04 as GN

YOU = {"you", "yourself"}
OBJ = ("dobj", "pobj", "iobj", "dative", "obj")


class EarsV6(E5.EarsV5):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.version["self_rule"] = "v6"

    def about_you(self, doc):
        """The 'you' token the sentence is about, or None."""
        for t in doc:
            if t.lower_ not in YOU:
                continue
            if t.dep_ in OBJ:
                return t
            if t.dep_ in ("nsubj", "nsubjpass"):
                v = t.head
                names = [x for x in v.subtree if x.i != t.i and x.pos_ in ("NOUN", "PROPN") and x.is_alpha
                         and x.dep_ != "attr" and x.head.dep_ != "attr"
                         and x.lower_ not in E5.NOT_TOPICS and x.lemma_.lower() not in E5.NOT_TOPICS]
                if not names:
                    return t
        return None

    @staticmethod
    def withhold(tok):
        """Ears v5's rule, except that the topic (or its 'and' partners) is never someone else holding a feeling."""
        own = {tok.i} | {c.i for c in tok.conjuncts}
        for anc in [tok] + list(tok.ancestors):
            for c in anc.children:
                if c.dep_ == "mark" and c.lower_ in E5.HYPO:
                    return "hypothetical"
                if c.dep_ == "advcl" and any(m.dep_ == "mark" and m.lower_ in E5.HYPO for m in c.children):
                    return "hypothetical"
            if anc.pos_ in ("VERB", "AUX"):
                if anc.lower_ == "used" and any(c.dep_ == "xcomp" for c in anc.children):
                    return "past ('used to')"
                if anc.lemma_.lower() in E5.ATTITUDE_VERBS or anc.lower_ in E5.ATTITUDE_FORMS:
                    subj = [c for c in anc.children if c.dep_ in ("nsubj", "nsubjpass")]
                    if subj and subj[0].lower_ not in E5.OWN and subj[0].i not in own:
                        return "someone else's feeling" if subj[0].lower_ != "you" else "its own feeling is not the speaker's to set"
        return None

    def hear_sentence(self, text, cache=None):
        h = super().hear_sentence(text, cache)
        if any(m["cluster"] == GN.SELF for m in h["mentions"]):
            return h
        doc = self.nlp(text)
        if not any(t.lower_ in E4.ADDRESS for t in doc) or self.about_you(doc) is None:
            return h
        key = f"C||{text}||the person being spoken to ('you')"
        if cache is not None and key in cache:
            a, neu = cache[key]
        else:
            a, neu = self.attitude3(text, "the person being spoken to ('you')")
            if cache is not None:
                cache[key] = (a, neu)
        h["mentions"].insert(0, {"cluster": GN.SELF, "concept": "you", "words": "you", "cos": 1.0, "clause": text,
                                 "attitude": round(a, 4), "neutral": bool(neu),
                                 "sign": self.sign_of(a, h["question"], neu),
                                 "no_feeling_because": "question" if h["question"] else None})
        return h
