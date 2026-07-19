"""Calibrate the severed-arm conditioning sources from FREE-RUN Core statistics.

A1 (severed) uses the Core's long-run mean readout; A3 (lava lamp) uses the
Core's marginal readout statistics with dynamics destroyed; A2 (decoupled) uses
readout streams recorded from OTHER scripts' A0 runs. All are derived from fresh
synthetic instances — never Teich's real state. Deterministic; cached to JSON.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from arms import _CoreEngine  # noqa: E402

CACHE = HERE / "out_maturity" / "calibration.json"


def calibrate(model, n_ticks=8000, seed=7):
    e = _CoreEngine(model, seed, deaf=True)
    reads = []
    step = 60
    for _ in range(n_ticks // step):
        reads.append(e.advance(step))
    basins = np.array([r["basin"] for r in reads])
    sp = np.array([r["saddle_proximity"] for r in reads])
    lam = np.array([r["lambda_running"] for r in reads if r["lambda_running"] == r["lambda_running"]])
    sts = np.array([r["steps_to_switch"] for r in reads])
    nsw = np.array([r["n_switches"] for r in reads])
    flip = np.array([1.0 if r["will_flip"] else 0.0 for r in reads])

    mean_readout = dict(
        basin=int(np.sign(basins.mean()) or 1),
        saddle_proximity=float(sp.mean()),
        lambda_running=float(lam.mean()) if len(lam) else 0.0,
        steps_to_switch=int(sts.mean()),
        will_flip=bool(flip.mean() >= 0.5),
        n_switches=int(nsw.mean()))
    p_pos = float((basins == 1).mean())
    marginal = {
        "basin_p": [1 - p_pos, p_pos],
        "saddle": [float(sp.mean()), float(sp.std() + 1e-6)],
        "lambda": [float(lam.mean()) if len(lam) else 0.0,
                   float(lam.std() + 1e-6) if len(lam) else 0.1],
        "steps": [float(sts.mean()), float(sts.std() + 1e-6)],
        "nsw": [float(nsw.mean()), float(nsw.std() + 1e-6)],
        "flip_p": float(flip.mean())}
    return dict(mean_readout=mean_readout, marginal=marginal)


def load_or_build(model):
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    cal = calibrate(model)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cal, indent=1))
    return cal


if __name__ == "__main__":
    import compat
    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)
    cal = load_or_build(model)
    print(json.dumps(cal, indent=1))
