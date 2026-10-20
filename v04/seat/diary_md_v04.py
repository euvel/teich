"""Teich v0.4's diary as files: one markdown page per night of its life, written from its own diary records (its
reading of its own attention, its heart, what it heard, and its self's account with receipts). No language model.

Entries live in the seat (the creature's outbox) until the log has another home; every wake regenerates the pages
from them, and a page, once written, is never rewritten (its sha256 would change).

    python3 diary_md_v04.py OUT_DIR [--seat teich-04]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "build"))
import creature_v04s as CS          # noqa: E402
import genome_v04 as GN             # noqa: E402
import self_text_v04 as TX          # noqa: E402

REG = {"LLL": "food & drink", "LLR": "body & matter", "LRL": "living things", "LRR": "objects & places",
       "RLL": "people & feeling", "RLR": "mind & society", "RRL": "arts & events", "RRR": "work & things made",
       "self": "itself"}


def page(e, t0):
    night_end = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(t0 + e["tick"]))
    L = [f"# Teich v0.4 — night {e['day'] + 1}", "",
         f"Written by itself at the end of night {e['day'] + 1} of its life ({night_end}), tick {e['tick']:,}. "
         "Nothing here was written by a language model.", ""]
    L += ["## Attending most to", ""]
    L += [f"- {a['name']} — read +{a['read']} after {a['nights']} quiet nights" for a in e["attending_most"]] or \
         ["- nothing stands out yet: every handle it can read is at its birth length"]
    L += ["", "## Shifts it read tonight", ""]
    L += [f"- {s['name']}: {s['from']} → {s['to']}" for s in e["shifts"]] or ["- none"]
    if e["still_reading"]:
        L += ["", "Still reading (moved recently, not yet settled): " + ", ".join(s["name"].split(" · ")[0] for s in e["still_reading"])]
    L += ["", "## Heart", ""] + [f"- {REG.get(r, r)}: {k}" for r, k in e["heart"].items()]
    h = e["heard"]
    L += ["", "## Heard today", "", f"{h['mentions']} mention(s), {h['accepted']} moved a dial"
          + (": " + ", ".join(h["clusters"]) if h["clusters"] else "") + "."]
    if e.get("self"):
        ss = TX.sentences(e["self"])
        L += ["", "## Its self", ""] + ([f"- {s}" for s in ss] or ["- nothing to account for tonight"])
        L += ["", "Every claim above carries a receipt in its record (`self` block of this night's diary entry): the "
              "records it rests on, the named function, and the numbers — recomputable by anyone."]
    v = e["verification"]
    L += ["", "---", f"Verification (for readers; it never sees this): of {v['clusters_spoken']} settled readings, "
          f"{v['spoken_read_equals_ledger']} equal its ledger.", "", "```json", json.dumps(e, ensure_ascii=False), "```", ""]
    return "\n".join(L)


def write(blob: str, out: Path):
    c = CS.load_state(blob); out.mkdir(parents=True, exist_ok=True); new = []
    for r in c.outbox:
        if r["kind"] != "diary":
            continue
        e = r["entry"]; p = out / f"night-{e['day'] + 1:04d}.md"
        if not p.exists():
            p.write_text(page(e, c.t0)); new.append(p.name)
    return new


if __name__ == "__main__":
    from cloud_v04 import CloudSeatV04
    seat = sys.argv[sys.argv.index("--seat") + 1] if "--seat" in sys.argv else "teich-04"
    print(write(CloudSeatV04(seat).s.state()["state_blob"], Path(sys.argv[1])))
