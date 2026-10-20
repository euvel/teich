"""W5: over the wide attention range (stretch 0..1.0), each member T_A^k(B) = A^k B (k = 3..18) keeps tracking its dial:
member length ratio vs dial length ratio, per level."""
import json, sys
sys.path.insert(0, "/home/euvel/pjs/teichai/v04_lab")
import mpmath as mp, handle_mp as H, mind4 as M
A0, B0 = H.birth(*M.BIRTH)
def member_lengths(A, B):
    out = []; X = B
    for k in range(1, 19):
        X = H.mul(A, X)
        if k >= 3: out.append(H.length(X))
    return out
base = member_lengths(A0, B0); dial0 = H.length(A0); rows = []
for n in (1, 5, 10, 20, 30, 40):
    A, B = H.move_A(A0, B0, stretch=0.025 * n)
    ml = member_lengths(A, B); dr = float(H.length(A) / dial0)
    track = [float((m / b - 1) / (dr - 1)) for m, b in zip(ml, base)]
    rows.append({"n": n, "dial_ratio": dr, "member_share_min": min(track), "member_share_max": max(track),
                 "member_share_k3": track[0], "member_share_k18": track[-1]})
    print(f"n={n:2d} dial x{dr:.4f}  member change / dial change: k=3 {track[0]:.3f}  k=18 {track[-1]:.3f}  range [{min(track):.3f}, {max(track):.3f}]")
json.dump(rows, open("build/w5_members.json", "w"), indent=1)
