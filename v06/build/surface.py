"""v0.4 design probe — a closed genus-2 hyperbolic surface built from two handles (one-holed tori)
glued along a separating curve C, and the geodesic flow on it. Design phase only.

Model: hyperboloid {p : <p,p> = -1, p0 > 0} in R^{2,1}, <a,b> = -a0 b0 + a1 b1 + a2 b2.
SL(2,R) acts through its adjoint representation on sl(2,R) ~ R^{2,1}; base point o = (1,0,0).

Handle i is given by trace coordinates (x, y, z) = (tr A, tr B, tr AB), all > 2, with
kappa = tr[A,B] = x^2 + y^2 + z^2 - xyz - 2 < -2 (geodesic boundary). Both handles share kappa;
handle 2 is conjugated so that [A1,B1][A2,B2] = 1. The gluing twist along C is a free parameter.

THE TICK uses only +, -, *, / and sqrt (all correctly rounded in IEEE 754), element by element, in a
fixed order — no BLAS, no transcendental functions — so it can be bit-identical across machines.
Everything transcendental (cosh dt, group matrices) is computed once, outside the tick.
"""
from __future__ import annotations

import itertools
import math

import numpy as np

O = np.array([1.0, 0.0, 0.0])
_E = [np.array([[0., 1.], [-1., 0.]]), np.array([[1., 0.], [0., -1.]]), np.array([[0., 1.], [1., 0.]])]


def mink(a, b):
    return -a[..., 0] * b[..., 0] + a[..., 1] * b[..., 1] + a[..., 2] * b[..., 2]


def adj(g):
    """SL(2,R) element -> 3x3 Lorentz matrix (columns = images of the basis)."""
    gi = np.linalg.inv(g)
    cols = []
    for e in _E:
        X = g @ e @ gi
        cols.append([(X[0, 1] - X[1, 0]) / 2, X[0, 0], (X[0, 1] + X[1, 0]) / 2])
    return np.array(cols).T


def length(g):
    return 2 * math.acosh(abs(np.trace(g)) / 2)


def handle(x, y, z):
    lam = (x + math.sqrt(x * x - 4)) / 2
    A = np.diag([lam, 1 / lam])
    p = (z - y / lam) / (lam - 1 / lam); s = y - p
    B = np.array([[p, 1.0], [p * s - 1, s]])
    return A, B


def comm(a, b):
    return a @ b @ np.linalg.inv(a) @ np.linalg.inv(b)


def z_for(x, y, kappa):
    """Larger root z of z^2 - xy z + (x^2 + y^2 - 2 - kappa) = 0."""
    b, c = -x * y, x * x + y * y - 2 - kappa
    return (-b + math.sqrt(b * b - 4 * c)) / 2


def genus2(h1=(3.2, 3.2, 3.2), h2xy=(3.0, 3.6), glue=0.0, twist_a1=0.0):
    """Generators [a1, b1, a2, b2] in SL(2,R). twist_a1 = Fenchel–Nielsen twist along a1 (B1 -> B1 E_t)."""
    A1, B1 = handle(*h1)
    B1 = B1 @ np.diag([math.exp(twist_a1 / 2), math.exp(-twist_a1 / 2)])
    kappa = np.trace(comm(A1, B1))
    x2, y2 = h2xy
    A2, B2 = handle(x2, y2, z_for(x2, y2, kappa))
    C1i, C2 = np.linalg.inv(comm(A1, B1)), comm(A2, B2)
    w1, P1 = np.linalg.eig(C1i); w2, P2 = np.linalg.eig(C2)
    P1 = P1[:, np.argsort(w1.real)].real; P2 = P2[:, np.argsort(w2.real)].real
    M = P1 @ np.linalg.inv(P2)
    if np.linalg.det(M) < 0:
        P2[:, 0] *= -1; M = P1 @ np.linalg.inv(P2)
    M = M / math.sqrt(np.linalg.det(M))
    # gluing twist: translate along the axis of C1 (commutes with C1)
    d = np.diag([math.exp(glue / 2), math.exp(-glue / 2)])
    M = P1 @ d @ np.linalg.inv(P1) @ M
    a2, b2 = M @ A2 @ np.linalg.inv(M), M @ B2 @ np.linalg.inv(M)
    gens = [A1, B1, a2, b2]
    rel = comm(A1, B1) @ comm(a2, b2)
    return gens, float(np.abs(rel - np.eye(2)).max()), kappa


