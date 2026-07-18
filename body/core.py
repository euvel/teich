from __future__ import annotations
"""Auto-extracted from main.ipynb — every model/trainer/metric definition, no execution.

Regenerate with the extraction script if main.ipynb changes. Lab code imports from here.
"""
import os
os.environ["GEOMSTATS_BACKEND"] = "pytorch"   # must precede geomstats import below


# ==============================================================================
# from notebook cell: from __future__ import annotations
# ==============================================================================

import json
import math
import os
import random
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, TensorDataset
from tqdm.auto import tqdm

# Geometry / dynamics
import geomstats.backend as gs  # noqa: F401  (forces backend init under PyTorch)
from geomstats.geometry.poincare_ball import PoincareBall
from torchdiffeq import odeint

import matplotlib.pyplot as plt

print(f"PyTorch        : {torch.__version__}")
print(f"NumPy          : {np.__version__}")
print(f"CUDA available : {torch.cuda.is_available()}")


# ==============================================================================
# from notebook cell: def set_seed(
# ==============================================================================
def set_seed(seed: int, deterministic: bool = True) -> None:
    """Seed every RNG used in the pipeline for bit-reproducible runs.

    Args:
        seed: Master seed propagated to ``random``, NumPy and PyTorch.
        deterministic: If ``True``, force deterministic cuDNN kernels. This can
            slow training slightly but removes run-to-run variance — the right
            default for a benchmark.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    if deterministic:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        os.environ["PYTHONHASHSEED"] = str(seed)


def get_device(prefer_cuda: bool = True) -> torch.device:
    """Return the best available compute device.

    Args:
        prefer_cuda: Prefer a CUDA GPU when one is visible.

    Returns:
        A ``torch.device`` (``cuda`` > ``mps`` > ``cpu``).
    """
    if prefer_cuda and torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


# ==============================================================================
# from notebook cell: class Config:
# ==============================================================================
@dataclass
class Config:
    """Global experiment configuration (single source of truth)."""

    # --- reproducibility / IO ---
    seed: int = 42
    out_dir: str = "artifacts"

    # --- system selection ---
    system: str = "lorenz"           # "lorenz" | "rossler" | "rossler4"; routes rhs/jacobian/data

    # --- Lorenz system ---
    sigma: float = 10.0
    rho: float = 28.0
    beta: float = 8.0 / 3.0

    # --- Rossler system (classic chaotic: a=b=0.2, c=5.7; lam1~0.0714, D_KY~2.01) ---
    ros_a: float = 0.2
    ros_b: float = 0.2
    ros_c: float = 5.7

    # --- hyperchaotic Rossler system (Rossler 1979: a=0.25, b=3, c=0.5, d=0.05;
    #     two positive exponents, lam ~ (0.11, 0.02, 0, -25)) ---
    r4_a: float = 0.25
    r4_b: float = 3.0
    r4_c: float = 0.5
    r4_d: float = 0.05

    dt: float = 0.01                 # integration step (also model rollout step)
    traj_len: int = 2000             # steps kept per trajectory (after burn-in)
    burn_in: int = 1000              # discarded transient steps
    n_trajectories: int = 50         # distinct initial conditions
    ic_spread: float = 15.0          # std of initial-condition sampling

    # --- windowing / splits ---
    horizon: int = 25                # multi-step prediction length H
    stride: int = 5                  # sliding-window stride
    train_frac: float = 0.7
    val_frac: float = 0.15           # test_frac = 1 - train - val

    # --- model (shared) ---
    state_dim: int = 3
    latent_dim: int = 8
    hidden_dim: int = 128
    n_layers: int = 3
    curvature: float = 1.0           # Poincare-ball curvature c (>0); learnable in future work
    genus: int = 2                   # genus of the Teichmuller base surface (dim T = 6g-6)

    # --- optimization ---
    batch_size: int = 256
    lr: float = 1e-3
    weight_decay: float = 1e-5
    max_epochs: int = 200
    patience: int = 20               # early-stopping patience (epochs)
    grad_clip: float = 1.0

    # --- ODE solver (Euclidean baseline) ---
    ode_solver: str = "dopri5"
    ode_rtol: float = 1e-4
    ode_atol: float = 1e-5

    @property
    def test_frac(self) -> float:
        return max(0.0, 1.0 - self.train_frac - self.val_frac)

    def save(self, path: str | os.PathLike) -> None:
        Path(path).write_text(json.dumps(asdict(self), indent=2))


# ==============================================================================
# from notebook cell: def lorenz_rhs(
# ==============================================================================
def lorenz_rhs(state: np.ndarray, sigma: float, rho: float, beta: float) -> np.ndarray:
    """Right-hand side of the Lorenz '63 ODE.

    Args:
        state: Array ``[x, y, z]``.
        sigma, rho, beta: Lorenz parameters.

    Returns:
        Time derivative ``[xdot, ydot, zdot]``.
    """
    x, y, z = state
    return np.array([sigma * (y - x), x * (rho - z) - y, x * y - beta * z])


def integrate_lorenz(
    n_steps: int,
    dt: float,
    init_state: np.ndarray,
    sigma: float,
    rho: float,
    beta: float,
) -> np.ndarray:
    """Integrate the Lorenz system with a fixed-step RK4 scheme.

    Args:
        n_steps: Number of integration steps to record.
        dt: Step size.
        init_state: Initial ``[x, y, z]``.
        sigma, rho, beta: Lorenz parameters.

    Returns:
        Trajectory of shape ``(n_steps, 3)``.
    """
    traj = np.empty((n_steps, 3), dtype=np.float64)
    s = init_state.astype(np.float64)
    for i in range(n_steps):
        k1 = lorenz_rhs(s, sigma, rho, beta)
        k2 = lorenz_rhs(s + 0.5 * dt * k1, sigma, rho, beta)
        k3 = lorenz_rhs(s + 0.5 * dt * k2, sigma, rho, beta)
        k4 = lorenz_rhs(s + dt * k3, sigma, rho, beta)
        s = s + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        traj[i] = s
    return traj


def rossler_rhs(state: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """Right-hand side of the Rossler ODE.

    Args:
        state: Array ``[x, y, z]``.
        a, b, c: Rossler parameters (classic chaotic: a=b=0.2, c=5.7).

    Returns:
        Time derivative ``[xdot, ydot, zdot]``.
    """
    x, y, z = state
    return np.array([-y - z, x + a * y, b + z * (x - c)])


def integrate_rossler(
    n_steps: int, dt: float, init_state: np.ndarray, a: float, b: float, c: float
) -> np.ndarray:
    """Integrate the Rossler system with a fixed-step RK4 scheme.

    Returns:
        Trajectory of shape ``(n_steps, 3)``.
    """
    traj = np.empty((n_steps, 3), dtype=np.float64)
    s = init_state.astype(np.float64)
    for i in range(n_steps):
        k1 = rossler_rhs(s, a, b, c)
        k2 = rossler_rhs(s + 0.5 * dt * k1, a, b, c)
        k3 = rossler_rhs(s + 0.5 * dt * k2, a, b, c)
        k4 = rossler_rhs(s + dt * k3, a, b, c)
        s = s + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        traj[i] = s
    return traj


def rossler4_rhs(state: np.ndarray, a: float, b: float, c: float, d: float) -> np.ndarray:
    """Right-hand side of the hyperchaotic Rossler (1979) ODE.

    Args:
        state: Array ``[x, y, z, w]``.
        a, b, c, d: Parameters (classic hyperchaotic: a=0.25, b=3, c=0.5, d=0.05).

    Returns:
        Time derivative ``[xdot, ydot, zdot, wdot]``.
    """
    x, y, z, w = state
    return np.array([-y - z, x + a * y + w, b + x * z, -c * z + d * w])


def integrate_rossler4(
    n_steps: int, dt: float, init_state: np.ndarray,
    a: float, b: float, c: float, d: float
) -> np.ndarray:
    """Integrate the hyperchaotic Rossler system with a fixed-step RK4 scheme.

    Returns:
        Trajectory of shape ``(n_steps, 4)``.
    """
    traj = np.empty((n_steps, 4), dtype=np.float64)
    s = init_state.astype(np.float64)
    for i in range(n_steps):
        k1 = rossler4_rhs(s, a, b, c, d)
        k2 = rossler4_rhs(s + 0.5 * dt * k1, a, b, c, d)
        k3 = rossler4_rhs(s + 0.5 * dt * k2, a, b, c, d)
        k4 = rossler4_rhs(s + dt * k3, a, b, c, d)
        s = s + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        traj[i] = s
    return traj


def _system_integrate(cfg: Config, n_steps: int, ic: np.ndarray) -> np.ndarray:
    """Dispatch RK4 integration on ``cfg.system``."""
    if cfg.system == "rossler":
        return integrate_rossler(n_steps, cfg.dt, ic, cfg.ros_a, cfg.ros_b, cfg.ros_c)
    if cfg.system == "rossler4":
        return integrate_rossler4(n_steps, cfg.dt, ic,
                                  cfg.r4_a, cfg.r4_b, cfg.r4_c, cfg.r4_d)
    return integrate_lorenz(n_steps, cfg.dt, ic, cfg.sigma, cfg.rho, cfg.beta)


def _rossler_initial_conditions(cfg: Config, rng: np.random.Generator) -> np.ndarray:
    """On-attractor ICs for Rossler: sample points from one long burned-in
    reference orbit. (A Lorenz-scale ``ic_spread`` would launch Rossler orbits
    past x>c with z>0, where zdot = b + z(x-c) escapes to infinity.)"""
    ref = integrate_rossler(cfg.burn_in * 4 + cfg.n_trajectories * 200, cfg.dt,
                            np.array([-5.0, 5.0, 0.0]), cfg.ros_a, cfg.ros_b, cfg.ros_c)
    ref = ref[cfg.burn_in * 4:]                       # drop transient
    idx = rng.integers(0, len(ref), size=cfg.n_trajectories)
    return ref[idx]


def _rossler4_initial_conditions(cfg: Config, rng: np.random.Generator) -> np.ndarray:
    """On-attractor ICs for hyperchaotic Rossler: sample from one long burned-in
    reference orbit (same rationale as ``_rossler_initial_conditions``: off-attractor
    launches can escape through the ``b + x z`` term)."""
    ref = integrate_rossler4(cfg.burn_in * 4 + cfg.n_trajectories * 200, cfg.dt,
                             np.array([-10.0, -6.0, 0.0, 10.0]),
                             cfg.r4_a, cfg.r4_b, cfg.r4_c, cfg.r4_d)
    ref = ref[cfg.burn_in * 4:]                       # drop transient
    idx = rng.integers(0, len(ref), size=cfg.n_trajectories)
    return ref[idx]


def generate_trajectories(cfg: Config, rng: np.random.Generator) -> np.ndarray:
    """Generate a stack of on-attractor trajectories for ``cfg.system``.

    Returns:
        Array of shape ``(n_trajectories, traj_len, 3)`` (post burn-in).
    """
    trajs: List[np.ndarray] = []
    base = np.array([1.0, 1.0, 1.0])
    desc = f"Integrating {cfg.system.capitalize()}"
    if cfg.system == "rossler":
        ros_ics = _rossler_initial_conditions(cfg, rng)
    elif cfg.system == "rossler4":
        ros_ics = _rossler4_initial_conditions(cfg, rng)
    else:
        ros_ics = None
    for i in tqdm(range(cfg.n_trajectories), desc=desc):
        if ros_ics is not None:
            ic = ros_ics[i]
        else:
            ic = base + rng.normal(0.0, cfg.ic_spread, size=3)  # Lorenz path unchanged
        full = _system_integrate(cfg, cfg.burn_in + cfg.traj_len, ic)
        trajs.append(full[cfg.burn_in:])  # drop transient
    return np.stack(trajs).astype(np.float32)


# ==============================================================================
# from notebook cell: def split_by_trajectory(
# ==============================================================================
def split_by_trajectory(
    trajectories: np.ndarray, cfg: Config
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Partition whole trajectories into train/val/test (no temporal leakage)."""
    n = trajectories.shape[0]
    n_train = int(round(cfg.train_frac * n))
    n_val = int(round(cfg.val_frac * n))
    perm = np.random.default_rng(cfg.seed).permutation(n)
    tr, va, te = perm[:n_train], perm[n_train:n_train + n_val], perm[n_train + n_val:]
    return trajectories[tr], trajectories[va], trajectories[te]


