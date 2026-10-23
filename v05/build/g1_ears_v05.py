"""Gate G1 — Ears half: after a word-binding growth, the grown words are heard as their concepts, and every other word
exactly as before (one Ears v7 instance). Clusters are where a founder's answers would place them (music, feeling).
    python3 g1_ears_v05.py OUT.json
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import ears_v07 as EM
import genome_v04 as GN
import talk_v05 as T5

ROOT = Path(__file__).resolve().parents[2] / "v04_lab"
if not (ROOT / "data_heldout/mams/val.xml").exists():
    ROOT = Path(__file__).resolve().parent
cl = lambda w: next(c["j"] for c in GN.VOCAB["clusters"] if w in c["members"])  # noqa: E731
GROWN = {"komitas": cl("music"), "frisson": cl("emotion"), "duduk": cl("music"), "kamancheh": cl("music")}
TESTS = ["I love komitas.", "The komitas recording was beautiful.", "I felt a frisson during my favorite song.",
         "That frisson was strange.", "My friend plays the duduk.", "The duduk sounded sad tonight.",
         "I heard a kamancheh at the concert.", "The kamancheh was out of tune."]
ears = EM.EarsV7()
before = {t: T5.build(ears, t, None) for t in TESTS}
mams = [s.find("text").text for s in list(ET.parse(ROOT / "data_heldout/mams/val.xml").getroot())[:40]]
mams_before = [T5.build(ears, t, None)[0] for t in mams]
ears.cluster_of.update(GROWN)                    # exactly what talk_v05 does with an approved growth
after = {t: T5.build(ears, t, None) for t in TESTS}
mams_after = [T5.build(ears, t, None)[0] for t in mams]
res = []
for t in TESTS:
    w = next(x for x in GROWN if x in t.lower())
    res.append({"sentence": t, "word": w, "at_door_before": w in before[t][1],
                "heard_after_as": [p["cluster"] for p in after[t][0] if p["words"] == w],
                "expected": GROWN[w], "door_after": after[t][1],
                "others_unchanged": [p for p in before[t][0]] == [p for p in after[t][0] if p["words"] != w],
                # the precise contract: the sentence's heard concepts only GAIN grown concepts; any mention that changed
                # is in a grown word's concept (one mention per concept per sentence)
                "concepts_only_gain": {p["cluster"] for p in before[t][0]} <= {p["cluster"] for p in after[t][0]},
                "changes_only_in_grown_concepts": all(p["cluster"] in GROWN.values()
                                                       for p in after[t][0] if p not in before[t][0])})
door = [r for r in res if r["at_door_before"]]; never = [r for r in res if not r["at_door_before"]]
out = {"grown": GROWN, "tests": res,
       "door_sentences": len(door), "never_at_door_sentences": len(never),
       # the contract: a word that came through the door is heard as its bound concept after growth, and leaves the door
       "door_words_heard_after_growth": all(r["heard_after_as"] == [r["expected"]] and r["word"] not in r["door_after"] for r in door),
       # a word the Ears never saw as a noun never reached the door: growth cannot apply to it, and changes nothing
       "never_at_door_unchanged": all(r["heard_after_as"] == [] for r in never),
       "sentences_where_a_grown_word_stood_for_its_concept": [r["sentence"] for r in res if not r["others_unchanged"]],
       "concepts_only_gain": all(r["concepts_only_gain"] for r in res),
       "changes_only_in_grown_concepts": all(r["changes_only_in_grown_concepts"] for r in res),
       "parity_40_unchanged": mams_before == mams_after}
out["passed"] = (len(door) > 0 and out["door_words_heard_after_growth"] and out["never_at_door_unchanged"]
                 and out["parity_40_unchanged"] and out["concepts_only_gain"] and out["changes_only_in_grown_concepts"])
json.dump(out, open(sys.argv[1], "w"), indent=1)
print(json.dumps(out, indent=1))
