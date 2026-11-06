"""The other half of test_worker_seal.mjs: the seal the WORKER signed (JavaScript) must verify under the ANCHORED
Python seal_v07: signature, head, t0, a canonical log, quiet; fraud silent on the honest journal, firing on a
backdated op and on a rewritten record.
    python3 verify_seal_fixture.py FIXTURE.json OUT.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "v07" / "build"))
import creature_v07 as C7   # noqa: E402
import genome_v04 as GN     # noqa: E402
import seal_v07 as SL       # noqa: E402

fx, o = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
signed = {"seal": json.loads(o["seal"]["canon"]), "sig": o["seal"]["sig"], "pub": o["seal"]["pub"]}
recs = [json.loads(r) for r in o["log_raw"]]
r = {"canon_roundtrips": SL.canonical(signed["seal"]).decode() == o["seal"]["canon"],
     "sig_ok_anchored": SL.sig_ok(signed, o["pub"]),
     "head_matches_anchored": SL.head(fx["start_blob"], recs, signed["seal"]["seq"]) == signed["seal"]["head"],
     "t0_matches_birth": signed["seal"]["t0"] == C7.load_state(fx["start_blob"]).t0,
     "log_is_canonical": all(SL.canonical(x).decode() == raw for x, raw in zip(recs, o["log_raw"]))}
ops = [x for x in recs if x["kind"] == "op" and x["seq"] > signed["seal"]["seq"]]
r["quiet_holds"] = all(x["op"] == "wake" or x["n"] + x["owed"] >= GN.DAY for x in ops)
r["fraud_silent_on_honest"] = SL.fraud(signed, None, fx["start_blob"], recs) is None
forged = dict(recs[-1], op="present", owed=100, seq=recs[-1]["seq"] + 1)
r["fraud_fires_on_backdate"] = SL.fraud(signed, None, fx["start_blob"], recs + [forged]) is not None
tampered = [dict(x) for x in recs]; tampered[3]["kind_x"] = 1
r["fraud_fires_on_rewrite"] = SL.fraud(signed, None, fx["start_blob"], tampered) is not None
print(json.dumps(r)); print("ALL OK" if all(r.values()) else "FAILURES")
