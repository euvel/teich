"""Talk to Teich v0.4 at its real seat (/o/teich-04): Ears v7 -> PRESENT (its predictions committed first) -> your
read-back strikes -> DECIDE. Founder-only speech. The record keeps the text's sha256, never the text.

    python3 talk_v04.py "My dog is wonderful. The rain was awful."
    python3 talk_v04.py --veto 2 "..."          # strike read-back line 2 without the prompt
"""
import argparse
import hashlib
import json
import sys
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "build"))
import seat_v04s as SS                          # noqa: E402
from cloud_v04 import CloudSeatV04              # noqa: E402
from talk_v04s import name, proposals           # noqa: E402

RECORD = HERE / "conversations_v04.jsonl"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("text"); ap.add_argument("--veto", default=None)
    ap.add_argument("--seat", default="teich-04")
    a = ap.parse_args()
    import ears_v07 as EM
    ears = EM.EarsV7()
    _, heard = ears.hear(a.text)
    props = proposals(ears, heard)
    organ = hashlib.sha256(json.dumps(ears.version, sort_keys=True).encode()).hexdigest()[:16]
    conv = f"c-{uuid.uuid4().hex[:12]}"
    seat = CloudSeatV04(a.seat)
    items = SS.present(seat, [{k: v for k, v in p.items() if k != "words"} for p in props], conv, organ)
    lines, shown = [], []
    for p, it in zip(props, items):
        if not it["shown"]:
            lines.append(f"     (unsure, not offered: '{p['words']}' -> {name(p['cluster'])})"); continue
        shown.append(it)
        feel = {1: "warm", -1: "cold", 0: "no feeling"}[it["sign"]] + (" (unsure of the feeling)" if it["altered"] else "")
        tag = "  [probe: I'm unsure here; I'm testing myself]" if it["probe"] else ""
        lines.append(f"  {len(shown)}. {p['words']}  ->  {name(p['cluster'])}  ({feel}){tag}")
    for h in heard:
        for noun, _ in h["unheard"]:
            lines.append(f"     (not heard: '{noun}' — no concept close enough)")
    print("I heard:\n" + ("\n".join(lines) or "  nothing"))
    if a.veto is not None:
        idx = {int(x) for x in a.veto.split(",") if x.strip()}
    elif shown and sys.stdin.isatty():
        ans = input("Strike any? (numbers, comma-separated; Enter = keep all): ").strip()
        idx = {int(x) for x in ans.split(",") if x.strip()}
    else:
        idx = set()
    if any(not 1 <= i <= len(shown) for i in idx):
        print("refusing: a veto can only strike a line that was shown (the lease will expire; nothing was heard)."); return 1
    struck = {shown[i - 1]["pid"] for i in idx}
    out = SS.decide(seat, conv, struck, "founder")
    with open(RECORD, "a") as f:
        f.write(json.dumps({"ts": time.time(), "seat": a.seat, "conversation": conv,
                            "text_sha256": hashlib.sha256(a.text.encode()).hexdigest(), "organ": organ,
                            "shown": [it["pid"] for it in shown], "struck": sorted(struck), "outcomes": out}) + "\n")
    print(f"{len(shown) - len(struck)} kept, {len(struck)} struck; outcomes (pid, heart, mind): {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