class Standardizer:
    """Per-dimension standardization fitted on training data only."""

    def __init__(self) -> None:
        self.mean: Optional[np.ndarray] = None
        self.std: Optional[np.ndarray] = None

    def fit(self, x: np.ndarray) -> "Standardizer":
        flat = x.reshape(-1, x.shape[-1])
        self.mean = flat.mean(axis=0, keepdims=True)
        self.std = flat.std(axis=0, keepdims=True) + 1e-8
        return self

    def transform(self, x: np.ndarray) -> np.ndarray:
        return (x - self.mean) / self.std

    def inverse_transform(self, x: np.ndarray) -> np.ndarray:
        return x * self.std + self.mean


def make_windows(
    trajectories: np.ndarray, horizon: int, stride: int
) -> Tuple[np.ndarray, np.ndarray]:
    """Slice trajectories into (initial_state, future_states) windows.

    Args:
        trajectories: ``(N, T, D)`` standardized trajectories.
        horizon: Number of future steps ``H`` to predict.
        stride: Step between consecutive window starts.

    Returns:
        ``x0`` of shape ``(M, D)`` and ``targets`` of shape ``(M, H, D)``.
    """
    x0_list, tgt_list = [], []
    n, T, d = trajectories.shape
    for traj in trajectories:
        for start in range(0, T - horizon, stride):
            x0_list.append(traj[start])
            tgt_list.append(traj[start + 1: start + 1 + horizon])
    x0 = np.stack(x0_list).astype(np.float32)
    targets = np.stack(tgt_list).astype(np.float32)
    return x0, targets


# ==============================================================================
# from notebook cell: def make_loader(
# ==============================================================================
def make_loader(
    x0: np.ndarray, targets: np.ndarray, batch_size: int, shuffle: bool
) -> DataLoader:
    """Wrap arrays in a ``TensorDataset`` / ``DataLoader``."""
    ds = TensorDataset(torch.from_numpy(x0), torch.from_numpy(targets))
    return DataLoader(ds, batch_size=batch_size, shuffle=shuffle, drop_last=False)


# ==============================================================================
# from notebook cell: def build_mlp(
# ==============================================================================
def build_mlp(
    in_dim: int, out_dim: int, hidden_dim: int, n_layers: int,
    activation: Callable[[], nn.Module] = nn.SiLU,
) -> nn.Sequential:
    """Construct a simple MLP: ``n_layers`` hidden layers of width ``hidden_dim``."""
    layers: List[nn.Module] = [nn.Linear(in_dim, hidden_dim), activation()]
    for _ in range(n_layers - 1):
        layers += [nn.Linear(hidden_dim, hidden_dim), activation()]
    layers += [nn.Linear(hidden_dim, out_dim)]
    return nn.Sequential(*layers)


class WorldModel(nn.Module):
    """Abstract base: every world model exposes ``rollout(x0, horizon)``."""

    def rollout(self, x0: torch.Tensor, horizon: int) -> torch.Tensor:  # pragma: no cover
        """Predict ``horizon`` future states from initial state ``x0``.

        Args:
            x0: ``(B, state_dim)`` initial states.
            horizon: Number of steps ``H`` to predict.

        Returns:
            ``(B, H, state_dim)`` predicted trajectory.
        """
        raise NotImplementedError


# ==============================================================================
# from notebook cell: class ODEFunc(
# ==============================================================================
class ODEFunc(nn.Module):
    """Latent vector field ``dz/dt = f_theta(z)`` for the Neural ODE."""

    def __init__(self, latent_dim: int, hidden_dim: int, n_layers: int) -> None:
        super().__init__()
        self.net = build_mlp(latent_dim, latent_dim, hidden_dim, n_layers)

    def forward(self, t: torch.Tensor, z: torch.Tensor) -> torch.Tensor:  # noqa: D401
        """Time-invariant field (``t`` ignored), shape-preserving in ``z``."""
        return self.net(z)


class EuclideanNeuralODE(WorldModel):
    """Euclidean Neural ODE world model (Baseline A)."""

    def __init__(self, cfg: Config) -> None:
        super().__init__()
        self.cfg = cfg
        self.encoder = build_mlp(cfg.state_dim, cfg.latent_dim, cfg.hidden_dim, cfg.n_layers)
        self.odefunc = ODEFunc(cfg.latent_dim, cfg.hidden_dim, cfg.n_layers)
        self.decoder = build_mlp(cfg.latent_dim, cfg.state_dim, cfg.hidden_dim, cfg.n_layers)

    def rollout(self, x0: torch.Tensor, horizon: int) -> torch.Tensor:
        z0 = self.encoder(x0)                                   # (B, L)
        t = torch.arange(horizon + 1, device=x0.device, dtype=x0.dtype) * self.cfg.dt
        zt = odeint(
            self.odefunc, z0, t,
            method=self.cfg.ode_solver, rtol=self.cfg.ode_rtol, atol=self.cfg.ode_atol,
        )                                                        # (H+1, B, L)
        preds = self.decoder(zt[1:])                            # drop t0 -> (H, B, D)
        return preds.permute(1, 0, 2).contiguous()             # (B, H, D)

    # --- autonomous latent flow (for the latent-flow Lyapunov, see §8.1) -------
    def encode_latent(self, x0: torch.Tensor) -> torch.Tensor:
        return self.encoder(x0)

    def latent_step(self, z: torch.Tensor) -> torch.Tensor:
        """One ``dt`` step of the latent ODE flow (the map iterated when forecasting)."""
        t = torch.tensor([0.0, self.cfg.dt], device=z.device, dtype=z.dtype)
        return odeint(self.odefunc, z, t, method=self.cfg.ode_solver,
                      rtol=self.cfg.ode_rtol, atol=self.cfg.ode_atol)[-1]


