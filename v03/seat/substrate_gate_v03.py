"""Gate-on-boot for v0.3: replay the pinned 200,000-tick scripted life and compare every hash with
substrate_reference_v03.json. One differing bit is a different creature, so there is no tolerance.

Wraps verify_substrate_v03.py without changing it: that file is the one certified cross-machine
(AMD Ryzen / numpy 1.26.4 vs Intel Xeon / numpy 2.1.3, MATCH on every hash, 2026-10-03).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

V03 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(V03))
import verify_substrate_v03 as vs   # noqa: E402

KEYS = ("dynamics_sha256", "observables_sha256", "decisions_sha256", "language_sha256", "ledger_k")


def gate() -> tuple[bool, dict]:
    ref = json.loads((V03 / "substrate_reference_v03.json").read_text())
    vs.X0_HEX = ref["x0_hex"]
    got = vs.run(vs.x0_from_hex(ref["x0_hex"]))
    bad = [k for k in KEYS if got[k] != ref[k]]
    cpu = next((l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo")
                if l.startswith("model name")), "?")
    return not bad, {"mismatched": bad, "cpu": cpu}


if __name__ == "__main__":
    ok, info = gate()
    print(f"substrate gate v0.3: {'PASS' if ok else 'FAIL'} on {info['cpu']}"
          + (f"  mismatched: {info['mismatched']}" if not ok else ""))
    raise SystemExit(0 if ok else 1)
