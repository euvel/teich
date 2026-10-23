"""Teich v0.4 Ears (BUILD candidate, lab only) — the v4c design as one module.

An organ, not substrate: what the Ears heard is stored in the creature's log (cluster, sign, text sha256), so a replay
never needs them. Per sentence:
  1. SELF routing: a sentence that addresses the creature ("you", "your", "Teich") and names a self-cluster trait goes
     to the self cluster.
  2. Topic: a dead organ (Qwen2.5-1.5B-Instruct, greedy) names the main thing the sentence talks about as one noun; the
     noun maps to its nearest vocabulary concept by MiniLM, and the concept to its cluster.
  3. Attitude toward that topic: the organ's next-token log-probabilities of "positive" vs "negative" (no sampling);
     sign = +1 / -1 by which is larger.
Design-phase score (ears_v4c_design, set written by Claude — NOT independent): sign 46/47, cluster 42/47, self 12/12.
"""
from __future__ import annotations

import hashlib
import os
import re

import numpy as np

import genome_v04 as GN

os.environ.setdefault("HF_HUB_OFFLINE", "1")
ORGAN = "Qwen/Qwen2.5-1.5B-Instruct"
ENCODER = "sentence-transformers/all-MiniLM-L6-v2"
ADDRESS = ("you", "your", "you're", "teich")


class EarsV4:
    def __init__(self, threads=4):
        import torch
        from sentence_transformers import SentenceTransformer
        from transformers import AutoModelForCausalLM, AutoTokenizer
        torch.set_num_threads(threads)
        self.torch = torch
        self.enc = SentenceTransformer(ENCODER, device="cpu")
        cl = GN.VOCAB["clusters"]
        self.cluster_of = {w: c["j"] for c in cl[:GN.SELF] for w in c["members"]}
        self.words = sorted(self.cluster_of)
        self.W = self._emb(self.words)
        self.traits = set(cl[GN.SELF]["members"])
        self.tok = AutoTokenizer.from_pretrained(ORGAN)
        self.lm = AutoModelForCausalLM.from_pretrained(ORGAN, torch_dtype=torch.float32).eval()
        t = self.tok
        self.pos = [t.encode(" positive")[0], t.encode("positive")[0]]
        self.neg = [t.encode(" negative")[0], t.encode("negative")[0]]

    def _emb(self, texts):
        return np.asarray(self.enc.encode(list(texts), normalize_embeddings=True, show_progress_bar=False), np.float64)

    def _singular(self, t):
        return t[:-1] if t.endswith("s") and t[:-1] in self.cluster_of else t

    def _ask(self, system, user, gen=0):
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        ids = self.tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt")
        with self.torch.no_grad():
            if gen:
                out = self.lm.generate(ids, max_new_tokens=gen, do_sample=False)
                return self.tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True)
            return self.torch.log_softmax(self.lm(ids).logits[0, -1], -1)

    def topic_word(self, text):
        w = self._ask("Name the main thing the sentence talks about, as one common noun. Answer with the noun only.",
                      text, gen=4).strip().lower()
        w = re.findall(r"[a-z]+", w)
        return self._singular(w[0]) if w else ""

    def concept_of(self, word, text):
        if word in self.cluster_of:
            return word
        e = self._emb([word or text])[0]
        return self.words[int(np.argmax(self.W @ e))]

    def attitude(self, text, self_target: bool, concept: str | None):
        who = "the person being spoken to ('you')" if self_target else f"'{concept}'"
        lp = self._ask("You judge attitudes. Answer with one word: positive or negative.",
                       f"Sentence: \"{text}\"\nWhat is the speaker's attitude toward {who}?")
        t = self.torch
        return float(t.logsumexp(lp[self.pos], 0) - t.logsumexp(lp[self.neg], 0))

    def hear_sentence(self, text):
        toks = [self._singular(t) for t in re.findall(r"[a-z']+", text.lower())]
        addressed = any(t in ADDRESS for t in toks)
        trait = next((t for t in toks if t in self.traits), None)
        tw = None
        if addressed and trait:
            j, concept = GN.SELF, trait
        else:
            tw = self.topic_word(text)
            if addressed and tw in ("you", "person", "listener", "teich"):
                j, concept = GN.SELF, tw
            else:
                concept = self.concept_of(tw, text); j = self.cluster_of[concept]
        a = self.attitude(text, j == GN.SELF, concept)
        return {"cluster": int(j), "concept": concept, "topic_word": tw, "attitude": round(a, 4),
                "sign": 1 if a > 0 else -1}

    def hear(self, utterance: str):
        """-> mentions [(cluster, sign, text_sha256)] for creature.hear, plus what was heard (for the founder's eyes)."""
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", utterance.strip()) if s.strip()]
        heard = [self.hear_sentence(s) for s in sents]
        mentions = [(h["cluster"], h["sign"], hashlib.sha256(s.encode()).hexdigest()) for h, s in zip(heard, sents)]
        return mentions, heard
