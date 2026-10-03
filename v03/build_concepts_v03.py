"""Build the v0.3 BIRTH concept placement (frozen artifact). Reads words only — never a similarity score.
V = SimLex-999 noun words ∪ WordSim-353 words; MiniLM embeddings; Ward dendrogram; Stern–Brocot slopes."""
import json, os
os.environ.setdefault("HF_HUB_OFFLINE", "1")
import meaning_design as M
from meaning_variants import load, place_E
from sentence_transformers import SentenceTransformer
import scipy, sentence_transformers
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
sl = set()
for i, line in enumerate(open(os.path.join(M.HERE, "data", "SimLex-999", "SimLex-999.txt"))):
    if i == 0: continue
    w1, w2, pos = line.split("\t")[:3]
    if pos == "N": sl |= {w1.lower(), w2.lower()}
ws = {w for fn in ("ws353.txt", "ws353sim.txt") for a, b, _ in load(fn) for w in (a, b)}
V = sorted(sl | ws)
addr = place_E(V, model.encode(V, normalize_embeddings=True), "ward")
out = {"method": "all-MiniLM-L6-v2 normalized embeddings -> scipy Ward linkage -> dendrogram L/R path -> Stern-Brocot p/q",
       "versions": {"scipy": scipy.__version__, "sentence_transformers": sentence_transformers.__version__},
       "n": len(V), "concepts": {w: list(addr[w]) for w in V}}
json.dump(out, open("concepts_v03.json", "w"), indent=0, sort_keys=True)
print(len(V), "concepts;", "sample:", {w: addr[w] for w in ("tiger", "cat", "car", "love")})
