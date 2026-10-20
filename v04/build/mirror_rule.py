"""Ears v8 spontaneous-mirror rule (PRECISION FIRST) — fires only on unmistakable mirror forms; deterministic spaCy.

Founder decision 10-10 (option E): Teich's main mirror channel is ASKING (its reply-to-a-self-question is a mirror by
context). Spontaneous mirrors are a secondary channel where a wrong mirror is worse than a missed one, so only these
forms count:
  F1  "you" is the subject of "be" and the complement describes it   — "you are so patient", "are you okay?",
      "you're just a system" (not "you are going to ...": a verb complement is an action, not a description)
  F2  thanks                                                         — "thank you", "thanks"
  F3  the speaker's own feeling/stance verb with "you" as its object — "I love you", "I miss you", "I trust you"
  F4  a feeling adjective of the speaker about the listener          — "I'm proud of you", "I'm angry with you",
                                                                       "I'm glad for you", "I'm sorry for you"
  F5  a wish for the listener                                        — "I hope you ...", "good luck to you",
                                                                       "take care of yourself"
"""
from __future__ import annotations

YOU = {"you", "yourself", "u"}
STANCE_VERBS = {"love", "like", "hate", "miss", "trust", "admire", "appreciate", "adore", "respect", "need", "thank",
                "forgive", "blame", "believe", "understand", "envy"}
STANCE_ADJ = {"proud", "angry", "mad", "glad", "happy", "sorry", "grateful", "thankful", "worried", "disappointed",
              "upset", "jealous", "afraid", "scared", "fond", "tired", "sick"}
OWN = {"i", "we"}


def mirror_form(doc):
    """-> the matching form name, or None."""
    toks = list(doc)
    low = [t.lower_ for t in toks]
    if "thank" in low and any(w in YOU for w in low) or low[:1] == ["thanks"] or low[:2] == ["thank", "you"]:
        return "F2"
    for t in toks:
        if t.lower_ not in YOU:
            continue
        h = t.head
        # F1: you + be + (ADJ | NOUN | ADV-less description); "are you okay?" too
        if t.dep_ in ("nsubj", "nsubjpass") and h.lemma_.lower() == "be":
            comps = [c for c in h.children if c.dep_ in ("acomp", "attr")]
            if comps and not any(c.pos_ == "VERB" for c in comps) and not any(c.dep_ == "xcomp" for c in h.children):
                return "F1"
        # F3: I/we + stance verb + you (object)
        if t.dep_ in ("dobj", "obj") and h.lemma_.lower() in STANCE_VERBS:
            subj = [c for c in h.children if c.dep_ == "nsubj"]
            if subj and subj[0].lower_ in OWN:
                return "F3"
        # F4: I'm proud of you / angry with you / glad for you
        if t.dep_ == "pobj" and h.dep_ == "prep" and h.head.lemma_.lower() in STANCE_ADJ:
            adj = h.head; be = adj.head
            subj = [c for c in be.children if c.dep_ == "nsubj"]
            if subj and subj[0].lower_ in OWN:
                return "F4"
        # F5: wishes — "I hope you ...", "good luck to you"
        if t.dep_ == "nsubj" and any(a.lemma_.lower() in ("hope", "wish") and
                                     any(c.dep_ == "nsubj" and c.lower_ in OWN for c in a.children)
                                     for a in t.ancestors):
            return "F5"
        if t.dep_ == "pobj" and h.lower_ == "to" and h.head.lower_ == "luck":
            return "F5"
    return None
