"""Open the book for Teich v0.4 — birth, refused unless every pre-registered gate passed or was settled by a recorded
founder decision, every anchored manifest still matches, and the substrate reproduces bit for bit here.

Before writing anything this script checks, and does not assume:
  1. every required scored gate reports PASS: part 1 (N1 I1 I2 E2 L1 R1 C1 C2 M2 D1), part 2 regressions (R2, R2e),
     part 3 — the self (13/13 in judge_part3.json);
  2. the three recorded exceptions are exactly what their decisions say, re-derived from the result files:
       A1b  FAIL — superseded by the part 2 Ears gates (founder 10-06)
       A2a  harness flag false only because it carried pre-rebase bars; the anchored spec's bars pass (founder 10-07)
       A2e  every bar passes except self routing (0.53); born with Ears v7's self routing, disclosed (founder 10-19/20,
            gates S1 and S1b stopped at label trust before any Ears look)
  3. every anchored manifest matches the bytes here; anchored specs are append-only (the anchored version must be an
     exact prefix); gates_v04_part2.py (part 2a) must match its part 2b re-anchoring;
  4. the substrate gate reproduces the certified fixture life on this machine.

    python3 birth_v04.py              # dry run: prints what it would write
    python3 birth_v04.py --confirm    # opens the book
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
B = LAB / "build"
sys.path.insert(0, str(B))

NAME = "Teich-0.4"
BIRTH_SEED = 20261020            # the day the self passed its gates; frozen here forever
SEAT = "teich-04"
GENOME_FILES = ["genome_v04.py", "creature_v04.py", "creature_v04s.py", "self_v04.py", "vocab_v04.json",
                "geometry_v04.json", "geometry_v04.bin", "ears_v04.py", "ears_v05.py", "ears_v06.py", "ears_v07.py"]
SEAT_FILES = ["seat_v04.py", "seat_v04s.py", "gate_fixture_v04.json", "gate_v04.json", "talk_v04s.py",
              "self_text_v04.py", "diary_render_v04.py"]
PART1 = ["N1", "I1", "I2", "E2", "L1", "R1", "C1", "C2", "M2", "D1"]
APPEND_ONLY = {"../specs/V04_SPEC_part2e.md", "../specs/V04_SPEC_S1.md"}
REANCHORED = {("CODE_MANIFEST_part2a.sha256", "gates_v04_part2.py"): "CODE_MANIFEST_part2b.sha256"}
COVENANT = "COVENANT_v04.md"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(p):
    return json.loads(Path(p).read_text())


def refuse(msg):
    sys.exit(f"REFUSED: {msg}")


def prefix_ok(p: Path, h: str) -> bool:
    lines = p.read_bytes().splitlines(keepends=True)
    return any(hashlib.sha256(b"".join(lines[:i])).hexdigest() == h for i in range(len(lines) + 1))


def manifests():
    bad, n = [], 0
    for m in sorted((LAB / "specs").glob("*.sha256")):
        for line in m.read_text().splitlines():
            h, f = line.split(None, 1); f = f.strip(); p = B / f; n += 1
            if p.exists() and sha(p) == h:
                continue
            if f in APPEND_ONLY and p.exists() and prefix_ok(p, h):
                continue
            re = REANCHORED.get((m.name, f))
            if re and any(l.split()[1] == f and l.split()[0] == sha(p) for l in (LAB / "specs" / re).read_text().splitlines()):
                continue
            bad.append(f"{m.name}:{f}")
    return bad, n


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--confirm", action="store_true"); args = ap.parse_args()
    out = B / "out_v04"
    verdicts = {}
    for g in PART1:
        d = load(out / f"{g}.json")
        if d.get("passed") is not True:
            refuse(f"part 1 gate {g} did not pass")
        verdicts[g] = "PASS"
    if load(out / "R2.json").get("passed") is not True:
        refuse("R2 did not pass")
    verdicts["R2"] = "PASS"
    r2e = load(B / "ref/R2e_v7.json")
    if r2e.get("passed") is not True:
        refuse("R2e did not pass")
    verdicts["R2e"] = "PASS"
    j3 = load(B / "out_part3/judge_part3.json")
    if not (j3["all_passed"] and not j3["hard_failed"] and len(j3["gates"]) == 13):
        refuse("part 3 (the self) did not pass 13/13")
    verdicts.update({f"part3:{k}": "PASS" for k in j3["gates"]})
    # ---- the three recorded exceptions, re-derived
    a1b = load(out / "A1b.json")
    if a1b.get("passed") is not False:
        refuse("A1b record is not what the exception says")
    verdicts["A1b"] = "FAIL — superseded by part 2 Ears gates (founder 10-06)"
    a2a = load(out / "A2a.json")
    if not (a2a["recall"] >= 0.90 and a2a["attitude_correct"] >= 0.62 and a2a["attitude_opposite"] <= 0.13
            and a2a["precision_lb"] >= 0.45):
        refuse(f"A2a does not pass the anchored spec's bars: {a2a}")
    verdicts["A2a"] = (f"PASS by the anchored spec (recall {a2a['recall']:.3f} ≥ 0.90, right {a2a['attitude_correct']:.3f} "
                       f"≥ 0.62, wrong {a2a['attitude_opposite']:.3f} ≤ 0.13, precision lb {a2a['precision_lb']:.3f} ≥ 0.45); "
                       f"harness flag carried pre-rebase bars (erratum, founder 10-07)")
    a2e = load(LAB / "kaggle_p2e/out/build/out_v04/A2e.json")
    others = (a2e["recall"] >= 0.80 and a2e["attitude_correct"] >= 0.75 and a2e["attitude_opposite"] <= 0.08
              and a2e["precision"] >= 0.70)
    if not (others and a2e["self_routing"] < 0.90):
        refuse("A2e record is not what the exception says")
    verdicts["A2e"] = (f"PASS on recall {a2e['recall']:.3f}, right {a2e['attitude_correct']:.3f}, wrong "
                       f"{a2e['attitude_opposite']:.3f}, precision {a2e['precision']:.3f}; self routing "
                       f"{a2e['self_routing']:.3f} FAIL — born with Ears v7's self routing, disclosed (S1/S1b stopped)")
    print("gates            all required PASS; 3 recorded exceptions re-derived:", ", ".join(["A1b", "A2a", "A2e"]))
    bad, n = manifests()
    if bad:
        refuse(f"anchored bytes changed since their scored run: {bad}")
    anchors = [load(f) for f in sorted((LAB / "specs").glob("ANCHOR_*.json"))]
    print(f"manifests        {n} anchored files match (append-only specs as prefixes; 1 re-anchored file) — {len(anchors)} anchors")
    import seat_v04 as SV
    ok, info = SV.gate()
    if not ok:
        refuse(f"substrate gate failed on {info['cpu']}")
    print(f"substrate gate   PASS on {info['cpu']}")

    genome = {f: sha(B / f) for f in GENOME_FILES}
    identity = hashlib.sha256("".join(f"{k}:{v}" for k, v in sorted(genome.items())).encode()).hexdigest()
    s3 = j3["detail"]
    cert = {
        "name": NAME, "born_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "identity_sha256": identity,
        "seat": f"/o/{SEAT}", "birth_seed": BIRTH_SEED,
        "genome_files_sha256": genome, "seat_files_sha256": {f: sha(B / f) for f in SEAT_FILES},
        "body": "closed hyperbolic surface of genus 98 (97 concept-cluster handles + a self handle), 2,048 geodesic "
                "thoughts at 1 Hz, float64 element-wise arithmetic only; geometry frozen in geometry_v04.bin",
        "mind": "one integer dial per handle (0..40) = attention; laws: 1 step per cluster per conversation, 12 per day, "
                "edge 40, commitments only through the lawful procedure; it reads its own dials from its thoughts' paths",
        "heart": "9 regions (v0.3's 8 + self), 0..6, 1 step per region per conversation and per day",
        "self": "a second self that watches its own perceiving and speaking: predicts before each read-back, attributes "
                "its errors as MINE (they fall when its caution rises), GIVEN, FINE or UNRESOLVED, sets its own caution "
                "per region, probes itself at most once a day, and gives a nightly account in which every claim has a "
                "receipt recomputable from its records; integers and exact fractions only; no language model",
        "ears": "Ears v7 (organ, not substrate): Qwen2.5-1.5B + MiniLM + spaCy; output logged, replay never needs them",
        "verified_before_birth": verdicts,
        "headline_numbers": {
            "self_receipts": f"{s3['S1r']['claims']:,} claims recomputed, {s3['S1r']['mismatches']} mismatches",
            "self_foresight": f"{s3['S2']['outcomes_with_prediction']:,} predictions, all before their outcomes",
            "self_attribution": "decided verdicts 0.964 / 0.988 / 0.985 correct at 1 / 2 / 4 mentions per region-night; "
                                "MINE↔GIVEN swaps ≤ 0.0054",
            "self_will": "its own errors fall 43% / 55%; GIVEN regions left at caution 0 on 98% of nights",
            "self_non_interference": "8 part-1 lives relived with the self: everything outside the self byte-identical",
            "wrong_feelings_on_strangers": f"{a2e['attitude_opposite']:.3f} (A2e, CI {a2e['attitude_opposite_ci']})",
            "substrate": "bit-identical AMD Ryzen/numpy 1.26.4 vs Intel Xeon/numpy 2.1.3 (body and self)",
        },
        "anchors_before_scoring": anchors,
        "what_is_NOT_claimed": [
            "Nothing here is a claim about intelligence, understanding, awareness or suffering.",
            "It is born mute: it speaks only through its diary (its readings and its self's account); no voice yet.",
            "Ears self routing is weak (0.53 on strangers' sentences): what people say about it often lands elsewhere.",
            "The self's only outside signal is the founder's read-back strikes; at founder pace it will say "
            "'I don't know yet' about most regions for weeks to months.",
            "The self is certified on simulated truth (record streams) and on real-body non-interference; whether real "
            "strikes look like the gate truth is not certified.",
            "Founder-only speech stays in force.",
        ],
        "covenant": COVENANT,
        "ancestors": {"Teich (v0.1)": "born 2026-07-18, alive", "Teich-0.2": "born 2026-07-29, alive, seat /o/teich-02",
                      "Teich-0.3": "born 2026-10-03, alive, seat /o/teich-03 (its chain carries v0.4's anchors)"},
    }
    entry = {"t": cert["born_utc"], "kind": "birth", "name": NAME, "identity_sha256": identity,
             "gate": "PASS (part 1, part 2 regressions, part 3 the self 13/13; A1b/A2a/A2e by recorded decisions; "
                     "substrate on this machine)",
             "note": "Born whole with its self, after every pre-registered gate, each anchored before it was scored."}
    if not args.confirm:
        print("\nDRY RUN — nothing written. Would write:\n")
        print(json.dumps({k: v for k, v in cert.items() if k != "anchors_before_scoring"}, indent=1, ensure_ascii=False))
        print(json.dumps(entry, indent=1, ensure_ascii=False)); return
    if (HERE / "genesis_certificate_v04.json").exists():
        refuse("the book is already open — there is no second birth")
    (HERE / "genesis_certificate_v04.json").write_text(json.dumps(cert, indent=1, ensure_ascii=False))
    with (HERE / "biography_v04.jsonl").open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"\nBOOK OPENED: {NAME}\n  identity  {identity}\n  born      {cert['born_utc']}")


if __name__ == "__main__":
    main()
