"""Teich v0.4 Ears v5 (BUILD candidate, lab only) — every topic in a sentence, attitude per topic, abstain when unsure.

An organ, not substrate: what it heard is logged (cluster, sign, text sha256) and replay never needs it.
Per sentence:
  1. Topics, by rule (deterministic): spaCy (en_core_web_sm) finds nouns; a compound modifier folds into its head
     ("battery life" -> life is the head; both words are tried, head first). A noun whose lemma is one of our 1,066
     concepts is that concept; otherwise MiniLM maps it to the nearest concept only if cosine >= TAU_MAP, else the noun
     is UNHEARD (logged, moves nothing). Words that address the creature ("you", "Teich") are never topics.
  2. Self: a sentence that addresses the creature and names a self-cluster trait adds one mention of the self cluster.
  3. One mention per cluster per sentence (first topic wins).
  4. Attitude toward each topic, in its own words, judged on ITS CLAUSE only (spaCy: the governing verb's subtree minus
     coordinated / subordinate clauses that do not hold the topic; no verb -> the topic's own phrase), by the
     target-aware organ (Qwen2.5-1.5B-Instruct, three-way log-probs positive / negative / neutral, no sampling):
     neutral most likely -> sign 0; else +1 above THETA, -1 below -THETA, 0 inside the band. A question carries
     attention but no feeling (sign 0). Chosen on design data (e5_dev2: MAMS val + spent SemEval): opposite-sign
     errors 14.8% vs 16.9% for whole-sentence two-way, neutral left neutral 18.7% vs 2.6%.
  5. INVARIANCE (founder decision 10-06): the feeling toward a topic counts only if it is the same judged on its clause
     alone and on the whole sentence — a judgement must survive removing the other topics. Disagreement -> no feeling
     ("unsure"). Design: opposite errors 14.8% -> 9.3%, neutral left neutral 18.7% -> 39.6%, abstained 5.9% -> 17.6%.
  6. WHOSE FEELING (founder decision 10-06): only the speaker's own present attitude is feeling. The topic gets attention
     but no feeling when it sits under someone else's attitude or speech ("my friend hates dogs", "she said the soup
     was bad", and "you love music" — the speaker may not write the creature's feelings for it), under an if / unless
     / whether clause, or under "used to".
Every withheld feeling carries its reason, shown in the founder's read-back.
Founder decisions 10-06: abstain when unsure; organ stays 1.5B; veto-only read-back happens in the conversation path.
"""
from __future__ import annotations

import hashlib
import re

import numpy as np

import ears_v04 as E4
import genome_v04 as GN

TAU_MAP = 0.60           # min MiniLM cosine for a non-vocabulary noun to count as a concept (tuned on design data)
THETA = 1.0              # attitude abstain band, in log-odds of positive vs negative (tuned on design data)
SPACY = "en_core_web_sm"
ORGAN_REV = "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"      # Qwen2.5-1.5B-Instruct snapshot (pinned)
ENCODER_REV = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"    # all-MiniLM-L6-v2 snapshot (pinned)
ATTITUDE_VERBS = {"love", "like", "hate", "adore", "enjoy", "dislike", "prefer", "detest", "admire", "miss", "fear",
                  "think", "believe", "feel", "find", "consider", "say", "tell", "claim", "write", "complain", "want"}
OWN = {"i", "we"}
IRREGULAR = {"thought", "felt", "found", "said", "told", "wrote", "written"}


def _forms(v):
    stem = v[:-1] if v.endswith("e") else v
    return {v, v + "s", v + "es", v + "d", v + "ed", stem + "ing", v + "ing", stem + "ed"}


ATTITUDE_FORMS = set().union(*(_forms(v) for v in ATTITUDE_VERBS)) | IRREGULAR    # the lemmatizer is not trusted alone
HYPO = ("if", "unless", "whether")
NOT_TOPICS = {"you", "teich", "i", "we", "it", "they", "he", "she", "one", "thing", "something", "anything", "everything",
              "lot", "bit", "kind", "sort", "way"}


