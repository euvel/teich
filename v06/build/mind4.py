"""v0.4 mind engine (design phase). The creature's memory state is an integer per cluster dial (n_j); the geometry is
DERIVED from it, never accumulated, so it cannot drift:

  handle j at state n  =  FN move of the birth handle along its dial by stretch = DELTA * n  (twist and seam fixed)

Every seam is PINNED: the gluing maps a canonical point of one side's seam axis onto the other side's canonical point
(handle: foot of the perpendicular from its dial; pants cuff i: foot of the perpendicular from cuff i+1), so a dial move
changes nothing about how pieces are glued. Changing a dial updates only that handle's rows (its faces, its seam map
and the neighbouring pants' faces that point into it).
"""
from __future__ import annotations

import math
import numpy as np

import surface as S
import body_pants as BP
import handle_mp as H

inv = np.linalg.inv
J = np.array([-1.0, 1.0, 1.0])
DELTA = 0.05                     # one step = 5% of dial length
N_MAX = 10                       # dials live in -10..10 steps (e^{±0.5}); edges refuse
BIRTH = (3.2, 3.2, 3.2)


def perp_foot(h_from, h_on):
    n1, n2 = BP.axis_n(h_from), BP.axis_n(h_on)
    return BP.foot(n2, np.cross(J * n1, J * n2))


def translation_along(h, s):
    """Lorentz matrix translating by s (signed, units of distance) along the axis of hyperbolic h."""
    a = h if np.trace(h) > 0 else -h
    w, P = np.linalg.eig(a); P = P.real[:, np.argsort(-w.real)]; lam = float(max(w.real))
    ell = 2 * math.log(lam)
    E = P @ np.diag([math.exp(s / 2), math.exp(-s / 2)]) @ inv(P)
    return S.adj(E), ell


def signed_dist_along(h, x, y):
    R = S.adj(h); d = math.acosh(max(1.0, -S.mink(x, y)))
    return d if -S.mink(y, R @ x) < -S.mink(y, inv(R) @ x) else -d


def pinned_seam(h_from, x_from, h_to, x_to, tau=0.0):
    T = BP.seam_map(h_from, h_to)
    y = T @ x_from
    d = signed_dist_along(h_to, x_to, y)
    for sgn in (-1, 1):
        E, _ = translation_along(h_to, sgn * d + tau)
        T2 = E @ T
        ch = -S.mink(T2 @ x_from, x_to)                   # cosh of the residual; the wrong branch is >= 0.45 away
        if (ch - 1 < 1e-10) if tau == 0 else (math.acosh(max(1.0, ch)) < 1e-6 + abs(tau)):
            return T2
    raise RuntimeError("seam pinning failed")


class HandleCache:
    def __init__(self, L=8):
        self.L = L; self.c = {}

    def get(self, n):
        if n not in self.c:
            A0, B0 = H.birth(*BIRTH)
            A, B = H.move_A(A0, B0, stretch=DELTA * n) if n else (A0, B0)
            x, y, z = float(H.tr(A)), float(H.tr(B)), float(H.tr(H.mul(A, B)))
            G, Bd = BP.handle_group(x, y, z)
            dom = BP.piece_domain(G, Bd, L=self.L)
            dial_lifts = BP.lifts(G[0], G, dom["radius"], L=7)
            self.c[n] = {"G": G, "bnd": Bd[0], "dom": dom, "canon": perp_foot(G[0], Bd[0]),
                         "dial_len": S.length(G[0]), "dial_lifts": dial_lifts}
        return self.c[n]


