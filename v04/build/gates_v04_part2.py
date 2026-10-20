"""Teich v0.4 — SCORED harness for spec part 2 (Ears v5): A2a (MAMS test), R2 (regression), A2b (founder set).

Run A2a / R2 only after part 2a is frozen and anchored; A2b only after part 2b is. One look each.
    python3 gates_v04_part2.py a2a | r2 | a2b          (TEICH_SMOKE=1: a2a on 40 MAMS *val* sentences, out_smoke/)
"""
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SMOKE = os.environ.get("TEICH_SMOKE") == "1"
OUT = HERE / ("out_smoke" if SMOKE else "out_v04"); OUT.mkdir(exist_ok=True)
D = HERE.parent / "data_heldout"


def save(name, d):
    json.dump(d, open(OUT / f"{name}.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in d.items() if k != "detail"}, indent=1))


def gold_of(ears, term):
    doc = ears.nlp(term); heads = [t for t in doc if t.pos_ in ("NOUN", "PROPN")] or list(doc)
    lemma = heads[-1].lemma_.lower()
    certain = lemma in ears.cluster_of
    c, _ = ears.map_noun(lemma)
    nearest = c if c is not None else ears._map_cache.get(lemma, (None,))[0]
    return nearest, certain


def a2a():
    import ears_v05 as E5
    ears = E5.EarsV5()
    if SMOKE:
        sents = list(ET.parse(D / "mams/val.xml").getroot())[:40]
    else:
        sents = list(ET.parse(D / "mams/test.xml").getroot())
    m = dict(rc=0, rn=0, ok=0, opp=0, pn=0, prec=0, heard=0); detail = []
    for s in sents:
        text = s.find("text").text
        h = ears.hear_sentence(text)
        hc = {x["cluster"]: x for x in h["mentions"]}
        golds = []
        for a in s.find("aspectTerms"):
            concept, certain = gold_of(ears, a.get("term"))
            golds.append((ears.cluster_of.get(concept) if concept else None, certain, a.get("polarity")))
        gcl = {g[0] for g in golds}
        m["heard"] += len(hc); m["prec"] += sum(j in gcl for j in hc)
        for j, certain, pol in golds:
            if certain:
                m["rn"] += 1; m["rc"] += j in hc
            if j in hc and pol in ("positive", "negative"):
                gs = 1 if pol == "positive" else -1; sg = hc[j]["sign"]
                m["pn"] += 1; m["ok"] += sg == gs; m["opp"] += sg == -gs
        detail.append({"n_gold": len(golds), "heard": [[x["cluster"], x["sign"]] for x in h["mentions"]]})
    r = {"gate": "A2a", "sentences": len(sents), "recall": m["rc"] / max(1, m["rn"]), "gold_certain": m["rn"],
         "attitude_correct": m["ok"] / max(1, m["pn"]), "attitude_opposite": m["opp"] / max(1, m["pn"]),
         "attitude_n": m["pn"], "precision_lb": m["prec"] / max(1, m["heard"]), "ears": ears.version}
    r["passed"] = (r["recall"] >= 0.90 and r["attitude_correct"] >= 0.72 and r["attitude_opposite"] <= 0.20
                   and r["precision_lb"] >= 0.45)
    save("A2a", {**r, "detail": detail})


def r2():
    import ears_v05 as E5, creature_v04 as CR, genome_v04 as GN
    import numpy as np
    ears = E5.EarsV5()
    mentions, heard = ears.hear("My dog is wonderful.")
    dog = next(c["j"] for c in GN.VOCAB["clusters"] if "dog" in c["members"])
    c = CR.birth(seed=2012, t0=0.0); b = c.body; before = (b.fn.copy(), b.fG.copy(), b.ln.copy(), c.heart.k.copy())
    for j, s, h in mentions:
        c.hear(j, s, {"speaker": "founder", "conversation": "r2", "text_sha256": h})
    reg = int(GN.REGION_OF[dog]); others = [j for j in range(GN.G) if j != dog]
    same = all(np.array_equal(b.fn[j], before[0][j]) and np.array_equal(b.fG[j], before[1][j])
               and np.array_equal(b.ln[j], before[2][j]) for j in others)
    heart_ok = c.heart.k[reg] == before[3][reg] + 1 and all(c.heart.k[r] == before[3][r] for r in range(len(GN.REGIONS)) if r != reg)
    ok = len(mentions) == 1 and mentions[0][:2] == (dog, 1) and int(b.n.sum()) == 1 and same and bool(heart_ok)
    save("R2", {"gate": "R2", "passed": ok, "heard": heard, "ears": ears.version})


def a2b():
    import ears_v05 as E5, genome_v04 as GN
    ears = E5.EarsV5(); lines = []
    for raw in open(HERE.parent / "ears_founder_set/founder_labels.txt", encoding="utf-8"):
        if raw.strip() and not raw.lstrip().startswith("#"):
            sent, tags = raw.split("|")
            lines.append((sent.strip(), [tuple(x.strip() for x in t.lower().split(":")) for t in tags.split(",") if t.strip()]))
    m = dict(rc=0, rn=0, ok=0, opp=0, pn=0, prec=0, heard=0, self_ok=0, self_n=0)
    for sent, tags in lines:
        mentions, heard = ears.hear(sent)
        hc = {}
        for h in heard:
            for x in h["mentions"]:
                hc.setdefault(x["cluster"], x)
        gold = {}
        for noun, att in tags:
            j = GN.SELF if noun == "itself" else ears.cluster_of.get(ears.map_noun(noun)[0] or
                                                                     ears._map_cache.get(noun, (None,))[0])
            gold[j] = att
            if noun == "itself":
                m["self_n"] += 1; m["self_ok"] += GN.SELF in hc
        m["heard"] += len(hc); m["prec"] += sum(j in gold for j in hc)
        for j, att in gold.items():
            m["rn"] += 1; m["rc"] += j in hc
            if j in hc and att in ("warm", "cold"):
                gs = 1 if att == "warm" else -1; sg = hc[j]["sign"]
                m["pn"] += 1; m["ok"] += sg == gs; m["opp"] += sg == -gs
    r = {"gate": "A2b", "lines": len(lines), "recall": m["rc"] / max(1, m["rn"]), "attitude_correct": m["ok"] / max(1, m["pn"]),
         "attitude_opposite": m["opp"] / max(1, m["pn"]), "precision": m["prec"] / max(1, m["heard"]),
         "self_routing": m["self_ok"] / max(1, m["self_n"]), "ears": ears.version}
    # AMENDMENT 2026-10-07 (announced before the founder set exists): bars aligned with the founder-approved,
    # anchored spec V04_SPEC_part2a (correct >= 0.75, opposite <= 0.08); the harness had kept the pre-rebase draft.
    r["passed"] = (r["recall"] >= 0.80 and r["attitude_correct"] >= 0.75 and r["attitude_opposite"] <= 0.08
                   and r["precision"] >= 0.70 and r["self_routing"] >= 0.90)
    save("A2b", r)


if __name__ == "__main__":
    if SMOKE and sys.argv[1] != "a2a":
        raise SystemExit("smoke mode runs a2a on MAMS val only")
    {"a2a": a2a, "r2": r2, "a2b": a2b}[sys.argv[1]]()
