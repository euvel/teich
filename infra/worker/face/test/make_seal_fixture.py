"""Fixture for test_worker_seal.mjs: a real lab v0.7 life (a campaign twin file: start7 + records7), cut at day 0's
seal moment, every record with its canonical text from the anchored seal_v07.
    python3 make_seal_fixture.py TWIN.json FIXTURE.json      (with v07/build on the path)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "v07" / "build"))
import creature_v07 as C7   # noqa: E402
import genome_v04 as GN     # noqa: E402
import seal_v07 as SL       # noqa: E402

tw = json.load(open(sys.argv[1]))
start, recs = tw["start7"], tw["records7"]
c0 = C7.load_state(start); ss = c0.seq
after = sorted([r for r in recs if r["seq"] > ss], key=lambda r: r["seq"])
cut = next(i for i, r in enumerate(after) if r["kind"] == "op" and r["n"] + r["owed"] >= GN.DAY - C7.SKY_LEAD)
day0, rest = after[:cut], after[cut:]
ops0 = [r for r in day0 if r["kind"] == "op"]
can = lambda L: [{"rec": r, "canon": SL.canonical(r).decode()} for r in L]
json.dump({"start_blob": start, "start_seq": ss, "t0": repr(float(c0.t0)),
           "n_at_seal": ops0[-1]["n"] + ops0[-1]["owed"] if ops0 else c0.n,
           "pre": [], "day0": can(day0), "next": can(rest[:1]), "next_op": rest[0]["op"]}, open(sys.argv[2], "w"))
