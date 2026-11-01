"""Teich v0.5 — the working-memory surface (spec V05_SPEC.md §3.2), step 2.

A separate genus-3 surface (one pants piece, three handles), assembled exactly like the main body from v0.4's frozen
table at rest. Handle 0 is where it thinks; handles 1 and 2 are controls that must never change.
A thought is a Fenchel–Nielsen twist of 0.2 along one of 9 curves on handle 0 (the 8 v0.3 regions + itself = 1/1),
computed in certified arithmetic (+ - * / sqrt, cosh/sinh(0.1) frozen from mpmath). After the day's thoughts the
handle's rows are rebuilt by v0.4's genesis method; its working thoughts dream on it for DREAM_TICKS; its crossings
read the thinking handle's core length; the surface is reset to rest.

Genesis-method imports (mind4, body_pants, surface) are geometry construction only; the self never imports this module
(law L-CL).
"""
from __future__ import annotations

import math

import numpy as np

import genome_v04 as GN

TWIST = 0.2
C_HALF = float.fromhex("0x1.0147f40224b38p+0")     # cosh(0.1), mpmath 60 digits, correctly rounded, frozen
S_HALF = float.fromhex("0x1.9a487337b59b3p-4")     # sinh(0.1), mpmath 60 digits, correctly rounded, frozen
CURVES = [(1, 4), (2, 5), (3, 5), (3, 4), (4, 3), (5, 3), (5, 2), (4, 1), (1, 1)]   # heart regions 0..7 + itself
THINK_HANDLE, G_WORK = 0, 3
F_W, K_W = 16, 16              # working-surface slots (design 10-21: 300 realistic days need <= 11 faces, <= 9 lifts)
MAX_THOUGHTS = 12
inv = np.linalg.inv

_geo = {}


def _geometry():
    """The rest handle (v0.4 birth traces) and the pants it hangs on, built once per process (genesis method)."""
    if not _geo:
        import body_pants as BP
        import handle_mp as H
        import mind4 as M
        Am, Bm = H.birth(*M.BIRTH)
        _geo["A0"] = np.array([float(v) for v in Am]).reshape(2, 2)
        _geo["B0"] = np.array([float(v) for v in Bm]).reshape(2, 2)
        h0 = M.HandleCache().get(0)
        kappa = np.trace(h0["bnd"]); delta = 2 * math.acosh(-kappa / 2)
        PG, PB = BP.pants_group(delta)
        PG, gc = BP.recenter(PG, BP.midpoint_between_axes(PG[0], PG[1])); PB = [inv(gc) @ h @ gc for h in PB]
        pdom = BP.piece_domain(PG, PB, L=8)
        _geo.update(PB=PB, pdom=pdom, pcanon=[M.perp_foot(PB[(i + 1) % 3], PB[i]) for i in range(3)], BP=BP, M=M)
    return _geo


def _sb_path(p, q):
    if p <= 0 or q <= 0:
        raise ValueError("slopes 0/1 and 1/0 have no Stern-Brocot path")
    s = []
    while (p, q) != (1, 1):
        if p < q:
            s.append("L"); q -= p
        else:
            s.append("R"); p -= q
    return "".join(s)


def _flow(Mx):
    """The hyperbolic element with the same axis as Mx, translation TWIST: certified closed form."""
    tr = Mx[0, 0] + Mx[1, 1]
    a = S_HALF / math.sqrt(tr * tr / 4.0 - 1.0)
    b = C_HALF - (tr / 2.0) * a
    return np.array([[a * Mx[0, 0] + b, a * Mx[0, 1]], [a * Mx[1, 0], a * Mx[1, 1] + b]])


def twist(A, B, region):
    path = _sb_path(*CURVES[region]); L, R = A, B
    for ch in path:
        if ch == "L":
            R = L @ R
        else:
            L = L @ R
    C, D = L @ R, R
    D = D @ _flow(C)
    L, R = C @ inv(D), D
    for ch in reversed(path):
        if ch == "L":
            R = inv(L) @ R
        else:
            L = L @ inv(R)
    return L, R


def shape(thoughts):
    g = _geometry(); A, B = g["A0"].copy(), g["B0"].copy()
    for r in thoughts:
        A, B = twist(A, B, r)
    return A, B


