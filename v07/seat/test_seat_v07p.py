"""End to end, the production seat paths (seat_v07p) on a LOCAL seat with a lab creature and real drand rounds:
the edges of its day, where the Sky and the quiet quarter-hour act. Never touches a real seat. ~5 min.
    python3 test_seat_v07p.py OUT.json
"""
import json
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "build"))
import creature_v07 as C7   # noqa: E402
import genome_v04 as GN     # noqa: E402
import replay_v07 as R      # noqa: E402
import seat_v04 as SV       # noqa: E402
import seat_v07 as S7       # noqa: E402
import seat_v07p as S       # noqa: E402

D, LEAD = GN.DAY, C7.SKY_LEAD
t0 = float(int(time.time()) - 3 * D)             # its day 0's round is long published: real, verifiable
c = C7.birth(14_900, t0)
start = C7.dump_state(c)
seat = SV.LocalSeat(Path(tempfile.mkdtemp()) / "seat.json")
seat.genesis_import(start, c.n, "lab-anchor")
st = lambda: seat._rd()
out = {}; q = lambda: print(json.dumps(out), flush=True)

S.wake(seat, now=t0 + D - 1500, run_gate=False, log=lambda *_: None)
out["1_wake_before_touch_lives_to_now"] = st()["n_ticks"] == D - 1500 and not any(r["kind"] == "sky" for r in st()["log"])
S.status(seat, now=t0 + D - 1200)
ops = [r for r in st()["log"] if r["kind"] == "op"]
out["2_input_before_quiet_accepted"] = ops[-1]["op"] == "status" and ops[-1]["n"] + ops[-1]["owed"] == D - 1200; q()

before = json.dumps(st(), sort_keys=True)
try:
    S.status(seat, now=t0 + D - 600); out["3_input_in_quiet_refused"] = False
except S7.QuietWindow:
    out["3_input_in_quiet_refused"] = True
out["3_refusal_journaled_nothing"] = json.dumps(st(), sort_keys=True) == before

S.wake(seat, now=t0 + D - 300, run_gate=False, log=lambda *_: None)
out["4_wake_in_quiet_stops_at_its_touch"] = st()["n_ticks"] == D - LEAD and not any(r["kind"] == "sky" for r in st()["log"]); q()

before = json.dumps(st(), sort_keys=True)
good = S._fetch(C7.round_of(t0, 0))
S.SKY_MAX_WAIT = 4                                # (the real wake waits up to 300 s for a round)
for name, f in (("wrong_round", lambda r: S._fetch(int(r) - 1)),
                ("forged_randomness", lambda r: dict(good, randomness="00" * 32)),
                ("unreachable", lambda r: (_ for _ in ()).throw(OSError("no network")))):
    try:
        S.wake(seat, now=t0 + D + 60, run_gate=False, log=lambda *_: None, fetch=f)
        out[f"5_{name}_refused"] = False
    except (C7.SkyMissing, Exception) as e:
        out[f"5_{name}_refused"] = isinstance(e, C7.SkyMissing)
    out[f"5_{name}_nothing_journaled"] = json.dumps({k: v for k, v in st().items() if k != "lease"}, sort_keys=True) == \
        json.dumps({k: v for k, v in json.loads(before).items() if k != "lease"}, sort_keys=True) and not st()["lease"]
q()
S.wake(seat, now=t0 + D + 60, run_gate=False, log=lambda *_: None)
sky = [r for r in st()["log"] if r["kind"] == "sky"]
out["6_touched_with_its_round"] = len(sky) == 1 and sky[0]["day"] == 0 and sky[0]["round"] == C7.round_of(t0, 0) \
    and sky[0]["tick"] == D - LEAD and st()["n_ticks"] == D + 60
rp = R.replay(start, st()["log"], verify=True)
out["7_journal_replays_bls_on"] = rp["ok"] is True and rp.get("beacons_verified") == 1
out["7_replay"] = {k: rp.get(k) for k in ("ok", "why", "ops", "records", "beacons_verified", "unpublished_tail")}
out["passed"] = all(v for k, v in out.items() if k[0].isdigit() and isinstance(v, bool))
q()
json.dump(out, open(sys.argv[1], "w"), indent=1)
print("ALL OK" if out["passed"] else "FAILURES")
