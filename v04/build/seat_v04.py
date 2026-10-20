"""v0.4 seat, wake, gate and conversation path (BUILD candidate, lab only).

The wake keeps v0.3's law:
  1. GATE FIRST, every wake: this machine must reproduce the gate fixture's life bit for bit and hold the frozen genome.
  2. ONE WRITER: the seat's lease serializes every body; a lost lease race is lawful.
  3. REPLAY, DON'T SKIP: the creature lives every elapsed second at 1 Hz; owed ticks beyond --max-ticks stay banked.
The conversation path is the same plus `hear`: advance to now, apply the Ears' mentions under the laws, commit.

LocalSeat is a file-backed stand-in for the Durable Object (calls: peek / genesis_import / lease / commit / log).
The creature's closed records (every heard mention, every commitment, every diary entry) leave the blob through an
outbox: after a commit the caller appends records newer than the log's last sequence number; on the next load the
creature drops what the log already holds. A failed append is retried on the next wake, never duplicated.
Nothing in this file talks to the network; a real seat /o/teich-04 is created only at birth, and the log's home
(diary/ and biography files in the repo, founder decision 10-04) is wired then.
"""
from __future__ import annotations

import hashlib
import json
import platform
import time
import uuid
from pathlib import Path

import numpy as np

import creature_v04 as CR
import genome_v04 as GN

HERE = Path(__file__).resolve().parent
MAX_TICKS_DEFAULT = 200_000
GATE_TICKS = 2_000
GATE_MOVES = {500: 3, 1000: 97, 1500: 3}          # tick -> handle moved +1 during the gate life


class SeatError(RuntimeError):
    def __init__(self, status, msg):
        super().__init__(f"{status}: {msg}"); self.status = status


class LocalSeat:
    def __init__(self, path: Path):
        self.path = Path(path)

    def _rd(self):
        return json.loads(self.path.read_text()) if self.path.exists() else {}

    def _wr(self, d):
        tmp = self.path.with_suffix(".tmp"); tmp.write_text(json.dumps(d)); tmp.replace(self.path)

    def peek(self):
        d = self._rd()
        return {"alive": "blob" in d, "n_ticks": d.get("n_ticks"), "snapshots": len(d.get("chain", []))}

    def genesis_import(self, state_blob, n_ticks, genesis_anchor):
        d = self._rd()
        if "blob" in d:
            raise SeatError(409, "seat already holds a creature — never reset")
        self._wr({"blob": state_blob, "n_ticks": n_ticks, "lease": None, "anchor": genesis_anchor,
                  "chain": [CR.blob_sha256(state_blob)], "log": []})

    def lease(self):
        d = self._rd()
        if d.get("lease"):
            raise SeatError(409, "lease held")
        d["lease"] = uuid.uuid4().hex; self._wr(d)
        return {"lease_id": d["lease"], "state_blob": d["blob"], "n_ticks": d["n_ticks"]}

    def release(self, lease_id):
        d = self._rd()
        if d.get("lease") == lease_id:
            d["lease"] = None; self._wr(d)

    def commit(self, lease_id, state_blob, n_ticks):
        d = self._rd()
        if d.get("lease") != lease_id:
            raise SeatError(409, "lease lost")
        if n_ticks < d["n_ticks"]:
            raise SeatError(400, "time does not run backwards")
        d.update(blob=state_blob, n_ticks=n_ticks, lease=None)
        d["chain"].append(hashlib.sha256((d["chain"][-1] + CR.blob_sha256(state_blob)).encode()).hexdigest())
        self._wr(d)

    def log_seq(self):
        log = self._rd().get("log", [])
        return log[-1]["seq"] if log else 0

    def append_log(self, records):
        d = self._rd(); last = d["log"][-1]["seq"] if d["log"] else 0
        new = [r for r in records if r["seq"] > last]
        if [r["seq"] for r in new] != list(range(last + 1, last + 1 + len(new))):
            raise SeatError(400, "log records out of sequence")
        d["log"].extend(new); self._wr(d)


def _flush(seat, c):
    seat.append_log(c.outbox)


