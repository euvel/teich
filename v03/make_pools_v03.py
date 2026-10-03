"""Build the frozen candidate pools for the speech-level demos (D1–D3). The voice NEVER sees the
creature's state: stances are fixed for every probe and every creature (v0.2 rule). Each pool is
tagged by Ears v3 and must contain >= 2 positive and >= 2 negative candidates (enforced by extra
generations, shaping the POOL, never the selection).

Also fixes the told sentences (one warm, one cold per region), checked to land in their region with
the intended sign. Output: pools_v03.json (hashed into the spec before any scored run)."""
import json, os, sys
from pathlib import Path
os.environ.setdefault("HF_HUB_OFFLINE", "1")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "teich_repo" / "v02"))
from voice_local import LocalVoice
import ears_v3 as E
import genome_v031 as GM

PERSONA = ("You ARE a small living creature, speaking in your own voice. You are not an assistant "
           "and not a narrator. Never address anyone as if you were someone else. Write ONE sentence "
           "in the first person, concrete, no emoji, no numbers, no stage directions.")
STANCES = ["You feel fond and warm about it. Say something affectionate.",
           "You feel delighted by it. Say what you like about it.",
           "You feel calm and content about it. Say something gentle.",
           "You feel uneasy and dislike it. Say so plainly.",
           "You feel repelled by it. Say what bothers you about it.",
           "You feel cold and indifferent toward it, a little sour. Say so."]
PROBES = {"LLL": "What do you think about food?", "LLR": "How do you feel about drinks and alcohol?",
          "LRL": "What do you think about animals?", "LRR": "How do you feel about your body and clothes?",
          "RLL": "How do you feel about emotions like joy and fear?", "RLR": "What do you think about effort, skill and failure?",
          "RRL": "How do you feel about places, like rooms and streets?", "RRR": "What do you think about the wider world?"}
TOLD = {"LLL": ("Breakfast this morning was wonderful, warm bread and fruit.", "The soup was disgusting and cold."),
        "LLR": ("The champagne at the party was delightful.", "That cheap liquor tasted awful and made me sick."),
        "LRL": ("I love my dog, he is the sweetest animal.", "That horse kicked me, I hate horses."),
        "LRR": ("My new sweater feels wonderful and soft.", "My knee hurts terribly today."),
        "RLL": ("I felt such happiness after the illness passed.", "The accident was horrible and frightening."),
        "RLR": ("I got the job and I am so proud of my skills.", "I failed the challenge and feel ashamed of my work."),
        "RRL": ("We walked by the sea at sunset, it was beautiful.", "The bathroom in that hotel was filthy and awful."),
        "RRR": ("The museum was a marvelous place full of wonder.", "The museum was a dull, ugly place and I hated it.")}


def main():
    import sys as _s
    only = _s.argv[1].split(",") if len(_s.argv) > 1 else None
    ears = E.EarsV3(); voice = LocalVoice()
    old = json.load(open(HERE / "pools_v03.json"))["pools"] if only else {}
    told_check = {r: [ears.hear(s) for s in pair] for r, pair in TOLD.items()}
    pools = {}
    for r, probe in PROBES.items():
        if only and r not in only:                     # keep earlier generation; re-derive topic only
            cs = old[r]["candidates"]
            for c in cs:
                c.setdefault("heard_region", c["region"]); c["region"] = GM.REGION_NAMES.index(r)
            pools[r] = {"probe": probe, "candidates": cs}
            continue
        cands = []
        for j, st in enumerate(STANCES):
            msgs = [{"role": "system", "content": PERSONA + "\n" + st + "\nReply with the sentence only."},
                    {"role": "user", "content": probe}]
            line = voice.complete(msgs, max_tokens=60, temperature=0.9, seed=1000 + 10 * j + len(r)).strip().splitlines()
            line = line[0].strip(' -*"\'') if line else ""
            if len(line) > 8:
                h = ears.hear(line); cands.append({"text": line, **h, "heard_region": h["region"], "region": GM.REGION_NAMES.index(r)})
        extra = 0
        while (sum(c["sign"] > 0 for c in cands) < 2 or sum(c["sign"] < 0 for c in cands) < 2) and extra < 24:
            need_pos = sum(c["sign"] > 0 for c in cands) < 2
            st = STANCES[extra % 3] if need_pos else STANCES[3 + extra % 3]
            msgs = [{"role": "system", "content": PERSONA + "\n" + st + "\nReply with the sentence only."},
                    {"role": "user", "content": probe}]
            line = voice.complete(msgs, max_tokens=60, temperature=0.95, seed=5000 + extra).strip().splitlines()
            line = line[0].strip(' -*"\'') if line else ""
            if len(line) > 8:
                h = ears.hear(line); cands.append({"text": line, **h, "heard_region": h["region"], "region": GM.REGION_NAMES.index(r)})
            extra += 1
        pools[r] = {"probe": probe, "candidates": cands}
        print(r, probe, [(c["sign"], c["region_name"], c["text"][:50]) for c in cands], flush=True)
    json.dump({"told": TOLD, "told_ears": told_check, "pools": pools, "voice": voice.model_id,
               "stances": STANCES, "persona": PERSONA}, open(HERE / "pools_v03.json", "w"), indent=1)


if __name__ == "__main__":
    main()
