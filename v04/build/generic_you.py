"""Ears v9 self routing (S1 retry, founder's broad reading 2026-10-19): a sentence MIRRORS the listener when some
you-word refers to the actual listener. Not a mirror: only the discourse filler "you know" ("you know, ...",
"you never know", "if you know what I mean", "before you know it") — generic "you" is left to the organ."""
from __future__ import annotations

YOU = {"you", "your", "yours", "yourself", "yourselves", "u", "ya"}


def you_tokens(doc):
    return [t for t in doc if t.lower_ in YOU]


def discourse(t):
    """True when this you-word is the filler 'you know' / 'you never know' / 'before you know it'."""
    h = t.head
    if t.lower_ not in ("you", "u", "ya") or h.lemma_.lower() != "know" or t.dep_ != "nsubj":
        return False
    if any(c.dep_ == "aux" and c.lemma_.lower() == "do" and c.i < t.i for c in h.children):
        return False                                    # "do you know what caused it?" asks the listener
    if any(c.dep_ in ("dobj", "obj") and c.lower_ not in ("what", "how") for c in h.children):
        return False                                    # "you know him" — a real object
    return True


def listener_you(doc):
    """-> True when some you-word is not a discourse filler."""
    return any(not discourse(t) for t in you_tokens(doc))