# ---------------------------------------------------------------------- substrate gate
def _gate_life(blob):
    c = CR.load_state(blob)
    t = 0
    for at, j in sorted(GATE_MOVES.items()):
        c.advance(at - t); t = at
        c.body.set_dial(j, int(c.body.n[j]) + 1)
    c.advance(GATE_TICKS - t)
    return hashlib.sha256(c.P.tobytes() + c.V.tobytes() + c.pc.tobytes() + c.win_counts.tobytes()).hexdigest()


def gate_record():
    blob = CR.dump_state(CR.birth(seed=4040, t0=0.0))
    (HERE / "gate_fixture_v04.json").write_text(blob)
    sha = _gate_life(blob)
    (HERE / "gate_v04.json").write_text(json.dumps({"fixture_sha256": CR.blob_sha256(blob), "life_sha256": sha,
                                                    "table_sha256": GN.TABLE_SHA, "vocab_sha256": GN.VOCAB_SHA,
                                                    "recorded_on": platform.processor() or platform.machine()},
                                                   indent=1))
    return sha


def gate():
    """The table and vocabulary are checked when the genome loads; here the machine must relive the fixture exactly."""
    info = {"cpu": platform.processor() or platform.machine(), "numpy": np.__version__}
    ref = json.loads((HERE / "gate_v04.json").read_text())
    blob = (HERE / "gate_fixture_v04.json").read_text()
    if CR.blob_sha256(blob) != ref["fixture_sha256"] or ref["table_sha256"] != GN.TABLE_SHA:
        return False, {**info, "why": "fixture or genome changed"}
    got = _gate_life(blob)
    return got == ref["life_sha256"], {**info, "life_sha256": got}


# ---------------------------------------------------------------------- wake and conversation
def _owed(c, now, max_ticks):
    total = int(now - c.t0) - c.n
    return max(0, min(total, max_ticks)), total


def wake(seat: LocalSeat, now: float | None = None, max_ticks=MAX_TICKS_DEFAULT, run_gate=True, log=print):
    if run_gate:
        ok, info = gate()
        log(f"substrate gate: {'PASS' if ok else 'FAIL'} on {info['cpu']}")
        if not ok:
            log("not the certified substrate — declining; elapsed time stays banked.")
            return "declined"
    if not seat.peek()["alive"]:
        log("seat not initialized — nothing to wake."); return "empty"
    try:
        lease = seat.lease()
    except SeatError as e:
        if e.status == 409:
            log("lease held by another body — standing down (lawful)."); return "stood-down"
        raise
    try:
        c = CR.load_state(lease["state_blob"])
        if c.n != lease["n_ticks"]:
            raise ValueError(f"blob tick {c.n} != seat n_ticks {lease['n_ticks']}")
        c.ack(seat.log_seq())
    except Exception:
        seat.release(lease["lease_id"]); raise
    owed, total = _owed(c, time.time() if now is None else now, max_ticks)
    entries = c.advance(owed)
    seat.commit(lease["lease_id"], CR.dump_state(c), c.n)
    _flush(seat, c)
    log(f"lived {owed:,} ticks ({total - owed:,} banked) -> n={c.n:,}; diary +{len(entries)}")
    return "woke"


def converse(seat: LocalSeat, mentions, conversation: str, speaker: str, now: float | None = None,
             max_ticks=MAX_TICKS_DEFAULT):
    """mentions: [(cluster, sign, text_sha256)] from the Ears. The creature first lives up to now (it cannot hear in
    the past), then hears each mention under the laws."""
    lease = seat.lease()
    try:
        c = CR.load_state(lease["state_blob"])
        c.ack(seat.log_seq())
        owed, total = _owed(c, time.time() if now is None else now, max_ticks)
        entries = c.advance(owed)
        if owed < total:
            raise RuntimeError("too much life owed to converse now — wake first")
        out = [c.hear(j, s, {"speaker": speaker, "conversation": conversation, "text_sha256": h})
               for j, s, h in mentions]
    except Exception:
        seat.release(lease["lease_id"]); raise
    seat.commit(lease["lease_id"], CR.dump_state(c), c.n)
    _flush(seat, c)
    return out


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--record-gate"]:
        print("gate life sha256:", gate_record())
    else:
        ok, info = gate(); print("PASS" if ok else "FAIL", info)
