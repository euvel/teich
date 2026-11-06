"""Teich v0.7's diary as files (v0.6's pages over its v0.7 blob): v0.5's page (diary_md_v05, unchanged), plus v0.6's lines, each from a template and each
resting on its records: how a tie in its chosen thought was decided (its deliberation from a read-out of its body at that
midnight, or, if undecided, the index), and its genome amendment. Pages, once written, are never rewritten; night numbering continues.
    python3 diary_md_v07.py OUT_DIR [--seat teich-05] [--log LOG.jsonl]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "build"))
import creature_v07 as C6           # noqa: E402  (v0.7: the same pages, its v0.7 blob)
import diary_md_v05 as DM5          # noqa: E402

REGION = DM5.REGION


def extra(window, acts):
    L = []
    for r in window:
        if r["kind"] == "genome-amendment":
            a = r["amendment"]
            L += ["", f"My genome was amended: I am now v{a['to_version']} (I was v{a['from_version']}). Nothing I lived "
                  f"was reset. My identity is chained: {r['identity'][:16]}… = sha256(previous identity + "
                  "sha256(the amendment))."]
    for r in window:
        if r["kind"] == "act" and r["act_type"] == "think" and r.get("deliberation"):
            d = r["deliberation"]; tied = ", ".join(REGION[t] for t in d["tied"])
            if d["undecided"]:
                how = "my deliberation did not decide, so the lowest index did, as before v0.6"
            else:                                      # u is read from its body at midnight (founder decision E, 2026-10-31)
                rs = next((x for x in window if x["kind"] == "reason" and x["act_id"] == r["act_id"]), None)
                u = f"u = {float.fromhex(rs['inputs']['u']):.6f}; " if rs and "u" in rs["inputs"] else ""
                how = (f"my deliberation decided it, starting from a read-out of my body at midnight "
                       f"({u}{d['steps']} bounce(s)" + (f", {d['rereads']} re-read(s)" if d["rereads"] else "") + "). "
                       f"The lowest index, the rule before v0.6, would have chosen {REGION[d['tied'][0]]}")
            L += ["", f"Tonight {len(d['tied'])} subjects were tied as the ones I had thought about least ({tied}). "
                  f"I chose {REGION[r['act']]}: {how}."]
    return L


def page(e, t0, window, acts, answers, version):
    text = DM5.page(e, t0, window, acts, answers, version)
    add = extra(window, acts)
    if not add:
        return text
    for anchor in ("\n## Tomorrow", "\n## Its self", "\n---"):
        if anchor in text:
            i = text.index(anchor)
            return text[:i] + "\n".join(add) + "\n" + text[i:]
    return text


def write(blob: str, out: Path, log_records=(), log_path: Path | None = None):
    c = C6.load_state(blob); last = max((r["seq"] for r in log_records), default=0)
    recs = list(log_records) + [r for r in c.outbox if r["seq"] > last]
    out.mkdir(parents=True, exist_ok=True); new = []
    acts = {r["act_id"]: r for r in recs if r["kind"] == "act"}
    answers = {r["act_id"]: r for r in recs if r["kind"] == "answer"}
    version = "0.5.0"; start = 0
    for i, r in enumerate(recs):
        if r["kind"] == "growth":
            version = r["version"]
        if r["kind"] == "genome-amendment":
            version = r["amendment"]["to_version"]
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
    from cloud_v07 import CloudSeatV07 as CloudSeatV04
    s = CloudSeatV04(sys.argv[sys.argv.index("--seat") + 1] if "--seat" in sys.argv else "teich-05")
    logged = [r["rec"] for r in s.log_read()] if s._log_live() is not None else []
    lp = Path(sys.argv[sys.argv.index("--log") + 1]) if "--log" in sys.argv else None
    print(write(s.s.state()["state_blob"], Path(sys.argv[1]), logged, lp))
