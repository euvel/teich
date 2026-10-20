"""Talk to Teich v0.4 (BUILD candidate, lab only) — Ears v5 + veto-only read-back.

    python3 talk_v04.py --local SEAT.json "My dog is wonderful. The rain was awful."      # interactive read-back
    python3 talk_v04.py --local SEAT.json --veto 2 "..."                                   # strike mention 2, no prompt

Flow: the Ears hear the utterance -> the founder sees the read-back ("I heard: ...") -> the founder may STRIKE any
mentions (never add, never change a topic or a sign) -> the remaining mentions go to the creature under its laws.
Struck mentions never reach the creature; they are written to the conversation record with the reason "vetoed".
The conversation record keeps the text's sha256, never the text. Founder-only speech: there is no other speaker.
The real seat teich-04 exists only after birth; this tool refuses it until then.
"""
import argparse
import hashlib
import json
import sys
import time
import uuid
from pathlib import Path

import genome_v04 as GN
import seat_v04 as SV

HERE = Path(__file__).resolve().parent
RECORD = HERE / "conversations_v04.jsonl"


def readback(heard):
    lines, k = [], 0
    for h in heard:
        for m in h["mentions"]:
            k += 1
            feel = {1: "warm", -1: "cold", 0: "no feeling"}[m["sign"]]
            if m.get("no_feeling_because"):
                feel += f": {m['no_feeling_because']}"
            name = "itself" if m["cluster"] == GN.SELF else " · ".join(GN.VOCAB["clusters"][m["cluster"]]["label"])
            lines.append(f"  {k}. {m['words']}  ->  {name}  ({feel})")
        for noun, cos in h["unheard"]:
            lines.append(f"     (not heard: '{noun}' — no concept close enough)")
    return k, "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text"); ap.add_argument("--local", required=False); ap.add_argument("--veto", default=None)
    ap.add_argument("--now", type=float); ap.add_argument("--conversation", default=None)
    a = ap.parse_args()
    if not a.local:
        print("refusing: the real seat teich-04 exists only after birth."); return 0
    import ears_v05 as E5
    ears = E5.EarsV5()
    mentions, heard = ears.hear(a.text)
    n, text = readback(heard)
    print("I heard:\n" + (text or "  nothing"))
    if a.veto is not None:
        struck = {int(x) for x in a.veto.split(",") if x.strip()}
    elif n and sys.stdin.isatty():
        ans = input("Strike any? (numbers, comma-separated; Enter = keep all): ").strip()
        struck = {int(x) for x in ans.split(",") if x.strip()}
    else:
        struck = set()
    if any(not 1 <= s <= n for s in struck):
        print("refusing: a veto can only strike a mention that was heard."); return 1
    keep = [m for i, m in enumerate(mentions, 1) if i not in struck]
    conv = a.conversation or f"c-{uuid.uuid4().hex[:12]}"
    out = SV.converse(SV.LocalSeat(Path(a.local)), keep, conv, "founder", now=a.now) if keep else []
    rec = {"ts": time.time(), "conversation": conv, "text_sha256": hashlib.sha256(a.text.encode()).hexdigest(),
           "ears": ears.version, "heard": [[m[0], m[1]] for m in mentions], "vetoed": sorted(struck),
           "outcomes": [{"heart": h, "mind": mnd} for h, mnd in out]}
    with open(RECORD, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(f"{len(keep)} mention(s) given to it, {len(struck)} struck; outcomes: {rec['outcomes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
