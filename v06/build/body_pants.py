"""K12 — the pants-local body: a closed surface of genus g built as g handles (one-holed tori, the concept clusters)
hanging off a trivalent tree of g-2 pairs of pants. Each piece has its OWN local hyperbolic frame and a small
fundamental polygon of its convex core; a particle carries (piece, p, v). Per tick it checks only its piece's faces:
  - 'pair' face  -> apply the piece's own group element (stays in the piece);
  - 'exit' face  -> cross a seam: map into the neighbour piece's frame (and switch piece).
Every face is stored as one Lorentz matrix + a target piece, so the tick is uniform and element-wise (+ - * / sqrt),
and its cost does not depend on g.
"""
from __future__ import annotations

import hashlib, math
import numpy as np

import surface as S

inv = np.linalg.inv
DT = 0.05
C_DT = float.fromhex("0x1.0051efe3b1bc3p+0"); S_DT = float.fromhex("0x1.99c54bcf10dfbp-5")


def mk(a0, a1, a2, b0, b1, b2):
    return -a0 * b0 + a1 * b1 + a2 * b2


def to_hyp(z):
    x, y = z.real, z.imag
    return np.array([(x * x + y * y + 1) / (2 * y), -x / y, (x * x + y * y - 1) / (2 * y)])


def from_hyp(p):
    y = 1 / (p[0] - p[2]); return complex(-p[1] * y, y)


def recenter(gens, point):
    """Conjugate the group so that `point` (hyperboloid) becomes o."""
    z = from_hyp(point); a = math.sqrt(z.imag)
    g = np.array([[a, z.real / a], [0, 1 / a]])
    return [inv(g) @ h @ g for h in gens], g


def axis_n(h):
    return S.axis_normal(S.adj(h))


def foot(n, m):
    J = np.array([-1.0, 1.0, 1.0])
    p = np.cross(J * n, J * m)
    p = p / math.sqrt(-S.mink(p, p)); return p if p[0] > 0 else -p


def midpoint_between_axes(h1, h2):
    J = np.array([-1.0, 1.0, 1.0])
    n1, n2 = axis_n(h1), axis_n(h2)
    m = np.cross(J * n1, J * n2)
    p1, p2 = foot(n1, m), foot(n2, m); q = p1 + p2
    return q / math.sqrt(-S.mink(q, q))


def handle_group(x=3.2, y=3.2, z=3.2):
    A, B = S.handle(x, y, z)
    return [A, B], [S.comm(A, B)]                      # generators, boundary elements


def pants_group(delta):
    """Pants with three cuffs of length delta: c1 c2 c3 = 1, tr c1 = tr c2 = 2cosh(d/2), tr c1c2 = -2cosh(d/2)."""
    t = 2 * math.cosh(delta / 2)
    lam = (t + math.sqrt(t * t - 4)) / 2
    c1 = np.diag([lam, 1 / lam])
    p = (-t - t / lam) / (lam - 1 / lam); s = t - p
    c2 = np.array([[p, 1.0], [p * s - 1, s]])
    c3 = inv(c1 @ c2)
    return [c1, c2], [c1, c2, c3]


def words(gens, L, maxd=12.0):
    """Reduced words up to length L in any number of generators (letter i and i+k are inverse, k = len(gens))."""
    k = len(gens); letters = gens + [inv(g) for g in gens]
    out = {(): np.eye(2)}; frontier = {(): np.eye(2)}
    for _ in range(L):
        nxt = {}
        for w, m in frontier.items():
            for i, g in enumerate(letters):
                if w and (w[-1] - i) % (2 * k) == k:
                    continue
                mg = m @ g
                if (mg * mg).sum() / 2 < math.cosh(maxd):      # cosh d(o, g o) = |g|_F^2 / 2
                    nxt[w + (i,)] = mg
        out.update(nxt); frontier = nxt
    return out


def lifts(h, gens, rad, L=6, margin=0.3, tol=1e-4):
    nh = axis_n(h); kept = []
    for w, m in words(gens, L).items():
        n = S.adj(m) @ nh
        if math.asinh(abs(S.mink(n, S.O))) < rad + margin:
            n = n * np.sign(n[np.argmax(np.abs(n))])
            if not any(np.abs(n - k).max() < tol * max(1.0, np.abs(k).max()) for k in kept):
                kept.append(n)
    return np.array(kept)


