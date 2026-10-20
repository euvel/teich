"""Part 2e — draw the A2e sentences from EmpatheticDialogues TEST split (strangers talking to a listener).

Deterministic: fixed seed, fixed strata (surface patterns only, no model), fixed sizes. Run once, after the part 2e
anchor. Output: data_heldout/dialog/a2e_sentences.jsonl  {"id", "conv_id", "stratum", "sentence"}  — no labels.
"""
import csv
import hashlib
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data_heldout/dialog/ed/empatheticdialogues/test.csv"
OUT = ROOT / "data_heldout/dialog/a2e_sentences.jsonl"
SEED = 20261009
STRATA = [                                     # first match wins, in this order
    ("listener", re.compile(r"\b(you|your|yourself)\b", re.I), 110),
    ("hypothetical", re.compile(r"\b(if|unless|whether|used to)\b", re.I), 40),
    ("other_holder", re.compile(r"\b(my|his|her|their)\s+\w+\s+(loves?|hates?|likes?|enjoys?|thinks?|said|says|wants?|"
                                r"feels?|felt|thought|adores?|misses?|prefers?)\b|\b(he|she|they)\s+(loves?|hates?|likes?|"
                                r"enjoys?|thinks?|said|says|wants?|feels?|felt|thought|adores?|misses?|prefers?)\b", re.I), 40),
    ("question", re.compile(r"\?\s*$"), 30),
    ("contrast", re.compile(r"\b(but|although|though|however|while)\b", re.I), 60),
    ("negation", re.compile(r"\b(not|never|no|n't)\b|n't\b", re.I), 50),
    ("plain", re.compile(r".*"), 70),
]


def sentences():
    seen = set()
    with open(SRC, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) < 6 or row[0] == "conv_id":
                continue
            text = row[5].replace("_comma_", ",").strip()
            for s in re.split(r"(?<=[.!?])\s+", text):
                s = s.strip()
                words = re.findall(r"[A-Za-z']+", s)
                if not 4 <= len(words) <= 30 or not re.fullmatch(r"[A-Za-z0-9 ,.'!?;:\-\"()$%&/]+", s):
                    continue
                if not re.search(r"[A-Za-z]", s[:1]) or s.lower() in seen:
                    continue
                seen.add(s.lower())
                yield row[0], s


def main():
    if OUT.exists() and "--force" not in sys.argv:
        raise SystemExit(f"{OUT} exists; the draw is done once")
    pools = {name: [] for name, _, _ in STRATA}
    for conv, s in sentences():
        for name, rx, _ in STRATA:
            if rx.search(s):
                pools[name].append((conv, s)); break
    rng = random.Random(SEED); out, used_conv = [], set()
    for name, _, n in STRATA:
        pool = sorted(pools[name]); rng.shuffle(pool); k = 0
        for conv, s in pool:
            if conv in used_conv:                     # at most one sentence per conversation: independent items
                continue
            out.append({"id": len(out), "conv_id": conv, "stratum": name, "sentence": s}); used_conv.add(conv); k += 1
            if k == n:
                break
    with open(OUT, "w") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    print(len(out), "sentences", {n: sum(r["stratum"] == n for r in out) for n, _, _ in STRATA},
          "sha256", hashlib.sha256(OUT.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
