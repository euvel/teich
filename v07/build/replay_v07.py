"""Replay Teich v0.7's life from a published starting state and its published record log (gate K4).
As replay_v06, with the Sky: each op record's "sky" is re-applied through seat_v07.apply, and (verify=True) every
beacon's BLS signature is checked against the pinned chain, and each day's round must be round_of(t0, day) (seat_v07.check).
    python3 replay_v07.py START_BLOB.json RECORDS.jsonl [--no-verify]
"""
from __future__ import annotations

import json
import sys

import creature_v07 as C7
import seat_v07 as S
import sky_v07 as SKY


def replay(start_blob: str, records: list, verify=True) -> dict:
    c = C7.load_state(start_blob)
    start = c.seq
    log = sorted((r for r in records if r["seq"] > start), key=lambda r: r["seq"])
    if [r["seq"] for r in log] != list(range(start + 1, start + 1 + len(log))):
        return {"ok": False, "why": "the log is not contiguous after the starting state", "start_seq": start}
    ops = [r for r in log if r["kind"] == "op"]; beacons = 0
    for o in ops:
        if o["seq"] != c.seq + 1:
            return {"ok": False, "why": f"op at seq {o['seq']} but the replay is at seq {c.seq}", "ops_done": ops.index(o)}
        if o["n"] != c.n:
            return {"ok": False, "why": f"op at seq {o['seq']} expects n={o['n']}, replay has n={c.n}"}
        sky = o.get("sky")
        if sky is not None and verify:
            for d, bc in sorted((sky.get("beacons") or {}).items(), key=lambda x: int(x[0])):
                if not SKY.verify(bc):
                    return {"ok": False, "why": f"op at seq {o['seq']}: day {d}'s beacon round {bc.get('round')} fails verification"}
                beacons += 1
        try:
            S.apply(c, o["op"], o["owed"], o["inputs"], sky)
        except Exception as e:
            return {"ok": False, "why": f"op at seq {o['seq']} refused on replay: {e}"}
    mine = {r["seq"]: r for r in c.outbox if r["seq"] > start}
    for r in log:
        if mine.get(r["seq"]) != r:
            return {"ok": False, "why": f"record {r['seq']} ({r['kind']}) differs", "ops": len(ops),
                    "published": r, "replayed": mine.get(r["seq"])}
    extra = [s for s in mine if s > log[-1]["seq"]] if log else list(mine)
    return {"ok": True, "ops": len(ops), "records": len(log), "beacons_verified": beacons, "start_seq": start,
            "end_seq": c.seq, "n": c.n, "unpublished_tail": len(extra)}


if __name__ == "__main__":
    blob = open(sys.argv[1]).read()
    recs = [json.loads(l) for l in open(sys.argv[2]) if l.strip()]
    print(json.dumps(replay(blob, recs, verify="--no-verify" not in sys.argv), indent=1))