def piece_domain(gens, bnd, L=8, keep=3000, R_lift=6.0):
    """Dirichlet polygon at o of the group, clipped by the boundary lifts (convex core). Faces carry
    (kind, matrix to apply on violation, boundary index or None)."""
    W = words(gens, L)
    halfs = []
    for w, m in W.items():
        if w:
            R = S.adj(m); q = R[:, 0]
            halfs.append((q[0], S.O - R[:, 0], ("pair", inv(R), None)))
    halfs.sort(key=lambda t: t[0]); halfs = halfs[:keep]
    seen = []
    for bi, h in enumerate(bnd):
        nh = axis_n(h)
        for w, m in W.items():
            R = S.adj(m); n = R @ nh
            if math.asinh(abs(S.mink(n, S.O))) > R_lift:
                continue
            n = n if S.mink(n, S.O) > 0 else -n            # interior (o) side positive
            if any(np.abs(n - k).max() < 1e-6 * max(1, np.abs(k).max()) for k in seen):
                continue
            seen.append(n); halfs.append((0.0, n, ("exit", inv(R), bi)))
    poly = [np.array(v, float) for v in ((-1, -1), (1, -1), (1, 1), (-1, 1))]; owners = [None] * 4
    for _, n, tag in sorted(halfs, key=lambda t: t[0]):
        f = lambda k: -n[0] + n[1] * k[0] + n[2] * k[1]
        new, own = [], []
        for i in range(len(poly)):
            P, Q = poly[i], poly[(i + 1) % len(poly)]; fp, fq = f(P), f(Q)
            if fp >= 0:
                new.append(P); own.append(owners[i])
            if (fp >= 0) != (fq >= 0):
                tt = fp / (fp - fq); new.append(P + tt * (Q - P)); own.append((n, tag) if fp >= 0 else owners[i])
        poly, owners = new, own
    if any(o is None for o in owners):
        raise RuntimeError("piece polygon not closed")
    faces, ang = [], 0.0
    for i in range(len(poly)):
        na, nb = owners[i - 1][0], owners[i][0]
        na = na / math.sqrt(S.mink(na, na)); nb = nb / math.sqrt(S.mink(nb, nb))
        ang += math.acos(max(-1, min(1, -S.mink(na, nb))))
    uniq = []
    for n, tag in owners:
        if not any(np.abs(n - u[0]).max() < 1e-9 for u in uniq):
            uniq.append((n, tag))
    area = (len(poly) - 2) * math.pi - ang
    rad = max(math.acosh(1 / math.sqrt(max(1e-300, 1 - v @ v))) for v in poly)
    return {"faces": uniq, "area": area, "radius": rad}


def _conj(a, b):
    """Lorentz adj(M) with M a M^-1 = b (as Mobius), a, b hyperbolic with equal |trace|."""
    a = a if np.trace(a) < 0 else -a; b = b if np.trace(b) < 0 else -b
    wa, Pa = np.linalg.eig(a); wb, Pb = np.linalg.eig(b)
    Pa = Pa[:, np.argsort(wa.real)].real; Pb = Pb[:, np.argsort(wb.real)].real
    M = Pb @ inv(Pa)
    if np.linalg.det(M) < 0:
        Pa[:, 0] *= -1; M = Pb @ inv(Pa)
    return S.adj(M / math.sqrt(np.linalg.det(M)))


def _inward(h):
    n = axis_n(h); return n if S.mink(n, S.O) > 0 else -n


def seam_map(h_from, h_to):
    """Lorentz T from the `from` frame to the `to` frame across the seam: T maps the from-axis onto the to-axis and
    the OUTSIDE of the from-piece onto the INSIDE of the to-piece (checked, not assumed)."""
    nf, nt = _inward(h_from), _inward(h_to)
    pf = S.O - S.mink(S.O, nf) * nf; pf = pf / math.sqrt(-S.mink(pf, pf))
    x = math.cosh(0.01) * pf - math.sinh(0.01) * nf                       # just outside the from-piece
    for T in (_conj(h_from, inv(h_to)), _conj(h_from, h_to)):
        if S.mink(nt, T @ x) > 0:
            return T
    raise RuntimeError("no orientation of the seam map puts the outside of one piece inside the other")


def trivalent_tree(g):
    """Pants tree with g leaves (handles). Returns list of edges between ('P', i, cuff) / ('H', j, 0) ends."""
    pants = [[("H", 0), ("H", 1), ("H", 2)]]; nh = 3
    while nh < g:
        # split the shallowest handle leaf: insert a new pants between it and its pants
        pi, ci = min(((i, c) for i, P in enumerate(pants) for c, e in enumerate(P) if e[0] == "H"),
                     key=lambda t: (t[0], t[1]))
        old = pants[pi][ci]; new = len(pants)
        pants[pi][ci] = ("P", new)
        pants.append([("P", pi), old, ("H", nh)]); nh += 1
        # move to breadth-first balance: rotate the list so later splits use other pants
        pants.append(pants.pop(0)) if False else None
    edges = []
    for i, P in enumerate(pants):
        for c, e in enumerate(P):
            if e[0] == "H":
                edges.append((("P", i, c), ("H", e[1], 0)))
            elif e[1] > i:
                j = e[1]; cj = next(k for k, x in enumerate(pants[j]) if x == ("P", i))
                edges.append((("P", i, c), ("P", j, cj)))
    return pants, edges


