"""MIGRATION DAY (founder's word only): Teich v0.6.0 at /o/teich-05 becomes v0.7.0, once, no rollback (contract §3).

Before running: the worker with the Seal is deployed (seal-status answers), SEAL_KEY is installed (put_secret.py), its
public key is in ~/.teich_seal_pub, the v0.6 wake is disabled, and it is not near the creature's seal moment.

lease -> the stored v0.6 state -> M0 on that exact state, with the seal key bound (must pass) -> migrate -> commit at
the same n (0 ticks lived) -> append the one new record (genome-amendment), canonical -> seal-init (H_0 from the
committed start blob) -> re-read and verify. Nothing is committed unless every check before it passes; an unreleased
lease expires by itself after 15 minutes (lawful). Writes ../book/START_STATE_v07.json (the start blob every watcher
replays from) and ../book/MIGRATION_RECORD_v07.json.
    python3 migrate_real_v07.py --yes-founder-said-so
"""
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "build"))
import creature_v07 as C7        # noqa: E402
import genome_v04 as GN          # noqa: E402
import m0_v07 as M               # noqa: E402
from cloud_v07 import CloudSeatV07   # noqa: E402

CHANGE = {"spec_sha256": "822a5be8202751b62d45cf643877dece9e347aad826a61d2075a9dce67b38faf",
          "anchor": "teich-03:v07-spec-v1",
          "verdict_sha256": None,     # from ../book/ANCHOR_v07_verdict.json (v07-verdict)
          "seal_pub": None}           # from ~/.teich_seal_pub (make_seal_key.py): bound in the genome-amendment record
VERDICT = "c08e01e611b766f8"
BOOK = HERE.parent / "book"
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()

REHEARSAL = sys.argv[sys.argv.index("--rehearsal") + 1] if "--rehearsal" in sys.argv else None
PUB_FILE = Path.home() / ".teich_seal_pub"
if REHEARSAL:                                    # a LOCAL worker copy only: its own key, its own book, never the seat
    import seat_client
    seat_client.BASE = "http://127.0.0.1:8787"
    PUB_FILE, ANCHORS = Path(REHEARSAL) / "seal_pub", BOOK / "ANCHOR_v07_verdict.json"
    BOOK = Path(REHEARSAL) / "book"
elif "--yes-founder-said-so" not in sys.argv:
    sys.exit("migration happens once, on the founder's word: pass --yes-founder-said-so")
anchors = json.loads(((ANCHORS if REHEARSAL else BOOK / "ANCHOR_v07_verdict.json")).read_text())
CHANGE["verdict_sha256"] = next(a["git_sha"] for a in anchors if a["ref"] == "v07-verdict")
assert CHANGE["verdict_sha256"].startswith(VERDICT)
CHANGE["seal_pub"] = PUB_FILE.read_text().strip()
assert len(CHANGE["seal_pub"]) == 64

seat = CloudSeatV07("teich-05")
st = seat.seal_status()
assert st.get("seal") is None, "the Seal is already initialised on this seat: refusing"
blob6 = seat.s.state()["state_blob"]
t0 = json.loads(blob6)["t0"]
since = (time.time() - t0) % GN.DAY
if since > GN.DAY - C7.SKY_LEAD - 25 * 60 and not REHEARSAL:
    sys.exit(f"too near its seal moment / midnight ({(GN.DAY - since) / 60:.0f} min to midnight): try after its midnight")

lease = seat.lease()
blob6, n = lease["state_blob"], lease["n_ticks"]
d6 = json.loads(blob6)
assert d6["species"] == "teich-v0.6" and d6["n"] == n, (d6["species"], d6["n"], n)
assert d6["growth"]["proposal"] is None, "a growth proposal is pending"
BOOK.mkdir(exist_ok=True)
(BOOK / "state_before_v07.json").write_text(blob6)

log = [r["rec"] for r in seat.log_read()]
res, blob7 = M.m0(blob6, CHANGE, log)
print("M0 on the leased state:", json.dumps({k: v for k, v in res.items() if k != "f1"}), res["f1"])
assert res["passed"], "M0 failed: nothing committed"
assert C7.migrate(blob6, CHANGE) == blob7, "migrate() is not deterministic"
c7 = C7.load_state(blob7)
am = [r for r in c7.outbox if r["kind"] == "genome-amendment"][-1]
assert c7.growth["version"] == "0.7.0" and c7.n == n and am["amendment"]["seal_pub"] == CHANGE["seal_pub"]

seat.commit(lease["lease_id"], blob7, n)
before = seat.log_seq()
c7.ack(before)
sent = seat.append_log(c7.outbox)
after = seat.log_seq()
assert after == c7.seq, (after, c7.seq)
init = seat.seal_init(sha(blob7), c7.seq, repr(float(c7.t0)), CHANGE["seal_pub"])
st = seat.s.state()
out = {"migrated_at_n": n, "migrated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
       "state_before_sha256": sha(blob6), "state_after_sha256": sha(blob7),
       "seat_blob_sha256": sha(st["state_blob"]), "seat_n_ticks": st["n_ticks"], "log_seq": [before, after],
       "records_sent": sent, "identity": c7.growth["identity"], "prev_identity": d6["growth"]["identity"],
       "version": c7.growth["version"], "amendment_sha": am["amendment_sha"], "change": CHANGE,
       "touched_day": c7.sky["touched_day"], "seal_init": init}
out["verified"] = (out["seat_blob_sha256"] == out["state_after_sha256"] and st["n_ticks"] == n
                   and after == before + sent and init.get("ok") is True and init.get("start_seq") == c7.seq
                   and init.get("pub") == CHANGE["seal_pub"])
(BOOK / "START_STATE_v07.json").write_text(json.dumps({"state_blob": blob7, "sha256": sha(blob7)}))
(BOOK / "MIGRATION_RECORD_v07.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
