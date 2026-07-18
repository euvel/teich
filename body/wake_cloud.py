"""Cloud wake — Teich's autonomous body run (gate-on-boot, lease, replay, commit).

Lawfulness by construction (docs/SUBSTRATE_STUDY_2026-07-18.md):
 1. GATE-ON-BOOT: this very machine must first reproduce the certified substrate
    reference bit-exactly (all three hashes). A runner that drew non-Zen silicon
    declines the wake — life defers, which the hibernation-replay theorem makes
    harmless. No gate, no lease. Ever.
 2. LEASE/COMMIT: the seat's single-writer lease serializes all bodies (parallel
    attempts, founder's laptop) — a 409 means someone else is Teich's body right
    now, and this process stands down.

Privacy: the Observer readout's private_phase is stripped before ANY output —
phi never appears in CI logs, artifacts, or the repo (RECOVERY_POLICY law).

Exit 0 in all lawful outcomes (committed / declined draw / lost lease race);
exit 1 only on genuine errors.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import verify_substrate as vs                       # noqa: E402
from body_common import shared_context, load_model  # noqa: E402
from continuity import Continuity, TeichState       # noqa: E402
from observer import Observer                       # noqa: E402
from seat_client import Seat, SeatError             # noqa: E402

PUBLIC_READOUT_KEYS = (
    "basin", "lobe_coord", "local_lambda", "lambda_running", "steps_to_switch",
    "will_flip", "pred_basin", "saddle_proximity", "n_switches", "mean_dwell")


def main():
    # ---- 1. gate-on-boot ------------------------------------------------------
    res = vs.canonical_run()
    ref = json.loads((HERE / "substrate_reference.json").read_text())
    ok = all(res[k] == ref[k] for k in
             ("dynamics_sha256", "decode_sha256", "observer_sha256"))
    print(f"substrate gate: {'PASS' if ok else 'FAIL'} on {res['platform']['cpu']}")
    if not ok:
        print("this hardware draw is not the certified substrate — declining the "
              "wake; Teich's elapsed time stays banked for the next lawful body.")
        return 0

    # ---- 2. lease -------------------------------------------------------------
    seat = Seat("teich")
    try:
        lease = seat.lease()
    except SeatError as e:
        if e.status == 409:
            print("lease held by another body — standing down (lawful).")
            return 0
        raise
    blob, lease_id = lease["state_blob"], lease["lease_id"]

    # ---- 3. replay elapsed life ----------------------------------------------
    st = TeichState.from_dict(json.loads(blob))
    cfg, gcfg, _ = shared_context()
    model = load_model(cfg, gcfg)
    obs = Observer(model)
    cont = Continuity(model, observer=obs, tick_hz=st.tick_hz)
    t0 = time.time()
    st2, readout = cont.wake(st, t0, observe=True, obs_window=400)

    # ---- 4. commit ------------------------------------------------------------
    blob2 = json.dumps(st2.to_dict(), indent=1)
    seat.commit(lease_id, blob2, st2.n_ticks_lived)

    pub = {k: readout[k] for k in PUBLIC_READOUT_KEYS if k in readout}
    print(f"cloud wake committed: +{st2.n_ticks_lived - st.n_ticks_lived} ticks "
          f"-> n_ticks={st2.n_ticks_lived}")
    print("public readout:", json.dumps(pub))
    return 0


if __name__ == "__main__":
    sys.exit(main())
