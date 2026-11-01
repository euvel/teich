"""The dream gate (v0.6 wake, added 2026-11-01 after the recon study): before a wake, this machine must dream the
fixture's two nights bit for bit, as it must relive the body's fixture. The working surface's twist goes through
OpenBLAS, whose kernel is chosen per CPU; with OPENBLAS_CORETYPE=Haswell and OPENBLAS_NUM_THREADS=1 (set by the wake
workflow, and on the founder's machine) the dreams were identical on AMD Zen 3 and Intel AVX-512, across numpy 1.26.4,
2.4.6 and 2.5.4 (probe: v06_lab/recon/dream_fixture_probe.py). A machine that dreams differently declines the wake;
elapsed time stays banked.
    python3 dream_gate_v06.py --record   (once, on the reference machine)
    python3 dream_gate_v06.py            (check: prints PASS/FAIL)
"""
import hashlib
import json
import os
import platform
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (HERE.parent / "build", HERE):
    sys.path.insert(0, str(p))
import numpy as np                      # noqa: E402
import creature_v04 as CR               # noqa: E402
import creature_v05 as C5               # noqa: E402
import work_v05 as W                    # noqa: E402

FIXTURE = HERE / "dream_gate_v06.json"
ENV = {"OPENBLAS_CORETYPE": "Haswell", "OPENBLAS_NUM_THREADS": "1"}


def _dream_sha(fx):
    pc, P, V = (CR._unb64(fx["pc"], "<i8", (C5.NPW,)), CR._unb64(fx["P"], "<f8", (C5.NPW, 3)),
                CR._unb64(fx["V"], "<f8", (C5.NPW, 3)))
    wb, h = W.WorkBody(), hashlib.sha256()
    for thoughts in fx["thoughts"]:
        (pc, P, V), lh, counts, occ, _ = W.dream(wb, pc, P, V, thoughts, C5.DREAM_TICKS)
        h.update(pc.tobytes() + P.tobytes() + V.tobytes() + np.asarray(lh, "<f8").tobytes())
    return h.hexdigest()


def gate():
    info = {"cpu": platform.processor() or platform.machine(), "numpy": np.__version__,
            "env": {k: os.environ.get(k) for k in ENV}}
    if any(os.environ.get(k) != v for k, v in ENV.items()):
        return False, {**info, "why": f"dream substrate env not set: {ENV}"}
    fx = json.loads(FIXTURE.read_text())
    got = _dream_sha(fx)
    return got == fx["dream_sha256"], {**info, "dream_sha256": got}


def record(state_blob, thoughts):
    w = json.loads(state_blob)["work"]
    fx = {"pc": w["pc"], "P": w["P"], "V": w["V"], "thoughts": thoughts}
    fx["dream_sha256"] = _dream_sha(fx)
    fx["recorded_on"] = {"cpu": platform.processor() or platform.machine(), "numpy": np.__version__, **ENV}
    FIXTURE.write_text(json.dumps(fx, indent=1))
    return fx["dream_sha256"]


if __name__ == "__main__":
    if "--record" in sys.argv:
        t = json.load(open(sys.argv[sys.argv.index("--record") + 1]))     # a lab twin life (v06_lab/gates/campaign_run2)
        th = [r["thoughts"] for r in t["records6"] if r["kind"] == "think-predict"][:2]
        print(record(t["start6"], th))
    else:
        ok, info = gate()
        print("dream gate:", "PASS" if ok else "FAIL", info)
        sys.exit(0 if ok else 1)