class EarsV5(E4.EarsV4):
    def __init__(self, threads=4, tau_map=TAU_MAP, theta=THETA):
        super().__init__(threads)
        import spacy
        self.nlp = spacy.load(SPACY)
        self.tau_map, self.theta = tau_map, theta
        self._map_cache = {}
        import os
        hub = os.path.expanduser("~/.cache/huggingface/hub")
        for name, rev in ((E4.ORGAN, ORGAN_REV), (E4.ENCODER, ENCODER_REV)):
            got = open(os.path.join(hub, "models--" + name.replace("/", "--"), "refs", "main")).read().strip()
            if got != rev:
                raise RuntimeError(f"{name} snapshot {got} is not the pinned {rev}; refusing to hear")
        self.version = {"organ": f"{E4.ORGAN}@{ORGAN_REV[:12]}", "encoder": f"{E4.ENCODER}@{ENCODER_REV[:12]}", "tagger": f"{SPACY}-{self.nlp.meta['version']}",
                        "tau_map": tau_map, "theta": theta}

    # ------------------------------------------------------------------ topics
    def map_noun(self, lemma):
        """-> (concept, cosine) or (None, cosine) when too far from every concept."""
        if lemma in self.cluster_of:
            return lemma, 1.0
        if lemma not in self._map_cache:
            e = self._emb([lemma])[0]; s = self.W @ e; i = int(np.argmax(s))
            self._map_cache[lemma] = (self.words[i], float(s[i]))
        c, s = self._map_cache[lemma]
        return (c if s >= self.tau_map else None), s

    def topics(self, text):
        """-> (candidates [(concept, surface words, cosine)], unheard [(noun, cosine)], addressed, trait, question)"""
        doc = self.nlp(text)
        low = [t.lower_ for t in doc]
        addressed = any(w in E4.ADDRESS for w in low)
        trait = next((t.lemma_.lower() for t in doc if t.lemma_.lower() in self.traits or t.lower_ in self.traits), None)
        question = text.strip().endswith("?")
        cands, unheard, seen = [], [], set()
        for t in doc:
            if t.pos_ not in ("NOUN", "PROPN") or not t.is_alpha or t.lower_ in NOT_TOPICS or t.lemma_.lower() in NOT_TOPICS:
                continue
            if t.dep_ == "compound" and t.head.pos_ in ("NOUN", "PROPN"):
                continue                                              # folded into its head below
            mods = [c for c in t.children if c.dep_ == "compound" and c.pos_ in ("NOUN", "PROPN")]
            surface = " ".join([m.text for m in mods] + [t.text])
            got = None
            for w in [t] + mods:                                      # head first, then its compound modifiers
                lemma = w.lemma_.lower()
                if lemma in self.traits and addressed:
                    continue
                c, s = self.map_noun(lemma)
                if c is not None:
                    got = (c, surface, s); break
            if got is None:
                unheard.append((t.lemma_.lower(), round(self.map_noun(t.lemma_.lower())[1], 3)))
            elif got[0] not in seen:
                seen.add(got[0]); cands.append((*got, self.clause_of(doc, t), self.withhold(t)))
        return cands, unheard, addressed, trait, question

    # ------------------------------------------------------------------ hearing
    def attitude_toward(self, text, words):
        lp = self._ask("You judge attitudes. Answer with one word: positive or negative.",
                       f"Sentence: \"{text}\"\nWhat is the speaker's attitude toward {words}?")
        t = self.torch
        return float(t.logsumexp(lp[self.pos], 0) - t.logsumexp(lp[self.neg], 0))

    def attitude3(self, text, words):
        """Three-way: -> (log-odds positive vs negative, neutral is the most likely of the three)."""
        if not hasattr(self, "neu"):
            self.neu = [self.tok.encode(" neutral")[0], self.tok.encode("neutral")[0]]
        lp = self._ask("You judge attitudes. Answer with one word: positive, negative or neutral.",
                       f"Sentence: \"{text}\"\nWhat is the speaker's attitude toward {words}?")
        t = self.torch
        p, n, z = (float(t.logsumexp(lp[ids], 0)) for ids in (self.pos, self.neg, self.neu))
        return p - n, z > max(p, n)

    def clause_of(self, doc, tok):
        """The clause that holds `tok`: its governing verb's subtree minus coordinated / subordinate clauses that do not
        contain it, and minus their conjunctions."""
        h = tok
        while h.head.i != h.i and h.pos_ not in ("VERB", "AUX"):
            h = h.head
        if h.pos_ not in ("VERB", "AUX"):
            h = tok                                                    # no verb: the topic's own phrase
        drop = set()
        for c in h.children:
            if c.dep_ in ("conj", "advcl", "parataxis", "ccomp", "appos") and tok.i not in {x.i for x in c.subtree}:
                drop |= {x.i for x in c.subtree}
            if c.dep_ in ("cc", "mark") :
                drop.add(c.i)
        span = [x for x in h.subtree if x.i not in drop]
        return " ".join(x.text for x in span) if span else doc.text

    @staticmethod
    def withhold(tok):
        """Why the speaker's own present feeling cannot be read for this topic, or None."""
        for anc in [tok] + list(tok.ancestors):
            for c in anc.children:
                if c.dep_ == "mark" and c.lower_ in HYPO:
                    return "hypothetical"
                if c.dep_ == "advcl" and any(m.dep_ == "mark" and m.lower_ in HYPO for m in c.children):
                    return "hypothetical"                              # the consequence of an if / unless clause
            if anc.pos_ in ("VERB", "AUX"):
                if anc.lower_ == "used" and any(c.dep_ == "xcomp" for c in anc.children):
                    return "past ('used to')"
                if anc.lemma_.lower() in ATTITUDE_VERBS or anc.lower_ in ATTITUDE_FORMS:
                    subj = [c for c in anc.children if c.dep_ in ("nsubj", "nsubjpass")]
                    if subj and subj[0].lower_ not in OWN:
                        return "someone else's feeling" if subj[0].lower_ != "you" else "its own feeling is not the speaker's to set"
        return None

    def sign_of(self, a, question, neutral=False):
        if question or neutral:
            return 0
        return 1 if a > self.theta else -1 if a < -self.theta else 0

    def hear_sentence(self, text, cache=None):
        cands, unheard, addressed, trait, question = self.topics(text)
        out, clusters = [], set()

        def att(scope, words):
            key = f"C||{scope}||{words}"
            if cache is not None and key in cache:
                return cache[key]
            r = self.attitude3(scope, words)
            if cache is not None:
                cache[key] = r
            return r
        if addressed and trait:
            a, neu = att(text, "the person being spoken to ('you')")
            out.append({"cluster": GN.SELF, "concept": trait, "words": "you", "cos": 1.0, "clause": text,
                        "attitude": round(a, 4), "neutral": bool(neu), "sign": self.sign_of(a, question, neu)})
            clusters.add(GN.SELF)
        for c, words, s, clause, held in cands:
            j = self.cluster_of[c]
            if j in clusters:
                continue
            a, neu = att(clause, f"'{words}'")
            sc = self.sign_of(a, question, neu)
            if clause.strip() != text.strip():
                b, bneu = att(text, f"'{words}'")
                sb = self.sign_of(b, question, bneu)
            else:
                b, sb = a, sc
            sign, why = (0, held) if held else (sc, None) if sc == sb else (0, "unsure (clause and sentence disagree)")
            if question and not why:
                why = "question"
            out.append({"cluster": j, "concept": c, "words": words, "cos": round(s, 3), "clause": clause,
                        "attitude_clause": round(a, 4), "attitude_sentence": round(b, 4), "sign": sign,
                        "no_feeling_because": why})
            clusters.add(j)
        return {"mentions": out, "unheard": unheard, "question": question}

    def hear(self, utterance: str):
        """-> mentions [(cluster, sign, text_sha256)] for creature.hear, plus what was heard (for the read-back)."""
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", utterance.strip()) if s.strip()]
        heard = [{"sentence": s, **self.hear_sentence(s)} for s in sents]
        mentions = [(m["cluster"], m["sign"], hashlib.sha256(h["sentence"].encode()).hexdigest())
                    for h in heard for m in h["mentions"]]
        return mentions, heard
