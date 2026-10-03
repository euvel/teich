"""v0.3 part 2 — DESIGN PHASE of the meaning test (M1). Uses WordSim-353 ONLY.
SimLex-999 (the scored dataset) is not touched by this file.

Question: if concepts are placed as simple closed curves on the torus (slopes p/q in the
Stern–Brocot tree), does the geometry (intersection number) preserve semantic relatedness?

Placements:
  H  — a hierarchy built by humans (WordNet hypernym tree), binarised, mapped into Stern–Brocot
  E  — a hierarchy built by the dead organ (Ward dendrogram of MiniLM embeddings), mapped likewise
Relatedness of two concepts: -log i(c1, c2), i = |p1 q2 - p2 q1| (Farey neighbours: i = 1).
Control: the same addresses shuffled across words (1000 permutations).
References (ceilings, not the geometry): MiniLM cosine; WordNet path similarity.
"""
from __future__ import annotations

import math
import os
import sys
from fractions import Fraction

os.environ.setdefault("HF_HUB_OFFLINE", "1")
import numpy as np
from scipy.cluster.hierarchy import linkage, to_tree
from scipy.stats import spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
import nltk
nltk.data.path.insert(0, os.path.join(HERE, "data", "nltk"))
from nltk.corpus import wordnet as wn


# ---------------------------------------------------------------- Stern–Brocot addressing
def sb_rational(path: str) -> tuple[int, int]:
    """Path of 'L'/'R' from the root 1/1 -> the rational (p, q) at that node."""
    lp, lq, rp, rq = 0, 1, 1, 0                    # left bound 0/1, right bound 1/0
    p, q = 1, 1
    for ch in path:
        if ch == "L":
            rp, rq = p, q
        else:
            lp, lq = p, q
        p, q = lp + rp, lq + rq
    return p, q


def inter(a, b) -> int:
    return abs(a[0] * b[1] - a[1] * b[0])


def binary_code(i: int, k: int) -> str:
    """Balanced binary code of child i among k siblings (depth ceil(log2 k))."""
    if k <= 1:
        return ""
    half = (k + 1) // 2
    return ("L" + binary_code(i, half)) if i < half else ("R" + binary_code(i - half, k - half))


# ---------------------------------------------------------------- data
def load_ws353():
    rows = []
    for line in open(os.path.join(HERE, "data", "ws353.txt")):
        a, b, s = line.split()
        rows.append((a.lower(), b.lower(), float(s)))
    return rows


def pick_synset(word, model, how):
    ss = wn.synsets(word, pos=wn.NOUN)
    if not ss:
        return None
    if how == "first":
        return ss[0]
    if how == "freq":
        return max(ss, key=lambda s: sum(l.count() for l in s.lemmas()))
    if how == "gloss":                               # sense whose definition is nearest the bare word
        e = model.encode([word] + [s.definition() for s in ss], normalize_embeddings=True)
        return ss[int(np.argmax(e[1:] @ e[0]))]
    raise ValueError(how)


# ---------------------------------------------------------------- placements
def place_wordnet(words, syn):
    """Union of hypernym paths -> tree; children ordered by name (deterministic); balanced codes."""
    children, path_of = {}, {}
    for w in words:
        p = syn[w].hypernym_paths()[0]               # one path, root first
        for par, ch in zip(p, p[1:]):
            children.setdefault(par.name(), set()).add(ch.name())
        path_of[w] = [s.name() for s in p]
    code = {path_of[words[0]][0]: ""}
    order = [path_of[words[0]][0]]
    while order:
        node = order.pop()
        kids = sorted(children.get(node, ()))
        for i, k in enumerate(kids):
            code[k] = code[node] + binary_code(i, len(kids))
            order.append(k)
    return {w: sb_rational(code[path_of[w][-1]] or "") for w in words}


def place_embedding(words, emb):
    tree = to_tree(linkage(emb, method="ward"))
    addr = {}
    def walk(node, path):
        if node.is_leaf():
            addr[words[node.id]] = sb_rational(path)
        else:
            walk(node.get_left(), path + "L"); walk(node.get_right(), path + "R")
    walk(tree, "")
    return addr


# ---------------------------------------------------------------- scoring
def rho_geom(pairs, addr):
    xs = [-math.log(max(1, inter(addr[a], addr[b]))) for a, b, _ in pairs]
    return spearmanr(xs, [s for *_, s in pairs]).correlation


def shuffled_null(pairs, addr, n=1000, seed=0):
    rng = np.random.default_rng(seed); words = sorted(addr); vals = [addr[w] for w in words]
    out = []
    for _ in range(n):
        perm = rng.permutation(len(vals)); a2 = {w: vals[i] for w, i in zip(words, perm)}
        out.append(rho_geom(pairs, a2))
    return np.array(out)


def main():
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
    rows = load_ws353()
    for how in ("first", "freq", "gloss"):
        syn = {}
        for a, b, _ in rows:
            for w in (a, b):
                if w not in syn:
                    s = pick_synset(w, model, how)
                    if s is not None: syn[w] = s
        pairs = [(a, b, s) for a, b, s in rows if a in syn and b in syn and a != b]
        words = sorted({w for a, b, _ in pairs for w in (a, b)})
        emb = model.encode(words, normalize_embeddings=True)
        E = dict(zip(words, emb))
        cos = spearmanr([float(E[a] @ E[b]) for a, b, _ in pairs], [s for *_, s in pairs]).correlation
        wnp = spearmanr([syn[a].path_similarity(syn[b]) or 0 for a, b, _ in pairs], [s for *_, s in pairs]).correlation
        H = place_wordnet(words, syn); Em = place_embedding(words, emb)
        print(f"\n[sense={how}] {len(pairs)} noun pairs, {len(words)} words")
        print(f"  ceilings:  MiniLM cosine rho={cos:.3f}   WordNet path-sim rho={wnp:.3f}")
        for name, addr in (("H wordnet->SB", H), ("E embedding->SB", Em)):
            r = rho_geom(pairs, addr); null = shuffled_null(pairs, addr)
            print(f"  {name:16s} rho={r:.3f}   shuffled null mean {null.mean():+.3f}, 97.5% {np.percentile(null, 97.5):+.3f}"
                  f"   max denominator {max(q for _, q in addr.values())}")


if __name__ == "__main__":
    main()
