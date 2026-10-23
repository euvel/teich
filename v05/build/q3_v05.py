"""Gate Q3 (asked-context hearing changes no free talk) — one Ears v7 instance, the 40 MAMS-val parity sentences.
For every sentence: v0.5's talk path with NO pending question must give exactly v0.4's proposals (talk_v04s), and
with a pending REGION question it may only ADD the "asked" tag (every other field identical).
    python3 q3_v05.py OUT.json
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import ears_v07 as EM
import talk_v05 as T5
from talk_v04s import proposals as v04_proposals

ROOT = Path(__file__).resolve().parents[2] / "v04_lab"
if not (ROOT / "data_heldout/mams/val.xml").exists():          # in the Kaggle kernel the file sits beside this script
    ROOT = Path(__file__).resolve().parent
sents = [s.find("text").text for s in list(ET.parse(ROOT / "data_heldout/mams/val.xml").getroot())[:40]]
ears = EM.EarsV7()
same_free = same_tagged = 0; diffs = []
for i, t in enumerate(sents):
    _, heard = ears.hear(t)
    ref = v04_proposals(ears, heard)
    free, _, _ = T5.build(ears, t, None)
    tagged, _, _ = T5.build(ears, t, {"act_id": 0, "q": ["region", 0]})
    strip = lambda ps: [{k: v for k, v in p.items() if k != "asked"} for p in ps]  # noqa: E731
    same_free += free == ref
    same_tagged += strip(tagged) == ref
    if free != ref or strip(tagged) != ref:
        diffs.append(i)
out = {"sentences": len(sents), "free_identical": same_free, "tagged_identical_but_tag": same_tagged, "differing": diffs,
       "passed": same_free == same_tagged == len(sents)}
json.dump(out, open(sys.argv[1], "w"), indent=1)
print(json.dumps(out, indent=1))
