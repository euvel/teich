"""Part 2e AMENDMENT 2 (2026-10-10, before the founder audit and before any Ears look): remove pronoun 'topics'.

The judge (Mistral-Small-24B) listed pronouns as topics in 90 of 740 kept topics although the GUIDE forbids them
("NOT topics: pronouns"). This mechanical cleanup applies the guide's own rule with a FIXED list; nothing else changes
(adjectives / verbs the judge listed are left for the founder audit to judge — removing them would need a POS tagger,
and the only one at hand is the Ears' own).
    python3 part2e_clean.py   judge_mistral/a2e_labels.jsonl -> a2e_labels.jsonl
"""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "data_heldout/dialog"
PRONOUNS = {"i", "me", "my", "mine", "myself", "you", "your", "yours", "yourself", "yourselves", "he", "him", "his",
            "himself", "she", "her", "hers", "herself", "it", "its", "we", "us", "our", "ours",
            "ourselves", "they", "them", "their", "theirs", "themselves", "this", "that", "these", "those", "one",
            "someone", "somebody", "something", "anyone", "anybody", "anything", "everyone", "everybody", "everything",
            "nobody", "nothing", "noone", "who", "whom", "what", "which", "others", "other"}


def main():
    src, out = D / "judge_mistral/a2e_labels.jsonl", D / "a2e_labels.jsonl"
    removed = 0
    with open(out, "w") as f:
        for r in map(json.loads, open(src)):
            keep = [[n, a] for n, a in r["tags"] if n not in PRONOUNS]
            removed += len(r["tags"]) - len(keep)
            f.write(json.dumps({**r, "tags": keep}) + "\n")
    print("pronoun topics removed:", removed, "| labels sha256", hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
