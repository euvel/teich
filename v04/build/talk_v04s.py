"""Talk to Teich v0.4 WITH ITS SELF (BUILD candidate, lab only) — Ears + veto-only read-back, in two phases.

    python3 talk_v04s.py --local SEAT.json [--ears v7|v9] "My dog is wonderful. The rain was awful."
    python3 talk_v04s.py --local SEAT.json --veto 2 "..."            # strike read-back line 2, no prompt

1. The Ears hear the utterance and propose mentions (with the margins of their own confidence).
2. PRESENT (seat commit 1): its second self applies its caution and writes its predictions into the seat's log BEFORE
   you see anything; withheld mentions are listed as "unsure"; a probe is marked as a probe.
3. You may STRIKE any shown line (never add, never change a topic or a sign), as before.
4. DECIDE (seat commit 2): the kept mentions are heard under its laws.
The conversation record keeps the text's sha256, never the text. The real seat teich-04 exists only after birth.
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
import seat_v04s as SS
from self_v04 import cw_of_mention

HERE = Path(__file__).resolve().parent
RECORD = HERE / "conversations_v04s.jsonl"


def proposals(ears, heard):
    out = []
    for h in heard:
        for m in h["mentions"]:
            cn, cf = cw_of_mention(m, ears.tau_map, ears.theta)
            out.append({"cluster": int(m["cluster"]), "sign": int(m["sign"]), "words": m["words"],
                        "text_sha256": hashlib.sha256(h["sentence"].encode()).hexdigest(), "cn": cn, "cf": cf})
    return out


def name(j):
    return "itself" if j == GN.SELF else " · ".join(GN.VOCAB["clusters"][j]["label"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text"); ap.add_argument("--local"); ap.add_argument("--veto", default=None)
    ap.add_argument("--ears", default="v7", choices=["v7", "v9"])  # v7: S1b stopped 10-20 (anchored fallback)
    ap.add_argument("--now", type=float)
    a = ap.parse_args()
    if not a.local:
        print("refusing: the real seat teich-04 exists only after birth."); return 0
    if a.ears == "v9":
        import ears_v09 as EM; ears = EM.EarsV9()
    else:
        import ears_v07 as EM; ears = EM.EarsV7()
    _, heard = ears.hear(a.text)
    props = proposals(ears, heard)
    organ = hashlib.sha256(json.dumps(ears.version, sort_keys=True).encode()).hexdigest()[:16]
    conv = f"c-{uuid.uuid4().hex[:12]}"
    seat = SV.LocalSeat(Path(a.local))
    items = SS.present(seat, [{k: v for k, v in p.items() if k != "words"} for p in props], conv, organ, now=a.now)
    lines, shown = [], []
    for p, it in zip(props, items):
        if not it["shown"]:
            lines.append(f"     (unsure, not offered: '{p['words']}' -> {name(p['cluster'])})"); continue
        shown.append(it)
        feel = {1: "warm", -1: "cold", 0: "no feeling"}[it["sign"]] + (" (unsure of the feeling)" if it["altered"] else "")
        tag = "  [probe: I'm unsure here; I'm testing myself]" if it["probe"] else ""
        lines.append(f"  {len(shown)}. {p['words']}  ->  {name(p['cluster'])}  ({feel}){tag}")
    print("I heard:\n" + ("\n".join(lines) or "  nothing"))
    if a.veto is not None:
        idx = {int(x) for x in a.veto.split(",") if x.strip()}
    elif shown and sys.stdin.isatty():
        ans = input("Strike any? (numbers, comma-separated; Enter = keep all): ").strip()
        idx = {int(x) for x in ans.split(",") if x.strip()}
    else:
        idx = set()
    if any(not 1 <= i <= len(shown) for i in idx):
        print("refusing: a veto can only strike a line that was shown."); return 1
    struck = {shown[i - 1]["pid"] for i in idx}
    out = SS.decide(seat, conv, struck, "founder", now=a.now)
    with open(RECORD, "a") as f:
        f.write(json.dumps({"ts": time.time(), "conversation": conv, "text_sha256": hashlib.sha256(a.text.encode()).hexdigest(),
                            "ears": ears.version, "organ": organ, "shown": [it["pid"] for it in shown],
                            "struck": sorted(struck), "outcomes": out}) + "\n")
    print(f"{len(shown) - len(struck)} kept, {len(struck)} struck; outcomes: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
