"""Shared lab harness: config, data, butterfly-topology metrics, plots, reports.

The point of this lab is the *butterfly problem*: models that match Lorenz's invariant
STATISTICS (std_ratio, sliced-W, D_KY) but free-run as a space-filling tangle instead of
the two-lobe butterfly. So beyond the notebook's metrics we add topology-sensitive ones:

  * hole_fill   — fraction of free-run points inside the two attractor "holes" (balls
                  around the unstable fixed points C±). True Lorenz ≈ 0; a tangle fills them.
  * rm_thickness— return-map (z-maxima) graph thickness: within-bin std of z_{k+1}
                  normalized by total std. True Lorenz is a thin curve (≈0.0x); tangle ≈ O(1).
  * lobe stats  — number of lobe switches, mean dwell (steps), lobe balance. A tangle
                  switches sides constantly; collapsed dynamics never switch.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Dict, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

import core

# Device policy: local ROCm GPU is unsupported for torch compute, so default to CPU.
# On Kaggle (CUDA) set DM_USE_CUDA=1 before importing to train on the GPU.
if os.environ.get("DM_USE_CUDA") == "1" and torch.cuda.is_available():
    DEVICE = torch.device("cuda")
else:
    DEVICE = torch.device("cpu")
    torch.set_num_threads(int(os.environ.get("DM_THREADS", "14")))

# Output root. On Kaggle the module lives under a READ-ONLY input dataset, so the
# notebook sets DM_RUNS_DIR=/kaggle/working/runs before importing.
RUNS = Path(os.environ.get("DM_RUNS_DIR", str(Path(__file__).parent / "runs")))

_TRUE_REF: dict = {}


def true_reference(cfg: core.Config, n_steps: int = 8000) -> np.ndarray:
    """A long freshly-integrated on-attractor Lorenz trajectory (PHYSICAL coords)."""
    key = (n_steps, cfg.dt, cfg.sigma, cfg.rho, cfg.beta)
    if key not in _TRUE_REF:
        ic = np.array([1.0, 1.0, 1.0]) + np.random.default_rng(7).normal(0, 10.0, 3)
        _TRUE_REF[key] = core.integrate_lorenz(
            cfg.burn_in + n_steps, cfg.dt, ic, cfg.sigma, cfg.rho, cfg.beta)[cfg.burn_in:]
    return _TRUE_REF[key]


def lab_cfg(out_dir: str, **overrides) -> core.Config:
    """Mid-scale config: big enough to show the tangle/butterfly distinction, minutes on CPU."""
    base = dict(
        out_dir=out_dir,
        n_trajectories=12, traj_len=800, burn_in=400,
        horizon=15, stride=8,
        hidden_dim=64, n_layers=3,
        batch_size=256, max_epochs=60, patience=15,
    )
    base.update(overrides)
    return core.Config(**base)


def get_data(cfg: core.Config):
    core.set_seed(cfg.seed)
    return core.build_dataset(cfg)


# --------------------------------------------------------------------------------------
# Butterfly-topology metrics (all on PHYSICAL coordinates)
# --------------------------------------------------------------------------------------

def fixed_points(cfg: core.Config) -> np.ndarray:
    """The two unstable foci C± the lobes wind around (the attractor's 'holes')."""
    r = math.sqrt(cfg.beta * (cfg.rho - 1.0))
    return np.array([[r, r, cfg.rho - 1.0], [-r, -r, cfg.rho - 1.0]])


def hole_fill(phys: np.ndarray, cfg: core.Config, radius: float = 3.0) -> float:
    """Fraction of points within `radius` of either C±. True Lorenz ≈ 0; tangle > 0."""
    C = fixed_points(cfg)
    d = np.minimum(np.linalg.norm(phys - C[0], axis=1), np.linalg.norm(phys - C[1], axis=1))
    return float((d < radius).mean())


def return_map_thickness(phys: np.ndarray, nbins: int = 16) -> float:
    """Graph-thickness of the z-max return map (0 = perfect function, ~1 = unstructured)."""
    zm = core.z_maxima(phys)
    if len(zm) < 30:
        return float("nan")
    x, y = zm[:-1], zm[1:]
    edges = np.quantile(x, np.linspace(0.0, 1.0, nbins + 1))
    stds, ws = [], []
    for i in range(nbins):
        m = (x >= edges[i]) & (x <= edges[i + 1])
        if m.sum() >= 4:
            stds.append(y[m].std())
            ws.append(m.sum())
    if not stds:
        return float("nan")
    return float(np.average(stds, weights=ws) / (y.std() + 1e-12))


def lobe_stats(phys: np.ndarray) -> Dict[str, float]:
    s = np.sign(phys[:, 0])
    s[s == 0] = 1.0
    switches = np.where(np.diff(s) != 0)[0]
    dwell = np.diff(switches) if len(switches) > 1 else np.array([float(len(s))])
    return {
        "switches_per_1k": float(len(switches) / len(s) * 1000.0),
        "mean_dwell": float(dwell.mean()) if len(dwell) else float("nan"),
        "lobe_balance": float((s > 0).mean()),
    }


def butterfly_metrics(phys: np.ndarray, cfg: core.Config) -> Dict[str, float]:
    out: Dict[str, float] = {
        "hole_fill": hole_fill(phys, cfg),
        "rm_thickness": return_map_thickness(phys),
    }
    out.update(lobe_stats(phys))
    return out


# --------------------------------------------------------------------------------------
# Evaluation report: free-run a model, compare against truth, save figures + JSON
# --------------------------------------------------------------------------------------

def butterfly_report(name: str, model, data, cfg: core.Config,
                     n_steps: int = 6000, burn: int = 300,
                     out_dir: Optional[Path] = None) -> Dict[str, object]:
    scaler = data["scaler"]
    test_n = data["test_norm"]
    out_dir = Path(out_dir or cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    traj_n = core.free_run(model, test_n[0, 0], n_steps + burn, DEVICE)[burn:]
    finite = bool(np.isfinite(traj_n).all())

    true_cloud_n = test_n.reshape(-1, 3)
    true_phys = true_reference(cfg)                             # long reference (physical)

    report: Dict[str, object] = {"name": name, "free_run_finite": finite}
    report["true"] = butterfly_metrics(true_phys, cfg)
    report["true"]["std_ratio"] = 1.0

    if finite:
        phys = scaler.inverse_transform(traj_n)
        report["model"] = butterfly_metrics(phys, cfg)
        report["model"]["std_ratio"] = core.attractor_std_ratio(traj_n)
        report["model"]["sliced_W"] = core.sliced_wasserstein(
            traj_n, true_cloud_n[np.random.default_rng(0).integers(0, len(true_cloud_n), 4000)])
    else:
        phys = None
        report["model"] = {}

    # latent Lyapunov spectrum + Kaplan-Yorke (kept cheap for CPU)
    try:
        spec, ky = core.latent_spectrum_and_ky(model, test_n[0, 0], DEVICE,
                                               n_steps=500, warmup=100)
        report["latent_spectrum_top4"] = [float(v) for v in spec[:4]]
        report["kaplan_yorke"] = float(ky)
    except Exception as exc:  # pragma: no cover
        report["latent_spectrum_error"] = f"{type(exc).__name__}: {exc}"

    _butterfly_figure(name, true_phys, phys, out_dir / f"{name}_butterfly.png")
    with open(out_dir / f"{name}_report.json", "w") as f:
        json.dump(report, f, indent=2, default=float)
    return report


def _butterfly_figure(name: str, true_phys: np.ndarray, phys: Optional[np.ndarray],
                      path: Path) -> None:
    fig = plt.figure(figsize=(13, 8))
    # row 1: 3D attractors
    for col, (title, tr) in enumerate([("TRUE Lorenz", true_phys), (name, phys)]):
        ax = fig.add_subplot(2, 3, col + 1, projection="3d")
        if tr is not None:
            ax.plot(tr[:4000, 0], tr[:4000, 1], tr[:4000, 2], lw=0.3)
        ax.set_title(title, fontsize=10)
    # row 1 col 3: x-y projection overlay (lobes / holes)
    ax = fig.add_subplot(2, 3, 3)
    ax.plot(true_phys[:4000, 0], true_phys[:4000, 2], lw=0.2, alpha=0.6, label="true")
    if phys is not None:
        ax.plot(phys[:4000, 0], phys[:4000, 2], lw=0.2, alpha=0.6, label="model")
    ax.set_xlabel("x"); ax.set_ylabel("z"); ax.legend(fontsize=8)
    ax.set_title("x–z projection (holes visible)", fontsize=10)
    # row 2: return maps + x(t) trace
    for col, (title, tr) in enumerate([("TRUE return map", true_phys), ("model return map", phys)]):
        ax = fig.add_subplot(2, 3, 4 + col)
        if tr is not None:
            zm = core.z_maxima(tr)
            if len(zm) > 3:
                ax.scatter(zm[:-1], zm[1:], s=4, alpha=0.5)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel(r"$z_k^{max}$"); ax.set_ylabel(r"$z_{k+1}^{max}$")
    ax = fig.add_subplot(2, 3, 6)
    if phys is not None:
        ax.plot(phys[:2000, 0], lw=0.5)
    ax.set_title("model free-run x(t) — lobe switching", fontsize=10)
    ax.set_xlabel("step"); ax.set_ylabel("x")
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close(fig)


def print_report(rep: Dict[str, object]) -> None:
    t, m = rep["true"], rep.get("model", {})
    print(f"\n=== {rep['name']} (finite={rep['free_run_finite']}) ===")
    hdr = f"{'metric':<14}{'TRUE':>10}{'model':>10}"
    print(hdr); print("-" * len(hdr))
    for k in ["std_ratio", "hole_fill", "rm_thickness", "switches_per_1k", "mean_dwell",
              "lobe_balance", "sliced_W"]:
        tv = t.get(k, float("nan")); mv = m.get(k, float("nan"))
        print(f"{k:<14}{tv:>10.3f}{mv:>10.3f}")
    if "kaplan_yorke" in rep:
        print(f"{'D_KY':<14}{2.06:>10.3f}{rep['kaplan_yorke']:>10.3f}")
        print("latent spectrum top4:", np.round(rep["latent_spectrum_top4"], 3))
