"""Teich v0.4 — SCORED harness for spec part 2e (Ears v7): R2e (regression), A2e (EmpatheticDialogues test sentences,
independent GLM-5.3 labels, founder-audited), plus the
MAMS-val parity smoke. Bars are those of A2b (gates_v04_part2.py); the instrument is v7, and recall counts topics the mind has a word for
(A2a's gold_certain definition; founder decision 10-07), with coverage of all topics reported alongside.

Run R2e / A2e only after part 2e is frozen and anchored. One look.
    python3 gates_v04_part2e.py smoke | r2e | a2e      (smoke: 40 MAMS *val* sentences, out_smoke/, parity only)
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
D = HERE.parent / "data_heldout"
LABELS = HERE.parent / "data_heldout/dialog/a2e_labels.jsonl"
AUDIT_RESULT = HERE.parent / "data_heldout/dialog/a2e_audit_result.json"


def save(sub, name, d):
    out = HERE / sub; out.mkdir(exist_ok=True)
    json.dump(d, open(out / f"{name}.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in d.items() if k != "detail"}, indent=1))


def smoke():
    import ears_v07 as E7
    ears = E7.EarsV7(); detail = []
    for s in list(ET.parse(D / "mams/val.xml").getroot())[:40]:
        h = ears.hear_sentence(s.find("text").text)
        detail.append({"heard": [[x["cluster"], x["sign"]] for x in h["mentions"]]})
    save("out_smoke", "A2e_smoke", {"sentences": len(detail), "ears": ears.version, "detail": detail})


def r2e():
    import ears_v07 as E7, creature_v04 as CR, genome_v04 as GN
    import numpy as np
    ears = E7.EarsV7()
    mentions, heard = ears.hear("My dog is wonderful.")
    dog = next(c["j"] for c in GN.VOCAB["clusters"] if "dog" in c["members"])
    c = CR.birth(seed=2012, t0=0.0); b = c.body; before = (b.fn.copy(), b.fG.copy(), b.ln.copy(), c.heart.k.copy())
    for j, s, h in mentions:
        c.hear(j, s, {"speaker": "founder", "conversation": "r2e", "text_sha256": h})
    reg = int(GN.REGION_OF[dog]); others = [j for j in range(GN.G) if j != dog]
    same = all(np.array_equal(b.fn[j], before[0][j]) and np.array_equal(b.fG[j], before[1][j])
               and np.array_equal(b.ln[j], before[2][j]) for j in others)
    heart_ok = c.heart.k[reg] == before[3][reg] + 1 and all(c.heart.k[r] == before[3][r] for r in range(len(GN.REGIONS)) if r != reg)
    ok = len(mentions) == 1 and mentions[0][:2] == (dog, 1) and int(b.n.sum()) == 1 and same and bool(heart_ok)
    save("out_v04", "R2e", {"gate": "R2e", "passed": ok, "heard": heard, "ears": ears.version})


def wilson(k, n, z=1.96):
    if n == 0:
        return [0.0, 1.0]
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * ((p * (1 - p) + z * z / (4 * n)) / n) ** 0.5
    return [round((c - h) / d, 3), round((c + h) / d, 3)]


def a2e():
    import collections
    import ears_v07 as E7, genome_v04 as GN
    ears = E7.EarsV7(); rows = [json.loads(l) for l in open(LABELS)]
    audit = json.load(open(AUDIT_RESULT))
    if not audit.get("trusted"):
        raise SystemExit("annotator labels not trusted by the founder audit: no Ears look")
    m = collections.Counter(); per = collections.defaultdict(collections.Counter); detail = []
    for row in rows:
        mentions, heard = ears.hear(row["sentence"])
        hc = {}
        for h in heard:
            for x in h["mentions"]:
                hc.setdefault(x["cluster"], x)
        gold = {}
        for noun, att in row["tags"]:
            lemma = noun if noun == "itself" else (lambda d: ([t for t in d if t.pos_ in ("NOUN", "PROPN")] or list(d))[-1].lemma_.lower())(ears.nlp(noun))
            known = noun == "itself" or lemma in ears.cluster_of
            j = GN.SELF if noun == "itself" else ears.cluster_of.get(ears.map_noun(lemma)[0] or
                                                                     ears._map_cache.get(lemma, (None,))[0])
            gold[j] = (att, known) if j not in gold else (att, known or gold[j][1])
        st = per[row["stratum"]]
        for c in (m, st):
            c["self_n"] += GN.SELF in gold; c["self_ok"] += GN.SELF in gold and GN.SELF in hc
            c["self_fp"] += GN.SELF in hc and GN.SELF not in gold; c["nonself"] += GN.SELF not in gold
            c["heard"] += len(hc); c["prec"] += sum(j in gold for j in hc)
        for j, (att, known) in gold.items():
            for c in (m, st):
                c["an"] += 1; c["ac"] += j in hc; c["rn"] += known; c["rc"] += known and j in hc
                if j in hc and att in ("warm", "cold"):
                    gs = 1 if att == "warm" else -1; sg = hc[j]["sign"]
                    c["pn"] += 1; c["ok"] += sg == gs; c["opp"] += sg == -gs
        detail.append({"id": row["id"], "heard": [[x["cluster"], x["sign"]] for x in hc.values()]})
    r = {"gate": "A2e", "sentences": len(rows), "audit": audit,
         "recall": m["rc"] / max(1, m["rn"]), "recall_ci": wilson(m["rc"], m["rn"]), "known_topics": m["rn"],
         "attitude_correct": m["ok"] / max(1, m["pn"]), "attitude_correct_ci": wilson(m["ok"], m["pn"]),
         "attitude_opposite": m["opp"] / max(1, m["pn"]), "attitude_opposite_ci": wilson(m["opp"], m["pn"]), "attitude_n": m["pn"],
         "precision": m["prec"] / max(1, m["heard"]), "precision_ci": wilson(m["prec"], m["heard"]),
         "self_routing": m["self_ok"] / max(1, m["self_n"]), "self_routing_ci": wilson(m["self_ok"], m["self_n"]),
         "self_n": m["self_n"], "self_false_routes": m["self_fp"], "self_false_rate": m["self_fp"] / max(1, m["nonself"]),
         "coverage_all_topics": m["ac"] / max(1, m["an"]), "all_topics": m["an"],
         "per_stratum": {k: dict(v) for k, v in per.items()}, "ears": ears.version}
    r["passed"] = (r["recall"] >= 0.80 and r["attitude_correct"] >= 0.75 and r["attitude_opposite"] <= 0.08
                   and r["precision"] >= 0.70 and r["self_routing"] >= 0.90)
    save("out_v04", "A2e", {**r, "detail": detail})


if __name__ == "__main__":
    {"smoke": smoke, "r2e": r2e, "a2e": a2e}[sys.argv[1]]()
