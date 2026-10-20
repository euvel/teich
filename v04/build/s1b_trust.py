"""Gate S1b — automatic trust check of the judge's broad-reading labels against the founder's 50 audited labels
(ears_founder_set/s1_audit.txt, sha d5f2665b, done 2026-10-19). No new founder judgement is needed.

TRUSTED when, over the audited sentences the judge labelled (not "unsure"):
  mirror-vs-none agreement >= 0.85, AND the judge says NONE on at least 2 of the founder's 3 NONE sentences
  (kappa is not used: with ~94% mirrors in the founder's reading it is not a meaningful statistic).
    python3 s1b_trust.py      -> data_heldout/dialog/s1b_trust.json
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data_heldout/dialog"
AUDIT = ROOT / "ears_founder_set/s1_audit.txt"


def founder_labels():
    out = {}
    for l in open(AUDIT):
        if l.strip() and not l.startswith("#"):
            out[int(l.split("|")[0])] = l.rsplit("|", 1)[1].strip().upper()
    return out


def main():
    f = founder_labels()
    judge = {r["id"]: r["label"] for r in map(json.loads, open(D / "s1b_labels.jsonl"))}
    pairs = [(f[i] != "NONE", judge[i] == "MIRROR") for i in f if judge.get(i) in ("MIRROR", "NONE")]
    agree = sum(a == b for a, b in pairs) / max(1, len(pairs))
    f_none = [i for i in f if f[i] == "NONE"]
    none_hit = sum(judge.get(i) == "NONE" for i in f_none)
    r = {"audited": len(f), "judge_labelled": len(pairs), "mirror_agreement": round(agree, 3),
         "founder_none": len(f_none), "judge_none_on_founder_none": none_hit,
         "judge_none_on_founder_mirror": sum(f[i] != "NONE" and judge.get(i) == "NONE" for i in f),
         "trusted": agree >= 0.85 and none_hit >= 2}
    json.dump(r, open(D / "s1b_trust.json", "w"), indent=1)
    print(json.dumps(r, indent=1))


if __name__ == "__main__":
    main()