class Mind:
    def __init__(self, g, L=8, Fmax=16, Kmax=24):
        self.g = g; self.hc = HandleCache(L)
        h0 = self.hc.get(0)
        kappa = np.trace(h0["bnd"]); delta = 2 * math.acosh(-kappa / 2)
        PG, PB = BP.pants_group(delta)
        PG, gc = BP.recenter(PG, BP.midpoint_between_axes(PG[0], PG[1])); PB = [inv(gc) @ h @ gc for h in PB]
        self.PB = PB; self.pdom = BP.piece_domain(PG, PB, L=L)
        self.pcanon = [perp_foot(PB[(i + 1) % 3], PB[i]) for i in range(3)]
        pants, edges = BP.trivalent_tree(g)
        self.pieces = [("H", j) for j in range(g)] + [("P", i) for i in range(len(pants))]
        self.idx = {p: k for k, p in enumerate(self.pieces)}
        self.edges = edges
        self.n = np.zeros(g, dtype=np.int64)
        N = len(self.pieces)
        self.fn = np.zeros((N, Fmax, 3)); self.fn[:, :, 0] = -1.0
        self.fG = np.tile(np.eye(3), (N, Fmax, 1, 1)); self.ft = np.tile(np.arange(N)[:, None], (1, Fmax))
        self.ln = np.zeros((N, Kmax, 3)); self.ln[:, :, 0] = 1.0; self.lc = np.full((N, Kmax), -1)
        self.curve_names = [(j, "dial") for j in range(g)]
        self.handle_of_seam = {}
        for (a, b) in edges:
            if b[0] == "H":
                self.handle_of_seam[b[1]] = (self.idx[a[:2]], a[2])          # handle j hangs on (pants piece, cuff)
        self.pp_link = {}
        for (a, b) in edges:
            if a[0] == "P" and b[0] == "P":
                ka, kb = self.idx[a[:2]], self.idx[b[:2]]
                T = pinned_seam(PB[a[2]], self.pcanon[a[2]], PB[b[2]], self.pcanon[b[2]])
                self.pp_link[(ka, a[2])] = (kb, T); self.pp_link[(kb, b[2])] = (ka, inv(T))
        for k, (t, i) in enumerate(self.pieces):
            if t == "P":
                self._write_pants(k)
        for j in range(g):
            self._write_handle(j)

    # ------------------------------------------------------------------ geometry rows
    def _link_handle(self, j):
        h = self.hc.get(int(self.n[j])); pk, cuff = self.handle_of_seam[j]
        T_hp = pinned_seam(h["bnd"], h["canon"], self.PB[cuff], self.pcanon[cuff])
        return pk, cuff, T_hp

    def _write_handle(self, j):
        h = self.hc.get(int(self.n[j])); pk, cuff, T_hp = self._link_handle(j)
        self.fn[j] = 0; self.fn[j, :, 0] = -1.0; self.fG[j] = np.eye(3); self.ft[j] = j
        for f, (nrm, (kind, Ginv, bi)) in enumerate(h["dom"]["faces"]):
            self.fn[j, f] = nrm
            if kind == "pair":
                self.fG[j, f] = Ginv
            else:
                self.fG[j, f] = T_hp @ Ginv; self.ft[j, f] = pk
        self.ln[j] = 0; self.ln[j, :, 0] = 1.0; self.lc[j] = -1
        for i, nrm in enumerate(h["dial_lifts"]):
            self.ln[j, i] = nrm; self.lc[j, i] = j
        # the pants faces pointing into this handle
        for f, (nrm, (kind, Ginv, bi)) in enumerate(self.pdom["faces"]):
            if kind == "exit" and bi == cuff:
                self.fG[pk, f] = inv(T_hp) @ Ginv; self.ft[pk, f] = j

    def _write_pants(self, k):
        for f, (nrm, (kind, Ginv, bi)) in enumerate(self.pdom["faces"]):
            self.fn[k, f] = nrm
            if kind == "pair":
                self.fG[k, f] = Ginv
            elif (k, bi) in self.pp_link:
                tgt, T = self.pp_link[(k, bi)]; self.fG[k, f] = T @ Ginv; self.ft[k, f] = tgt
            # faces into handles are written by _write_handle

    def set_dial(self, j, n):
        self.n[j] = n; self._write_handle(j)

    # ------------------------------------------------------------------ life
    def area(self, k):
        t, i = self.pieces[k]
        return self.hc.get(int(self.n[i]))["dom"]["area"] if t == "H" else self.pdom["area"]

    @property
    def doms(self):
        return {k: ({"area": self.area(k), "radius": (self.hc.get(int(self.n[self.pieces[k][1]]))["dom"]["radius"]
                     if self.pieces[k][0] == "H" else self.pdom["radius"])}) for k in range(len(self.pieces))}

    def start(self, n, seed):
        self.area_total = sum(self.area(k) for k in range(len(self.pieces)))
        return BP.Surface.start(self, n, seed)

    def run(self, piece, P, V, ticks, hash_every=0):
        return BP.Surface.run(self, piece, P, V, ticks, hash_every)

    def dial_true(self, j):
        return self.hc.get(int(self.n[j]))["dial_len"]

    def self_read(self, counts, occ, dt):
        """Local Crofton: l_hat_j = (pi * area_j / 2) * crossings_j / time_in_j."""
        a = np.array([self.area(j) for j in range(self.g)])
        return counts[:self.g] / np.maximum(occ[:self.g] * dt, 1e-12) * math.pi * a / 2
