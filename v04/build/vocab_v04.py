"""v0.4 vocabulary (BUILD candidate): clusters -> handles, members, heart region, bridges, diary labels.
Diary label of a cluster = its 3 members nearest the cluster's MiniLM centroid (fixed at genesis; the diary never runs
a language model). Handle index j = position in clusters_S16.json; the self cluster is the last handle."""
import hashlib, json
import numpy as np
from sentence_transformers import SentenceTransformer

cl = json.load(open("../clusters_S16.json"))["clusters"]
bo = json.load(open("../bridges_design.json"))["best_other"]
selfm = json.load(open("../self_cluster.json"))["self_cluster"]["members_in_line_order"]
REGIONS = ["LLL", "LLR", "LRL", "LRR", "RLL", "RLR", "RRL", "RRR"]
E = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
id2j = {c["id"]: j for j, c in enumerate(cl)}
out = {"clusters": [], "bridges": [], "regions": REGIONS + ["self"]}
for j, c in enumerate(cl):
    m = sorted(c["members"]); X = E.encode(m, normalize_embeddings=True); cen = X.mean(0)
    lab = [m[i] for i in np.argsort(-(X @ cen), kind="stable")[:3]]
    out["clusters"].append({"j": j, "id": c["id"], "region": REGIONS.index(c["id"][:3]), "members": m, "label": lab})
out["clusters"].append({"j": len(cl), "id": "SELF", "region": 8, "members": selfm, "label": ["itself"]})
for w, (r, other) in sorted(bo.items()):
    if r >= 1.00 and other in id2j:
        own = next(c["j"] for c in out["clusters"] if w in c["members"])
        out["bridges"].append({"concept": w, "own": own, "other": id2j[other], "r": round(r, 4)})
s = json.dumps(out, sort_keys=True, indent=0)
open("vocab_v04.json", "w").write(s)
print(len(out["clusters"]), "handles,", len(out["bridges"]), "bridges, sha256", hashlib.sha256(s.encode()).hexdigest())
for c in out["clusters"][:6] + out["clusters"][-2:]: print(c["j"], c["id"], c["label"])
