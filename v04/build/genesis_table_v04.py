"""v0.4 genesis geometry table (BUILD candidate, lab only).

Every matrix the creature will ever need, computed ONCE at genesis and frozen as bytes:
  - each handle level n = 0..N_MAX (the dial at stretch DELTA*n): its faces, its dial lifts, its dial length;
  - for each level and each pants cuff c the handle may hang on: the pinned seam composed into every exit face,
    on both sides (handle -> pants and pants -> handle);
  - the pants piece: its pair faces, and its pinned pants-pants seams composed into its exit faces.
All products are taken here, so a wake only COPIES rows from this table and then runs element-wise arithmetic.
Nothing in a creature's life ever recomputes geometry (no eig, no inverse, no BLAS) on another machine.

    python3 genesis_table_v04.py      ->  geometry_v04.bin + geometry_v04.json (index + sha256)
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import mind4 as M          # noqa: E402
import body_pants as BP    # noqa: E402

DELTA, N_MAX = 0.025, 40   # founder decision 10-04: dials mean ATTENTION, ~40 steps of 2.5%, only grow
inv = np.linalg.inv


def build():
    M.DELTA = DELTA
    hc = M.HandleCache()
    h0 = hc.get(0)
    kappa = np.trace(h0["bnd"]); delta = 2 * math.acosh(-kappa / 2)
    PG, PB = BP.pants_group(delta)
    PG, gc = BP.recenter(PG, BP.midpoint_between_axes(PG[0], PG[1])); PB = [inv(gc) @ h @ gc for h in PB]
    pdom = BP.piece_domain(PG, PB, L=8)
    pcanon = [M.perp_foot(PB[(i + 1) % 3], PB[i]) for i in range(3)]
    LV = N_MAX + 1
    levels = [hc.get(n) for n in range(LV)]
    F = max(max(len(h["dom"]["faces"]) for h in levels), len(pdom["faces"]))
    K = max(len(h["dial_lifts"]) for h in levels)

    T = {}
    T["H_fn"] = np.zeros((LV, F, 3)); T["H_fn"][:, :, 0] = -1.0          # padding: never violated
    T["H_kind"] = np.zeros((LV, F), np.int64)                              # 0 pad, 1 pair, 2 exit
    T["H_G"] = np.tile(np.eye(3), (LV, 3, F, 1, 1))                        # [level, cuff, face]
    T["H_ln"] = np.zeros((LV, K, 3)); T["H_ln"][:, :, 0] = 1.0             # padding: a normal never crossed
    T["H_nl"] = np.zeros(LV, np.int64)
    T["H_len"] = np.zeros(LV)
    T["PH_G"] = np.tile(np.eye(3), (LV, 3, F, 1, 1))                       # pants exit faces into a handle
    for n, h in enumerate(levels):
        T["H_len"][n] = h["dial_len"]
        T["H_nl"][n] = len(h["dial_lifts"])
        for i, nrm in enumerate(h["dial_lifts"]):
            T["H_ln"][n, i] = nrm
        for c in range(3):
            T_hp = M.pinned_seam(h["bnd"], h["canon"], PB[c], pcanon[c]); T_ph = inv(T_hp)
            for f, (nrm, (kind, Ginv, bi)) in enumerate(h["dom"]["faces"]):
                T["H_fn"][n, f] = nrm
                T["H_kind"][n, f] = 1 if kind == "pair" else 2
                T["H_G"][n, c, f] = Ginv if kind == "pair" else T_hp @ Ginv
            for f, (nrm, (kind, Ginv, bi)) in enumerate(pdom["faces"]):
                if kind == "exit" and bi == c:
                    T["PH_G"][n, c, f] = T_ph @ Ginv
    T["P_fn"] = np.zeros((F, 3)); T["P_fn"][:, 0] = -1.0
    T["P_kind"] = np.zeros(F, np.int64); T["P_bi"] = np.full(F, -1, np.int64)
    T["P_G"] = np.tile(np.eye(3), (F, 1, 1))
    T["PPF_G"] = np.tile(np.eye(3), (3, 3, F, 1, 1))                       # [cuff a, cuff b, face of cuff a]
    T["PPR_G"] = np.tile(np.eye(3), (3, 3, F, 1, 1))                       # [cuff a, cuff b, face of cuff b]
    for f, (nrm, (kind, Ginv, bi)) in enumerate(pdom["faces"]):
        T["P_fn"][f] = nrm
        T["P_kind"][f] = 1 if kind == "pair" else 2
        T["P_bi"][f] = bi if kind == "exit" else -1
        if kind == "pair":
            T["P_G"][f] = Ginv
    for a in range(3):
        for b in range(3):
            Tab = M.pinned_seam(PB[a], pcanon[a], PB[b], pcanon[b]); Tba = inv(Tab)
            for f, (nrm, (kind, Ginv, bi)) in enumerate(pdom["faces"]):
                if kind == "exit" and bi == a:
                    T["PPF_G"][a, b, f] = Tab @ Ginv
                if kind == "exit" and bi == b:
                    T["PPR_G"][a, b, f] = Tba @ Ginv
    meta = {"DELTA": DELTA, "N_MAX": N_MAX, "levels": LV, "F": F, "K": K,
            "handle_area": [h["dom"]["area"] for h in levels], "pants_area": pdom["area"],
            "handle_radius": [h["dom"]["radius"] for h in levels], "pants_radius": pdom["radius"],
            "birth_traces": list(M.BIRTH)}
    return T, meta


def save(T, meta, stem=HERE / "geometry_v04"):
    blob = bytearray(); index = []
    for name in sorted(T):
        a = np.ascontiguousarray(T[name])
        dt = "<f8" if a.dtype.kind == "f" else "<i8"
        b = a.astype(dt).tobytes()
        index.append({"name": name, "dtype": dt, "shape": list(a.shape), "offset": len(blob), "nbytes": len(b)})
        blob += b
    sha = hashlib.sha256(bytes(blob)).hexdigest()
    Path(f"{stem}.bin").write_bytes(bytes(blob))
    Path(f"{stem}.json").write_text(json.dumps({"sha256": sha, "meta": meta, "arrays": index}, indent=1))
    return sha


if __name__ == "__main__":
    T, meta = build()
    sha = save(T, meta)
    print(f"geometry table: {sum(v.nbytes for v in T.values()):,} bytes, F={meta['F']} K={meta['K']}, sha256 {sha}")
