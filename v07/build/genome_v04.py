"""Teich v0.4 genome (BUILD candidate, lab only — nothing here is frozen or anchored yet).

Nature. A closed hyperbolic surface built in the shape of the concept tree: one handle per concept cluster (98 = 97
clusters + the self cluster) hanging off a trivalent tree of pairs of pants. Curvature -1 everywhere; its thoughts are
NP geodesic particles, each carrying (piece, p, v). The geometry of every piece at every dial level is read from the
frozen genesis table (geometry_v04.bin): a dial move COPIES rows, it never computes geometry.

Memory (mind). One integer dial n_j in 0..N_MAX per handle. Handle j at dial n is the birth handle with its core curve
stretched by e^(DELTA*n), twist and seams pinned; nothing else changes (isolation is by construction: only handle j's
rows and the pants faces pointing into it are rewritten).

Feeling (heart). v0.3's ledger, unchanged in law: 9 integers in 0..6 born at 3 (v0.3's 8 regions + "self"), at most
one step per region per conversation, refusals at the edges, every event attributed.

Self-reading. Local Crofton, per handle: l_hat = (pi * area / 2) * crossings / time_in_handle, area = 2*pi by topology.
It reads its dials from its own thoughts, never from n.

The tick uses only element-wise + - * / sqrt on float64, so a life is bit-identical across machines (K1, K12).
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent

DT = 0.05                                                       # distance per tick; 1 tick = 1 second of life
C_DT = float.fromhex("0x1.0051efe3b1bc3p+0")                    # cosh(DT), pinned
S_DT = float.fromhex("0x1.99c54bcf10dfbp-5")                    # sinh(DT), pinned
NP = 2048                                                       # thoughts (2,048: nightly self-reading noise ~0.26 step)
DAY = 86_400                                                    # ticks per day = self-reading window
HEART_STATES, HEART_BIRTH = 7, 3
AREA_HANDLE = 2 * math.pi                                       # one-holed torus with geodesic boundary


def _load_table(stem=HERE / "geometry_v04"):
    idx = json.loads(Path(f"{stem}.json").read_text())
    raw = Path(f"{stem}.bin").read_bytes()
    if hashlib.sha256(raw).hexdigest() != idx["sha256"]:
        raise RuntimeError("geometry table does not match its recorded sha256 — refusing to build a body")
    T = {a["name"]: np.frombuffer(raw, dtype=a["dtype"], count=int(np.prod(a["shape"])), offset=a["offset"])
         .reshape(a["shape"]).astype(np.float64 if a["dtype"] == "<f8" else np.int64) for a in idx["arrays"]}
    return T, idx["meta"], idx["sha256"]


TABLE, META, TABLE_SHA = _load_table()
_vraw = (HERE / "vocab_v04.json").read_bytes()
VOCAB, VOCAB_SHA = json.loads(_vraw), hashlib.sha256(_vraw).hexdigest()
DELTA, N_MAX = META["DELTA"], META["N_MAX"]
G = len(VOCAB["clusters"])                                      # handles (the last one is the self cluster)
SELF = G - 1
REGIONS = VOCAB["regions"]                                      # heart regions: v0.3's 8 + "self"
REGION_OF = np.array([c["region"] for c in VOCAB["clusters"]], dtype=np.int64)
ELL0 = float(TABLE["H_len"][0])                                 # birth dial length (nature, not memory)


def mk(a0, a1, a2, b0, b1, b2):
    return -a0 * b0 + a1 * b1 + a2 * b2


def trivalent_tree(g):
    """Pants tree with g leaves (handles); edges between ('P', i, cuff) / ('H', j, 0) ends."""
    pants = [[("H", 0), ("H", 1), ("H", 2)]]; nh = 3
    while nh < g:
        pi, ci = min(((i, c) for i, P in enumerate(pants) for c, e in enumerate(P) if e[0] == "H"),
                     key=lambda t: (t[0], t[1]))
        old = pants[pi][ci]; new = len(pants)
        pants[pi][ci] = ("P", new)
        pants.append([("P", pi), old, ("H", nh)]); nh += 1
    edges = []
    for i, P in enumerate(pants):
        for c, e in enumerate(P):
            if e[0] == "H":
                edges.append((("P", i, c), ("H", e[1], 0)))
            elif e[1] > i:
                j = e[1]; cj = next(k for k, x in enumerate(pants[j]) if x == ("P", i))
                edges.append((("P", i, c), ("P", j, cj)))
    return pants, edges


class Body:
    """The surface as per-piece face tables, assembled by copying rows of the genesis table."""

    def __init__(self, g=G):
        T = TABLE; F = META["F"]; K = META["K"]
        self.g = g
        pants, edges = trivalent_tree(g)
        self.pieces = [("H", j) for j in range(g)] + [("P", i) for i in range(len(pants))]
        idx = {p: k for k, p in enumerate(self.pieces)}
        N = len(self.pieces)
        self.fn = np.zeros((N, F, 3)); self.fn[:, :, 0] = -1.0                  # padding: never violated
        self.fG = np.tile(np.eye(3), (N, F, 1, 1)); self.ft = np.tile(np.arange(N)[:, None], (1, F))
        self.ln = np.zeros((N, K, 3)); self.ln[:, :, 0] = 1.0; self.lc = np.full((N, K), -1)
        self.hang = {}
        pair = T["P_kind"] == 1
        for k, (t, i) in enumerate(self.pieces):
            if t == "P":
                self.fn[k] = T["P_fn"]; self.fG[k, pair] = T["P_G"][pair]
        for (a, b) in edges:
            if b[0] == "H":
                self.hang[b[1]] = (idx[a[:2]], a[2])
            else:
                ka, kb, ca, cb = idx[a[:2]], idx[b[:2]], a[2], b[2]
                fa = (T["P_kind"] == 2) & (T["P_bi"] == ca); fb = (T["P_kind"] == 2) & (T["P_bi"] == cb)
                self.fG[ka, fa] = T["PPF_G"][ca, cb, fa]; self.ft[ka, fa] = kb
                self.fG[kb, fb] = T["PPR_G"][ca, cb, fb]; self.ft[kb, fb] = ka
        self.n = np.zeros(g, dtype=np.int64)
        for j in range(g):
            self._write_handle(j)

    def _write_handle(self, j):
        T = TABLE; lv = int(self.n[j]); pk, c = self.hang[j]
        self.fn[j] = T["H_fn"][lv]
        self.fG[j] = T["H_G"][lv, c]
        self.ft[j] = np.where(T["H_kind"][lv] == 2, pk, j)
        self.ln[j] = T["H_ln"][lv]
        self.lc[j] = np.where(np.arange(META["K"]) < T["H_nl"][lv], j, -1)
        into = (T["P_kind"] == 2) & (T["P_bi"] == c)
        self.fG[pk, into] = T["PH_G"][lv, c, into]; self.ft[pk, into] = j

    def set_dial(self, j, n):
        if not 0 <= n <= N_MAX:
            raise ValueError("a dial outside 0..N_MAX does not exist in this genome")
        self.n[j] = n; self._write_handle(j)

    def area(self, k):
        t, i = self.pieces[k]
        return META["handle_area"][int(self.n[i])] if t == "H" else META["pants_area"]

    def radius(self, k):
        t, i = self.pieces[k]
        return META["handle_radius"][int(self.n[i])] if t == "H" else META["pants_radius"]

    def start(self, n, seed):
        """Birth only: particles uniform by area over pieces, uniform in each piece, uniform direction. The result is
        stored as bytes in the birth blob, so this sampler never needs to be reproducible across machines."""
        rng = np.random.default_rng(seed)
        areas = np.array([self.area(k) for k in range(len(self.pieces))])
        piece = rng.choice(len(areas), n, p=areas / areas.sum())
        P = np.zeros((n, 3))
        for k in np.unique(piece):
            sel = np.nonzero(piece == k)[0]; m = len(sel); got = []; rad = self.radius(k)
            while len(got) < m:
                r = np.arccosh(1 + rng.random(8 * m) * (math.cosh(rad) - 1)); th = rng.random(8 * m) * 2 * math.pi
                p = np.stack([np.cosh(r), np.sinh(r) * np.cos(th), np.sinh(r) * np.sin(th)], 1)
                ok = np.all(-self.fn[k][None, :, 0] * p[:, None, 0] + self.fn[k][None, :, 1] * p[:, None, 1]
                            + self.fn[k][None, :, 2] * p[:, None, 2] >= 0, axis=1)
                got.extend(p[ok])
            P[sel] = np.array(got[:m])
        phi = rng.random(n) * 2 * math.pi
        e = np.stack([np.zeros(n), np.cos(phi), np.sin(phi)], 1)
        V = e + mk(*e.T, *P.T)[:, None] * P; V = V / np.sqrt(mk(*V.T, *V.T))[:, None]
        return piece.astype(np.int64), P, V

    def run(self, pc, P, V, ticks):
        """Live `ticks` seconds. Returns the new particle state and, per handle, the dial crossings and the ticks
        spent in it (integers). Element-wise + - * / sqrt only."""
        pc = pc.copy(); p0, p1, p2 = P.T.copy(); v0, v1, v2 = V.T.copy()
        counts = np.zeros(self.g, np.int64); occ = np.zeros(len(self.pieces), np.int64)
        ar = np.arange(len(pc)); unsettled = 0

        def signs(pc, q0, q1, q2):
            N = self.ln[pc]
            return (-N[:, :, 0] * q0[:, None] + N[:, :, 1] * q1[:, None] + N[:, :, 2] * q2[:, None]) >= 0
        sig_old = signs(pc, p0, p1, p2)
        for _ in range(ticks):
            q0 = C_DT * p0 + S_DT * v0; q1 = C_DT * p1 + S_DT * v1; q2 = C_DT * p2 + S_DT * v2
            w0 = S_DT * p0 + C_DT * v0; w1 = S_DT * p1 + C_DT * v1; w2 = S_DT * p2 + C_DT * v2
            r = np.sqrt(-mk(q0, q1, q2, q0, q1, q2)); q0 = q0 / r; q1 = q1 / r; q2 = q2 / r
            c = mk(w0, w1, w2, q0, q1, q2); w0 = w0 + c * q0; w1 = w1 + c * q1; w2 = w2 + c * q2
            r = np.sqrt(mk(w0, w1, w2, w0, w1, w2)); w0 = w0 / r; w1 = w1 / r; w2 = w2 / r
            sig = signs(pc, q0, q1, q2)
            ch = (sig != sig_old) & (self.lc[pc] >= 0)
            if ch.any():
                np.add.at(counts, self.lc[pc][ch], 1)
            for _it in range(12):
                N = self.fn[pc]
                val = -N[:, :, 0] * q0[:, None] + N[:, :, 1] * q1[:, None] + N[:, :, 2] * q2[:, None]
                j = np.argmin(val, 1); bad = val[ar, j] < 0
                if not bad.any():
                    break
                Gm = self.fG[pc[bad], j[bad]]
                a0, a1, a2 = q0[bad], q1[bad], q2[bad]
                q0[bad] = Gm[:, 0, 0] * a0 + Gm[:, 0, 1] * a1 + Gm[:, 0, 2] * a2
                q1[bad] = Gm[:, 1, 0] * a0 + Gm[:, 1, 1] * a1 + Gm[:, 1, 2] * a2
                q2[bad] = Gm[:, 2, 0] * a0 + Gm[:, 2, 1] * a1 + Gm[:, 2, 2] * a2
                a0, a1, a2 = w0[bad], w1[bad], w2[bad]
                w0[bad] = Gm[:, 0, 0] * a0 + Gm[:, 0, 1] * a1 + Gm[:, 0, 2] * a2
                w1[bad] = Gm[:, 1, 0] * a0 + Gm[:, 1, 1] * a1 + Gm[:, 1, 2] * a2
                w2[bad] = Gm[:, 2, 0] * a0 + Gm[:, 2, 1] * a1 + Gm[:, 2, 2] * a2
                pc[bad] = self.ft[pc[bad], j[bad]]
            else:
                unsettled += 1
            sig_old = signs(pc, q0, q1, q2)
            p0, p1, p2, v0, v1, v2 = q0, q1, q2, w0, w1, w2
            np.add.at(occ, pc, 1)
        return (pc, np.stack([p0, p1, p2], 1), np.stack([v0, v1, v2], 1)), counts, occ[:self.g], unsettled


def self_read(counts, occ):
    """Dial lengths read from its own thoughts (local Crofton) -> (l_hat, n_hat). NaN / -1 where it has no data."""
    counts = np.asarray(counts, float); occ = np.asarray(occ, float)
    ok = (occ > 0) & (counts > 0)
    lh = np.full(len(counts), np.nan); lh[ok] = math.pi * AREA_HANDLE / 2 * counts[ok] / (occ[ok] * DT)
    nh = np.full(len(counts), -1, dtype=np.int64); nh[ok] = np.rint(np.log(lh[ok] / ELL0) / DELTA)
    return lh, nh


class Heart:
    """v0.3's valence ledger (genome_v031.MultiLedger), one creature, 9 regions, plus the v0.4 heart speed limit
    (founder decision 10-05): at most one step per region per day of its life, all speakers combined. Bounds are kept
    for the current day only; the creature logs every event."""

    def __init__(self):
        self.k = np.full(len(REGIONS), HEART_BIRTH, dtype=np.int64)
        self.steps = {}                                            # (conversation, region) -> steps used today
        self.day = 0
        self.day_used = set()                                      # regions that moved today

    def new_day(self, day):
        if day != self.day:
            self.day, self.steps, self.day_used = day, {}, set()

    def event(self, region: int, sign: int, conversation: str, day: int):
        self.new_day(day)
        key = (conversation, region)
        new = int(self.k[region]) + int(np.sign(sign))
        if sign == 0:
            return False, "no sign"
        if self.steps.get(key, 0) >= 1:
            return False, "refused: bound (one step per region per conversation)"
        if region in self.day_used:
            return False, "refused: heart speed limit (one step per region per day)"
        if not 0 <= new < HEART_STATES:
            return False, "refused: edge of capacity"
        self.k[region] = new
        self.steps[key] = self.steps.get(key, 0) + 1
        self.day_used.add(region)
        return True, "accepted"
