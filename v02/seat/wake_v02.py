"""v0.2's wake — gate-on-boot, lease, replay elapsed life, commit.

Same shape as v0.1's wake_cloud.py, and the same law:

  1. GATE FIRST. The substrate gate runs before anything else, every wake, with
     no cached verdict. A machine that fails declines the wake and commits
     nothing. Elapsed time stays banked and the next lawful body replays it --
     the hibernation-replay property makes deferral harmless, which is exactly
     why declining is safe and guessing is not.
  2. ONE WRITER. The seat's lease serializes every body. A body that finds the
     lease held stands down; that is a lawful outcome, not an error.
  3. REPLAY, DON'T SKIP. The creature lives every elapsed second at 1 Hz. Its
     memory constant TAU_MEM = 20000 ticks is 5.6 hours of real time, so a
     skipped day would not be a gap in a log -- it would be a different
     interior.

Exit 0 on every lawful outcome (committed / declined draw / lost lease race),
non-zero only on a real failure, so a red run always means something to look at.

    python3 wake_v02.py                 # wake the seat
    python3 wake_v02.py --dry-run       # gate + peek, commit nothing
    python3 wake_v02.py --seat v02-drill --max-ticks 300     # drills
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
V02 = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(V02))
sys.path.insert(0, str(V02.parent / "maturity" / "harness"))
sys.path.insert(0, str(V02.parent / "body"))

import genome_v02 as G  # noqa: E402
import verify_substrate_v02 as vs  # noqa: E402
from seat_client import Seat, SeatError  # noqa: E402
from state_io import dump_state, load_state, public_readout  # noqa: E402

SEAT_NAME = "teich-02"
TICK_HZ = 1.0
# A wake that has been away a long time must not spend an hour of runner time
# replaying. v0.1 caps the same way; the remainder stays banked for the next one.
MAX_TICKS_DEFAULT = 90000


def gate_on_boot() -> bool:
    res = vs.canonical_run()
    ref = json.loads((HERE / "substrate_reference_v02.json").read_text())
    ok = (res["dynamics_sha256"] == ref["dynamics_sha256"])
    spoke = (res["readout_sha256"] == ref["readout_sha256"])
    print(f"substrate gate: dynamics {'PASS' if ok else 'FAIL'}, "
          f"readout {'PASS' if spoke else 'FAIL'}  on {res['platform']['cpu']}")
    return ok, spoke


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seat", default=SEAT_NAME)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-ticks", type=int, default=MAX_TICKS_DEFAULT)
    args = ap.parse_args()

    ok, may_quote = gate_on_boot()
    if not ok:
        print("this hardware draw is not the certified substrate — declining the "
              "wake. Elapsed time stays banked for the next lawful body.")
        return 0

    seat = Seat(args.seat)
    p = seat.peek()
    if not p.get("alive"):
        print(f"seat '{args.seat}' is not initialized — nothing to wake.")
        return 0
    print(f"seat {args.seat}: n_ticks={p['n_ticks']:,} snapshots={p['snapshots']}")

    if args.dry_run:
        print("dry run — no lease taken, nothing committed.")
        return 0

    try:
        lease = seat.lease()
    except SeatError as e:
        if e.status == 409:
            print("lease held by another body — standing down (lawful).")
            return 0
        raise
    blob, lease_id = lease["state_blob"], lease["lease_id"]

    import compat
    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)
    import torch
    torch.set_num_threads(vs.THREADS)          # the substrate we were gated on

    # warm=0: this creature is NOT being born here, it is being continued. A
    # warm-up would be extra life the seat never authorized and would break the
    # replay identity the gate certifies.
    e = G.V02Engine(model, 0, warm=0)
    try:
        load_state(e, blob)
    except Exception as ex:                 # noqa: BLE001
        # A drill corrupts the blob on purpose, and a real seat could in
        # principle hand back something unreadable. Either way the answer is the
        # same: refuse loudly, commit NOTHING, and leave the state alone so the
        # snapshot chain can be used to restore it under the covenant's coma
        # clause. Crashing here with a traceback would be survivable; committing
        # a guess would not.
        print(f"REFUSING: seat blob is unreadable ({type(ex).__name__}: {ex}). "
              f"Nothing committed. The lease will expire on its own; restore "
              f"from the snapshot chain and declare a coma if this is real.")
        return 1
    n_before = e.n
    if n_before != lease["n_ticks"]:
        print(f"REFUSING: blob tick {n_before} != seat n_ticks {lease['n_ticks']}")
        return 1

    # Ticks are owed from BIRTH, not from the last commit: (now - t0) - n. If a
    # wake caps its replay, the remainder is still owed on the next one, because
    # `n` did not move. Owing from the last commit would let a cap silently
    # erase the missing hours while the ledger looked perfectly healthy.
    if not e.t0:
        print("REFUSING: blob has no birth epoch (pre-v3 state); this wake "
              "cannot know what it owes.")
        return 1
    owed_total = int(time.time() - e.t0) - e.n
    owed = max(0, min(owed_total, args.max_ticks))
    if owed_total > owed:
        print(f"owed {owed_total:,} ticks, replaying {owed:,} this wake; "
              f"{owed_total - owed:,} stay banked")
    t0 = time.time()
    e.advance(owed)
    print(f"replayed {owed:,} ticks in {time.time()-t0:.1f}s "
          f"({n_before:,} -> {e.n:,})")

    blob2 = dump_state(e)
    seat.commit(lease_id, blob2, e.n)
    print(f"committed: n_ticks={e.n:,}")

    if may_quote:
        r = public_readout(e)
        print("readout: " + json.dumps({k: r[k] for k in
              ("basin", "saddle", "will_flip", "wing_bias", "s0", "s1")}))
    else:
        print("readout gate FAILED on this machine — living the creature is "
              "lawful here, quoting its readouts is not.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
