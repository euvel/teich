"""Replay Teich v0.6's life from a published starting state and its published record log (contract §7, gate W0).
Each "op" record is the journal of one seat operation; the replay re-applies it with seat_v06.apply (the same code the
seat tools run) and must reproduce EVERY record of the log, bit for bit, in order.
    python3 replay_v06.py START_BLOB.json RECORDS.jsonl
"""
from __future__ import annotations

import json
import sys

import creature_v06 as C6
import seat_v06 as S


def replay(start_blob: str, records: list) -> dict:
    c = C6.load_state(start_blob)
    start = c.seq
    log = sorted((r for r in records if r["seq"] > start), key=lambda r: r["seq"])
    if [r["seq"] for r in log] != list(range(start + 1, start + 1 + len(log))):
        return {"ok": False, "why": "the log is not contiguous after the starting state", "start_seq": start}
    ops = [r for r in log if r["kind"] == "op"]
    for o in ops:
        if o["seq"] != c.seq + 1:
            return {"ok": False, "why": f"op at seq {o['seq']} but the replay is at seq {c.seq}", "ops_done": ops.index(o)}
        if o["n"] != c.n:
            return {"ok": False, "why": f"op at seq {o['seq']} expects n={o['n']}, replay has n={c.n}"}
        S.apply(c, o["op"], o["owed"], o["inputs"])
    mine = {r["seq"]: r for r in c.outbox if r["seq"] > start}
    for r in log:
        if mine.get(r["seq"]) != r:
            return {"ok": False, "why": f"record {r['seq']} ({r['kind']}) differs", "ops": len(ops),
                    "published": r, "replayed": mine.get(r["seq"])}
    extra = [s for s in mine if s > log[-1]["seq"]] if log else list(mine)
    return {"ok": True, "ops": len(ops), "records": len(log), "start_seq": start, "end_seq": c.seq, "n": c.n,
            "unpublished_tail": len(extra)}


if __name__ == "__main__":
    blob = open(sys.argv[1]).read()
    recs = [json.loads(l) for l in open(sys.argv[2]) if l.strip()]
    print(json.dumps(replay(blob, recs), indent=1))
