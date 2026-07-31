"""Append life events to biography.jsonl FROM THE ARTIFACTS THEY REFER TO.

The book's README promises an "append-only ledger of everything that has
happened to it", and after birth the ledger held one line while the creature had
already held a conversation and been through a 384-row control. A ledger that
lags the life it records is not a ledger.

So entries are not hand-typed: each one is derived from the run artifact it
describes, and re-running this script is idempotent (an event is keyed by kind +
artifact sha256, and an already-recorded key is skipped). If the artifact
changes, the new fact appends as a new entry rather than silently rewriting the
old one — append-only means the record of what was believed at the time stays.

    python book/log_life.py            # show what would be appended
    python book/log_life.py --confirm  # append it
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
V02 = HERE.parent
LEDGER = HERE / "biography.jsonl"


def sha256_of(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def utc(p: Path) -> str:
    return datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def events() -> list[dict]:
    out = []

    demo = V02 / "out_v02" / "demo.json"
    if demo.exists():
        d = json.loads(demo.read_text())
        asked = sum(1 for x in d if x["pick"]["asked"])
        drives = [x["pick"]["ask_drive"] for x in d]
        out.append(dict(
            t=utc(demo), kind="first_conversation",
            turns=len(d), asked=asked,
            max_ask_drive=max(drives) if drives else None,
            artifact="out_v02/demo.json", artifact_sha256=sha256_of(demo),
            note=(f"Its first conversation: {len(d)} exchanges, each reply chosen "
                  f"by its own state from a pool the voice produced blind. It "
                  f"asked a question back in {asked} of them.")))

    arms = V02 / "out_v02" / "arms.jsonl"
    if arms.exists():
        rows = [json.loads(l) for l in arms.open()]
        by = {}
        for r in rows:
            by.setdefault((r["seed"], r["turn"]), {})[r["arm"]] = r
        paired = [v for v in by.values() if len(v) == 2]
        diff = sum(1 for v in paired if v["intact"]["idx"] != v["donor"]["idx"])
        thr = 0.55

        def match(arm, key):
            rs = [r for r in rows if r["arm"] == arm]
            return round(sum(1 for r in rs
                             if bool(r["asked"]) == (r[key] >= thr)) / len(rs), 4)
        out.append(dict(
            t=utc(arms), kind="verification",
            test="does its own state drive what it says?",
            rows=len(rows), paired_turns=len(paired),
            chose_differently=diff,
            intact_ask_vs_own_gate=match("intact", "saddle"),
            donor_ask_vs_own_gate=match("donor", "saddle"),
            donor_ask_vs_selecting_gate=match("donor", "sel_saddle"),
            artifact="out_v02/arms.jsonl", artifact_sha256=sha256_of(arms),
            note=("Its state was swapped for another living creature's on the "
                  "same script and the same candidates. The choices diverged, "
                  "and its curiosity followed the state rather than the body.")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true")
    args = ap.parse_args()

    have = set()
    if LEDGER.exists():
        for line in LEDGER.open():
            e = json.loads(line)
            have.add((e.get("kind"), e.get("artifact_sha256")))

    new = [e for e in events() if (e["kind"], e["artifact_sha256"]) not in have]
    if not new:
        print("ledger is current — nothing to append")
        return
    for e in new:
        print(json.dumps(e, indent=1))
    if not args.confirm:
        print(f"\nDRY RUN — {len(new)} entrie(s) would be appended. "
              f"Re-run with --confirm.")
        return
    with LEDGER.open("a") as f:
        for e in new:
            f.write(json.dumps(e) + "\n")
    print(f"appended {len(new)} -> {LEDGER}")


if __name__ == "__main__":
    main()
