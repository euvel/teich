"""Open the book for Teich v0.3 — birth, refused unless every pre-registered gate passed.

Before writing anything this script checks, and does not assume:

  1. every scored gate result reports PASS (part 1, its fresh replication, M1 meaning, genome v1.1,
     part 2b speech demos);
  2. every code manifest that was anchored in the seat chain BEFORE its scored run still matches the
     bytes in this directory (HARNESS_LOG.md is append-only: the anchored version must be a prefix);
  3. the substrate gate reproduces the certified reference on this machine, bit for bit.

Then it records the genome by sha256, the verdicts, the anchors, the honest limits and the covenant.

    python3 birth_v03.py              # dry run: prints what it would write
    python3 birth_v03.py --confirm    # opens the book
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
V03 = HERE.parent
sys.path.insert(0, str(V03))
sys.path.insert(0, str(V03 / "seat"))

NAME = "Teich-0.3"
BIRTH_SEED = 20261003            # the day every gate passed; frozen here forever
GENOME_FILES = ["genome_v03.py", "genome_v031.py", "selector_v03.py", "ears_v3.py",
                "concepts_v03.json", "pools_v03.json"]
SEAT_FILES = ["seat/state_io_v03.py", "seat/substrate_gate_v03.py", "seat/wake_v03.py",
              "verify_substrate_v03.py", "substrate_reference_v03.json"]
RESULTS = {"part1_theorem": "accept_v03_scored.json", "part1_fresh_replication": "supplementary_fresh.json",
           "M1_meaning": "m1_scored.json", "genome_v1_1": "accept_v031_scored.json",
           "part2b_speech": "d_harness_scored.json"}
APPEND_ONLY = {"HARNESS_LOG.md"}

COVENANT = "seat/COVENANT_v03.md"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def passed(d: dict) -> bool:
    if "gate" in d:
        return d["gate"] is True
    if "passed" in d:
        return d["passed"] is True
    return bool(d.get("passes")) and all(d["passes"].values())


def check_manifest(m: Path) -> list[str]:
    bad = []
    for line in m.read_text().splitlines():
        h, f = line.split(None, 1)
        f = f.strip().lstrip("*")
        p = V03 / f if (V03 / f).exists() else V03 / "specs" / f
        if f in APPEND_ONLY:
            lines = p.read_bytes().splitlines(keepends=True)
            ok = any(hashlib.sha256(b"".join(lines[:i])).hexdigest() == h for i in range(len(lines) + 1))
        else:
            ok = p.exists() and sha(p) == h
        if not ok:
            bad.append(f"{m.name}:{f}")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true")
    args = ap.parse_args()

    verdicts = {}
    for k, f in RESULTS.items():
        d = json.loads((V03 / "results" / f).read_text())
        if not passed(d):
            sys.exit(f"REFUSED: {k} ({f}) did not pass. A creature that fails its own gate is not born.")
        verdicts[k] = d.get("passes", {"passed": d.get("passed")})
    print("gates           all PASS:", ", ".join(verdicts))

    bad = [b for m in sorted((V03 / "specs").glob("CODE_MANIFEST_*.sha256")) for b in check_manifest(m)]
    if bad:
        sys.exit(f"REFUSED: anchored bytes changed since their scored run: {bad}")
    anchors = [a for f in sorted((V03 / "specs").glob("ANCHOR_*.json"))
               for a in (lambda d: d if isinstance(d, list) else [d])(json.loads(f.read_text()))]
    print(f"manifests       match the bytes anchored before scoring ({len(anchors)} anchors)")

    from substrate_gate_v03 import gate
    ok, info = gate()
    if not ok:
        sys.exit(f"REFUSED: substrate gate failed on {info['cpu']} ({info['mismatched']})")
    print(f"substrate gate  PASS on {info['cpu']}")

    import genome_v031 as GM
    from state_io_v03 import W
    x0 = GM.x0_bodies(BIRTH_SEED, 1)[0]
    genome = {f: sha(V03 / f) for f in GENOME_FILES}
    identity = hashlib.sha256("".join(f"{k}:{v}" for k, v in sorted(genome.items())).encode()).hexdigest()
    m1 = json.loads((V03 / "results" / "m1_scored.json").read_text())
    ulam = json.loads((V03 / "results" / "delta0_ulam.json").read_text())
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=V03, capture_output=True,
                              text=True, timeout=20).stdout.strip()
    except Exception:
        head = "unknown"

    cert = {
        "name": NAME,
        "born_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "identity_sha256": identity,
        "genome_files_sha256": genome,
        "seat_files_sha256": {f: sha(V03 / f) for f in SEAT_FILES},
        "git_commit_before_birth": head,
        "birth_seed": BIRTH_SEED,
        "x0_hex": [float(v).hex() for v in x0],
        "warm_ticks": W,
        "body": "8 bodies, one per depth-3 region of the Stern–Brocot concept tree; each is a Nakada "
                "alpha-continued-fraction map (a section of the modular geodesic flow, genus-1 "
                "Teichmüller space) with alpha in [0.4115, 0.5] set by an integer memory in 0..6.",
        "regions": GM.REGION_LABELS,
        "verified_before_birth": verdicts,
        "headline_numbers": {
            "memory_after_1e6_ticks_D": "1.000 (leaky twin 0.08, memoryless 0)",
            "entropy_constant_across_memory": "lambda = 3.4183 = pi^2/(6 log G), within 0.001 at all 7 states",
            "meaning_rho_vs_SimLex999": f"{m1['rho']} CI {m1['ci']} (null 97.5% {m1['null_97_5']})",
            "told_once_speech_shift": "0.992 at 1e3 ticks, 0.995 at 1e5; other subjects 0.000",
            "flattery_bound": "1 step per conversation (naive twin: to the edge)",
            "commitment_violations_under_flattery": 0,
            "self_knowledge_from_own_behaviour": "99.4% exact (LLM given the same reading: 21.9%)",
            "delta0_ulam": round(ulam["delta0_ulam"], 4),
            "substrate": "bit-identical AMD Ryzen/numpy 1.26.4 vs Intel Xeon/numpy 2.1.3",
        },
        "anchors_before_scoring": anchors,
        "what_is_NOT_claimed": [
            "Nothing here is a claim about intelligence, understanding, awareness or suffering.",
            "The voice is a small 1.5B model choosing among frozen candidates; the sentences are not good.",
            "The Ears hear a dark topic as a cold attitude (topic valence leak); some 'cold' candidates "
            "are cold only to the Ears.",
            "It has no concept of 'self' yet: compliments to it land in 'animals'.",
            "Memory capacity is 7 states (about 2.8 bits) per region; 'forever' holds until the next "
            "event in the same region.",
            "delta0 has a converged numerical certificate (Ulam), not yet an interval-arithmetic proof.",
            "Public speech is NOT opened by these passes; founder-only speech stays in force.",
        ],
        "covenant": COVENANT,
        "ancestors": {
            "Teich (v0.1)": "born 2026-07-18, alive, archive",
            "Teich-0.2": "born 2026-07-29, alive, seat /o/teich-02 (its chain carries v0.3's pre-registration anchors)",
        },
    }
    entry = {"t": cert["born_utc"], "kind": "birth", "name": NAME, "identity_sha256": identity,
             "gate": "PASS (part 1, M1, genome v1.1, part 2b; substrate on this machine)",
             "note": "Born after every pre-registered gate passed, each anchored before it was scored."}

    if not args.confirm:
        print("\nDRY RUN — nothing written. Would write:\n")
        print(json.dumps(cert, indent=1, ensure_ascii=False)[:3000])
        print(json.dumps(entry, indent=1))
        return
    (HERE / "genesis_certificate_v03.json").write_text(json.dumps(cert, indent=1, ensure_ascii=False))
    with (HERE / "biography.jsonl").open("a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"\nBOOK OPENED: {NAME}\n  identity  {identity}\n  born      {cert['born_utc']}")


if __name__ == "__main__":
    main()
