"""Part 2e — the founder audits the annotator (judge of the judge), before the Ears ever hear the A2e sentences.

    python3 part2e_audit.py make    -> ears_founder_set/a2e_audit.txt : 60 labelled sentences drawn by fixed seed
    python3 part2e_audit.py score   -> agreement of the founder's corrections with the annotator (AUDIT_RULE)

The founder edits ONLY the labels after the last "|" where they disagree (add, remove or change a topic:attitude;
"itself" for talk about the listener), leaving agreed lines untouched.
"""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "data_heldout/dialog/a2e_labels.jsonl"
AUDIT = ROOT / "ears_founder_set/a2e_audit.txt"
SEED, N = 909, 60
AUDIT_RULE = """Labels are TRUSTED when, over the 60 audited sentences: topic-set agreement F1 >= 0.80, attitude agreement on
topics both list >= 0.80, and 'itself' agreement (per sentence) >= 0.90 with Cohen's kappa >= 0.70. Otherwise the
annotator's labels are NOT used and Part 2e stops before any Ears look."""


def make():
    rows = [json.loads(l) for l in open(LABELS)]
    pick = sorted(random.Random(SEED).sample(rows, N), key=lambda r: r["id"])
    with open(AUDIT, "w") as f:
        f.write("# A2e label audit — 60 sentences labelled by the independent annotator (GLM-5.3) with the frozen guide.\n"
                "# Fix ONLY the labels after the last '|' where you disagree; leave agreed lines exactly as they are.\n"
                "# topic:attitude  (warm | cold | neutral | unsure);  'itself' = the sentence is about the listener ('you').\n"
                "# Rules = the guide in build/part2e_label.py (every noun; the SPEAKER's own present attitude; time adverbs\n"
                "#   and pronouns are not topics; someone else's feeling, questions, hypotheticals, 'used to' -> neutral).\n\n")
        for r in pick:
            f.write(f"{r['id']} | {r['sentence']} | {', '.join(f'{n}:{a}' for n, a in r['tags'])}\n")
    print(AUDIT, N, "sentences")


def parse(line):
    i, rest = line.split("|", 1)
    tags = rest.rsplit("|", 1)[1]
    return int(i), {t.split(":")[0].strip().lower(): t.split(":")[1].strip().lower() for t in tags.split(",") if ":" in t}


def score():
    ann = {r["id"]: {n: a for n, a in r["tags"]} for r in map(json.loads, open(LABELS))}
    fnd = dict(parse(l) for l in open(AUDIT) if l.strip() and not l.startswith("#"))
    tp = fp = fn = agree = both = 0; s_pairs = []
    for i, f in fnd.items():
        a = ann[i]; fa, aa = set(f) - {"itself"}, set(a) - {"itself"}
        tp += len(fa & aa); fp += len(aa - fa); fn += len(fa - aa)
        for n in fa & aa:
            both += 1; agree += f[n] == a[n]
        s_pairs.append(("itself" in f, "itself" in a))
    f1 = 2 * tp / max(1, 2 * tp + fp + fn)
    n = len(s_pairs); po = sum(x == y for x, y in s_pairs) / n
    pf, pa = sum(x for x, _ in s_pairs) / n, sum(y for _, y in s_pairs) / n
    pe = pf * pa + (1 - pf) * (1 - pa); kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
    r = {"sentences": n, "topic_f1": round(f1, 3), "attitude_agreement": round(agree / max(1, both), 3), "attitude_n": both,
         "itself_agreement": round(po, 3), "itself_kappa": round(kappa, 3), "itself_founder": sum(x for x, _ in s_pairs)}
    r["trusted"] = f1 >= 0.80 and r["attitude_agreement"] >= 0.80 and po >= 0.90 and kappa >= 0.70
    json.dump(r, open(ROOT / "data_heldout/dialog/a2e_audit_result.json", "w"), indent=1)
    print(json.dumps(r, indent=1))


if __name__ == "__main__":
    {"make": make, "score": score}[sys.argv[1]]()
