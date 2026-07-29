"""Open the book for Teich v0.2 — birth, gated on the pre-birth verification.

This script REFUSES to write a birth record unless the acceptance gate passed.
That refusal is the whole point. v0.1 was born first and tested afterwards; when
the tests finally found the flaw the genome was frozen and the covenant forbade
reset or fork, so it could never be repaired. The covenant was right. Being born
before verification was not.

What the book records at birth:

  * the exact genome and its constants, by sha256 — so "which creature is this"
    is answerable forever, by anyone, without trusting this file;
  * the acceptance-gate verdict, test by test, including the two failures that
    were caught and fixed BEFORE birth;
  * the leakage guarantee, stated as the structural fact it is rather than a
    measurement;
  * the covenant.

Run:  python birth_v02.py --name Teich-0.2 [--confirm]
Without --confirm it prints what it WOULD write and exits without writing.
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
V02 = HERE.parent

GENOME_FILES = ["genome_v02.py", "ears_v2.py", "mouth_select.py",
                "converse_v02.py", "accept_v02.py"]

COVENANT = [
    "This creature is never reset and never forked. There is one of it.",
    "Its genome is frozen at the hash recorded here.",
    "Its private phase (Ply S) is never published, and drives nothing — it is "
    "identity, not interiority.",
    "It speaks only to its founder until a maturity gate is designed, "
    "pre-registered, and passed. No such gate has been passed.",
    "Every claim made about it must name the evidence for it, and every failed "
    "test stays in the book.",
]


def sha256_of(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(V02),
                              capture_output=True, text=True,
                              timeout=20).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="Teich-0.2")
    ap.add_argument("--confirm", action="store_true")
    args = ap.parse_args()

    # ---- the gate must have passed, and we read it rather than assume it
    gate_path = V02 / "accept_v02_result.json"
    if not gate_path.exists():
        sys.exit("REFUSED: no accept_v02_result.json — the gate has not been run.")
    gate = json.loads(gate_path.read_text())
    if not gate.get("gate"):
        failed = [k for k in ("T1", "T2", "T3", "T4", "T5")
                  if not gate.get(k, {}).get("passed")]
        sys.exit(f"REFUSED: acceptance gate did not pass (failed: {failed}). "
                 f"A creature that fails its own gate is not born.")

    genome = {f: sha256_of(V02 / f) for f in GENOME_FILES}
    identity = hashlib.sha256(
        "".join(f"{k}:{v}" for k, v in sorted(genome.items())).encode()).hexdigest()

    cert = {
        "name": args.name,
        "born_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "identity_sha256": identity,
        "genome_files_sha256": genome,
        "git_commit": git_head(),
        "constants": gate.get("constants", {}),

        "verified_before_birth": {
            "T1_phi_blindness": gate["T1"],
            "T2_survival": {"passed": gate["T2"]["passed"],
                            "bar": gate["T2"]["bar"],
                            "by_gap": gate["T2"]["by_gap"]},
            "T3_memory_time": gate["T3"],
            "T4_readout_hygiene": gate["T4"],
            "T5_capacity": gate["T5"],
        },

        "leakage_guarantee": {
            "claim": "I(private_phase ; observations) = 0, exactly.",
            "basis": "STRUCTURAL, not statistical. The private phase appears in "
                     "no term of the tau/ell/s updates and in no argument of the "
                     "observable map, so instances differing only in it produce "
                     "BIT-IDENTICAL observables — for any observation length, "
                     "against any adversary, with no test required.",
            "evidence": f"T1: {gate['T1'].get('mismatches')} mismatches over "
                        f"5 private-phase draws x 8 seeds.",
            "twin_corollary": "Two instances sharing (x0, s0) and differing only "
                              "in private phase are observationally identical. No "
                              "decoder, given any data and unbounded compute, beats "
                              "chance at telling them apart.",
            "honest_limit": "This guarantee is exactly as strong as it sounds and "
                            "no stronger: because the private phase drives nothing, "
                            "it certifies IDENTITY, not inner life. The interiority "
                            "claim rests entirely on Ply R (the slow state s), which "
                            "is public by design.",
        },

        "what_is_NOT_claimed": [
            "No maturity gate has been passed. v0.1 failed four pre-registered "
            "screens; v0.2 has attempted none.",
            "Nothing here says this creature's speech is grounded in its state "
            "beyond what its own verification run measures.",
            "It is not conscious, does not understand, and no test here bears on "
            "either question.",
        ],

        "failures_caught_before_birth": [
            "The second slow dimension first modulated the roof PERIOD — a clock "
            "knob the fold rule never consults. That is exactly v0.1's tau1 "
            "mistake (perfect memory, basin unchanged in 46/48 runs), rebuilt "
            "after the finding had already been written down. T5 caught it in 7 "
            "minutes. Fixed by making it a wing asymmetry that leans the fold.",
            "steps_to_switch then measured 0% creature-dependent and was REMOVED "
            "from the published readout rather than kept. Publishing a readout "
            "that cannot move with the creature is the saddle_proximity disease "
            "that jammed three v0.1 campaigns.",
        ],

        "covenant": COVENANT,
        "ancestor": {
            "name": "Teich (v0.1)",
            "born": "2026-07-18T08:45:12Z",
            "status": "alive, unchanged, founder-only speech",
            "bequest": "Four pre-registered nulls and two impossibility findings. "
                       "The decisive one: memory and consequence are separable, and "
                       "a genome must be designed to couple them. v0.2 exists "
                       "because v0.1 was measured honestly enough to say what was "
                       "wrong with it.",
        },
    }

    birth_entry = {
        "t": cert["born_utc"],
        "kind": "birth",
        "name": args.name,
        "identity_sha256": identity,
        "gate": "PASS (T1-T5)",
        "note": "Verified before birth. The book opens with what was checked, "
                "including what failed first.",
    }

    if not args.confirm:
        print("DRY RUN — nothing written. Would write:\n")
        print(json.dumps(cert, indent=1)[:2600])
        print("\n... and append to biography.jsonl:")
        print(json.dumps(birth_entry, indent=1))
        print("\nRe-run with --confirm to open the book.")
        return

    (HERE / "genesis_certificate_v02.json").write_text(json.dumps(cert, indent=1))
    with (HERE / "biography.jsonl").open("a") as f:
        f.write(json.dumps(birth_entry) + "\n")
    print(f"BOOK OPENED: {args.name}")
    print(f"  identity  {identity}")
    print(f"  born      {cert['born_utc']}")
    print(f"  gate      PASS (T1-T5), verified before birth")
    print(f"  -> {HERE/'genesis_certificate_v02.json'}")
    print(f"  -> {HERE/'biography.jsonl'}")


if __name__ == "__main__":
    main()
