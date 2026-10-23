"""Talk to Teich v0.5 (founder only) — its question first, then your words, read-back, strikes.

    python3 talk_v05.py --seat teich-05 "your words"          # answers its pending question, if it asked one
    python3 talk_v05.py --seat teich-05 --not-answering "..."  # speak without answering its question
    python3 talk_v05.py --local SEAT.json "..."               # a local (lab) seat

1. ASK: if it chose a question last night, it is delivered now (recorded before you speak) with its true reason.
2. Your words are heard by Ears v7 exactly as free talk. If you answer its question:
     about a region     -> mentions in that region are tagged "asked" (its self compares asked vs free hearing)
     "What am I to you?" -> your answer is a mirror by context: one mention of itself is ensured
     about a word       -> where your answer lands is a candidate binding for that word (2 days agreeing bind it)
   Nouns the Ears could not place wait at its door (single words, never sentences).
3. PRESENT -> read-back -> your strikes -> DECIDE (+ the answer). The record keeps the text's sha256, never the text.
"""
import argparse
import hashlib
import json
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "seat"))
import genome_v04 as GN  # noqa: E402
import seat_v05 as S  # noqa: E402
import self_text_v05 as TX  # noqa: E402
from self_v04 import cw_of_mention  # noqa: E402
from talk_v04s import name, proposals as free_proposals  # noqa: E402

YOU = "the person being spoken to ('you')"


def build(ears, text, q):
    """-> (proposals, door words, landed cluster). Free talk is exactly talk_v04s's; a question only adds tags."""
    _, heard = ears.hear(text)
    props = free_proposals(ears, heard)
    door = sorted({noun for h in heard for noun, _ in h["unheard"]})
    landed = None
    if q is not None:
        kind, x = q["q"]
        if kind == "region" and x == 8:
            mine = [p for p in props if p["cluster"] == GN.SELF]
            if mine:
                mine[0]["asked"] = q["act_id"]
            else:
                a, neu = ears.attitude3(text, YOU)
                sign = ears.sign_of(a, False, neu)
                cn, cf = cw_of_mention({"sign": sign, "attitude": a, "cos": 1.0}, ears.tau_map, ears.theta)
                props.append({"cluster": GN.SELF, "sign": sign, "words": "you (answering my question)",
                              "text_sha256": hashlib.sha256(text.encode()).hexdigest(), "cn": cn, "cf": cf,
                              "asked": q["act_id"]})
        elif kind == "region":
            for p in props:
                if int(GN.REGION_OF[p["cluster"]]) == x:
                    p["asked"] = q["act_id"]
        elif kind == "word":
            landed = next((p["cluster"] for p in props if p["cluster"] != GN.SELF), None)
    return props, door, landed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text"); ap.add_argument("--seat"); ap.add_argument("--local"); ap.add_argument("--veto")
    ap.add_argument("--not-answering", action="store_true")
    a = ap.parse_args()
    if a.local:
        import seat_v04 as SV
        seat = SV.LocalSeat(Path(a.local))
    else:
        from cloud_v04 import CloudSeatV04
        seat = CloudSeatV04(a.seat or "teich-05")
    q, inputs, grown, proposal = S.ask(seat)
    if proposal:
        print("(It has a growth proposal waiting for you: python3 grow_v05.py --seat ...)\n")
    if q:
        text, why = TX.question(q["q"], inputs)
        print(f"It asks: {text}\n   (because: {why})\n")
    import ears_v07 as EM
    ears = EM.EarsV7()
    ears.cluster_of.update(grown)            # words it learned through approved growth (v0.5.x) are now its own
    answering = q is not None and not a.not_answering
    props, door, landed = build(ears, a.text, q if answering else None)
    organ = hashlib.sha256(json.dumps(ears.version, sort_keys=True).encode()).hexdigest()[:16]
    conv = f"c-{uuid.uuid4().hex[:12]}"
    items = S.present(seat, [{k: v for k, v in p.items() if k != "words"} for p in props], conv, organ, door)
    shown = []
    print("I heard:")
    for p, it in zip(props, items):
        if not it["shown"]:
            print(f"     (unsure, not offered: '{p['words']}' -> {name(p['cluster'])})"); continue
        shown.append(it)
        feel = {1: "warm", -1: "cold", 0: "no feeling"}[it["sign"]] + (" (unsure of the feeling)" if it["altered"] else "")
        tags = ("  [answering my question]" if p.get("asked") else "") + ("  [probe: I'm testing myself]" if it["probe"] else "")
        print(f"  {len(shown)}. {p['words']}  ->  {name(p['cluster'])}  ({feel}){tags}")
    if door:
        print(f"     (at my door, not yet known: {', '.join(door)})")
    if a.veto is not None:
        idx = {int(x) for x in a.veto.split(",") if x.strip()}
    elif shown and sys.stdin.isatty():
        idx = {int(x) for x in input("Strike any? (numbers, comma-separated; Enter = keep all): ").split(",") if x.strip()}
    else:
        idx = set()
    if any(not 1 <= i <= len(shown) for i in idx):
        print("refusing: a veto can only strike a line that was shown."); return 1
    ans = {"act_id": q["act_id"], "answered": answering, "landed": landed} if q else None
    out = S.decide(seat, conv, {shown[i - 1]["pid"] for i in idx}, "founder", ans)
    print(f"{len(shown) - len(idx)} kept, {len(idx)} struck; outcomes: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