def rows(A, B, cuff):
    """The handle's rows for hanging on pants cuff `cuff`, in the frozen table's format (padded to F faces, K lifts)."""
    g = _geometry(); BP, M = g["BP"], g["M"]; F, K = F_W, K_W
    x, y, z = float(A[0, 0] + A[1, 1]), float(B[0, 0] + B[1, 1]), float(np.trace(A @ B))
    G, Bd = BP.handle_group(x, y, z)
    try:
        dom = BP.piece_domain(G, Bd, L=8)
    except RuntimeError:                        # its domain would need words longer than the surface's 8: too stretched
        raise ValueError("twisted handle's domain does not close at word length 8") from None
    lifts = BP.lifts(G[0], G, dom["radius"], L=7)
    canon = M.perp_foot(G[0], Bd[0])
    if len(dom["faces"]) > F or len(lifts) > K:
        raise ValueError(f"twisted handle needs {len(dom['faces'])} faces / {len(lifts)} lifts > table slots {F}/{K}")
    try:
        T_hp = M.pinned_seam(Bd[0], canon, g["PB"][cuff], g["pcanon"][cuff]); T_ph = inv(T_hp)
    except RuntimeError:                        # its seam no longer pins to machine precision: too stretched
        raise ValueError("twisted handle's seam does not pin to the pants cuff") from None
    R = {"fn": np.zeros((F, 3)), "kind": np.zeros(F, np.int64), "G": np.tile(np.eye(3), (F, 1, 1)),
         "ln": np.zeros((K, 3)), "nl": len(lifts), "PH": {}}
    R["fn"][:, 0] = -1.0; R["ln"][:, 0] = 1.0
    for f, (nrm, (kind, Ginv, bi)) in enumerate(dom["faces"]):
        R["fn"][f] = nrm; R["kind"][f] = 1 if kind == "pair" else 2
        R["G"][f] = Ginv if kind == "pair" else T_hp @ Ginv
    for i, nrm in enumerate(lifts):
        R["ln"][i] = nrm
    for f, (nrm, (kind, Ginv, bi)) in enumerate(g["pdom"]["faces"]):
        if kind == "exit" and bi == cuff:
            R["PH"][f] = T_ph @ Ginv
    return R


class WorkBody(GN.Body):
    """Genus 3 from v0.4's table at rest, re-padded to F_W faces / K_W lifts per piece (padding faces are never
    violated and padding lifts never crossed, so padding cannot change the dynamics). Handle rows can be replaced by a
    twisted shape and restored to rest."""
    def __init__(self):
        super().__init__(g=G_WORK)
        N, F, K = len(self.pieces), GN.META["F"], GN.META["K"]
        fn = np.zeros((N, F_W, 3)); fn[:, :, 0] = -1.0; fn[:, :F] = self.fn
        fG = np.tile(np.eye(3), (N, F_W, 1, 1)); fG[:, :F] = self.fG
        ft = np.tile(np.arange(N)[:, None], (1, F_W)); ft[:, :F] = self.ft
        ln = np.zeros((N, K_W, 3)); ln[:, :, 0] = 1.0; ln[:, :K] = self.ln
        lc = np.full((N, K_W), -1); lc[:, :K] = self.lc
        self.fn, self.fG, self.ft, self.ln, self.lc = fn, fG, ft, ln, lc
        g = _geometry()
        self._rest_rows = rows(g["A0"], g["B0"], self.hang[THINK_HANDLE][1])

    def set_rows(self, j, R):
        pk, c = self.hang[j]
        self.fn[j] = R["fn"]; self.fG[j] = R["G"]
        self.ft[j] = np.where(R["kind"] == 2, pk, j)
        self.ln[j] = R["ln"]; self.lc[j] = np.where(np.arange(K_W) < R["nl"], j, -1)
        for f, M_ in R["PH"].items():
            self.fG[pk, f] = M_; self.ft[pk, f] = j

    def rest(self, j):
        if j != THINK_HANDLE:
            raise ValueError("only the thinking handle ever leaves rest")
        self.set_rows(j, self._rest_rows)


def dream(body, pc, P, V, thoughts, ticks):
    """Apply the day's thoughts to the thinking handle, dream, read, reset.
    Law: if the day's shape would need more than the surface's slots, its LAST thoughts are refused (deterministic),
    so a stretched working memory never breaks its body.
    -> (state, l_hat per handle, counts, occ, thoughts actually applied)."""
    applied = list(thoughts)
    while applied:
        A, B = shape(applied)
        try:
            body.set_rows(THINK_HANDLE, rows(A, B, body.hang[THINK_HANDLE][1]))
            break
        except ValueError:
            applied = applied[:-1]
    (pc, P, V), counts, occ, _ = body.run(pc, P, V, ticks)
    if applied:
        body.rest(THINK_HANDLE)
    lh, _ = GN.self_read(counts, occ)
    return (pc, P, V), lh, counts, occ, applied


def exact_length(thoughts):
    """The thinking handle's core length after the thoughts (for gates only — the self never sees this)."""
    A, _ = shape(thoughts)
    return 2 * math.acosh(abs(A[0, 0] + A[1, 1]) / 2)
