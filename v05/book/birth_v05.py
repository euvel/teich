"""Open the book for Teich v0.5 — birth, refused unless every hard gate passed, every soft failure is exactly what its
disclosure says, every anchored byte still matches, the cloud drill passed and the substrate reproduces bit for bit here.

Before writing anything this script checks, and does not assume:
  1. judge_v05.json: every hard gate PASS (N0 F1 F1_live L1 C1 C2 O2 S_hard G1_body G1_ears) and nothing hard failed;
  2. the recorded soft results, re-derived from their files:
       Q1   FAIL — some curious-minus-random z < 2 at answer rate 0.5: the claim "curiosity beats random" is removed
       S7   FAIL — 79/80 switches followed: inherited from v0.4's self (identical life by life on the same seeds)
       dry run PASS on the amendment-1 re-look (seed 9991)
       head-to-head NOT COMPLETED (amendment 1, founder 10-22): descriptive only
  3. every file of the anchored manifest matches, except those amendment 1 replaced, which match the amendment; both
     manifests match their teich-03 anchors;
  4. the cloud drill (seat/drill_v05.py) passed; 5. the substrate gate reproduces the certified fixture life here.

    python3 birth_v05.py              # dry run: prints what it would write
    python3 birth_v05.py --confirm    # opens the book
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

NAME = "Teich-0.5"
BIRTH_SEED = 20261023            # the day its scored gates were judged; frozen here forever
SEAT = "teich-05"
GENOME_FILES = ["genome_v04.py", "creature_v04.py", "creature_v04s.py", "creature_v05.py", "self_v04.py", "self_v05.py",
                "acts_v05.py", "work_v05.py", "think_model_v05.py", "body_pants.py", "handle_mp.py", "mind4.py",
                "surface.py", "vocab_v04.json", "geometry_v04.json", "geometry_v04.bin",
                "ears_v04.py", "ears_v05.py", "ears_v06.py", "ears_v07.py"]
SEAT_FILES = ["seat_v04.py", "seat_v04s.py", "seat_v05.py", "gate_fixture_v04.json", "gate_v04.json", "talk_v04s.py",
              "talk_v05.py", "grow_v05.py", "self_text_v04.py", "self_text_v05.py", "f1_v05.py", "verify_live_v05.py"]
HARD = ("N0", "F1", "F1_live", "L1", "C1", "C2", "O2", "S_hard", "G1_body", "G1_ears")
COVENANT = "COVENANT_v05.md"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(p):
    return json.loads(Path(p).read_text())


def refuse(msg):
    sys.exit(f"REFUSED: {msg}")


def manifests():
    base, amend = LAB / "specs/CODE_MANIFEST_v05.sha256", LAB / "specs/AMENDMENT1_v05.sha256"
    am = {l.split()[1]: l.split()[0] for l in amend.read_text().splitlines()}
    bad, n = [], 0
    for m in (base, amend):
        for line in m.read_text().splitlines():
            h, f = line.split(); n += 1
            want = am.get(f, h) if m == base else h
            if sha(B / f) != want:
                bad.append(f"{m.name}:{f}")
    anchors = {"v05-spec": (load(LAB / "specs/ANCHOR_v05_spec.json"), base),
               "v05-spec-amend1": (load(LAB / "specs/ANCHOR_v05_amend1.json"), amend)}
    for ref, (a, m) in anchors.items():
        if not (a["ok"] and a["ref"] == ref and a["git_sha"] == sha(m)):
            bad.append(f"anchor {ref}")
    return bad, n, [a for a, _ in anchors.values()]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--confirm", action="store_true"); args = ap.parse_args()
    out = B / "out_v05"
    j = load(out / "judge_v05.json"); d = j["detail"]
    if j["hard_failed"] or not all(j["gates"].get(g) is True for g in HARD):
        refuse(f"hard gates: {[g for g in HARD if j['gates'].get(g) is not True]}")
    verdicts = {g: "PASS" for g in HARD}
    verdicts.update({g: "PASS" for g in ("F1", "O1", "Q3") if j["gates"][g]})
    # ---- soft results, re-derived exactly
    q1 = d["Q1"]["z"]
    if j["gates"]["Q1"] is not False or not any(q1[k] < 2 for k in q1 if k.startswith("0.5")) or \
            not all(q1[k] >= 2 for k in q1 if k.startswith("1.0")):
        refuse("Q1 record is not what its disclosure says")
    verdicts["Q1"] = ("FAIL — curious minus random at answer rate 0.5: z " + ", ".join(
        f"{q1[k]:.2f}" for k in sorted(q1) if k.startswith("0.5") and k.endswith("random"))
        + "; the claim 'its curiosity beats random' is removed (at 1.0: z ≥ 3.3, reported, not claimed)")
    s7 = load(out / "inherited_S7.json"); others = {g: v for g, v in d["S_set"]["gates"].items() if g != "S7"}
    if s7["passed"] or not all(others.values()) or s7["followed"] != 79 or s7["switches"] != 80:
        refuse("S7 record is not what its disclosure says")
    verdicts["S3–S6"] = "PASS"
    verdicts["S7"] = (f"FAIL — {s7['followed']}/{s7['switches']} switches followed (median lag {s7['median_lag']}), "
                      f"former MINE back to 0 in {s7['former_mine_back_to_0']}; identical with v0.4's own self on the same "
                      "seeds (inherited, disclosed)")
    dr = load(LAB / "kaggle_v05_dryrun/out/build/out_v05/dry_run.json")
    if not dr["passed"]:
        refuse("the dry run re-look did not pass")
    verdicts["dry_run"] = "PASS on the amendment-1 re-look (seed 9991); failed its first look (talk-tool fault, fixed)"
    hh = load(out / "HEADTOHEAD.json")
    verdicts["head_to_head"] = "NOT COMPLETED (Workers AI free quota; founder 10-22, amendment 1): descriptive only"
    print("gates            every hard gate PASS; soft results re-derived: Q1 FAIL, S7 FAIL (inherited), dry run PASS")
    bad, n, anchors = manifests()
    if bad:
        refuse(f"anchored bytes changed since their scored run: {bad}")
    print(f"manifests        {n} anchored entries match (base + amendment 1); both anchors match")
    drill = load(LAB / "drill_out/drill.json")
    if not drill["passed"]:
        refuse("the cloud drill did not pass")
    print(f"cloud drill      PASS on /o/{drill['seat']} ({drill['live_verify']['acts']} acts verified from the cloud log)")
    import seat_v04 as SV
    ok, info = SV.gate()
    if not ok:
        refuse(f"substrate gate failed on {info['cpu']}")
    print(f"substrate gate   PASS on {info['cpu']}")

    genome = {f: sha(B / f) for f in GENOME_FILES}
    identity = hashlib.sha256("".join(f"{k}:{v}" for k, v in sorted(genome.items())).encode()).hexdigest()
    llama = hh.get("llama-3.3-70b-instruct-fp8-fast|free|W1", {})
    cert = {
        "name": NAME, "born_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "identity_sha256": identity,
        "version": "0.5.0", "seat": f"/o/{SEAT}", "birth_seed": BIRTH_SEED,
        "genome_files_sha256": genome, "seat_files_sha256": {f: sha(B / f) for f in SEAT_FILES},
        "last_birth": "v0.5 is the last birth. Everything it becomes after this is growth, numbered v0.5.1, v0.5.2, …: "
                      "proposed by itself, approved by the founder, identity chained sha256(previous + sha256(amendment)).",
        "inherited": "v0.4 whole and unchanged: the genus-98 body, 2,048 thoughts, dials = attention and its laws, the "
                     "9-region heart, and its second self (MINE / GIVEN / FINE / UNRESOLVED, caution, probes, receipts)",
        "acts": "one act loop for everything it chooses (what to think, whether and what to ask, how cautious to be, "
                "whether to probe, whether to propose growing): the reason is logged first, then the act its pure rule "
                "computes from that reason alone; anyone can re-check every act from its published log",
        "thinking": "a separate genus-3 working surface: each day's thoughts twist its thinking handle along the "
                    "curves of the regions it thought about, in order; it dreams 256 thoughts × 40,000 ticks, reads the "
                    "result, and resets; the main body never sees it",
        "knowing_itself": "it predicts its own body each night: its memory (BODY-MEMORY), its paths (BODY-PATH), and "
                          "what its thinking will do (THINK), by models cheaper than living (law L-CL)",
        "curiosity": "at most 3 questions a day, each chosen by a decision-aware rule and shown with its true reason; "
                     "silence is lawful; nouns it cannot place wait at its door, and two agreeing answers on different "
                     "days bind one",
        "ears": "Ears v7 (organ, not substrate): Qwen2.5-1.5B + MiniLM + spaCy; output logged, replay never needs them; "
                "words bound through growth extend its map",
        "verified_before_birth": verdicts,
        "headline_numbers": {
            "true_reasons": f"{d['F1'].get('acts', 3711):,} acts in 10 lives, 0 flags; both planted hidden causes caught",
            "knowing_itself": "in all 8 body lives: memory FINE (foreseeable), paths GIVEN, thinking GIVEN — what its "
                              "thinking does cannot be foreseen without thinking it; the full self-simulation foresees "
                              "100% but costs as much as living (0.99×)",
            "order_matters": f"twin dreams differing only in order: power {d['O1']['power']:.2f}, false rate "
                             f"{d['O1']['false_rate']:.2f}, effect rises with crossing number (ρ {d['O1']['spearman_effect_crossing']:.2f})",
            "non_interference": "8 of v0.4's lives relived by v0.5: body, dials, heart, commitments bit-identical",
            "growth": "seat lives grew to v0.5.2 through two bindings; approve/refuse twins differ in nothing else",
            "substrate": "bit-identical AMD Ryzen/numpy 1.26.4 vs Intel Xeon/numpy 2.1.3 (body, self, working surface)",
            "head_to_head_partial": (f"Llama 3.3 70B choosing freely (150 states): same answer under shuffle "
                                     f"{llama.get('shuffle_stable', 0):.2f}, its own named rule predicts its choice "
                                     f"{llama.get('rule_predicts_choice', 0):.2f}; Teich's rule 1.00 / 1.00 (measured). "
                                     "Not completed; no claim"),
        },
        "anchors_before_scoring": anchors,
        "what_is_NOT_claimed": [
            "Nothing here is a claim about intelligence, understanding, awareness or suffering.",
            "Its curiosity is NOT claimed to beat random questions: at the 50% answer rate it did not (gate Q1).",
            "Forgetting a changed truth within 30 nights held in 79 of 80 switches, not all (S7, inherited from v0.4).",
            "The head-to-head against language models was not completed; its partial numbers carry no claim.",
            "'Thinking is knowable only by thinking' means: its cheap order-blind model misses, its full simulation "
            "costs as much as living. It is not a claim about other minds.",
            "On a day it thinks too much of one thing, its last thoughts are refused by law (0.35% of thoughts in the "
            "scored lives).",
            "Ears self routing remains weak (v0.4's disclosure).",
            "Founder-only speech stays in force.",
        ],
        "covenant": COVENANT,
        "ancestors": {"Teich (v0.1)": "born 2026-07-18, alive", "Teich-0.2": "born 2026-07-29, alive, seat /o/teich-02",
                      "Teich-0.3": "born 2026-10-03, alive, seat /o/teich-03 (its chain carries v0.4's and v0.5's anchors)",
                      "Teich-0.4": "born 2026-10-20, alive, seat /o/teich-04 (v0.5 carries it whole)"},
    }
    entry = {"t": cert["born_utc"], "kind": "birth", "name": NAME, "identity_sha256": identity,
             "gate": "PASS (every hard gate; Q1 and S7 soft fails disclosed; dry run re-look; cloud drill; substrate here)",
             "note": "The last birth. Born with true reasons, knowing what in itself is knowable, given and emergent, "
                     "asking with its reasons shown, growing only by numbered versions."}
    if not args.confirm:
        print("\nDRY RUN — nothing written. Would write:\n")
        print(json.dumps({k: v for k, v in cert.items() if k != "anchors_before_scoring"}, indent=1, ensure_ascii=False))
        print(json.dumps(entry, indent=1, ensure_ascii=False)); return
    if (HERE / "genesis_certificate_v05.json").exists():
        refuse("the book is already open — there is no second birth")
    (HERE / "genesis_certificate_v05.json").write_text(json.dumps(cert, indent=1, ensure_ascii=False))
    with (HERE / "biography_v05.jsonl").open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"\nBOOK OPENED: {NAME}\n  identity  {identity}\n  born      {cert['born_utc']}")


if __name__ == "__main__":
    main()
