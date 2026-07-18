"""Shared context for Teich's cloud body — mirror of birth_certify.shared_context.

The frozen convention: cfg/gcfg/scaler are rebuilt deterministically from the seeded
data pipeline on every run (identical to how every certification since Phase 0 ran).
Any platform that produces a different context is caught by verify_substrate.py.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
os.environ.setdefault("DM_THREADS", "8")
os.environ.setdefault("MPLBACKEND", "Agg")
sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import numpy as np                                  # noqa: E402
import torch                                        # noqa: E402

import core                                         # noqa: E402
import lab_common as lab                            # noqa: E402
from private_fiber_model import PrivateFiberSuspensionModel  # noqa: E402

K = 2
CKPT = HERE / "rad3_s1.pt"


def shared_context(tmp_dir: str | None = None):
    cfg = lab.lab_cfg(tmp_dir or str(HERE / "tmp"))
    core.set_seed(cfg.seed)
    rng = np.random.default_rng(cfg.seed)
    trajs = core.generate_trajectories(cfg, rng)
    tr, va, te = core.split_by_trajectory(trajs, cfg)
    scaler = core.Standardizer().fit(tr)
    te_n = scaler.transform(te)
    true_spec = core.true_lorenz_lyapunov(cfg, n_steps=8000, warmup=1000)
    gcfg = core.GrowthConfig(
        lyap_target=float(true_spec[0]),
        n_fiber=1, fiber_anchor_rate=0.02, contraction_bias=6.0,
        decoder_hidden=128, decoder_layers=3, fiber_scale=0.03,
    )
    return cfg, gcfg, te_n


def load_model(cfg, gcfg, path: Path | None = None) -> PrivateFiberSuspensionModel:
    model = PrivateFiberSuspensionModel(cfg, gcfg, k_private=K)
    missing, unexpected = model.load_state_dict(
        torch.load(path or CKPT, map_location="cpu")["model_state"], strict=False)
    assert not unexpected, f"unexpected keys: {unexpected}"
    assert set(missing) == {"priv_omega", "priv_eps"}, f"missing keys: {missing}"
    model.eval()
    return model
