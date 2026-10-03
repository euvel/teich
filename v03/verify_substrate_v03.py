"""Teich v0.3 substrate reference — a fixed scripted life, hashed. Any machine that reproduces these
hashes runs the same creature bit-for-bit; a seat must check them before committing.

Covers the GENOME only (8 bodies, ledger with provenance, commitments, selection, language). The Ears
(MiniLM, float matmuls) are an organ and are not part of the substrate: they run once per utterance and
their output (region, sign) is logged with the event, so replay never needs them.

    python3 verify_substrate_v03.py            -> prints hashes (and writes substrate_reference_v03.json
                                                  with --write)
"""
import hashlib, json, platform, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import genome_v03 as G1
import genome_v031 as GM
import selector_v03 as S

TICKS = 200_000
EVENTS = [(1000, 2, +1), (1000, 0, -1), (20000, 5, +1), (20000, 2, +1), (90000, 7, -1), (150000, 4, +1)]


def run(x0=None):
    x = GM.x0_bodies(424242, 4) if x0 is None else x0.copy()   # 4 creatures x 8 bodies
    L = GM.MultiLedger.born(4)
    L.commit(1, -1, {"speaker": "ref", "conversation": "ceremony", "tick": 0, "text_sha256": "0" * 64}, "lawful")
    dyn, obs = hashlib.sha256(), hashlib.sha256()
    acc = np.zeros_like(x); decisions = []
    pools = {r: {"candidates": [{"region": i, "sign": s, "text": f"{r}{s}"} for s in (1, -1, 0, 1, -1)]}
             for i, r in enumerate(GM.REGION_NAMES)}
    ev = {}
    for t, r, s in EVENTS:
        ev.setdefault(t, []).append((r, s))
    a = G1.alpha_of(L.k)
    for t in range(TICKS):
        for r, s in ev.get(t, []):
            for row in range(4):
                L.event(row, r, s, {"speaker": "ref", "conversation": f"c{t}", "tick": t, "text_sha256": "1" * 64})
            a = G1.alpha_of(L.k)
        acc += GM.observe(x)["neg"]
        x = G1.step(x, a)
        if (t + 1) % 1000 == 0:
            dyn.update(x.tobytes()); obs.update(acc.tobytes())
        if (t + 1) % 8000 == 0:
            d = S.infer_disposition(acc / 8000); acc[:] = 0
            for row in range(4):
                for ri, rname in enumerate(GM.REGION_NAMES):
                    sel = S.select(pools[rname]["candidates"], d[row], x[row], ri, L.commitments)
                    decisions.append(sel["index"])
    lang = hashlib.sha256()
    concepts = [(1, 1), (2, 3), (5, 8), (-3, 7), (7, 2)]
    for i in range(200):
        w = [((i * 7 + j) % 5, (i + j) % 7 - 3) for j in range(1 + i % 6)]
        M = G1.word_matrix(w, concepts); c = G1.classify(M)
        lang.update(f"{M.tolist()}|{c['type']}|{c['intensity']!r}".encode())
    return {"x0_hex": X0_HEX, "dynamics_sha256": dyn.hexdigest(), "observables_sha256": obs.hexdigest(),
            "decisions_sha256": hashlib.sha256(bytes(decisions)).hexdigest(),
            "ledger_k": L.k.tolist(), "language_sha256": lang.hexdigest(),
            "final_x_hex": [v.hex() for v in x[0]]}


def x0_from_hex(h):
    return np.array([[float.fromhex(v) for v in row] for row in h])


if __name__ == "__main__":
    pinned = HERE / "substrate_reference_v03.json"
    if "--write" in sys.argv or not pinned.exists():
        x0 = GM.x0_bodies(424242, 4)
    else:
        x0 = x0_from_hex(json.loads(pinned.read_text())["x0_hex"])   # same start on every machine
    X0_HEX = [[float(v).hex() for v in row] for row in x0]
    ref = run(x0)
    ref["platform"] = {"python": platform.python_version(), "numpy": np.__version__, "machine": platform.machine(),
                       "processor": platform.processor() or "", "cpu": next((l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")), "?")}
    print(json.dumps(ref, indent=1))
    if "--write" in sys.argv:
        (HERE / "substrate_reference_v03.json").write_text(json.dumps(ref, indent=1))
