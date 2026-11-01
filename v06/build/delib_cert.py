"""Teich v0.6 certified deliberation (spec V06_SPEC_DRAFT_v1 §2). Pure Python floats, fixed operation order:
+ - * /, math.sqrt, math.floor and % only (each correctly rounded or exact). No libm trigonometry, no numpy.

    u_of(pc0, P01, V02)      the read-out of working particle 0 after a dream
    xi_of(u)                 the point on the circle at turn fraction u (fixed polynomials)
    deliberate(k, u)         -> (choice 0..k-1, steps, rereads, final (x, y), undecided)
"""
import json
import math
from pathlib import Path

_C = json.loads((Path(__file__).resolve().parent / "deliberation_constants_v06.json").read_text())
_f = float.fromhex
HALF_PI = _f(_C["half_pi"])
INV_FACT = [_f(x) for x in _C["inv_fact"]]
K = {int(k): {"walls": v["walls"], "cos_w": _f(v["cos_w"]), "r2": _f(v["r2"]),
              "centre": [(_f(a), _f(b)) for a, b in v["centre"]], "C": [(_f(a), _f(b)) for a, b in v["C"]],
              "gap": [(_f(a), _f(b)) for a, b in v["gap_centre"]]} for k, v in _C["k"].items()}
N_MAX, MAX_REREAD = 400, 8


def u_of(pc0, P01, V02):
    return (1000.0 * (P01 + V02 + 0.618 * pc0)) % 1.0


def _cos_sin(t):
    """cos and sin of t in [0, pi/2] by fixed Horner polynomials (degrees 24 and 25)."""
    t2 = t * t
    # alternating-sign Horner: cos = sum (-1)^m t^(2m)/(2m)!, sin = sum (-1)^m t^(2m+1)/(2m+1)!
    c = INV_FACT[24]
    for m in range(11, -1, -1):
        c = INV_FACT[2 * m] - t2 * c
    s = INV_FACT[25]
    for m in range(11, -1, -1):
        s = INV_FACT[2 * m + 1] - t2 * s
    return c, s * t


def xi_of(u):
    v = 4.0 * u                      # exact (power of two)
    q = math.floor(v); r = v - q     # exact
    c, s = _cos_sin(r * HALF_PI)
    q = int(q) % 4
    if q == 0:
        return c, s
    if q == 1:
        return -s, c
    if q == 2:
        return -c, -s
    return s, -c


def deliberate(k, u):
    G = K[k]; nw = G["walls"]; cw = G["cos_w"]; r2 = G["r2"]
    rereads = 0
    while True:
        x, y = xi_of(u)
        for step in range(N_MAX + 1):
            wall = -1
            for i in range(nw):
                a, b = G["centre"][i]
                if x * a + y * b >= cw:
                    wall = i
                    break
            if wall < 0:
                best, bj = None, -1
                for j in range(nw):
                    a, b = G["gap"][j]
                    d = x * a + y * b
                    if best is None or d > best:
                        best, bj = d, j
                if k == 2 and bj == 2:                       # the "re-read" gap
                    break
                return bj, step, rereads, (x, y), False
            if step == N_MAX:
                return 0, step, rereads, (x, y), True       # index fallback, recorded undecided
            cx, cy = G["C"][wall]
            dx, dy = x - cx, y - cy
            n2 = dx * dx + dy * dy
            x, y = cx + r2 * dx / n2, cy + r2 * dy / n2
            nrm = math.sqrt(x * x + y * y)
            x, y = x / nrm, y / nrm
        rereads += 1
        if rereads > MAX_REREAD:
            return 0, 0, rereads, (x, y), True
        u = (1000.0 * u + 0.618) % 1.0