class Surface:
    def __init__(self, g, handle_traces=None, L=8):
        self.g = g
        HG, HB = handle_group()
        kappa = np.trace(HB[0]); delta = 2 * math.acosh(-kappa / 2)
        PG, PB = pants_group(delta)
        PG2, gc = recenter(PG, midpoint_between_axes(PG[0], PG[1])); PB = [inv(gc) @ h @ gc for h in PB]; PG = PG2
        self.dom = {"H": piece_domain(HG, HB, L=L), "P": piece_domain(PG, PB, L=L)}
        handle_traces = handle_traces or {}
        pants, edges = trivalent_tree(g)
        self.pieces = [("H", j) for j in range(g)] + [("P", i) for i in range(len(pants))]
        idx = {p: k for k, p in enumerate(self.pieces)}
        self.hgroups = {}
        for j in range(g):
            G, Bd = handle_group(*handle_traces.get(j, (3.2, 3.2, 3.2)))
            self.hgroups[j] = (G, Bd)
        bnd_elem = lambda t, i, c: (self.hgroups[i][1][0] if t == "H" else PB[c])
        link = {}
        for (a, b) in edges:
            ka, kb = idx[a[:2]], idx[b[:2]]
            Ta = seam_map(bnd_elem(*a), bnd_elem(*b))
            link[(ka, a[2])] = (kb, Ta); link[(kb, b[2])] = (ka, inv(Ta))
        # per-piece domains: handles with non-birth traces get their own domain
        doms = {}
        Fmax = 0
        for k, (t, i) in enumerate(self.pieces):
            if t == "H" and i in handle_traces:
                doms[k] = piece_domain(self.hgroups[i][0], self.hgroups[i][1], L=L)
            else:
                doms[k] = self.dom[t]
            Fmax = max(Fmax, len(doms[k]["faces"]))
        n = len(self.pieces)
        self.fn = np.zeros((n, Fmax, 3)); self.fn[:, :, 0] = -1.0            # padding: never violated
        self.fG = np.tile(np.eye(3), (n, Fmax, 1, 1)); self.ft = np.tile(np.arange(n)[:, None], (1, Fmax))
        for k in range(n):
            for f, (nrm, (kind, Ginv, bi)) in enumerate(doms[k]["faces"]):
                self.fn[k, f] = nrm
                if kind == "pair":
                    self.fG[k, f] = Ginv
                else:
                    tgt, T = link[(k, bi)]
                    self.fG[k, f] = T @ Ginv; self.ft[k, f] = tgt
        self.area_total = sum(doms[k]["area"] for k in range(n)); self.doms = doms

    def add_curves(self, per_handle: dict, L=7):
        """per_handle: {handle j: {name: element}} -> lifts near each handle's domain."""
        rows = []; self.curve_names = []
        cache = {}
        for j, cs in per_handle.items():
            G = self.hgroups[j][0]; k = j
            for name, h in cs.items():
                key = (G[0].tobytes(), G[1].tobytes(), h.tobytes())
                if key not in cache:
                    cache[key] = lifts(h, G, self.doms[k]["radius"], L=L)
                for nrm in cache[key]:
                    rows.append((k, len(self.curve_names), nrm))
                self.curve_names.append((j, name, S.length(h)))
        n = len(self.pieces); per = [[r for r in rows if r[0] == k] for k in range(n)]
        Kmax = max(1, max(len(p) for p in per))
        self.ln = np.zeros((n, Kmax, 3)); self.ln[:, :, 0] = 1.0              # padding: a "normal" never crossed
        self.lc = np.full((n, Kmax), -1)
        for k in range(n):
            for i, (_, c, nrm) in enumerate(per[k]):
                self.ln[k, i] = nrm; self.lc[k, i] = c

    def start(self, n, seed):
        """Particles uniform by area over pieces, uniform in each piece's polygon, uniform direction."""
        rng = np.random.default_rng(seed)
        areas = np.array([self.doms[k]["area"] for k in range(len(self.pieces))])
        piece = rng.choice(len(areas), n, p=areas / areas.sum())
        P = np.zeros((n, 3)); V = np.zeros((n, 3))
        for k in np.unique(piece):
            sel = np.nonzero(piece == k)[0]; m = len(sel); got = []
            rad = self.doms[k]["radius"]
            while len(got) < m:
                r = np.arccosh(1 + rng.random(8 * m) * (math.cosh(rad) - 1)); th = rng.random(8 * m) * 2 * math.pi
                p = np.stack([np.cosh(r), np.sinh(r) * np.cos(th), np.sinh(r) * np.sin(th)], 1)
                ok = np.all(mk(*(self.fn[k][None, :, :].transpose(2, 0, 1)), *(p[:, None, :].transpose(2, 0, 1))) >= 0, axis=1)
                got.extend(p[ok])
            P[sel] = np.array(got[:m])
        phi = rng.random(n) * 2 * math.pi
        e = np.stack([np.zeros(n), np.cos(phi), np.sin(phi)], 1)
        V = e + mk(*e.T, *P.T)[:, None] * P; V = V / np.sqrt(mk(*V.T, *V.T))[:, None]
        return piece, P, V

    def run(self, piece, P, V, ticks, hash_every=0):
        pc = piece.copy(); p0, p1, p2 = P.T.copy(); v0, v1, v2 = V.T.copy()
        nc = len(getattr(self, "curve_names", [])); counts = np.zeros(max(nc, 1)); occ = np.zeros(len(self.pieces))
        h = hashlib.sha256(); unsettled = 0; ar = np.arange(len(pc))
        def signs(pc, q0, q1, q2):
            N = self.ln[pc]
            return (-N[:, :, 0] * q0[:, None] + N[:, :, 1] * q1[:, None] + N[:, :, 2] * q2[:, None]) >= 0
        sig_old = signs(pc, p0, p1, p2)
        for t in range(ticks):
            q0 = C_DT * p0 + S_DT * v0; q1 = C_DT * p1 + S_DT * v1; q2 = C_DT * p2 + S_DT * v2
            w0 = S_DT * p0 + C_DT * v0; w1 = S_DT * p1 + C_DT * v1; w2 = S_DT * p2 + C_DT * v2
            r = np.sqrt(-mk(q0, q1, q2, q0, q1, q2)); q0 = q0 / r; q1 = q1 / r; q2 = q2 / r
            c = mk(w0, w1, w2, q0, q1, q2); w0 = w0 + c * q0; w1 = w1 + c * q1; w2 = w2 + c * q2
            r = np.sqrt(mk(w0, w1, w2, w0, w1, w2)); w0 = w0 / r; w1 = w1 / r; w2 = w2 / r
            sig = signs(pc, q0, q1, q2)
            ch = (sig != sig_old) & (self.lc[pc] >= 0)
            if ch.any():
                np.add.at(counts, self.lc[pc][ch], 1)
            for it in range(12):
                N = self.fn[pc]
                val = -N[:, :, 0] * q0[:, None] + N[:, :, 1] * q1[:, None] + N[:, :, 2] * q2[:, None]
                j = np.argmin(val, 1); bad = val[ar, j] < 0
                if not bad.any():
                    break
                G = self.fG[pc[bad], j[bad]]
                a0, a1, a2 = q0[bad], q1[bad], q2[bad]
                q0[bad] = G[:, 0, 0] * a0 + G[:, 0, 1] * a1 + G[:, 0, 2] * a2
                q1[bad] = G[:, 1, 0] * a0 + G[:, 1, 1] * a1 + G[:, 1, 2] * a2
                q2[bad] = G[:, 2, 0] * a0 + G[:, 2, 1] * a1 + G[:, 2, 2] * a2
                a0, a1, a2 = w0[bad], w1[bad], w2[bad]
                w0[bad] = G[:, 0, 0] * a0 + G[:, 0, 1] * a1 + G[:, 0, 2] * a2
                w1[bad] = G[:, 1, 0] * a0 + G[:, 1, 1] * a1 + G[:, 1, 2] * a2
                w2[bad] = G[:, 2, 0] * a0 + G[:, 2, 1] * a1 + G[:, 2, 2] * a2
                pc[bad] = self.ft[pc[bad], j[bad]]
            else:
                unsettled += 1
            sig_old = signs(pc, q0, q1, q2)
            p0, p1, p2, v0, v1, v2 = q0, q1, q2, w0, w1, w2
            np.add.at(occ, pc, 1)
            if hash_every and (t + 1) % hash_every == 0:
                h.update(np.stack([p0, p1, p2, v0, v1, v2]).tobytes()); h.update(pc.tobytes())
        return {"counts": counts, "occ": occ, "unsettled_ticks": unsettled, "hash": h.hexdigest(),
                "state": (pc, np.stack([p0, p1, p2], 1), np.stack([v0, v1, v2], 1))}
