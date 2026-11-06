"""Teich v0.7 gate K3 (PREREG_V07 §2): the Sky's arithmetic is the same on every machine.
  (a) 10,000 fixed touch vectors (P, V, b; drawn once from seed 7 on a stored body) -> sha256 of every output's bytes
  (b) one day of v0.7 life from a STORED state (k3_state.json, made once by `make`), touched -> final state sha256
    python3 k3_substrate_v07.py make BEACONS.json      (once, on the laptop: writes k3_state.json)
    python3 k3_substrate_v07.py run  BEACONS.json      (on every machine: prints both hashes)
"""
import hashlib
import json
import platform
import sys

import numpy as np

import creature_v07 as C7
import genome_v04 as GN

mode, bpath = sys.argv[1], sys.argv[2]
beacons = json.load(open(bpath)); bc = beacons[min(beacons, key=int)]
if mode == "make":
    c = C7.birth(seed=14098, t0=0.0)
    c.advance(GN.DAY - C7.SKY_LEAD - 600)                          # stored just before a touch
    open("k3_state.json", "w").write(C7.dump_state(c))
    print("stored k3_state.json", hashlib.sha256(open("k3_state.json", "rb").read()).hexdigest()); raise SystemExit
c = C7.load_state(open("k3_state.json").read())
rng = np.random.default_rng(7); h = hashlib.sha256()
idx = rng.integers(0, len(c.P), 10_000); bs = rng.random(10_000)
for i, b in zip(idx, bs):
    P = c.P[[i, i]].copy(); V = c.V[[i, i]].copy()
    P2, V2 = C7.touch(P, V, float(b))
    h.update(P2[0].tobytes()); h.update(V2[0].tobytes())
c.sky_beacons = {str(c.n // GN.DAY): bc}                         # its first touch, with the stored beacon
c.advance(GN.DAY)                                                 # crosses the touch, a midnight and its dream
print(json.dumps({"machine": platform.processor() or platform.machine(), "numpy": np.__version__,
                  "touch_vectors_sha256": h.hexdigest(),
                  "day_state_sha256": hashlib.sha256(C7.dump_state(c).encode()).hexdigest()}))
