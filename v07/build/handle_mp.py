"""handle_geo in 80-digit arithmetic (design analysis only; the creature's body never needs this).
2x2 matrices as tuples (a, b, c, d)."""
from __future__ import annotations

import mpmath as mp

mp.mp.dps = 80


def mul(X, Y):
    a, b, c, d = X; e, f, g, h = Y
    return (a * e + b * g, a * f + b * h, c * e + d * g, c * f + d * h)


def inv(X):
    a, b, c, d = X; det = a * d - b * c
    return (d / det, -b / det, -c / det, a / det)


def tr(X):
    return X[0] + X[3]


def length(X):
    return 2 * mp.acosh(abs(tr(X)) / 2)


def birth(x=3.2, y=3.2, z=3.2):
    x, y, z = mp.mpf(x), mp.mpf(y), mp.mpf(z)
    lam = (x + mp.sqrt(x * x - 4)) / 2
    p = (z - y / lam) / (lam - 1 / lam); s = y - p
    return (lam, mp.mpf(0), mp.mpf(0), 1 / lam), (p, mp.mpf(1), p * s - 1, s)


def walk(A, B, path):
    L, R = A, B
    for ch in path:
        if ch == "L":
            R = mul(L, R)
        else:
            L = mul(L, R)
    return L, R


def lengths(A, B, paths):
    """All concept lengths, sharing prefixes."""
    memo = {"": (A, B)}
    def node(p):
        if p not in memo:
            L, R = node(p[:-1])
            memo[p] = (L, mul(L, R)) if p[-1] == "L" else (mul(L, R), R)
        return memo[p]
    out = []
    for p in paths:
        L, R = node(p)
        out.append(length(mul(L, R)))
    return out


def move(A, B, path, stretch=0, twist=0):
    L, R = walk(A, B, path)
    c = mul(L, R)
    kappa = tr(mul(mul(A, B), mul(inv(A), inv(B))))
    t = tr(c); sg = 1 if t > 0 else -1
    lam = (t + sg * mp.sqrt(t * t - 4)) / 2
    a, b, cc, d = c
    v1 = (b, lam - a) if abs(b) > abs(cc) else (lam - d, cc)
    mu = 1 / lam
    v2 = (b, mu - a) if abs(b) > abs(cc) else (mu - d, cc)
    P = (v1[0], v2[0], v1[1], v2[1]); Pi = inv(P)
    p, q, r, s = mul(mul(Pi, R), P)
    rho = p / s
    l_new = 2 * mp.log(abs(lam)) * mp.e ** stretch
    lam2 = sg * mp.e ** (l_new / 2)
    rho2 = rho * mp.e ** twist
    s2sq = (lam2 ** 2 + lam2 ** -2 - kappa) / (rho2 * (lam2 - 1 / lam2) ** 2)
    if s2sq <= 0:
        raise ValueError("move leaves the Teichmüller space of the handle")
    s2 = mp.sqrt(s2sq) * (1 if s > 0 else -1); p2 = rho2 * s2
    C2 = (lam2, mp.mpf(0), mp.mpf(0), 1 / lam2); R2 = (p2, q, (p2 * s2 - 1) / q, s2)
    L2 = mul(C2, inv(R2))
    for ch in reversed(path):
        if ch == "L":
            R2 = mul(inv(L2), R2)
        else:
            L2 = mul(L2, inv(R2))
    return L2, R2


def move_A(A, B, stretch=0, twist=0):
    """Fenchel–Nielsen move along the handle's own curve A (the CLUSTER curve), boundary fixed.
    In the eigenbasis of A, B = [[p, q], [r, s]]; FN twist tau = log(p/s) (tau = 0 at the shortest transversal);
    stretch changes l(A) by e^stretch at fixed tau; twist adds to tau."""
    kappa = tr(mul(mul(A, B), mul(inv(A), inv(B))))
    t = tr(A); sg = 1 if t > 0 else -1
    lam = (t + sg * mp.sqrt(t * t - 4)) / 2
    a, b, cc, d = A
    v1 = (b, lam - a) if abs(b) > abs(cc) else (lam - d, cc)
    v2 = (b, 1 / lam - a) if abs(b) > abs(cc) else (1 / lam - d, cc)
    if A[1] == 0 and A[2] == 0:
        v1, v2 = ((1, 0), (0, 1)) if abs(A[0]) > abs(A[3]) else ((0, 1), (1, 0))
    P = (mp.mpf(v1[0]), mp.mpf(v2[0]), mp.mpf(v1[1]), mp.mpf(v2[1])); Pi = inv(P)
    p, q, r, s = mul(mul(Pi, B), P)
    rho2 = (p / s) * mp.e ** twist
    lam2 = sg * mp.e ** (mp.log(abs(lam)) * mp.e ** stretch)
    s2 = mp.sqrt((lam2 ** 2 + lam2 ** -2 - kappa) / (rho2 * (lam2 - 1 / lam2) ** 2)) * (1 if s > 0 else -1)
    p2 = rho2 * s2
    return (lam2, mp.mpf(0), mp.mpf(0), 1 / lam2), (p2, q, (p2 * s2 - 1) / q, s2)
