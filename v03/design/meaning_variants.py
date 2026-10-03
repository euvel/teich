"""Design phase, part b: variants of placement E (and H) on the WordSim-353 SIMILARITY subset only."""
import math, os, sys
os.environ.setdefault("HF_HUB_OFFLINE", "1")
import numpy as np
from scipy.cluster.hierarchy import linkage, to_tree
from scipy.stats import spearmanr
import meaning_design as M

def load(fn):
    return [(a.lower(), b.lower(), float(s)) for a, b, s in (l.split() for l in open(os.path.join(M.HERE, "data", fn)))]

def place_E(words, emb, method):
    tree = to_tree(linkage(emb, method=method, metric="euclidean")); addr = {}
    def walk(n, p):
        if n.is_leaf(): addr[words[n.id]] = M.sb_rational(p)
        else: walk(n.get_left(), p + "L"); walk(n.get_right(), p + "R")
    walk(tree, ""); return addr

METRICS = {
    "neglog_i": lambda a, b: -math.log(max(1, M.inter(a, b))),
    "neg_slope_gap": lambda a, b: -abs(a[0] / a[1] - b[0] / b[1]),
    "neglog_i_over_qq": lambda a, b: -math.log(max(1, M.inter(a, b))) + 0.0 * math.log(a[1] * b[1]),
}

from sentence_transformers import SentenceTransformer
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
for fn in ("ws353sim.txt", "ws353.txt"):
    rows = load(fn)
    syn = {}
    for a, b, _ in rows:
        for w in (a, b):
            if w not in syn:
                s = M.pick_synset(w, model, "freq")
                if s is not None: syn[w] = s
    pairs = [(a, b, s) for a, b, s in rows if a in syn and b in syn and a != b]
    words = sorted({w for a, b, _ in pairs for w in (a, b)}); emb = model.encode(words, normalize_embeddings=True)
    E = dict(zip(words, emb)); hs = [s for *_, s in pairs]
    print(f"\n== {fn}: {len(pairs)} pairs, {len(words)} words;  MiniLM cosine rho={spearmanr([float(E[a]@E[b]) for a,b,_ in pairs], hs).correlation:.3f}")
    for method in ("ward", "average", "complete"):
        addr = place_E(words, emb, method)
        for mn in ("neglog_i", "neg_slope_gap"):
            r = spearmanr([METRICS[mn](addr[a], addr[b]) for a, b, _ in pairs], hs).correlation
            print(f"  E {method:8s} {mn:14s} rho={r:.3f}")
    H = M.place_wordnet(words, syn)
    for mn in ("neglog_i", "neg_slope_gap"):
        print(f"  H wordnet  {mn:14s} rho={spearmanr([METRICS[mn](H[a], H[b]) for a, b, _ in pairs], hs).correlation:.3f}")
