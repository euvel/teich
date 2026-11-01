"""Probe (not a gate): does forcing one OpenBLAS kernel make the working surface's dreams substrate-independent?
Replays the real life's published dream chain from the genesis working state and prints one sha over every night's
(pc, P, V) plus whether each night matches the published dream record. Run under different env / numpy / CPU.
    OPENBLAS_CORETYPE=Haswell OPENBLAS_NUM_THREADS=1 python3 dream_fixture_probe.py BUILD GENESIS LOG_ROWS
"""
import hashlib
import json
import os
import platform
import sys

sys.path.insert(0, sys.argv[1])
import numpy as np
import creature_v04 as CR, creature_v05 as C5, work_v05 as W

gen = json.loads(open(sys.argv[2]).read()); recs = [r["rec"] for r in json.load(open(sys.argv[3]))]
w = gen["work"]
pc, P, V = (CR._unb64(w["pc"], "<i8", (C5.NPW,)), CR._unb64(w["P"], "<f8", (C5.NPW, 3)), CR._unb64(w["V"], "<f8", (C5.NPW, 3)))
wb = W.WorkBody(); h = hashlib.sha256(); match = []
for tp in [r for r in recs if r["kind"] == "think-predict"]:
    pub = next(r for r in recs if r["kind"] == "dream" and r["night"] == tp["night"])
    (pc, P, V), lh, counts, occ, _ = W.dream(wb, pc, P, V, tp["thoughts"], C5.DREAM_TICKS)
    mine = {"read": [float(x).hex() for x in lh], "counts": [int(x) for x in counts], "occ": [int(x) for x in occ]}
    match.append(int(all(mine[k] == pub[k] for k in mine)))
    h.update(pc.tobytes() + P.tobytes() + V.tobytes())
cpu = next((l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")), platform.machine())
print(json.dumps({"sha": h.hexdigest(), "published_match": match, "numpy": np.__version__, "cpu": cpu,
                  "coretype": os.environ.get("OPENBLAS_CORETYPE"), "threads": os.environ.get("OPENBLAS_NUM_THREADS")}))
