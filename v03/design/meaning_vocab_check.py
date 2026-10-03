"""Design check: placement computed on the full BIRTH vocabulary (SimLex-999 nouns ∪ WordSim-353 words,
embeddings only — no SimLex score is read), evaluated on WordSim-353 similarity pairs only."""
import math, os
os.environ.setdefault("HF_HUB_OFFLINE", "1")
from scipy.stats import spearmanr
import meaning_design as M
from meaning_variants import load, place_E
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
sl_words = set()
for i, line in enumerate(open(os.path.join(M.HERE, "data", "SimLex-999", "SimLex-999.txt"))):
    if i == 0: continue
    w1, w2, pos = line.split("\t")[:3]          # columns 0-2 only: words and POS; the score column is never parsed
    if pos == "N": sl_words |= {w1.lower(), w2.lower()}
ws_words = {w for fn in ("ws353.txt", "ws353sim.txt") for a, b, _ in load(fn) for w in (a, b)}
V = sorted(sl_words | ws_words)
emb = model.encode(V, normalize_embeddings=True)
addr = place_E(V, emb, "ward")
pairs = [(a, b, s) for a, b, s in load("ws353sim.txt") if a in addr and b in addr and a != b]
r = spearmanr([-math.log(max(1, M.inter(addr[a], addr[b]))) for a, b, _ in pairs], [s for *_, s in pairs]).correlation
print(f"birth vocabulary |V|={len(V)} (SimLex nouns {len(sl_words)}, WordSim {len(ws_words)});  "
      f"WS-SIM pairs {len(pairs)}: rho={r:.3f};  max denominator {max(q for _, q in addr.values())}")
