"""v0.5 smoke: is a TWISTED working-memory handle's geometry bit-identical across machines?

For a fixed sequence of 12 thoughts (Fenchel-Nielsen twists of 0.3 along concept curves, v0.3 slopes), after each
thought the handle's geometry rows are built exactly as v0.4's genesis builds a handle level (faces, lifts, pinned
seam rows into the pants) and hashed. Two variants of the twist step itself:
  N  numpy as written in design (np.linalg.eig / inv)
  C  certified arithmetic: E = a*M + (c - tr(M)/2 * a) * I with a = s / sqrt(tr(M)^2/4 - 1), where c = cosh(0.15) and
     s = sinh(0.15) are FROZEN bit patterns — only + - * / sqrt at run time
The rest (handle group, domain, lifts, seams) is v0.4's design code unchanged. If every hash matches on every machine,
no fallback is needed.
    python3 geo_smoke.py OUT.json
"""
import hashlib
import json
import math
import platform
import sys

import numpy as np

import body_pants as BP
import mind4 as M

TWIST = 0.2
C_HALF = float.fromhex("0x1.0147f40224b38p+0")     # cosh(0.1), mpmath 60 digits, correctly rounded, frozen
S_HALF = float.fromhex("0x1.9a487337b59b3p-4")     # sinh(0.1), mpmath 60 digits, correctly rounded, frozen
THOUGHTS = [(1, 4), (5, 3), (3, 5), (4, 1), (2, 5), (4, 3), (5, 2), (3, 4), (1, 4), (4, 1), (3, 5), (5, 3)]   # the 8 v0.3 region curves (depth-3 Stern-Brocot nodes)
inv = np.linalg.inv


def sb_path(p, q):
    assert p > 0 and q > 0, "slopes 0/1 and 1/0 have no Stern-Brocot path (would loop forever)"
    s = []
    while (p, q) != (1, 1):
        if p < q:
            s.append("L"); q -= p
        else:
            s.append("R"); p -= q
    return "".join(s)


def to_b(A, B, path):
    L, R = A, B
    for ch in path:
        if ch == "L":
            R = L @ R
        else:
            L = L @ R
    return L, R


def from_b(L, R, path):
    for ch in reversed(path):
        if ch == "L":
            R = inv(L) @ R
        else:
            L = L @ inv(R)
    return L, R


def flow_N(Mx, t):
    w, V = np.linalg.eig(Mx); V = np.real(V)
    if abs(w[0]) < abs(w[1]):
        V = V[:, ::-1]
    return V @ np.diag([math.exp(t / 2), math.exp(-t / 2)]) @ inv(V)


def flow_C(Mx, t):
    assert t == TWIST
    tr = Mx[0, 0] + Mx[1, 1]
    a = S_HALF / math.sqrt(tr * tr / 4.0 - 1.0)
    b = C_HALF - (tr / 2.0) * a
    return np.array([[a * Mx[0, 0] + b, a * Mx[0, 1]], [a * Mx[1, 0], a * Mx[1, 1] + b]])


def twist(A, B, p, q, flow):
    path = sb_path(p, q); L, R = to_b(A, B, path); C, D = L @ R, R
    D = D @ flow(C, TWIST)
    return from_b(C @ inv(D), D, path)


def rows(x, y, z, PB, pcanon):
    G, Bd = BP.handle_group(x, y, z)
    dom = BP.piece_domain(G, Bd, L=8)
    lifts = BP.lifts(G[0], G, dom["radius"], L=7)
    canon = M.perp_foot(G[0], Bd[0])
    parts = [np.array([nrm for nrm, _ in dom["faces"]]), np.array(lifts)]
    for c in range(3):
        T_hp = M.pinned_seam(Bd[0], canon, PB[c], pcanon[c])
        parts += [Ginv if kind == "pair" else T_hp @ Ginv for _, (kind, Ginv, bi) in dom["faces"]]
    h = hashlib.sha256()
    for a in parts:
        h.update(np.ascontiguousarray(a, dtype="<f8").tobytes())
    return h.hexdigest(), len(dom["faces"])


def main():
    out = {"cpu": next((l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")), "?"),
           "python": platform.python_version(), "numpy": np.__version__}
    assert abs(C_HALF - math.cosh(0.1)) < 1e-15 and abs(S_HALF - math.sinh(0.1)) < 1e-15
    A0 = np.array([[1.0, 0.0], [0.0, 1.0]])
    import handle_mp as H
    Am, Bm = H.birth(*M.BIRTH)
    A0 = np.array([float(v) for v in Am]).reshape(2, 2); B0 = np.array([float(v) for v in Bm]).reshape(2, 2)
    hc = M.HandleCache(); h0 = hc.get(0)
    kappa = np.trace(h0["bnd"]); delta = 2 * math.acosh(-kappa / 2)
    PG, PB = BP.pants_group(delta)
    PG, gc = BP.recenter(PG, BP.midpoint_between_axes(PG[0], PG[1])); PB = [inv(gc) @ h @ gc for h in PB]
    pcanon = [M.perp_foot(PB[(i + 1) % 3], PB[i]) for i in range(3)]
    for name, flow in (("N", flow_N), ("C", flow_C)):
        A, B = A0.copy(), B0.copy(); seq = []
        for p, q in THOUGHTS:
            A, B = twist(A, B, p, q, flow)
            x, y, z = float(A[0, 0] + A[1, 1]), float(B[0, 0] + B[1, 1]), float(np.trace(A @ B))
            hx, nf = rows(x, y, z, PB, pcanon)
            seq.append({"traces_hex": [x.hex(), y.hex(), z.hex()], "rows_sha": hx, "faces": nf})
        out[name] = {"thoughts": seq,
                     "all_sha": hashlib.sha256("".join(s["rows_sha"] + "".join(s["traces_hex"]) for s in seq).encode()).hexdigest()}
    json.dump(out, open(sys.argv[1], "w"), indent=1)
    print(json.dumps({"cpu": out["cpu"], "numpy": out["numpy"], "N": out["N"]["all_sha"][:16], "C": out["C"]["all_sha"][:16]}))


if __name__ == "__main__":
    main()
