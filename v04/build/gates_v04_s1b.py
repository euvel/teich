"""Teich v0.4 — SCORED harness for gate S1b (Ears v9 self routing, founder's broad reading; spec V04_SPEC_S1 Amend. 1).
Bars (founder decision 10-19): caught >= 0.85 AND precision >= 0.90; false rate reported with its interval.

    python3 gates_v04_s1b.py smoke   40 MAMS val sentences -> out_smoke/S1b_smoke.json (Kaggle/laptop parity)
    python3 gates_v04_s1b.py rv9     regression R-v9: every non-self mention of v9 equals v7 on the 400 A2e sentences
                                     (v7's scored A2e output) and the 40 MAMS parity sentences (laptop v7 reference)
    python3 gates_v04_s1b.py s1b     the one look: S1 sentences; truth = founder label on the 50 audited sentences,
                                     the judge's majority label elsewhere ("unsure" not scored); needs s1b_trust.json
Run rv9 / s1b only after Amendment 1 is anchored. One look.
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
D = HERE.parent / "data_heldout"
REF_A2E = HERE / "ref/A2e_v7_detail.json"
REF_MAMS = HERE / "out_smoke/A2d_smoke.json"


def save(sub, name, d):
    out = HERE / sub; out.mkdir(exist_ok=True)
    json.dump(d, open(out / f"{name}.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in d.items() if k != "detail"}, indent=1))


def wilson(k, n, z=1.96):
    if n == 0:
        return [0.0, 1.0]
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * ((p * (1 - p) + z * z / (4 * n)) / n) ** 0.5
    return [round((c - h) / d, 3), round((c + h) / d, 3)]


def ears():
    import ears_v09 as E9
    return E9.EarsV9()


def mams():
    return [s.find("text").text for s in list(ET.parse(D / "mams/val.xml").getroot())[:40]]


def smoke():
    e = ears(); detail = []
    for t in mams():
        h = e.hear_sentence(t)
        detail.append({"heard": [[x["cluster"], x["sign"]] for x in h["mentions"]]})
    save("out_smoke", "S1b_smoke", {"sentences": len(detail), "ears": e.version, "detail": detail})


def rv9():
    import genome_v04 as GN
    e = ears(); bad = []
    ref = json.load(open(REF_A2E))["detail"]
    rows = {r["id"]: r for r in map(json.loads, open(D / "dialog/a2e_labels.jsonl"))}
    for r in ref:
        _, heard = e.hear(rows[r["id"]]["sentence"])
        hc = {}
        for h in heard:
            for x in h["mentions"]:
                hc.setdefault(x["cluster"], x)
        mine = [[j, x["sign"]] for j, x in hc.items() if j != GN.SELF]
        if mine != [m for m in r["heard"] if m[0] != GN.SELF]:
            bad.append(("a2e", r["id"]))
    mref = json.load(open(REF_MAMS))["detail"]
    for i, t in enumerate(mams()):
        got = [[x["cluster"], x["sign"]] for x in e.hear_sentence(t)["mentions"]]
        if [m for m in got if m[0] != GN.SELF] != [m for m in mref[i]["heard"] if m[0] != GN.SELF]:
            bad.append(("mams", i))
    save("out_v04", "Rv9", {"gate": "R-v9", "a2e_sentences": len(ref), "mams_sentences": 40, "differing": bad,
                            "passed": not bad, "ears": e.version})


def s1b():
    import genome_v04 as GN
    trust = json.load(open(D / "dialog/s1b_trust.json"))
    if not trust.get("trusted"):
        raise SystemExit("judge labels not trusted by the founder's audit: no Ears look")
    from s1b_trust import founder_labels
    f = founder_labels()
    judge = {r["id"]: r["label"] for r in map(json.loads, open(D / "dialog/s1b_labels.jsonl"))}
    e = ears(); n = {"m": 0, "m_ok": 0, "x": 0, "x_fp": 0, "m1": 0, "m1_ok": 0, "m2": 0, "m2_ok": 0}; detail = []
    for row in map(json.loads, open(D / "dialog/s1_sentences.jsonl")):
        i = row["id"]
        if i in f:
            truth, src = f[i] != "NONE", "founder"
        elif judge.get(i) in ("MIRROR", "NONE"):
            truth, src = judge[i] == "MIRROR", "judge"
        else:
            detail.append({"id": i, "scored": False}); continue
        mentions, heard = e.hear(row["sentence"])
        routed = any(c == GN.SELF for c, _, _ in mentions)
        if truth:
            n["m"] += 1; n["m_ok"] += routed
            if i in f:
                k = f[i].lower(); n[k] += 1; n[k + "_ok"] += routed
        else:
            n["x"] += 1; n["x_fp"] += routed
        detail.append({"id": i, "truth": "MIRROR" if truth else "NONE", "from": src, "routed": routed,
                       "by": [h.get("self_by") for h in heard]})
    r = {"gate": "S1b", "trust": trust, "mirrors": n["m"], "none": n["x"],
         "caught": n["m_ok"] / max(1, n["m"]), "caught_ci": wilson(n["m_ok"], n["m"]),
         "false": n["x_fp"] / max(1, n["x"]), "false_ci": wilson(n["x_fp"], n["x"]),
         "founder_m1_caught": [n["m1_ok"], n["m1"]], "founder_m2_caught": [n["m2_ok"], n["m2"]], "ears": e.version}
    routed = n["m_ok"] + n["x_fp"]
    r["precision"] = n["m_ok"] / max(1, routed); r["precision_ci"] = wilson(n["m_ok"], routed); r["routed"] = routed
    r["passed"] = r["caught"] >= 0.85 and r["precision"] >= 0.90
    save("out_v04", "S1b", {**r, "detail": detail})


if __name__ == "__main__":
    {"smoke": smoke, "rv9": rv9, "s1b": s1b}[sys.argv[1]]()