# ==============================================================================
# from notebook cell: class PoincareBallOps:
# ==============================================================================
class PoincareBallOps:
    """Numerically-stabilized Poincaré-ball operations (curvature ``c > 0``).

    Implements the gyrovector / Möbius formulation with epsilon-guarded ``artanh``
    and norm clamping so that ``exp`` / ``log`` and their gradients stay finite even
    under long rollouts. This realizes the same geometry as
    ``geomstats.geometry.poincare_ball.PoincareBall`` but is robust for training.
    """

    def __init__(self, c: float = 1.0, eps: float = 1e-5, min_norm: float = 1e-9) -> None:
        self.c = float(c)
        self.sqrt_c = math.sqrt(self.c)
        self.eps = eps
        self.min_norm = min_norm

    def project(self, x: torch.Tensor) -> torch.Tensor:
        """Project ``x`` into the open ball of radius ``(1 - eps)/sqrt(c)``."""
        norm = x.norm(dim=-1, keepdim=True).clamp_min(self.min_norm)
        max_norm = (1.0 - self.eps) / self.sqrt_c
        scale = torch.clamp(max_norm / norm, max=1.0)
        return x * scale

    def _artanh(self, x: torch.Tensor) -> torch.Tensor:
        x = x.clamp(-1.0 + 1e-7, 1.0 - 1e-7)
        return 0.5 * (torch.log1p(x) - torch.log1p(-x))

    def mobius_add(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Möbius addition ``x ⊕_c y`` (gyro-translation), broadcast over the batch."""
        x2 = (x * x).sum(dim=-1, keepdim=True)
        y2 = (y * y).sum(dim=-1, keepdim=True)
        xy = (x * y).sum(dim=-1, keepdim=True)
        num = (1 + 2 * self.c * xy + self.c * y2) * x + (1 - self.c * x2) * y
        den = 1 + 2 * self.c * xy + (self.c ** 2) * x2 * y2
        return num / den.clamp_min(self.min_norm)

    def expmap0(self, v: torch.Tensor) -> torch.Tensor:
        """Exponential map at the origin: tangent vector -> point on the ball."""
        v_norm = v.norm(dim=-1, keepdim=True).clamp_min(self.min_norm)
        gamma = torch.tanh(self.sqrt_c * v_norm) * v / (self.sqrt_c * v_norm)
        return self.project(gamma)

    def logmap0(self, y: torch.Tensor) -> torch.Tensor:
        """Logarithmic map at the origin: point on the ball -> tangent (Euclidean) coords."""
        y_norm = y.norm(dim=-1, keepdim=True).clamp_min(self.min_norm)
        return self._artanh(self.sqrt_c * y_norm) * y / (self.sqrt_c * y_norm)

    def expmap(self, v: torch.Tensor, p: torch.Tensor) -> torch.Tensor:
        """Exponential map at base point ``p`` of tangent vector ``v`` (Möbius form)."""
        v_norm = v.norm(dim=-1, keepdim=True).clamp_min(self.min_norm)
        p2 = (p * p).sum(dim=-1, keepdim=True)
        lam = 2.0 / (1.0 - self.c * p2).clamp_min(self.min_norm)        # conformal factor
        second = torch.tanh(self.sqrt_c * lam * v_norm / 2.0) * v / (self.sqrt_c * v_norm)
        return self.project(self.mobius_add(p, second))


class HyperbolicWorldModel(WorldModel):
    """Discrete-time world model whose latent state evolves on the Poincaré ball."""

    def __init__(self, cfg: Config, max_tangent_norm: float = 5.0) -> None:
        super().__init__()
        self.cfg = cfg
        self.ops = PoincareBallOps(c=cfg.curvature)
        self.max_tangent_norm = max_tangent_norm

        self.encoder = build_mlp(cfg.state_dim, cfg.latent_dim, cfg.hidden_dim, cfg.n_layers)
        # Transition reads tangent (log) coords of the current point, outputs a tangent vector.
        self.transition = build_mlp(cfg.latent_dim, cfg.latent_dim, cfg.hidden_dim, cfg.n_layers)
        self.decoder = build_mlp(cfg.latent_dim, cfg.state_dim, cfg.hidden_dim, cfg.n_layers)

        # Small init on the transition head -> tiny initial steps -> stable early training.
        with torch.no_grad():
            last = self.transition[-1]
            last.weight.mul_(1e-2)
            last.bias.zero_()

    def _clip_tangent(self, v: torch.Tensor) -> torch.Tensor:
        """Norm-clip tangent vectors as an extra stability guard."""
        norm = v.norm(dim=-1, keepdim=True).clamp_min(1e-12)
        scale = torch.clamp(self.max_tangent_norm / norm, max=1.0)
        return v * scale

    def rollout(self, x0: torch.Tensor, horizon: int) -> torch.Tensor:
        p = self.ops.expmap0(self._clip_tangent(self.encoder(x0)))    # z_0 on the ball
        preds: List[torch.Tensor] = []
        for _ in range(horizon):
            p = self.latent_step(p)                                   # z_{k+1} on the ball
            preds.append(self.decoder(self.ops.logmap0(p)))          # decode next state
        return torch.stack(preds, dim=1)                             # (B, H, D)

    # --- autonomous latent flow (for the latent-flow Lyapunov, see §8.1) -------
    def encode_latent(self, x0: torch.Tensor) -> torch.Tensor:
        return self.ops.expmap0(self._clip_tangent(self.encoder(x0)))

    def latent_step(self, p: torch.Tensor) -> torch.Tensor:
        """One step of the latent flow on the Poincaré ball (iterated when forecasting)."""
        v = self._clip_tangent(self.transition(self.ops.logmap0(p)))
        return self.ops.expmap(v, p)


# ==============================================================================
# from notebook cell: def multistep_mse(
# ==============================================================================
def multistep_mse(pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    """Mean-squared error averaged over horizon, batch and state dims."""
    return torch.mean((pred - target) ** 2)


class Trainer:
    """Reusable training loop with early stopping, checkpointing and logging."""

    def __init__(
        self,
        model: WorldModel,
        cfg: Config,
        device: torch.device,
        name: str,
    ) -> None:
        self.model = model.to(device)
        self.cfg = cfg
        self.device = device
        self.name = name
        self.optimizer = torch.optim.AdamW(
            model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay
        )
        self.history: List[Dict[str, float]] = []
        self.out_dir = Path(cfg.out_dir)
        self.ckpt_path = self.out_dir / f"{name}_best.pt"
        self.log_path = self.out_dir / f"{name}_log.csv"

    def _run_epoch(self, loader: DataLoader, train: bool) -> float:
        self.model.train(train)
        total, count = 0.0, 0
        torch.set_grad_enabled(train)
        # Match the model's parameter dtype: importing geomstats (PyTorch backend)
        # promotes Torch's default dtype to float64, so models are float64 while the
        # raw data tensors are float32. Cast per-batch to keep them consistent.
        model_dtype = next(self.model.parameters()).dtype
        for x0, target in loader:
            x0 = x0.to(self.device, dtype=model_dtype)
            target = target.to(self.device, dtype=model_dtype)
            pred = self.model.rollout(x0, self.cfg.horizon)
            loss = multistep_mse(pred, target)
            if train:
                self.optimizer.zero_grad(set_to_none=True)
                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), self.cfg.grad_clip)
                self.optimizer.step()
            total += loss.item() * x0.size(0)
            count += x0.size(0)
        torch.set_grad_enabled(True)
        return total / max(count, 1)

    def fit(self, train_loader: DataLoader, val_loader: DataLoader) -> Dict[str, float]:
        """Train to convergence (or ``max_epochs``) with early stopping.

        Returns:
            Summary dict with best validation loss and the epoch it occurred.
        """
        best_val = float("inf")
        best_epoch = -1
        epochs_no_improve = 0

        pbar = tqdm(range(1, self.cfg.max_epochs + 1), desc=f"[{self.name}] training")
        for epoch in pbar:
            t0 = time.time()
            train_loss = self._run_epoch(train_loader, train=True)
            val_loss = self._run_epoch(val_loader, train=False)
            self.history.append(
                {
                    "epoch": epoch,
                    "train_loss": train_loss,
                    "val_loss": val_loss,
                    "seconds": time.time() - t0,
                }
            )
            pbar.set_postfix(train=f"{train_loss:.4e}", val=f"{val_loss:.4e}")

            if not (math.isfinite(train_loss) and math.isfinite(val_loss)):
                pbar.write(f"[{self.name}] non-finite loss @ epoch {epoch} — stopping.")
                break

            if val_loss < best_val - 1e-6:
                best_val, best_epoch = val_loss, epoch
                epochs_no_improve = 0
                self._save_checkpoint(epoch, val_loss)
            else:
                epochs_no_improve += 1
                if epochs_no_improve >= self.cfg.patience:
                    pbar.write(f"[{self.name}] early stop @ epoch {epoch} "
                               f"(best val {best_val:.4e} @ {best_epoch})")
                    break

        pd.DataFrame(self.history).to_csv(self.log_path, index=False)
        return {"name": self.name, "best_val_loss": best_val, "best_epoch": best_epoch}

    def _save_checkpoint(self, epoch: int, val_loss: float) -> None:
        torch.save(
            {
                "epoch": epoch,
                "val_loss": val_loss,
                "model_state": self.model.state_dict(),
                "optimizer_state": self.optimizer.state_dict(),
                "config": asdict(self.cfg),
            },
            self.ckpt_path,
        )

    @torch.no_grad()
    def evaluate(self, loader: DataLoader) -> float:
        """Mean multi-step MSE over a loader using current weights."""
        return self._run_epoch(loader, train=False)


# ==============================================================================
# from notebook cell: def lorenz_jacobian_np(
# ==============================================================================
def lorenz_jacobian_np(state: np.ndarray, sigma: float, rho: float, beta: float) -> np.ndarray:
    """Analytic 3x3 Jacobian of the Lorenz vector field at ``state``."""
    x, y, z = state
    return np.array(
        [[-sigma, sigma, 0.0],
         [rho - z, -1.0, -x],
         [y, x, -beta]],
        dtype=np.float64,
    )


def _rk4_variational_step(
    state: np.ndarray, phi: np.ndarray, dt: float, sigma: float, rho: float, beta: float
) -> Tuple[np.ndarray, np.ndarray]:
    """One RK4 step of the coupled state + fundamental-matrix (variational) system."""
    def deriv(s: np.ndarray, p: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        return lorenz_rhs(s, sigma, rho, beta), lorenz_jacobian_np(s, sigma, rho, beta) @ p

    k1s, k1p = deriv(state, phi)
    k2s, k2p = deriv(state + 0.5 * dt * k1s, phi + 0.5 * dt * k1p)
    k3s, k3p = deriv(state + 0.5 * dt * k2s, phi + 0.5 * dt * k2p)
    k4s, k4p = deriv(state + dt * k3s, phi + dt * k3p)
    s2 = state + dt / 6.0 * (k1s + 2 * k2s + 2 * k3s + k4s)
    p2 = phi + dt / 6.0 * (k1p + 2 * k2p + 2 * k3p + k4p)
    return s2, p2


def true_lorenz_lyapunov(
    cfg: Config, n_steps: int = 20000, warmup: int = 2000
) -> np.ndarray:
    """Ground-truth Lorenz Lyapunov spectrum via RK4 variational equations + QR.

    Returns:
        Descending-sorted spectrum (length 3) in physical time units.
    """
    s = np.array([1.0, 1.0, 1.0])
    for _ in range(warmup):
        s, _ = _rk4_variational_step(s, np.eye(3), cfg.dt, cfg.sigma, cfg.rho, cfg.beta)
    q = np.eye(3)
    acc = np.zeros(3)
    for _ in range(n_steps):
        s, phi = _rk4_variational_step(s, q, cfg.dt, cfg.sigma, cfg.rho, cfg.beta)
        q, r = np.linalg.qr(phi)
        sign = np.sign(np.diag(r))
        sign[sign == 0] = 1.0
        q = q * sign
        acc += np.log(np.abs(np.diag(r)) + 1e-300)
    return np.sort(acc / (n_steps * cfg.dt))[::-1]


def rossler_jacobian_np(state: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """Analytic 3x3 Jacobian of the Rossler vector field at ``state``."""
    x, _y, z = state
    return np.array(
        [[0.0, -1.0, -1.0],
         [1.0, a, 0.0],
         [z, 0.0, x - c]],
        dtype=np.float64,
    )


def _rk4_variational_step_rossler(
    state: np.ndarray, phi: np.ndarray, dt: float, a: float, b: float, c: float
) -> Tuple[np.ndarray, np.ndarray]:
    """One RK4 step of the coupled state + fundamental-matrix system (Rossler)."""
    def deriv(s: np.ndarray, p: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        return rossler_rhs(s, a, b, c), rossler_jacobian_np(s, a, b, c) @ p

    k1s, k1p = deriv(state, phi)
    k2s, k2p = deriv(state + 0.5 * dt * k1s, phi + 0.5 * dt * k1p)
    k3s, k3p = deriv(state + 0.5 * dt * k2s, phi + 0.5 * dt * k2p)
    k4s, k4p = deriv(state + dt * k3s, phi + dt * k3p)
    s2 = state + dt / 6.0 * (k1s + 2 * k2s + 2 * k3s + k4s)
    p2 = phi + dt / 6.0 * (k1p + 2 * k2p + 2 * k3p + k4p)
    return s2, p2


def true_rossler_lyapunov(
    cfg: Config, n_steps: int = 40000, warmup: int = 4000
) -> np.ndarray:
    """Ground-truth Rossler Lyapunov spectrum via RK4 variational equations + QR.

    Returns:
        Descending-sorted spectrum (length 3) in physical time units. (More steps
        than Lorenz by default: Rossler's lam1 is ~13x smaller, so finite-time
        convergence needs a longer accumulation.)
    """
    s = np.array([1.0, 1.0, 1.0])
    a, b, c = cfg.ros_a, cfg.ros_b, cfg.ros_c
    for _ in range(warmup):
        s, _ = _rk4_variational_step_rossler(s, np.eye(3), cfg.dt, a, b, c)
    q = np.eye(3)
    acc = np.zeros(3)
    for _ in range(n_steps):
        s, phi = _rk4_variational_step_rossler(s, q, cfg.dt, a, b, c)
        q, r = np.linalg.qr(phi)
        sign = np.sign(np.diag(r))
        sign[sign == 0] = 1.0
        q = q * sign
        acc += np.log(np.abs(np.diag(r)) + 1e-300)
    return np.sort(acc / (n_steps * cfg.dt))[::-1]


def rossler4_jacobian_np(
    state: np.ndarray, a: float, b: float, c: float, d: float
) -> np.ndarray:
    """Analytic 4x4 Jacobian of the hyperchaotic Rossler vector field at ``state``."""
    x, _y, z, _w = state
    return np.array(
        [[0.0, -1.0, -1.0, 0.0],
         [1.0, a, 0.0, 1.0],
         [z, 0.0, x, 0.0],
         [0.0, 0.0, -c, d]],
        dtype=np.float64,
    )


def _rk4_variational_step_rossler4(
    state: np.ndarray, phi: np.ndarray, dt: float,
    a: float, b: float, c: float, d: float
) -> Tuple[np.ndarray, np.ndarray]:
    """One RK4 step of the coupled state + fundamental-matrix system (hyperchaotic Rossler)."""
    def deriv(s: np.ndarray, p: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        return rossler4_rhs(s, a, b, c, d), rossler4_jacobian_np(s, a, b, c, d) @ p

    k1s, k1p = deriv(state, phi)
    k2s, k2p = deriv(state + 0.5 * dt * k1s, phi + 0.5 * dt * k1p)
    k3s, k3p = deriv(state + 0.5 * dt * k2s, phi + 0.5 * dt * k2p)
    k4s, k4p = deriv(state + dt * k3s, phi + dt * k3p)
    s2 = state + dt / 6.0 * (k1s + 2 * k2s + 2 * k3s + k4s)
    p2 = phi + dt / 6.0 * (k1p + 2 * k2p + 2 * k3p + k4p)
    return s2, p2


def true_rossler4_lyapunov(
    cfg: Config, n_steps: int = 120000, warmup: int = 8000
) -> np.ndarray:
    """Ground-truth hyperchaotic-Rossler Lyapunov spectrum via RK4 variational + QR.

    Returns:
        Descending-sorted spectrum (length 4) in physical time units. Defaults are
        long: the second exponent (~0.02) is small, so finite-time convergence needs
        an even longer accumulation than plain Rossler. Unlike Lorenz there is no
        constant-divergence volume check; instead Sum(lam_i) should match the orbit
        average of the Jacobian trace, <a + d + x>.
    """
    s = np.array([-10.0, -6.0, 0.0, 10.0])
    a, b, c, d = cfg.r4_a, cfg.r4_b, cfg.r4_c, cfg.r4_d
    for _ in range(warmup):
        s, _ = _rk4_variational_step_rossler4(s, np.eye(4), cfg.dt, a, b, c, d)
    q = np.eye(4)
    acc = np.zeros(4)
    for _ in range(n_steps):
        s, phi = _rk4_variational_step_rossler4(s, q, cfg.dt, a, b, c, d)
        q, r = np.linalg.qr(phi)
        sign = np.sign(np.diag(r))
        sign[sign == 0] = 1.0
        q = q * sign
        acc += np.log(np.abs(np.diag(r)) + 1e-300)
    return np.sort(acc / (n_steps * cfg.dt))[::-1]


def true_lyapunov(cfg: Config, **kw) -> np.ndarray:
    """Ground-truth Lyapunov spectrum for ``cfg.system``."""
    if cfg.system == "rossler":
        return true_rossler_lyapunov(cfg, **kw)
    if cfg.system == "rossler4":
        return true_rossler4_lyapunov(cfg, **kw)
    return true_lorenz_lyapunov(cfg, **kw)


# ==============================================================================
# from notebook cell: def make_state_step_fn(
# ==============================================================================
def make_state_step_fn(
    model: WorldModel,
) -> Callable[[torch.Tensor], torch.Tensor]:
    """Wrap a world model as a one-step state map ``x_k -> x_{k+1}`` for autograd.

    The returned function maps a single state vector ``(D,)`` to ``(D,)`` via a
    one-step rollout, so its Jacobian is the learned discrete dynamics' Jacobian.
    """
    def step(x: torch.Tensor) -> torch.Tensor:
        return model.rollout(x.unsqueeze(0), 1).squeeze(0).squeeze(0)

    return step


def lyapunov_spectrum_from_step(
    step_fn: Callable[[torch.Tensor], torch.Tensor],
    x0: torch.Tensor,
    n_steps: int,
    dt: float,
    warmup: int = 200,
    n_exponents: Optional[int] = None,
) -> torch.Tensor:
    """Finite-time Lyapunov spectrum of a differentiable one-step map (QR method).

    Args:
        step_fn: Differentiable map ``(D,) -> (D,)``.
        x0: Initial state ``(D,)``.
        n_steps: Number of QR-accumulation steps (the "finite time").
        dt: Physical time per step (for per-unit-time normalization).
        warmup: Transient steps to discard before accumulation.
        n_exponents: Number of exponents (defaults to state dimension).

    Returns:
        Descending-sorted Lyapunov exponents (length ``n_exponents``).
    """
    x = x0.clone()
    with torch.no_grad():
        for _ in range(warmup):
            x = step_fn(x)
    n = x.numel() if n_exponents is None else n_exponents
    q = torch.eye(n, dtype=x.dtype, device=x.device)
    acc = torch.zeros(n, dtype=x.dtype, device=x.device)
    for _ in range(n_steps):
        with torch.enable_grad():
            jac = torch.autograd.functional.jacobian(step_fn, x)   # (D, D)
        with torch.no_grad():
            x = step_fn(x)
        m = jac @ q
        q, r = torch.linalg.qr(m)
        diag = torch.diagonal(r).clone()
        sign = torch.sign(diag)
        sign[sign == 0] = 1.0
        q = q * sign
        acc = acc + torch.log(diag.abs().clamp_min(1e-12))
    return torch.sort(acc / (n_steps * dt), descending=True).values


# ==============================================================================
# from notebook cell: class EvalConfig:
# ==============================================================================
@dataclass
class EvalConfig:
    """Configuration for the evaluation suite (separate from training cfg)."""

    horizons: Tuple[int, ...] = (10, 25, 50, 100)
    noise_levels: Tuple[float, ...] = (0.0, 0.01, 0.05, 0.1, 0.2)
    robustness_horizon: int = 50
    n_eval_windows: int = 512
    lyap_steps: int = 400
    lyap_warmup: int = 150
    eval_batch: int = 512
    seed: int = 123


def build_eval_windows(
    traj_norm: np.ndarray, horizon: int, n_windows: int, seed: int
) -> Tuple[np.ndarray, np.ndarray]:
    """Sample ``n_windows`` (initial_state, future[horizon]) pairs from trajectories."""
    rng = np.random.default_rng(seed)
    n, t, d = traj_norm.shape
    x0 = np.empty((n_windows, d), dtype=np.float32)
    fut = np.empty((n_windows, horizon, d), dtype=np.float32)
    for i in range(n_windows):
        traj = rng.integers(n)
        start = rng.integers(0, t - horizon - 1)
        x0[i] = traj_norm[traj, start]
        fut[i] = traj_norm[traj, start + 1: start + 1 + horizon]
    return x0, fut


class Evaluator:
    """Scores a trained world model: multi-horizon error, robustness, Lyapunov spectrum."""

    def __init__(self, model: WorldModel, cfg: Config, device: torch.device) -> None:
        self.model = model.to(device).eval()
        self.cfg = cfg
        self.device = device
        self.dtype = next(model.parameters()).dtype

    @torch.no_grad()
    def _rollout(self, x0: np.ndarray, horizon: int, batch: int = 512) -> np.ndarray:
        """Batched rollout returning predictions as a NumPy array ``(M, horizon, D)``."""
        preds: List[np.ndarray] = []
        for i in range(0, len(x0), batch):
            xb = torch.as_tensor(x0[i:i + batch], dtype=self.dtype, device=self.device)
            preds.append(self.model.rollout(xb, horizon).cpu().numpy())
        return np.concatenate(preds, axis=0)

    def multi_horizon_errors(
        self, x0: np.ndarray, fut: np.ndarray, horizons: Sequence[int]
    ) -> pd.DataFrame:
        """MSE and MAE evaluated over increasing prediction horizons."""
        pred = self._rollout(x0, max(horizons))
        rows = []
        for h in horizons:
            err = pred[:, :h] - fut[:, :h]
            rows.append({"horizon": h, "MSE": float((err ** 2).mean()),
                         "MAE": float(np.abs(err).mean())})
        return pd.DataFrame(rows)

    def robustness(
        self, x0: np.ndarray, fut: np.ndarray, horizon: int,
        noise_levels: Sequence[float], seed: int = 0,
    ) -> pd.DataFrame:
        """Prediction MSE@horizon as a function of additive input-noise std."""
        rng = np.random.default_rng(seed)
        rows = []
        for s in noise_levels:
            xn = x0 + rng.normal(0.0, s, size=x0.shape).astype(np.float32)
            pred = self._rollout(xn, horizon)
            rows.append({"noise_std": s, "MSE": float(((pred - fut[:, :horizon]) ** 2).mean())})
        df = pd.DataFrame(rows)
        base = float(df.loc[df.noise_std == 0.0, "MSE"].iloc[0])
        df["MSE_ratio"] = df["MSE"] / base
        return df

    def lyapunov(
        self, x0_state: np.ndarray, n_steps: int, warmup: int
    ) -> Dict[str, object]:
        """Finite-time Lyapunov spectrum + summary statistics for the learned dynamics.

        Uses the **autonomous latent-flow** map (``encode_latent`` → iterate ``latent_step``)
        when the model exposes it — this is the Lyapunov of the map the model actually iterates
        when free-running a forecast (encode once, roll the latent forward), and is the correct
        characterization of the model's long-term/chaotic behavior. Falls back to the
        closed-loop one-step **state** map otherwise.
        """
        x0 = torch.as_tensor(x0_state, dtype=self.dtype, device=self.device)
        if hasattr(self.model, "latent_step") and hasattr(self.model, "encode_latent"):
            z0 = self.model.encode_latent(x0.unsqueeze(0)).squeeze(0)
            step_fn = self.model.latent_step
            n_exp = z0.numel()
        else:
            z0 = x0
            step_fn = make_state_step_fn(self.model)
            n_exp = x0.numel()
        spec = lyapunov_spectrum_from_step(
            step_fn, z0, n_steps, self.cfg.dt, warmup, n_exponents=n_exp).cpu().numpy()
        return {
            "spectrum": spec,
            "lambda_max": float(spec[0]),
            "lambda_mean": float(spec.mean()),
            "lambda_sum": float(spec.sum()),
        }


# ==============================================================================
# from notebook cell: def build_dataset(
# ==============================================================================
from dataclasses import replace


def build_dataset(cfg: Config) -> Dict[str, object]:
    """End-to-end data pipeline (generate → split → standardize → window → loaders)."""
    rng = np.random.default_rng(cfg.seed)
    trajs = generate_trajectories(cfg, rng)
    tr, va, te = split_by_trajectory(trajs, cfg)
    scaler = Standardizer().fit(tr)
    tr_n, va_n, te_n = scaler.transform(tr), scaler.transform(va), scaler.transform(te)
    loaders = {
        "train": make_loader(*make_windows(tr_n, cfg.horizon, cfg.stride), cfg.batch_size, True),
        "val": make_loader(*make_windows(va_n, cfg.horizon, cfg.stride), cfg.batch_size, False),
        "test": make_loader(*make_windows(te_n, cfg.horizon, cfg.stride), cfg.batch_size, False),
    }
    return {"loaders": loaders, "test_norm": te_n, "scaler": scaler}


def run_single_experiment(
    base_cfg: Config, seed: int, name: str,
    factory: Callable[[Config], WorldModel], device: torch.device,
    eval_cfg: EvalConfig, true_spectrum: np.ndarray,
) -> Dict[str, float]:
    """Train one model for one seed and return its headline metrics."""
    cfg_s = replace(base_cfg, seed=seed)
    set_seed(seed)
    data = build_dataset(cfg_s)
    loaders = data["loaders"]

    model = factory(cfg_s)
    # Growing models need the growth-aware trainer; everything else uses the base Trainer.
    if "GrowingTeichmullerWorldModel" in globals() and isinstance(model, GrowingTeichmullerWorldModel):
        trainer = GrowingTrainer(model, cfg_s, device, name=f"{name}_seed{seed}")
    else:
        trainer = Trainer(model, cfg_s, device, name=f"{name}_seed{seed}")
    trainer.fit(loaders["train"], loaders["val"])
    if trainer.ckpt_path.exists():
        model.load_state_dict(torch.load(trainer.ckpt_path, map_location=device)["model_state"])
    test_mse = trainer.evaluate(loaders["test"])

    ev = Evaluator(model, cfg_s, device)
    x0_state = data["test_norm"][0, 0]
    ly = ev.lyapunov(x0_state, eval_cfg.lyap_steps, eval_cfg.lyap_warmup)
    return {
        "model": name, "seed": seed, "test_mse": test_mse,
        "lambda_max": ly["lambda_max"],
        "lambda_max_abs_err": abs(ly["lambda_max"] - float(true_spectrum[0])),
    }


def multi_seed_study(
    seeds: Sequence[int], quick_cfg: Config, device: torch.device,
    eval_cfg: EvalConfig, true_spectrum: np.ndarray,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Train every model over several seeds; return raw runs and a mean±std summary.

    Includes the Teichmüller and growing models when those classes are defined (i.e. when this
    is run after §10), so the contribution is measured with uncertainty alongside the baselines.
    """
    factories: Dict[str, Callable[[Config], WorldModel]] = {
        "euclidean_node": lambda c: EuclideanNeuralODE(c),
        "hyperbolic_poincare": lambda c: HyperbolicWorldModel(c),
    }
    if "TeichmullerWorldModel" in globals():
        factories["teichmuller_proxy"] = lambda c: TeichmullerWorldModel(c)
    if "GrowingTeichmullerWorldModel" in globals():
        factories["growing_teichmuller"] = (
            lambda c: GrowingTeichmullerWorldModel(c, GrowthConfig(lyap_target=float(true_spectrum[0]))))
    runs: List[Dict[str, float]] = []
    for seed in seeds:
        for name, factory in factories.items():
            runs.append(run_single_experiment(
                quick_cfg, seed, name, factory, device, eval_cfg, true_spectrum))
    raw = pd.DataFrame(runs)
    summary = (
        raw.groupby("model")[["test_mse", "lambda_max", "lambda_max_abs_err"]]
        .agg(["mean", "std"])
    )
    return raw, summary


# ==============================================================================
# from notebook cell: class TeichmullerProxy(
# ==============================================================================
class TeichmullerProxy(nn.Module):
    """Differentiable proxy for Teichmüller space T(Σ_g) in Fenchel–Nielsen coordinates.

    The latent point is ``(τ_i, ℓ_i)`` per pants curve, identified with the upper-half-plane
    ``ζ_i = τ_i + i ℓ_i ∈ ℍ²`` (Im ζ = ℓ > 0). Dynamics are realized by the exact
    ``SL(2,ℝ)`` action (geodesic flow ⊕ quasiconformal deformation ⊕ twist/earthquake).

    References:
        * Wolpert (1985), ``ω_WP = Σ dℓ_i ∧ dτ_i`` (FN are Darboux coordinates).
        * Teichmüller geodesic flow = diagonal SL(2,ℝ) action on translation surfaces.
        * Beltrami / quasiconformal deformation ``z ↦ z + μ z̄`` (‖μ‖∞ < 1).
    """

    def __init__(self, genus: int = 2, n_curves: Optional[int] = None,
                 ell_min: float = 1e-3, ell_max: float = 1e3, tau_max: float = 1e3) -> None:
        super().__init__()
        if n_curves is None and genus < 2:
            raise ValueError("Teichmüller space requires genus >= 2.")
        self.genus = genus
        # ``n_curves`` may exceed 3g-3 for the *growing* model (higher-complexity strata).
        self.n_curves = n_curves if n_curves is not None else 3 * genus - 3
        self.dim = 2 * self.n_curves           # dim_R T(Σ_g) = 6g - 6 for the base surface
        self.ell_min, self.ell_max, self.tau_max = ell_min, ell_max, tau_max

        # Learnable genus-g "base surface" in FN coordinates (length via softplus > 0).
        self.base_raw_length = nn.Parameter(torch.zeros(self.n_curves))
        self.base_twist = nn.Parameter(torch.zeros(self.n_curves))

    # --- coordinate helpers ---------------------------------------------------
    def raw_to_fn(self, raw: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Map an unconstrained ``(..., 2*n_curves)`` tensor to FN ``(τ, ℓ>0)``.

        Channels split as ``[twist | raw_length]``; ``ℓ = softplus(raw_length + base)``.
        """
        twist, raw_len = raw[..., :self.n_curves], raw[..., self.n_curves:]
        ell = nn.functional.softplus(raw_len + self.base_raw_length) + self.ell_min
        tau = twist + self.base_twist
        return self.project(tau, ell)

    def fn_to_features(self, tau: torch.Tensor, ell: torch.Tensor) -> torch.Tensor:
        """FN coordinates -> network features ``[τ, log ℓ]`` (log keeps lengths well-scaled)."""
        return torch.cat([tau, torch.log(ell)], dim=-1)

    def project(self, tau: torch.Tensor, ell: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Keep the point in the interior of ℍ² (away from cusp ℓ→0 and infinity)."""
        return tau.clamp(-self.tau_max, self.tau_max), ell.clamp(self.ell_min, self.ell_max)

    # --- SL(2,R) generator -> matrix exponential ------------------------------
    @staticmethod
    def sl2_exp(a: torch.Tensor, b: torch.Tensor, c: torch.Tensor, dt: float
                ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Exact ``exp(dt · X)`` for ``X = [[a, b], [c, -a]] ∈ sl(2,ℝ)``.

        Uses ``X² = (a²+bc) I`` to evaluate the series in closed form across the
        hyperbolic (Δ>0), elliptic (Δ<0) and parabolic (Δ=0) regimes; ``det = 1`` exactly.
        Returns the matrix entries ``(p, q, r, s)``.
        """
        a, b, c = a * dt, b * dt, c * dt
        delta = a * a + b * c                                   # (dt·X)² = delta · I
        sq = torch.sqrt(delta.abs().clamp_min(1e-30))
        pos = delta >= 0
        cosh_ = torch.where(pos, torch.cosh(sq), torch.cos(sq))
        sinhc = torch.where(pos, torch.sinh(sq) / sq, torch.sin(sq) / sq)
        p = cosh_ + sinhc * a
        q = sinhc * b
        r = sinhc * c
        s = cosh_ - sinhc * a
        return p, q, r, s

    def mobius(self, tau: torch.Tensor, ell: torch.Tensor,
               p: torch.Tensor, q: torch.Tensor, r: torch.Tensor, s: torch.Tensor,
               ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Apply the Möbius map ``ζ ↦ (pζ+q)/(rζ+s)`` on ``ζ = τ + iℓ`` (preserves ℍ²)."""
        den = ((r * tau + s) ** 2 + (r * ell) ** 2).clamp_min(1e-12)
        tau2 = ((p * tau + q) * (r * tau + s) + (p * ell) * (r * ell)) / den
        ell2 = ell / den                                        # = ℓ·(ps-qr)/|den|² = ℓ/|den|²
        return self.project(tau2, ell2)

    # --- named flows (interpretable building blocks) --------------------------
    def geodesic_step(self, tau, ell, rate, dt):
        """Teichmüller geodesic flow: diagonal generator ``a = rate`` ⇒ ℓ ↦ e^{2·rate·dt} ℓ."""
        z = torch.zeros_like(rate)
        return self.mobius(tau, ell, *self.sl2_exp(rate, z, z, dt))

    def twist_step(self, tau, ell, rate, dt):
        """Earthquake/twist flow (Wolpert): parabolic generator ⇒ τ ↦ τ + rate·dt, ℓ fixed."""
        z = torch.zeros_like(rate)
        return self.mobius(tau, ell, *self.sl2_exp(z, rate, z, dt))

    def quasiconformal_step(self, tau, ell, mu_re, mu_im, dt):
        """Quasiconformal deformation: Beltrami ``μ`` (‖μ‖<1) as a symmetric sl(2,ℝ) boost."""
        mu = torch.sqrt(mu_re ** 2 + mu_im ** 2).clamp_max(0.999)
        scale = 1.0 / (1.0 - mu ** 2).clamp_min(1e-6)
        a = mu_re * scale
        b = c = mu_im * scale                                   # symmetric off-diagonal
        return self.mobius(tau, ell, *self.sl2_exp(a, b, c, dt))

    # --- Weil–Petersson diagnostics ------------------------------------------
    def wp_symplectic_area(self, tau0, ell0, tau1, ell1) -> torch.Tensor:
        """Discrete WP area element ``Σ_i Δℓ_i ∧ Δτ_i`` swept between two states (diagnostic)."""
        return (0.5 * ((ell1 - ell0) * (tau1 + tau0) - (tau1 - tau0) * (ell1 + ell0))).sum(-1)


# ==============================================================================
# from notebook cell: class TeichmullerWorldModel(
# ==============================================================================
class TeichmullerWorldModel(WorldModel):
    """World model whose latent evolves on a Teichmüller-space proxy via SL(2,ℝ) dynamics."""

    def __init__(self, cfg: Config, max_gen: float = 3.0) -> None:
        super().__init__()
        self.cfg = cfg
        self.proxy = TeichmullerProxy(genus=cfg.genus)
        self.max_gen = max_gen
        d = self.proxy.dim                       # 6g - 6
        nc = self.proxy.n_curves

        self.encoder = build_mlp(cfg.state_dim, d, cfg.hidden_dim, cfg.n_layers)
        # Vector field: features [τ, log ℓ] (dim d) -> 3 generator channels per curve
        # (a = geodesic rate, b/c folded from twist & qc), here parameterized as (a, b, c).
        self.field = build_mlp(d, 3 * nc, cfg.hidden_dim, cfg.n_layers)
        self.decoder = build_mlp(d, cfg.state_dim, cfg.hidden_dim, cfg.n_layers)

        # Small init on the field head -> tiny initial steps -> stable early training.
        with torch.no_grad():
            self.field[-1].weight.mul_(1e-2)
            self.field[-1].bias.zero_()

    def _generators(self, tau: torch.Tensor, ell: torch.Tensor
                    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Learned, state-dependent sl(2,ℝ) generators per curve (bounded for stability)."""
        feats = self.proxy.fn_to_features(tau, ell)
        raw = self.field(feats).view(*tau.shape[:-1], self.proxy.n_curves, 3)
        gen = self.max_gen * torch.tanh(raw)     # bound |a|,|b|,|c| <= max_gen
        return gen[..., 0], gen[..., 1], gen[..., 2]

    def rollout(self, x0: torch.Tensor, horizon: int) -> torch.Tensor:
        tau, ell = self.proxy.raw_to_fn(self.encoder(x0))      # initial point in (ℍ²)^{nc}
        preds: List[torch.Tensor] = []
        for _ in range(horizon):
            tau, ell = self._latent_fn_step(tau, ell)          # Lie–Euler geodesic step
            preds.append(self.decoder(self.proxy.fn_to_features(tau, ell)))
        return torch.stack(preds, dim=1)                        # (B, H, D)

    def _latent_fn_step(self, tau: torch.Tensor, ell: torch.Tensor
                        ) -> Tuple[torch.Tensor, torch.Tensor]:
        a, b, c = self._generators(tau, ell)                   # X_i = [[a,b],[c,-a]]
        p, q, r, s = self.proxy.sl2_exp(a, b, c, self.cfg.dt)
        return self.proxy.mobius(tau, ell, p, q, r, s)

    # --- autonomous latent flow (for the latent-flow Lyapunov, see §8.1) -------
    def encode_latent(self, x0: torch.Tensor) -> torch.Tensor:
        tau, ell = self.proxy.raw_to_fn(self.encoder(x0))
        return torch.cat([tau, torch.log(ell)], dim=-1)        # flat z = (τ | log ℓ)

    def latent_step(self, z: torch.Tensor) -> torch.Tensor:
        nc = self.proxy.n_curves
        tau, ell = self.proxy.project(z[..., :nc], torch.exp(z[..., nc:]))
        tau, ell = self._latent_fn_step(tau, ell)
        return torch.cat([tau, torch.log(ell)], dim=-1)


# ==============================================================================
# from notebook cell: class _StraightThroughGate(
# ==============================================================================
class _StraightThroughGate(torch.autograd.Function):
    """Hard {0,1} gate in the forward pass, sigmoid-gradient in the backward pass (STE)."""

    @staticmethod
    def forward(ctx, logit: torch.Tensor) -> torch.Tensor:  # type: ignore[override]
        ctx.save_for_backward(logit)
        return (logit > 0).to(logit.dtype)

    @staticmethod
    def backward(ctx, grad_out: torch.Tensor):  # type: ignore[override]
        (logit,) = ctx.saved_tensors
        s = torch.sigmoid(logit)
        return grad_out * s * (1.0 - s)


def straight_through_gate(logit: torch.Tensor) -> torch.Tensor:
    """Straight-through binary gate (see :class:`_StraightThroughGate`)."""
    return _StraightThroughGate.apply(logit)


@dataclass
class GrowthConfig:
    """Configuration for the growing curriculum (separate from the model config)."""

    max_extra_curves: int = 3        # growable slots beyond the genus-2 base (3 -> up to 6)
    warmup_epochs: int = 20          # train base surface alone before any growth
    grow_every: int = 12             # evaluate the growth trigger on this cadence
    ramp_epochs: int = 8             # maturation ramp length for a newborn curve
    gate_temp: float = 1.0           # straight-through gate temperature
    saturation_level: float = 0.8    # |a_i| > level*max_gen counts as "saturated"
    saturation_trigger: float = 0.30 # grow if >30% of active curves are saturated
    plateau_rel: float = 0.01        # "plateau" = <1% relative val-loss improvement over window
    plateau_window: int = 8          # epochs used to assess the plateau
    lambda_growth: float = 0.0       # complexity (parsimony) — OFF: growth is permanent
    lambda_commit: float = 0.0       # gate-commitment — OFF: growth is permanent

    # --- Lyapunov coupling (couples geometry to dynamics) ---
    lyap_target: float = 0.9         # target maximal Lyapunov exponent (data-estimated)
    lyap_targets: Optional[Tuple[float, ...]] = None
                                     # OPTIONAL vector of positive-exponent targets (descending),
                                     # one anchored expanding curve per entry (hyperchaos: e.g.
                                     # (0.11, 0.02) for rossler4). None -> single-anchor path
                                     # driven by ``lyap_target`` (backward-compatible default).
    anchor_expansion: bool = True    # PRIMARY: Dehn-twist expanding-circle anchor (stable)
    anchor_period: float = 2.0       # fold period for the anchored twist (Dehn-twist wrap)
    n_fiber: int = 0                 # Higgs/Hitchin torus fibers (neutral modes; §12.3). 0=off
    fiber_scale: float = 0.4         # magnitude of the skew (Higgs-connection) fiber coupling
    fiber_anchor_rate: float = 0.0   # ε: tiny positive Dehn anchor on fibers → λ₂=0⁺ (Fix D),
                                     #     prevents the slow fiber-collapse that under-fills the attractor
    decoder_hidden: Optional[int] = None  # decoder width override (defaults to cfg.hidden_dim)
    decoder_layers: Optional[int] = None  # decoder depth override (defaults to cfg.n_layers)
    contraction_bias: float = 0.0    # force stable curves to contract strongly (λ_i ≤ -2·bias),
                                     #     pins Kaplan–Yorke dim ≈ 2.06 (else KY drifts high)
    lambda_expand: float = 0.0       # OPTIONAL soft Huber λ-controller (unstable; off by default)
    lambda_recon: float = 0.0        # autoencoder isometry (only for the closed-loop metric; off)
    lyap_power_iters: int = 10       # power-iteration steps for the (optional) soft λ estimate
    lyap_subbatch: int = 48          # sub-batch size for the (optional) soft λ estimate
    lyap_warmup_epochs: int = 12     # warm-up before the (optional) soft λ controller engages
    scheduled_growth: bool = True    # grow on the cadence (curriculum) vs. only on plateau


# ==============================================================================
# from notebook cell: class GrowingTeichmullerWorldModel(
# ==============================================================================
class GrowingTeichmullerWorldModel(WorldModel):
    """Teichmüller world model that dynamically grows length–twist pairs (curves).

    Architecture is sized for ``max_curves = (3g-3) + max_extra``; growth toggles
    structural ``born`` flags and learnable gates that activate the extra curves, so the
    *effective* dimension increases over training while the parameter count stays fixed.
    """

    def __init__(self, cfg: Config, growth_cfg: GrowthConfig, max_gen: float = 3.0) -> None:
        super().__init__()
        self.cfg = cfg
        self.gcfg = growth_cfg
        self.max_gen = max_gen
        self.base_curves = 3 * cfg.genus - 3
        self.max_extra = growth_cfg.max_extra_curves
        self.max_curves = self.base_curves + self.max_extra
        if growth_cfg.anchor_expansion:
            n_anchored = len(growth_cfg.lyap_targets or (growth_cfg.lyap_target,))
            if n_anchored + growth_cfg.n_fiber >= self.max_curves:
                raise ValueError(
                    f"anchored curves ({n_anchored}) + fibers ({growth_cfg.n_fiber}) must leave "
                    f"at least one contracting curve out of max_curves={self.max_curves}")

        self.proxy = TeichmullerProxy(genus=cfg.genus, n_curves=self.max_curves)
        d, nc = self.proxy.dim, self.max_curves
        dec_h = growth_cfg.decoder_hidden if growth_cfg.decoder_hidden is not None else cfg.hidden_dim
        dec_l = growth_cfg.decoder_layers if growth_cfg.decoder_layers is not None else cfg.n_layers
        self.encoder = build_mlp(cfg.state_dim, d, cfg.hidden_dim, cfg.n_layers)
        self.field = build_mlp(d, 3 * nc, cfg.hidden_dim, cfg.n_layers)
        self.decoder = build_mlp(d, cfg.state_dim, dec_h, dec_l)   # wider/deeper decoder optional
        with torch.no_grad():
            self.field[-1].weight.mul_(1e-2)
            self.field[-1].bias.zero_()

        # Higgs/Hitchin skew coupling ω(base) → torus-fiber rotation rates (§12.3).
        if growth_cfg.n_fiber > 0:
            self.fiber_coupling = build_mlp(2, growth_cfg.n_fiber, cfg.hidden_dim, 2)

        # --- growth state ---
        self.gate_logit = nn.Parameter(torch.full((self.max_extra,), -4.0))  # start closed
        self.register_buffer("born", torch.zeros(self.max_extra))
        self.register_buffer("birth_epoch", torch.full((self.max_extra,), -1.0))
        self.register_buffer("current_epoch", torch.tensor(0.0))

    # --- growth bookkeeping ---------------------------------------------------
    def set_epoch(self, epoch: int) -> None:
        self.current_epoch.fill_(float(epoch))

    def _maturity(self) -> torch.Tensor:
        age = self.current_epoch - self.birth_epoch
        ramp = torch.clamp(age / max(self.gcfg.ramp_epochs, 1), 0.0, 1.0)
        return ramp * self.born

    def gates(self) -> torch.Tensor:
        """Per-curve gates ``(max_curves,)`` in ``[0,1]``. Growth is **permanent**: once a
        curve is born it ramps to 1 and is kept (no pruning), so grown capacity persists."""
        g_extra = self._maturity()                          # born × maturation ramp ∈ [0,1]
        ones = torch.ones(self.base_curves, dtype=g_extra.dtype, device=g_extra.device)
        return torch.cat([ones, g_extra])

    def soft_gates(self) -> torch.Tensor:
        """Differentiable gate values (here equal to ``gates``; kept for API compatibility)."""
        return self._maturity()

    def can_grow(self) -> bool:
        return bool(self.born.sum().item() < self.max_extra)

    def grow(self, epoch: int) -> bool:
        """Birth the next dormant curve (permanently). Returns ``True`` if grown."""
        if not self.can_grow():
            return False
        k = int(self.born.sum().item())
        self.born[k] = 1.0
        self.birth_epoch[k] = float(epoch)
        return True

    def n_active_curves(self) -> int:
        return self.base_curves + int((self.gates()[self.base_curves:] > 0.5).sum().item())

    def effective_dim(self) -> int:
        """Effective real dimension of the active sub-surface (= 2 × active curves)."""
        return 2 * self.n_active_curves()

    def soft_effective_dim(self) -> float:
        return 2.0 * (self.base_curves + float(self.soft_gates().sum().item()))

    # --- regularization & expansion/isometry objective -----------------------
    def regularization(self) -> torch.Tensor:
        soft = self.soft_gates()
        complexity = soft.sum()                         # parsimony: prune unused curves
        commitment = (soft * (1.0 - soft)).sum()        # push gates toward {0,1}
        return self.gcfg.lambda_growth * complexity + self.gcfg.lambda_commit * commitment

    def latent_lyapunov_estimate(self, x0: torch.Tensor, n_power: int = 10) -> torch.Tensor:
        """Differentiable finite-time **top Lyapunov exponent of the latent flow** via power
        iteration (forward-mode ``jvp`` on ``latent_step``). This directly estimates the
        quantity §8 evaluates, giving a clean, low-variance training signal — far more stable
        than perturbation/output-space proxies.
        """
        z = self.encode_latent(x0).detach()
        v = torch.randn_like(z)
        v = v / v.norm(dim=-1, keepdim=True).clamp_min(1e-12)
        logsum = z.new_zeros(())
        for _ in range(n_power):
            out, jv = torch.func.jvp(self.latent_step, (z,), (v,))
            nrm = jv.norm(dim=-1, keepdim=True).clamp_min(1e-12)
            logsum = logsum + torch.log(nrm.squeeze(-1)).mean()
            v = (jv / nrm).detach()
            z = out.detach()
        return logsum / (n_power * self.cfg.dt)

    def encode(self, x0: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """State -> Fenchel–Nielsen coordinates ``(τ, ℓ)`` on the (gated) proxy surface."""
        return self.proxy.raw_to_fn(self.encoder(x0))

    def reconstruct(self, x0: torch.Tensor) -> torch.Tensor:
        """Zero-step autoencode ``D(E(x))`` used for the isometry loss."""
        tau, ell = self.encode(x0)
        return self.decoder(self._features(tau, ell, self.gates()))

    @torch.no_grad()
    def saturation_metric(self, x0: torch.Tensor) -> float:
        """Fraction of *active* curves whose geodesic rate is near saturation (∈[0,1])."""
        g = self.gates()
        tau, ell = self.proxy.raw_to_fn(self.encoder(x0))
        a, _, _ = self._generators(tau, ell, g)         # (B, max_curves)
        active = (g > 0.5).view(*([1] * (a.dim() - 1)), self.max_curves).expand_as(a)
        saturated = (a.abs() > self.gcfg.saturation_level * self.max_gen) & active
        return float(saturated.sum() / active.sum().clamp_min(1.0))

    # --- dynamics (gated) -----------------------------------------------------
    def _anchor_targets(self) -> Tuple[float, ...]:
        """Anchored positive-exponent targets (descending). ``lyap_targets`` when set
        (one expanding curve per entry), else the single scalar ``lyap_target``."""
        if self.gcfg.lyap_targets is not None:
            return tuple(float(t) for t in self.gcfg.lyap_targets)
        return (float(self.gcfg.lyap_target),)

    def _features(self, tau: torch.Tensor, ell: torch.Tensor, g: torch.Tensor) -> torch.Tensor:
        gvec = g.view(*([1] * (tau.dim() - 1)), self.max_curves)
        return torch.cat([tau * gvec, torch.log(ell) * gvec], dim=-1)

    def _generators(self, tau, ell, g):
        raw = self.field(self._features(tau, ell, g)).view(*tau.shape[:-1], self.max_curves, 3)
        gen = self.max_gen * torch.tanh(raw)
        a, b, c = gen[..., 0], gen[..., 1], gen[..., 2]
        if self.gcfg.anchor_expansion:
            # Curves beyond the anchored ones are forced into **pure-diagonal contractions**
            # (a<0, b=c=0) so they can only supply *stable* (contracting) directions — a generic
            # generator with free b,c is hyperbolic whenever a²+bc>0 and would add a spurious
            # expanding direction. This pins the latent positive exponents to the anchors' λ*'s
            # (curves 0..K-1 handled in ``_fn_step``; K=1 in the classic single-anchor mode).
            # ``contraction_bias`` makes the stable directions contract strongly (Lorenz-like),
            # keeping the Kaplan–Yorke dimension ≈ 2.06 rather than drifting high.
            k = len(self._anchor_targets())
            a = torch.cat([a[..., :k],
                           -nn.functional.softplus(a[..., k:]) - self.gcfg.contraction_bias], dim=-1)
            z = torch.zeros_like(b[..., k:])
            b = torch.cat([b[..., :k], z], dim=-1)
            c = torch.cat([c[..., :k], z], dim=-1)
        gvec = g.view(*([1] * (tau.dim() - 1)), self.max_curves)
        return a * gvec, b * gvec, c * gvec

    def _fn_step(self, tau, ell, g):
        """One latent step on the (gated) Teichmüller surface, plus the **Dehn-twist anchor**.

        The anchor turns curve 0 into a stretch-and-fold *expanding circle map*
        ``τ₀ → e^{λ* dt}·τ₀  (mod period)`` with ``ℓ₀`` held bounded. Its Jacobian entry
        ``∂τ₀'/∂τ₀ = e^{λ* dt}`` is fixed *by construction*, so the latent flow's top Lyapunov
        exponent equals ``λ*`` — sustained over arbitrarily long horizons (the fold prevents the
        coordinate from saturating) and robust across seeds/configs (no optimization tug-of-war).
        """
        tau_in = tau                                               # capture BEFORE the mobius
        a, b, c = self._generators(tau, ell, g)
        p, q, r, s = self.proxy.sl2_exp(a, b, c, self.cfg.dt)
        tau, ell = self.proxy.mobius(tau, ell, p, q, r, s)
        if self.gcfg.anchor_expansion:
            # Anchor off the INPUT τᵢ so ∂τᵢ'/∂τᵢ = e^{λᵢ* dt} *exactly* (independent of the
            # mobius derivative) — this is what makes the Lyapunov exponents guaranteed.
            # One anchored expanding curve per target: classic mode has a single target
            # (curve 0); hyperchaos mode anchors curves 0..K-1, each an independent
            # stretch-and-fold circle map (∂τᵢ'/∂τⱼ = 0 for i≠j, so the K rates are the
            # K leading exponents by construction).
            targets = self._anchor_targets()
            period = self.gcfg.anchor_period
            nf = self.gcfg.n_fiber
            new_tau, new_ell = [], []
            for i, lam in enumerate(targets):                          # curves 0..K-1: chaotic base
                rate = math.exp(lam * self.cfg.dt)
                t = rate * tau_in[..., i:i + 1]
                new_tau.append(t - period * torch.round(t / period))   # Dehn fold
                new_ell.append(torch.ones_like(ell[..., :1]))
            ka = len(targets)
            if nf > 0:
                # Hitchin torus fibers: skew rotation φ_k → φ_k + ω_k(base) (mod period),
                # with ω depending only on the base (so ∂φ_k'/∂φ_k = 1 → a neutral λ≈0 mode).
                base = tau_in[..., :1]
                emb = torch.cat([torch.cos(2 * math.pi * base / period),
                                 torch.sin(2 * math.pi * base / period)], dim=-1)
                omega = self.gcfg.fiber_scale * torch.tanh(self.fiber_coupling(emb))
                # Fix D: a tiny positive Dehn anchor (rate ε) on the fiber → ∂φ'/∂φ = e^{ε dt},
                # i.e. λ₂ = ε ≳ 0 (0⁺ rather than drifting negative), which stops the fiber
                # dimension from slowly collapsing over a long free-run.
                frate = math.exp(self.gcfg.fiber_anchor_rate * self.cfg.dt)
                for k in range(nf):
                    phi = frate * tau_in[..., ka + k:ka + k + 1] + omega[..., k:k + 1]
                    new_tau.append(phi - period * torch.round(phi / period))
                    new_ell.append(torch.ones_like(ell[..., :1]))
            rest = ka + nf
            tau = torch.cat(new_tau + [tau[..., rest:]], dim=-1)
            ell = torch.cat(new_ell + [ell[..., rest:]], dim=-1)
        return tau, ell

    def rollout(self, x0: torch.Tensor, horizon: int) -> torch.Tensor:
        g = self.gates()
        tau, ell = self.proxy.raw_to_fn(self.encoder(x0))
        preds: List[torch.Tensor] = []
        for _ in range(horizon):
            tau, ell = self._fn_step(tau, ell, g)
            preds.append(self.decoder(self._features(tau, ell, g)))
        return torch.stack(preds, dim=1)

    # --- autonomous latent flow (for the latent-flow Lyapunov, see §8.1) -------
    def encode_latent(self, x0: torch.Tensor) -> torch.Tensor:
        tau, ell = self.encode(x0)
        return torch.cat([tau, torch.log(ell)], dim=-1)        # flat z = (τ | log ℓ), gated

    def latent_step(self, z: torch.Tensor) -> torch.Tensor:
        nc = self.max_curves
        g = self.gates()
        tau, ell = self.proxy.project(z[..., :nc], torch.exp(z[..., nc:]))
        tau, ell = self._fn_step(tau, ell, g)
        return torch.cat([tau, torch.log(ell)], dim=-1)


# ==============================================================================
# from notebook cell: class GrowingTrainer(
# ==============================================================================
class GrowingTrainer(Trainer):
    """Trainer with a morphogenesis-style growth curriculum for the Teichmüller model."""

    def __init__(self, model: GrowingTeichmullerWorldModel, cfg: Config,
                 device: torch.device, name: str) -> None:
        super().__init__(model, cfg, device, name=name)
        self.gcfg = model.gcfg
        self.growth_events: List[int] = []
        self._last_lam: float = float("nan")     # most recent finite-time λ_max estimate

    def _run_epoch(self, loader: DataLoader, train: bool) -> float:
        """As ``Trainer._run_epoch`` but adds the growth regularizer to the train loss."""
        self.model.train(train)
        total, count = 0.0, 0
        torch.set_grad_enabled(train)
        model_dtype = next(self.model.parameters()).dtype
        for x0, target in loader:
            x0 = x0.to(self.device, dtype=model_dtype)
            target = target.to(self.device, dtype=model_dtype)
            pred = self.model.rollout(x0, self.cfg.horizon)
            mse = multistep_mse(pred, target)
            if train:
                loss = mse + self.model.regularization()
                epoch_now = int(self.model.current_epoch.item())
                if self.gcfg.lambda_expand > 0.0 and epoch_now >= self.gcfg.lyap_warmup_epochs:
                    # Latent-Lyapunov controller: Huber-bounded so the gradient cannot explode
                    # when the estimate overshoots (a squared loss blows up; Huber stays stable).
                    lam = self.model.latent_lyapunov_estimate(
                        x0[:self.gcfg.lyap_subbatch], self.gcfg.lyap_power_iters).clamp(-3.0, 5.0)
                    loss = loss + self.gcfg.lambda_expand * nn.functional.smooth_l1_loss(
                        lam, lam.new_tensor(self.gcfg.lyap_target))
                    self._last_lam = float(lam.detach())
                if self.gcfg.lambda_recon > 0.0:                       # autoencoder isometry (off)
                    loss = loss + self.gcfg.lambda_recon * multistep_mse(
                        self.model.reconstruct(x0), x0)
                self.optimizer.zero_grad(set_to_none=True)
                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), self.cfg.grad_clip)
                self.optimizer.step()
            total += mse.item() * x0.size(0)            # log pure MSE for comparability
            count += x0.size(0)
        torch.set_grad_enabled(True)
        return total / max(count, 1)

    def _should_grow(self, epoch: int, val_hist: List[float]) -> Tuple[bool, float]:
        """Growth trigger on the growth cadence while capacity remains.

        With ``scheduled_growth`` (default) the model grows on the cadence as a curriculum —
        unless the last window clearly worsened — reliably reaching the 4–6 curve regime that a
        curve-count sweep shows is needed to realize the target Lyapunov exponent. Otherwise it
        falls back to a learning **plateau** OR geodesic **saturation** trigger. Either way the
        complexity penalty prunes any curve that fails to reduce the loss.
        """
        if not self.model.can_grow() or epoch < self.gcfg.warmup_epochs:
            return False, 0.0
        if (epoch - self.gcfg.warmup_epochs) % self.gcfg.grow_every != 0:
            return False, 0.0
        x0, _ = next(iter(self.train_loader_ref))
        sat = self.model.saturation_metric(x0.to(self.device, dtype=next(self.model.parameters()).dtype))
        w = self.gcfg.plateau_window
        if self.gcfg.scheduled_growth:
            worsening = (len(val_hist) >= w and val_hist[-1] > 1.5 * min(val_hist[-w:]))
            return (not worsening), sat
        plateau = False
        if len(val_hist) >= w:
            recent = val_hist[-w:]
            plateau = (max(recent) - min(recent)) / (abs(recent[0]) + 1e-12) < self.gcfg.plateau_rel
        return (sat > self.gcfg.saturation_trigger or plateau), sat

    def fit(self, train_loader: DataLoader, val_loader: DataLoader) -> Dict[str, float]:
        self.train_loader_ref = train_loader
        best_val, best_epoch, no_improve = float("inf"), -1, 0
        val_hist: List[float] = []

        pbar = tqdm(range(1, self.cfg.max_epochs + 1), desc=f"[{self.name}] growing")
        for epoch in pbar:
            self.model.set_epoch(epoch)
            t0 = time.time()
            train_loss = self._run_epoch(train_loader, train=True)
            val_loss = self._run_epoch(val_loader, train=False)
            val_hist.append(val_loss)

            grew, sat = self._should_grow(epoch, val_hist)
            if grew and self.model.grow(epoch):
                self.growth_events.append(epoch)
                no_improve = 0  # give the new structure time to help
                pbar.write(f"[{self.name}] grew a curve @ epoch {epoch} "
                           f"(active={self.model.n_active_curves()}, sat={sat:.2f})")

            self.history.append({
                "epoch": epoch, "train_loss": train_loss, "val_loss": val_loss,
                "seconds": time.time() - t0,
                "n_active_curves": self.model.n_active_curves(),
                "effective_dim": self.model.effective_dim(),
                "soft_effective_dim": self.model.soft_effective_dim(),
                "saturation": sat, "lyap_est": self._last_lam,
                **{f"gate_{k}": float(self.model.soft_gates()[k]) for k in range(self.model.max_extra)},
            })
            pbar.set_postfix(val=f"{val_loss:.3e}", dim=self.model.effective_dim(),
                             active=self.model.n_active_curves(),
                             lam=f"{self._last_lam:.2f}")

            if not math.isfinite(val_loss):
                pbar.write(f"[{self.name}] non-finite loss @ epoch {epoch} — stopping.")
                break
            if val_loss < best_val - 1e-6:
                best_val, best_epoch, no_improve = val_loss, epoch, 0
                self._save_checkpoint(epoch, val_loss)
            else:
                no_improve += 1
                # Suspend early stopping while the structure is still growing.
                if not self.model.can_grow() and no_improve >= self.cfg.patience:
                    pbar.write(f"[{self.name}] early stop @ epoch {epoch} "
                               f"(best val {best_val:.4e} @ {best_epoch})")
                    break

        pd.DataFrame(self.history).to_csv(self.log_path, index=False)
        return {"name": self.name, "best_val_loss": best_val, "best_epoch": best_epoch,
                "final_effective_dim": self.model.effective_dim(),
                "growth_events": self.growth_events}


# ==============================================================================
# from notebook cell: def free_run(
# ==============================================================================
# --- Chaos-aware metrics (all operate on a model's autonomous free-run) -------
def free_run(model: WorldModel, x0_norm: np.ndarray, n_steps: int,
             device: torch.device) -> np.ndarray:
    """Autonomously roll the model out for ``n_steps`` from a single initial state.

    Returns the predicted trajectory in **standardized** coordinates ``(n_steps, D)``.
    """
    model.eval()
    dtype = next(model.parameters()).dtype
    with torch.no_grad():
        x0 = torch.as_tensor(x0_norm, dtype=dtype, device=device).reshape(1, -1)
        traj = model.rollout(x0, n_steps).squeeze(0).cpu().numpy()
    return traj


def attractor_std_ratio(traj_norm: np.ndarray) -> float:
    """Mean per-dimension std of a free-run (standardized data has std 1).

    ``≈1`` = healthy attractor; ``≪1`` = collapsed to the mean (chaos ignored);
    ``≫1`` = diverged / blown up.
    """
    return float(np.nanmean(traj_norm.std(axis=0)))


def sliced_wasserstein(x: np.ndarray, y: np.ndarray, n_proj: int = 200,
                       n_quant: int = 256, seed: int = 0) -> float:
    """Sliced-Wasserstein-1 distance between two point clouds (invariant-measure distance)."""
    rng = np.random.default_rng(seed)
    d = x.shape[1]
    dirs = rng.normal(size=(n_proj, d))
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True) + 1e-12
    qs = np.linspace(0.0, 1.0, n_quant)
    total = 0.0
    for u in dirs:
        total += np.mean(np.abs(np.quantile(x @ u, qs) - np.quantile(y @ u, qs)))
    return float(total / n_proj)


def power_spectrum_distance(traj_a: np.ndarray, traj_b: np.ndarray) -> float:
    """RMS distance between (log) power spectra, averaged over dimensions."""
    def log_psd(x: np.ndarray) -> np.ndarray:
        x = x - x.mean(axis=0, keepdims=True)
        p = np.abs(np.fft.rfft(x, axis=0)) ** 2
        return np.log(p.mean(axis=1) + 1e-12)
    la, lb = log_psd(traj_a), log_psd(traj_b)
    n = min(len(la), len(lb))
    return float(np.sqrt(np.mean((la[:n] - lb[:n]) ** 2)))


def z_maxima(traj_phys: np.ndarray, dim: int = 2) -> np.ndarray:
    """Successive local maxima of one coordinate — the Lorenz return-map observable."""
    z = traj_phys[:, dim]
    is_max = (z[1:-1] > z[:-2]) & (z[1:-1] > z[2:])
    return z[1:-1][is_max]


def valid_prediction_time(model: WorldModel, x0_norm: np.ndarray, true_future_norm: np.ndarray,
                          dt: float, lyap: float, device: torch.device,
                          threshold: float = 0.4) -> float:
    """Time (in **Lyapunov times**) until the free-run diverges past ``threshold``.

    Error is normalized by the attractor RMS; VPT $=\\lambda\\cdot t_{\\text{valid}}$.
    """
    horizon = len(true_future_norm)
    pred = free_run(model, x0_norm, horizon, device)
    attractor_rms = float(np.sqrt((true_future_norm ** 2).sum(axis=1).mean())) + 1e-12
    err = np.linalg.norm(pred - true_future_norm, axis=1) / attractor_rms
    bad = np.where(~np.isfinite(err) | (err > threshold))[0]
    steps = int(bad[0]) if bad.size else horizon
    return float(steps * dt * lyap)


# ==============================================================================
# from notebook cell: def chaos_metrics(
# ==============================================================================
def chaos_metrics(model: WorldModel, cfg: Config, device: torch.device,
                  true_cloud_norm: np.ndarray, eval_ics: np.ndarray,
                  true_futures_norm: np.ndarray, lyap: float,
                  n_freerun: int = 4000, burn_in: int = 500, seed: int = 0) -> Dict[str, object]:
    """Full chaos-fidelity metric bundle for one trained model (uses its free-run)."""
    traj = free_run(model, eval_ics[0], n_freerun + burn_in, device)[burn_in:]
    finite = bool(np.isfinite(traj).all())
    out: Dict[str, object] = {"free_run_finite": finite}
    if finite:
        sub = true_cloud_norm[np.random.default_rng(seed).integers(0, len(true_cloud_norm), 4000)]
        out["std_ratio"] = attractor_std_ratio(traj)
        out["sliced_W"] = sliced_wasserstein(traj, sub, seed=seed)
        out["psd_dist"] = power_spectrum_distance(traj, sub)
    else:
        out.update(std_ratio=np.nan, sliced_W=np.nan, psd_dist=np.nan)
    vpts = [valid_prediction_time(model, ic, fut, cfg.dt, lyap, device)
            for ic, fut in zip(eval_ics, true_futures_norm)]
    out["VPT_lyap"] = float(np.mean(vpts))
    out["trajectory_norm"] = traj
    return out


def compare_dynamical_fidelity(
    models: Dict[str, WorldModel], cfg: Config, device: torch.device,
    test_norm: np.ndarray, lyap: float, n_ic: int = 16, vpt_horizon: int = 300, seed: int = 0,
    reload_ckpt: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, Dict[str, object]]]:
    """Assemble the dynamical-fidelity table + per-model free-run trajectories.

    Set ``reload_ckpt=False`` when the passed models are already trained/loaded (e.g. the
    multi-seed loop), to avoid clobbering them with a stale ``{name}_best.pt`` of a different
    architecture.
    """
    rng = np.random.default_rng(seed)
    true_cloud = test_norm.reshape(-1, test_norm.shape[-1])
    n_traj, t_len, _ = test_norm.shape
    ics, futs = [], []
    for _ in range(n_ic):
        ti, si = rng.integers(n_traj), rng.integers(0, t_len - vpt_horizon - 1)
        ics.append(test_norm[ti, si])
        futs.append(test_norm[ti, si + 1: si + 1 + vpt_horizon])
    ics, futs = np.stack(ics), np.stack(futs)

    rows, artifacts = [], {}
    for name, model in models.items():
        ckpt = Path(cfg.out_dir) / f"{name}_best.pt"
        if reload_ckpt and ckpt.exists():
            model.load_state_dict(torch.load(ckpt, map_location=device)["model_state"])
        m = chaos_metrics(model, cfg, device, true_cloud, ics, futs, lyap, seed=seed)
        artifacts[name] = m
        rows.append({"model": name, "free_run_finite": m["free_run_finite"],
                     "std_ratio": m["std_ratio"], "sliced_W": m["sliced_W"],
                     "psd_dist": m["psd_dist"], "VPT_lyap": m["VPT_lyap"]})
    # Reference row for the ground-truth attractor (sanity: std_ratio≈1, distances≈0).
    true_traj = test_norm[0]
    rows.append({"model": "TRUE_lorenz", "free_run_finite": True,
                 "std_ratio": attractor_std_ratio(true_traj),
                 "sliced_W": sliced_wasserstein(true_traj, true_cloud[:4000], seed=seed),
                 "psd_dist": 0.0, "VPT_lyap": np.inf})
    return pd.DataFrame(rows).set_index("model"), artifacts


# ==============================================================================
# from notebook cell: def sliced_wasserstein_torch(
# ==============================================================================
def sliced_wasserstein_torch(x: torch.Tensor, y: torch.Tensor, n_proj: int = 64) -> torch.Tensor:
    """Differentiable sliced-Wasserstein-1 distance between two point clouds (invariant-measure loss).

    Matches *1-D marginals* (variance, projected histograms) — but is blind to global topology.
    """
    dirs = torch.randn(n_proj, x.shape[1], dtype=x.dtype, device=x.device)
    dirs = dirs / dirs.norm(dim=1, keepdim=True).clamp_min(1e-12)
    xp, yp = x @ dirs.T, y @ dirs.T
    n = min(xp.shape[0], yp.shape[0])
    return (torch.sort(xp, dim=0).values[:n] - torch.sort(yp, dim=0).values[:n]).abs().mean()


def gaussian_mmd(x: torch.Tensor, y: torch.Tensor,
                 bandwidths: Sequence[float] = (0.1, 0.2, 0.5, 1.0, 2.0)) -> torch.Tensor:
    """Squared MMD with a multi-bandwidth Gaussian kernel — a **shape-aware** (joint-density)
    distribution loss. Unlike sliced-Wasserstein it sees clustering / local structure (the
    small bandwidths resolve the attractor's *lobes*), so it can constrain topology, not just
    marginals. ``x, y`` are ``(N, D)`` clouds (subsample for the O(N²) kernel)."""
    def k(a, b):
        d2 = torch.cdist(a, b) ** 2
        return sum(torch.exp(-d2 / (2.0 * s * s)) for s in bandwidths)
    return k(x, x).mean() + k(y, y).mean() - 2.0 * k(x, y).mean()


def energy_distance(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    """Differentiable energy distance (parameter-free shape-aware distribution loss)."""
    return (2.0 * torch.cdist(x, y).mean()
            - torch.cdist(x, x).mean() - torch.cdist(y, y).mean())


def invariant_measure_loss(st: torch.Tensor, data: torch.Tensor, kind: str = "sw",
                           n_proj: int = 64, n_pairs: int = 512) -> torch.Tensor:
    """Dispatch the invariant-measure loss between a model free-run cloud ``st`` and the data
    cloud ``data``. ``kind``: ``"sw"`` (marginals), ``"mmd"`` or ``"energy"`` (joint/topology)."""
    if kind == "sw":
        idx = torch.randint(0, data.shape[0], (st.shape[0],), device=st.device)
        return sliced_wasserstein_torch(st, data[idx], n_proj=n_proj)
    xs = st[torch.randint(0, st.shape[0], (min(n_pairs, st.shape[0]),), device=st.device)]
    ys = data[torch.randint(0, data.shape[0], (n_pairs,), device=st.device)]
    return gaussian_mmd(xs, ys) if kind == "mmd" else energy_distance(xs, ys)


def latent_spectrum_and_ky(model: WorldModel, x0_norm: np.ndarray, device: torch.device,
                           n_steps: int = 1500, warmup: int = 300) -> Tuple[np.ndarray, float]:
    """Full autonomous latent-flow Lyapunov spectrum + Kaplan–Yorke dimension."""
    z0 = model.encode_latent(torch.as_tensor(x0_norm, dtype=next(model.parameters()).dtype,
                                             device=device).reshape(1, -1)).squeeze(0)
    spec = lyapunov_spectrum_from_step(model.latent_step, z0, n_steps, model.cfg.dt, warmup,
                                       n_exponents=z0.numel()).cpu().numpy()
    cs = np.cumsum(spec)
    j = np.where(cs >= 0)[0]
    if len(j) == 0:
        ky = 0.0
    else:
        j = int(j[-1])
        ky = float(j + 1) if j + 1 >= len(spec) else float(j + 1 + cs[j] / abs(spec[j + 1]))
    return spec, ky


def train_invariant_measure(model: GrowingTeichmullerWorldModel, train_loader: DataLoader,
                            data_cloud: np.ndarray, cfg: Config, device: torch.device,
                            lam_invmeas: float = 2.0, free_steps: int = 150, tbptt: int = 30,
                            epochs: int = 60, warmup_epochs: int = 30, ramp_epochs: int = 40,
                            n_proj: int = 64, free_batch: int = 64, sw_every: int = 1,
                            loss_kind: str = "sw") -> None:
    """Fine-tune with MSE + a long free-run invariant-measure loss.

    ``loss_kind``: ``"sw"`` (sliced-Wasserstein — matches marginals), or the shape-aware
    ``"mmd"`` / ``"energy"`` (joint density — can constrain the attractor's lobe topology).

    Fully activates the growing structure first (so the torus fiber is live), then trains the
    autonomous attractor to match the data via a *long* free-run with truncated back-prop.

    **Curriculum:** MSE-only for ``warmup_epochs`` (establish a sensible short-horizon model),
    then linearly ramp the invariant-measure weight over ``ramp_epochs``. During warm-up the
    expensive free-run is skipped.
    """
    for k in range(model.max_extra):           # mature all curves (fiber + contracting) up front
        model.born[k] = 1.0
        model.birth_epoch[k] = 0.0
    model.set_epoch(model.gcfg.ramp_epochs + 1)
    model.to(device)
    dtype = next(model.parameters()).dtype
    data = torch.as_tensor(data_cloud, dtype=dtype, device=device)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    for ep in tqdm(range(epochs), desc="[hitchin] invariant-measure"):
        lam_eff = lam_invmeas * min(1.0, max(0.0, (ep - warmup_epochs) / max(ramp_epochs, 1)))
        model.train()
        g = model.gates()
        for b, (x0, target) in enumerate(train_loader):
            x0, target = x0.to(device, dtype=dtype), target.to(device, dtype=dtype)
            loss = multistep_mse(model.rollout(x0, cfg.horizon), target)
            if lam_eff > 0.0 and (b % sw_every == 0):    # free-run only when ramping (subset → cheap)
                xs = x0[:free_batch]                     # SW needs a sample cloud, not the full batch
                tau, ell = model.proxy.raw_to_fn(model.encoder(xs))
                states: List[torch.Tensor] = []
                for k in range(free_steps):
                    tau, ell = model._fn_step(tau, ell, g)
                    states.append(model.decoder(model._features(tau, ell, g)))
                    if (k + 1) % tbptt == 0:
                        tau, ell = tau.detach(), ell.detach()
                st = torch.stack(states, dim=1).reshape(-1, cfg.state_dim)
                loss = loss + lam_eff * invariant_measure_loss(st, data, kind=loss_kind, n_proj=n_proj)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), cfg.grad_clip)
            opt.step()

