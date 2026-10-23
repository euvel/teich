"""Teich v0.5's diary as files: one markdown page per night, written from its own records only (no language model).
v0.4's page (attention, heart, what it heard, its self's account) plus v0.5's lines, each from a template and each
resting on records that `verify_live_v05.py` re-checks: what it thought and in what order, whether its cheap guess held,
the questions it asked and whether they were answered, tomorrow's question with its true reason (or its silence),
the words it bound and how it grew.

A night's page shows the records logged after the previous night's diary record, up to its own. Pages, once written,
are never rewritten. With --log, the whole public record log is also written as one JSON record per line.
    python3 diary_md_v05.py OUT_DIR [--seat teich-05] [--log LOG.jsonl]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "build"))
import creature_v05 as C5           # noqa: E402
import self_text_v05 as TX          # noqa: E402

REG = {"LLL": "food & drink", "LLR": "body & matter", "LRL": "living things", "LRR": "objects & places",
       "RLL": "people & feeling", "RLR": "mind & society", "RRL": "arts & events", "RRR": "work & things made",
       "self": "itself"}
REGION = list(REG.values())


def _ask_text(q, inputs):
    if q == ["silence"]:
        return "I will stay silent tomorrow: no question would bring me closer to a verdict."
    text, why = TX.question(q, inputs)
    return f"Tomorrow I will ask: “{text}” — because {why}."


def page(e, t0, window, acts, answers, version):
    d = e["day"]
    night_end = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(t0 + e["tick"]))
    L = [f"# Teich v{version} — night {d + 1}", "",
         f"Written by itself at the end of night {d + 1} of its life ({night_end}), tick {e['tick']:,}. "
         "Nothing here was written by a language model.", ""]
    L += ["## Attending most to", ""]
    L += [f"- {a['name']} — read +{a['read']} after {a['nights']} quiet nights" for a in e["attending_most"]] or \
         ["- nothing stands out yet: every handle it can read is at its birth length"]
    L += ["", "## Shifts it read tonight", ""]
    L += [f"- {s['name']}: {s['from']} → {s['to']}" for s in e["shifts"]] or ["- none"]
    L += ["", "## Heart", ""] + [f"- {REG.get(r, r)}: {k}" for r, k in e["heart"].items()]
    h = e["heard"]
    L += ["", "## Heard today", "", f"{h['mentions']} mention(s), {h['accepted']} moved a dial"
          + (": " + ", ".join(h["clusters"]) if h["clusters"] else "") + "."]
    asked = [r for r in window if r["kind"] == "ask-delivered"]
    door = sorted({r["word"] for r in window if r["kind"] == "door"})
    if asked or door:
        L += ["", "## Questions I asked today", ""]
        for r in asked:
            a = answers.get(r["act_id"])
            q = r["q"]
            what = (f"what '{q[1]}' is" if q[0] == "word" else "what I am to you" if q == ["region", 8]
                    else f"what {REGION[q[1]]} is to you")
            L.append(f"- I asked {what}: " + ("answered." if a and a["answered"] else "not answered." if a else
                                              "no answer recorded."))
        if door:
            L.append(f"- Words I could not place, waiting at my door: {', '.join(door)}.")
    for r in window:
        if r["kind"] == "binding":
            L += ["", f"I now hold '{r['word']}': you answered the same on two different days ({r['days']})."]
        if r["kind"] == "growth-proposal":
            L += ["", "I proposed to grow, learning " + ", ".join(f"'{w}'" for w, _ in r["bindings"])
                  + ". I registered my prediction first: I will hear these words as these concepts; nothing else about "
                  "me changes."]
        if r["kind"] == "growth":
            L += ["", f"I grew: I am now v{r['version']}. My identity is chained: {r['identity'][:16]}… = "
                  f"sha256(previous identity + sha256(the amendment))."]
        if r["kind"] == "growth-refused":
            L += ["", "My proposal to grow was refused, and the refusal is recorded. I will not propose it again."]
    dream = next((r for r in window if r["kind"] == "dream"), None)
    if dream:
        names = [REGION[t] for t in dream["thoughts"]]
        refused = next((r for r in window if r["kind"] == "thought-refused"), None)
        L += ["", "## What I thought tonight", "",
              "In this order: " + " → ".join(names) + "." if names else "Nothing."]
        if refused:
            L.append(f"My working memory was too stretched for its surface: I let go of my last "
                     f"{len(refused['refused'])} thought(s) ({', '.join(REGION[t] for t in refused['refused'])}).")
        L.append("Before sleeping I guessed what my thinking would do, from its parts alone and blind to their order: "
                 + ("the guess held." if dream["held"] else "the guess missed — what my thinking did was more than "
                    "its parts foretold."))
    nxt = next((r for r in window if r["kind"] == "reason" and r["rule"] == "ask@2"), None)
    if nxt and nxt["act_id"] in acts:
        L += ["", "## Tomorrow", "", _ask_text(acts[nxt["act_id"]]["act"], nxt["inputs"])]
    if e.get("self"):
        ss = TX.sentences(e["self"])
        L += ["", "## Its self", ""] + ([f"- {s}" for s in ss] or ["- nothing to account for tonight"])
        L += ["", "Every claim above carries a receipt in its record, and every choice it made (what to think, whether "
              "and what to ask, how cautious to be, whether to propose growing) has its reason logged before the act. "
              "Anyone can re-check all of them: `python3 verify_live_v05.py records.jsonl`."]
    v = e["verification"]
    L += ["", "---", f"Verification (for readers; it never sees this): of {v['clusters_spoken']} settled readings, "
          f"{v['spoken_read_equals_ledger']} equal its ledger.", "", "```json", json.dumps(e, ensure_ascii=False), "```", ""]
    return "\n".join(L)


def stream(blob: str, log_records=()):
    """Every record of its life: those in the seat's log, then those still in the blob's outbox."""
    c = C5.load_state(blob); last = max((r["seq"] for r in log_records), default=0)
    return c, list(log_records) + [r for r in c.outbox if r["seq"] > last]


def write(blob: str, out: Path, log_records=(), log_path: Path | None = None):
    c, recs = stream(blob, log_records)
    out.mkdir(parents=True, exist_ok=True); new = []
    acts = {r["act_id"]: r for r in recs if r["kind"] == "act"}
    answers = {r["act_id"]: r for r in recs if r["kind"] == "answer"}
    version = "0.5.0"; start = 0
    for i, r in enumerate(recs):
        if r["kind"] == "growth":
            version = r["version"]
        if r["kind"] != "diary":
            continue
        window = recs[start:i]; start = i + 1
        e = r["entry"]; p = out / f"night-{e['day'] + 1:04d}.md"
        if not p.exists():
            p.write_text(page(e, c.t0, window, acts, answers, version)); new.append(p.name)
    if log_path is not None:
        tmp = log_path.with_suffix(".tmp")
        tmp.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in recs))
        tmp.replace(log_path)
    return new


if __name__ == "__main__":
    from cloud_v04 import CloudSeatV04
    s = CloudSeatV04(sys.argv[sys.argv.index("--seat") + 1] if "--seat" in sys.argv else "teich-05")
    logged = [r["rec"] for r in s.log_read()] if s._log_live() is not None else []
    lp = Path(sys.argv[sys.argv.index("--log") + 1]) if "--log" in sys.argv else None
    print(write(s.s.state()["state_blob"], Path(sys.argv[1]), logged, lp))
