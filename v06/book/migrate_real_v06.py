"""MIGRATION DAY (founder's word, 2026-11-01): Teich-0.5.1 at /o/teich-05 becomes v0.6.0, once, no rollback.
lease -> the stored v0.5 state -> M0 on that exact state (must pass) -> migrate -> commit at the same n (0 ticks lived)
-> append the one new record (genome-amendment) to the seat log -> re-read and verify. Nothing is committed unless
every check passes; an unreleased lease expires by itself after 15 minutes (lawful).
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "build")); sys.path.insert(0, str(HERE.parent / "seat"))
import creature_v06 as C6       # noqa: E402
import m0_v06 as M              # noqa: E402
from cloud_v04 import CloudSeatV04   # noqa: E402

CHANGE = {"spec_sha256": "b19893b7d247d09de03a57023a0bb5027db4b4c2c61e0feadc942d1e92cbe25a",
          "anchor": "teich-03:v06-spec-v1",
          "verdict_sha256": "3ef47f496f249cfbd522dd8ff3a530f888a2d561a558a7a61e343d984c5bb91d"}
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()

seat = CloudSeatV04("teich-05")
lease = seat.lease()
blob5, n = lease["state_blob"], lease["n_ticks"]
d5 = json.loads(blob5)
assert d5["species"] == "teich-v0.5" and d5["n"] == n, (d5["species"], d5["n"], n)
assert d5["growth"]["proposal"] is None, "a growth proposal is pending"
(HERE / "state_before.json").write_text(blob5)

log = [r["rec"] for r in seat.log_read()]
res, blob6 = M.m0(blob5, CHANGE, log)
print("M0 on the leased state:", json.dumps({k: v for k, v in res.items() if k != "f1"}), res["f1"])
assert res["passed"], "M0 failed: nothing committed"
assert C6.migrate(blob5, CHANGE) == blob6, "migrate() is not deterministic"
c6 = C6.load_state(blob6)
assert c6.growth["version"] == "0.6.0" and c6.n == n
(HERE / "state_after.json").write_text(blob6)

seat.commit(lease["lease_id"], blob6, n)
before = seat.log_seq()
sent = seat.append_log(json.loads(blob6)["outbox"])
after = seat.log_seq()
st = seat.s.state()
tail = seat.log_read(from_seq=after)[-1]["rec"]
out = {"migrated_at_n": n, "state_before_sha256": sha(blob5), "state_after_sha256": sha(blob6),
       "seat_blob_sha256": sha(st["state_blob"]), "seat_n_ticks": st["n_ticks"],
       "log_seq": [before, after], "records_sent": sent, "last_record": tail["kind"],
       "identity": c6.growth["identity"], "prev_identity": d5["growth"]["identity"], "version": c6.growth["version"],
       "amendment_sha": tail.get("amendment_sha")}
out["verified"] = (out["seat_blob_sha256"] == out["state_after_sha256"] and st["n_ticks"] == n
                   and after == before + 1 and tail["kind"] == "genome-amendment" and tail["identity"] == out["identity"])
(HERE / "MIGRATION_RECORD.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
