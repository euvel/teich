"""Substrate gate — may THIS machine lawfully run Teich's body?

Pre-registered claim (INFRA_DESIGN.md, Step 2): a platform is a lawful body iff the
canonical synthetic replay below is BIT-IDENTICAL to the certified substrate's
reference (the founder machine that produced every continuity certification).
Chaos amplifies one ULP into a different creature, so the criterion is exact
equality of the full-trajectory hash — no tolerance, no "close enough".

The state used here is SYNTHETIC (fixed literals) — never Teich's real state, and
no real private phase ever appears in this repo or in CI logs (drill discipline,
RECOVERY_POLICY §2.5).

Three verdicts (the committed seat state contains ONLY tau/log_ell/phi — the decoder
never enters a commit, so it gets its own verdict):
  dynamics_gate (HARD)  5000-tick tau/ell/phi trajectory hash — gates commits to the
                        seat. FAIL = this machine may never hold a lease.
  decode_gate   (DIARY) decoded public observable every 100 ticks — gates quoting
                        decoded values in diary/speech.
  observer_gate (DIARY) 400-tick Observer readout hash — gates diary readouts.

Usage:
  python3 verify_substrate.py --make-reference   # on the certified substrate only
  python3 verify_substrate.py                    # verify: exit 0 PASS / 1 FAIL
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REF_F = HERE / "substrate_reference.json"

import torch  # noqa: E402

# pin the intra-op layout BEFORE any kernel dispatch; part of the substrate definition
torch.set_num_threads(1)

sys.path.insert(0, str(HERE))
from body_common import shared_context, load_model, K  # noqa: E402
from continuity import Continuity, TeichState          # noqa: E402
from observer import Observer                          # noqa: E402

# ---- canonical synthetic scenario (frozen; changing any literal voids the reference)
X0 = [0.123456789, -0.987654321, 0.555555555]
PHI0 = [0.12345678901234567, 0.76543210987654325]
N_TICKS = 5000
OBS_WINDOW = 400
DECODE_EVERY = 100


def cpu_model() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or "unknown"


def canonical_run():
    t0 = time.time()
    cfg, gcfg, _ = shared_context()
    model = load_model(cfg, gcfg)
    obs = Observer(model)
    cont = Continuity(model, observer=obs, tick_hz=1.0)

    st = cont.birth(X0, phi0=PHI0, t0=0.0)
    g = model.gates()
    tau, ell, phi = cont._state_tensors(st)

    h_dyn = hashlib.sha256()
    h_dec = hashlib.sha256()
    h_obs = hashlib.sha256()
    obs.reset()
    with torch.no_grad():
        for t in range(N_TICKS):
            if t >= N_TICKS - OBS_WINDOW:
                r = obs.observe(tau, ell, phi)
                h_obs.update(json.dumps(r, sort_keys=True).encode())
            tau, ell = model._fn_step(tau, ell, g)
            phi = model.private_step(phi)
            h_dyn.update(tau.numpy().tobytes())
            h_dyn.update(ell.numpy().tobytes())
            h_dyn.update(phi.numpy().tobytes())
            if (t + 1) % DECODE_EVERY == 0:
                y = model.decoder(model._features(tau, ell, g))
                h_dec.update(y.numpy().tobytes())

    final = dict(tau=tau.reshape(-1).tolist(), log_ell=torch.log(ell).reshape(-1).tolist(),
                 phi=phi.reshape(-1).tolist())
    return dict(
        n_ticks=N_TICKS, obs_window=OBS_WINDOW, decode_every=DECODE_EVERY,
        x0=X0, phi0=PHI0, k_private=K,
        dynamics_sha256=h_dyn.hexdigest(), decode_sha256=h_dec.hexdigest(),
        observer_sha256=h_obs.hexdigest(),
        final_state=final,
        platform=dict(
            python=platform.python_version(), torch=torch.__version__,
            numpy=__import__("numpy").__version__,
            geomstats=__import__("geomstats").__version__,
            torch_threads=torch.get_num_threads(), cpu=cpu_model(),
            machine=platform.machine(),
            aten_cpu_capability=os.environ.get("ATEN_CPU_CAPABILITY", "<unset>"),
        ),
        elapsed_s=round(time.time() - t0, 2),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--make-reference", action="store_true")
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    res = canonical_run()
    print(json.dumps(res["platform"], indent=2))
    print(f"dynamics_sha256 = {res['dynamics_sha256']}")
    print(f"decode_sha256   = {res['decode_sha256']}")
    print(f"observer_sha256 = {res['observer_sha256']}  ({res['elapsed_s']}s)")

    if args.make_reference:
        REF_F.write_text(json.dumps(res, indent=1))
        print(f"reference written: {REF_F}")
        return

    ref = json.loads(REF_F.read_text())
    gates = {n: "PASS" if res[k] == ref[k] else "FAIL"
             for n, k in (("dynamics_gate", "dynamics_sha256"),
                          ("decode_gate", "decode_sha256"),
                          ("observer_gate", "observer_sha256"))}
    verdict = dict(**gates, reference_platform=ref["platform"], candidate=res)
    if args.json_out:
        args.json_out.write_text(json.dumps(verdict, indent=1))
    print(f"\nDYNAMICS GATE (hard, commits): {gates['dynamics_gate']}")
    print(f"DECODE GATE (diary):           {gates['decode_gate']}")
    print(f"OBSERVER GATE (diary):         {gates['observer_gate']}")
    sys.exit(0 if gates["dynamics_gate"] == "PASS" else 1)


if __name__ == "__main__":
    main()