def words(gens, L):
    inv = [np.linalg.inv(g) for g in gens]
    letters = gens + inv                                    # index i and i+4 are inverses
    out = {(): np.eye(2)}
    frontier = {(): np.eye(2)}
    for _ in range(L):
        nxt = {}
        for w, m in frontier.items():
            for i, g in enumerate(letters):
                if w and (w[-1] - i) % 8 == 4:
                    continue
                nxt[w + (i,)] = m @ g
        out.update(nxt); frontier = nxt
    return out


def dirichlet(gens, L=5, keep=400):
    """Dirichlet polygon at o, clipped in the Klein model. Returns faces (group elements, Lorentz) and area."""
    W = words(gens, L)
    cand = []
    for w, m in W.items():
        if not w:
            continue
        R = adj(m); q = R[:, 0]
        cand.append((q[0], w, R))
    cand.sort(key=lambda t: t[0]); cand = cand[:keep]
    poly = [np.array(v, float) for v in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    owners = [None] * 4
    for _, w, R in cand:
        n = O - R[:, 0]
        f = lambda k: -n[0] + n[1] * k[0] + n[2] * k[1]
        new, new_own = [], []
        for i in range(len(poly)):
            P, Q = poly[i], poly[(i + 1) % len(poly)]
            fp, fq = f(P), f(Q)
            if fp >= 0:
                new.append(P); new_own.append(owners[i])
            if (fp >= 0) != (fq >= 0):
                tt = fp / (fp - fq); new.append(P + tt * (Q - P)); new_own.append((w, R) if fp >= 0 else owners[i])
        poly, owners = new, new_own
    faces = {}
    for o in owners:
        if o is None:
            raise RuntimeError("polygon not closed by group elements — not a compact fundamental domain")
        faces[o[0]] = o[1]
    # area by Gauss–Bonnet for polygons: (N-2) pi - sum of interior angles
    N = len(poly); ang = 0.0
    for i in range(N):
        a = owners[i - 1][1][:, 0]; b = owners[i][1][:, 0]
        na, nb = O - a, O - b
        na = na / math.sqrt(mink(na, na)); nb = nb / math.sqrt(mink(nb, nb))
        ang += math.acos(max(-1, min(1, -mink(na, nb))))
    area = (N - 2) * math.pi - ang
    rad = max(math.acosh(1 / math.sqrt(1 - v @ v)) for v in poly)
    return {"faces": list(faces.items()), "area": area, "n_sides": N, "circumradius": rad, "klein_vertices": poly}


def axis_normal(R):
    """Unit spacelike normal of the axis of a hyperbolic Lorentz matrix (its eigenvalue-1 eigenvector)."""
    w, V = np.linalg.eig(R)
    n = V[:, np.argmin(np.abs(w - 1))].real
    return n / math.sqrt(mink(n, n))


def lifts(h, gens, rad, L=5, margin=0.3, tol=1e-4):
    """Normals of all lifts of the closed geodesic of h passing within rad+margin of o (deduplicated
    with a tolerance: the same lift reached by different words differs by rounding)."""
    nh = axis_normal(adj(h)); kept = []
    for w, m in words(gens, L).items():
        n = adj(m) @ nh
        if math.asinh(abs(mink(n, O))) < rad + margin:
            n = n * np.sign(n[np.argmax(np.abs(n))])
            if not any(np.abs(n - k).max() < tol * max(1.0, np.abs(k).max()) for k in kept):
                kept.append(n)
    return np.array(kept)
