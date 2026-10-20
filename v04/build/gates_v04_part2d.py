"""Teich v0.4 — SCORED harness for spec part 2d (Ears v7): R2d (regression), A2d (third founder set), plus the
MAMS-val parity smoke. Bars are those of A2b (gates_v04_part2.py); the instrument is v7, and recall counts topics the mind has a word for
(A2a's gold_certain definition; founder decision 10-07), with coverage of all topics reported alongside.

Run R2d / A2d only after part 2d is frozen and anchored. One look.
    python3 gates_v04_part2d.py smoke | r2d | a2d      (smoke: 40 MAMS *val* sentences, out_smoke/, parity only)
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
D = HERE.parent / "data_heldout"
FOUNDER = HERE.parent / "ears_founder_set/founder_labels_3.txt"
SPENT = [HERE.parent / "ears_founder_set/founder_labels.txt", HERE.parent / "ears_founder_set/founder_labels_2.txt"]


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
    save("out_smoke", "A2d_smoke", {"sentences": len(detail), "ears": ears.version, "detail": detail})


def r2d():
    import ears_v07 as E7, creature_v04 as CR, genome_v04 as GN
    import numpy as np
    ears = E7.EarsV7()
    mentions, heard = ears.hear("My dog is wonderful.")
    dog = next(c["j"] for c in GN.VOCAB["clusters"] if "dog" in c["members"])
    c = CR.birth(seed=2012, t0=0.0); b = c.body; before = (b.fn.copy(), b.fG.copy(), b.ln.copy(), c.heart.k.copy())
    for j, s, h in mentions:
        c.hear(j, s, {"speaker": "founder", "conversation": "r2d", "text_sha256": h})
    reg = int(GN.REGION_OF[dog]); others = [j for j in range(GN.G) if j != dog]
    same = all(np.array_equal(b.fn[j], before[0][j]) and np.array_equal(b.fG[j], before[1][j])
               and np.array_equal(b.ln[j], before[2][j]) for j in others)
    heart_ok = c.heart.k[reg] == before[3][reg] + 1 and all(c.heart.k[r] == before[3][r] for r in range(len(GN.REGIONS)) if r != reg)
    ok = len(mentions) == 1 and mentions[0][:2] == (dog, 1) and int(b.n.sum()) == 1 and same and bool(heart_ok)
    save("out_v04", "R2d", {"gate": "R2d", "passed": ok, "heard": heard, "ears": ears.version})


def a2d():
    import ears_v07 as E7, genome_v04 as GN
    ears = E7.EarsV7(); lines = []; repeats = 0
    spent = {l.split("|")[0].strip().lower() for p in SPENT for l in open(p, encoding="utf-8") if "|" in l and not l.lstrip().startswith("#")}
    for raw in open(FOUNDER, encoding="utf-8"):
        if raw.strip() and not raw.lstrip().startswith("#"):
            sent, tags = raw.split("|")
            if sent.strip().lower() in spent:                     # design data for v6: not scored (fixed before the look)
                repeats += 1; continue
            lines.append((sent.strip(), [tuple(x.strip() for x in t.lower().split(":")) for t in tags.split(",") if t.strip()]))
    m = dict(rc=0, rn=0, ac=0, an=0, ok=0, opp=0, pn=0, prec=0, heard=0, self_ok=0, self_n=0)
    for sent, tags in lines:
        mentions, heard = ears.hear(sent)
        hc = {}
        for h in heard:
            for x in h["mentions"]:
                hc.setdefault(x["cluster"], x)
        gold = {}
        for noun, att in tags:
            lemma = noun if noun == "itself" else (lambda d: ([t for t in d if t.pos_ in ("NOUN", "PROPN")] or list(d))[-1].lemma_.lower())(ears.nlp(noun))
            known = noun == "itself" or lemma in ears.cluster_of            # A2a's gold_certain (founder decision 10-07)
            j = GN.SELF if noun == "itself" else ears.cluster_of.get(ears.map_noun(lemma)[0] or
                                                                     ears._map_cache.get(lemma, (None,))[0])
            gold[j] = (att, known) if j not in gold else (att, known or gold[j][1])
            if noun == "itself":
                m["self_n"] += 1; m["self_ok"] += GN.SELF in hc
        m["heard"] += len(hc); m["prec"] += sum(j in gold for j in hc)
        for j, (att, known) in gold.items():
            m["an"] += 1; m["ac"] += j in hc
            m["rn"] += known; m["rc"] += known and j in hc
            if j in hc and att in ("warm", "cold"):
                gs = 1 if att == "warm" else -1; sg = hc[j]["sign"]
                m["pn"] += 1; m["ok"] += sg == gs; m["opp"] += sg == -gs
    r = {"gate": "A2d", "lines": len(lines), "excluded_spent_repeats": repeats, "recall": m["rc"] / max(1, m["rn"]), "attitude_correct": m["ok"] / max(1, m["pn"]),
         "attitude_opposite": m["opp"] / max(1, m["pn"]), "precision": m["prec"] / max(1, m["heard"]),
         "self_routing": m["self_ok"] / max(1, m["self_n"]), "attitude_n": m["pn"], "known_topics": m["rn"],
         "coverage_all_topics": m["ac"] / max(1, m["an"]), "all_topics": m["an"], "ears": ears.version}
    # recall = over topics the mind has a word for (A2a's definition; founder decision 10-07, after A2b) — coverage of
    # ALL topics is reported, not barred; the unknown words are the door log's growth signal.
    r["passed"] = (r["recall"] >= 0.80 and r["attitude_correct"] >= 0.75 and r["attitude_opposite"] <= 0.08
                   and r["precision"] >= 0.70 and r["self_routing"] >= 0.90)
    save("out_v04", "A2d", r)


if __name__ == "__main__":
    {"smoke": smoke, "r2d": r2d, "a2d": a2d}[sys.argv[1]]()
