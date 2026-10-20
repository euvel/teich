"""Gate S1 — the founder audits the mirror labels before the Ears hear any S1 sentence.

    python3 s1_audit.py make    -> ears_founder_set/s1_audit.txt : 50 labelled sentences (seed 1010)
    python3 s1_audit.py score   -> agreement on MIRROR (M1 or M2) vs NONE, and on M1 vs M2

The founder changes only the label after the last "|" where they disagree (M1 | M2 | NONE).
"""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data_heldout/dialog"
AUDIT = ROOT / "ears_founder_set/s1_audit.txt"
SEED, N = 1010, 50
AUDIT_RULE = """Labels are TRUSTED when, over the audited sentences with a judge label (not 'unsure'), mirror-vs-none
agreement >= 0.85 and Cohen's kappa >= 0.65. Otherwise the judge's labels are NOT used and S1 stops before any Ears look."""


def make():
    sents = {r["id"]: r["sentence"] for r in map(json.loads, open(D / "s1_sentences.jsonl"))}
    labs = [r for r in map(json.loads, open(D / "s1_labels.jsonl")) if r["label"] != "unsure"]
    pick = sorted(random.Random(SEED).sample(labs, N), key=lambda r: r["id"])
    with open(AUDIT, "w") as f:
        f.write("# S1 mirror audit — 50 sentences labelled by the independent judge (Mistral-Small-24B).\n"
                "# Change ONLY the label after the last '|' where you disagree; leave agreed lines exactly as they are.\n"
                "#   M1   = says what the LISTENER is / has / can do / does / feels (questions about the listener's own state count)\n"
                "#   M2   = the SPEAKER's own feeling or stance toward the listener (thanks, liking, pride, anger, care, wishes)\n"
                "#   NONE = 'you' only leads to something else, or means people in general\n\n")
        for r in pick:
            f.write(f"{r['id']} | {sents[r['id']]} | {r['label']}\n")
    print(AUDIT, N, "sentences")


def score():
    judge = {r["id"]: r["label"] for r in map(json.loads, open(D / "s1_labels.jsonl"))}
    pairs = []
    for l in open(AUDIT):
        if l.strip() and not l.startswith("#"):
            i = int(l.split("|")[0]); f = l.rsplit("|", 1)[1].strip().upper()
            pairs.append((f, judge[i]))
    mir = [(f in ("M1", "M2"), j in ("M1", "M2")) for f, j in pairs]
    n = len(mir); po = sum(a == b for a, b in mir) / n
    pf, pj = sum(a for a, _ in mir) / n, sum(b for _, b in mir) / n
    pe = pf * pj + (1 - pf) * (1 - pj); kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
    both = [(f, j) for f, j in pairs if f in ("M1", "M2") and j in ("M1", "M2")]
    r = {"sentences": n, "changed": sum(f != j for f, j in pairs), "mirror_agreement": round(po, 3), "kappa": round(kappa, 3),
         "m1_m2_agreement": round(sum(f == j for f, j in both) / max(1, len(both)), 3), "founder_mirrors": sum(a for a, _ in mir)}
    r["trusted"] = po >= 0.85 and kappa >= 0.65
    json.dump(r, open(D / "s1_audit_result.json", "w"), indent=1)
    print(json.dumps(r, indent=1))


if __name__ == "__main__":
    {"make": make, "score": score}[sys.argv[1]]()
