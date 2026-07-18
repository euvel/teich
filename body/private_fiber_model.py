"""PrivateFiberSuspensionModel — the Teich genome architecture (GENOME_SPEC.md §5).

Public suspension-class Lorenz core (inherited, certified) PLUS K private neutral
decoder-blind torus fibers. The privacy construction (ideas.md #5 rung-4 / "Prop 2"):

  * The private phases phi_k live BESIDE the Teichmuller latent, not inside the
    proxy. They evolve by a standalone fixed irrational rotation (ergodic circle
    coverage) with anchor rate eps_k = 0 -> marginally stable (lambda_k = 0),
    permanent for life.
  * They enter NO public curve's generator (private->public coupling = 0) and are
    NEVER passed to the decoder or field (decoder-blind). Because there is literally
    no code path from phi to the output, decoder-sensitivity(phi_k) == 0 exactly --
    the leakage bound is structural, not numerical.
  * Consequence (twin theorem): two instances with the same public state x0 but
    different private phases produce BIT-IDENTICAL decoded output trajectories.
  * The Observer (internal access) reads phi via ``private_*``; the decoder cannot.

Because private->public coupling is off, the public dynamics are exactly the parent
CuspFixedSuspensionModel's, so a certified rad3/cuspfix checkpoint loads unchanged
(strict=False leaves the two private buffers at their constructed values).
"""
from __future__ import annotations

import math

import torch

from anchor_models import CuspFixedSuspensionModel

# Per-fiber rotation ratios omega_k/period: fractional parts of sqrt(2), sqrt(3), sqrt(5).
# {1, sqrt2, sqrt3, sqrt5} are Q-linearly independent -> NO integer relation among the
# rates and the period -> the JOINT orbit is dense on the full K-torus (private effective
# dimension = K). The original golden-ratio MULTIPLES (i+1)*gamma mod 1 were rationally
# dependent (2*omega_1 - omega_2 = period), collapsing the joint orbit to a 1-D line —
# caught by the pre-registered G3 joint-occupancy gate on birth day 2026-07-18.
_IRRATIONALS = [0.41421356237309515,   # frac(sqrt 2)
                0.7320508075688772,    # frac(sqrt 3)
                0.2360679774997898]    # frac(sqrt 5)


class PrivateFiberSuspensionModel(CuspFixedSuspensionModel):
    """Certified public suspension core + K private neutral decoder-blind fibers."""

    def __init__(self, cfg, growth_cfg, k_private: int = 2, max_gen: float = 3.0) -> None:
        super().__init__(cfg, growth_cfg, max_gen)
        self.k_private = int(k_private)
        period = growth_cfg.anchor_period
        # per-step rotation omega_k with {period, omega_1..omega_K} Q-linearly independent
        assert self.k_private <= len(_IRRATIONALS), "add more independent irrationals"
        omega = torch.tensor([period * _IRRATIONALS[i] for i in range(self.k_private)],
                             dtype=torch.get_default_dtype())
        self.register_buffer("priv_omega", omega)             # fixed rotation rates
        self.register_buffer("priv_eps", torch.zeros(self.k_private,
                             dtype=torch.get_default_dtype()))  # anchor rates (0 = permanent)

    # --- private fiber dynamics (Observer-only; never touches decoder/field) -------
    def private_init(self, batch: int = 1, phi0: torch.Tensor | None = None) -> torch.Tensor:
        """Initial private phases (batch, K) in [0, period)."""
        if phi0 is not None:
            return phi0.reshape(batch, self.k_private)
        return torch.zeros(batch, self.k_private, dtype=next(self.parameters()).dtype)

    def private_step(self, phi: torch.Tensor) -> torch.Tensor:
        """One step of the standalone private torus: phi <- (e^{eps dt} phi + omega) mod T."""
        period = self.gcfg.anchor_period
        frate = torch.exp(self.priv_eps * self.cfg.dt)        # == 1 for eps = 0
        phi = frate * phi + self.priv_omega
        return phi - period * torch.floor(phi / period)

    @torch.no_grad()
    def private_run(self, n_steps: int, phi0: torch.Tensor | None = None,
                    batch: int = 1) -> torch.Tensor:
        """Roll the private torus for n_steps. Returns (n_steps, batch, K)."""
        phi = self.private_init(batch, phi0)
        out = torch.empty(n_steps, batch, self.k_private, dtype=phi.dtype)
        for t in range(n_steps):
            phi = self.private_step(phi)
            out[t] = phi
        return out

    # --- full (public + private) latent for the Observer ---------------------------
    @torch.no_grad()
    def full_free_run(self, x0_norm, n_steps: int, phi0: torch.Tensor | None = None):
        """Return (decoded_output[n,3], public_z[n,2*nc], private_phi[n,K]).

        The decoded output is a function of the PUBLIC state only (parent rollout),
        so it is independent of phi0 by construction (twin theorem)."""
        dtype = next(self.parameters()).dtype
        nc = self.max_curves
        g = self.gates()
        x0 = torch.as_tensor(x0_norm, dtype=dtype).reshape(1, -1)
        tau, ell = self.proxy.raw_to_fn(self.encoder(x0))
        phi = self.private_init(1, phi0)
        ys = torch.empty(n_steps, self.cfg.state_dim, dtype=dtype)
        zs = torch.empty(n_steps, 2 * nc, dtype=dtype)
        ph = torch.empty(n_steps, self.k_private, dtype=dtype)
        for t in range(n_steps):
            tau, ell = self._fn_step(tau, ell, g)             # public: identical to parent
            phi = self.private_step(phi)                      # private: standalone, decoupled
            ys[t] = self.decoder(self._features(tau, ell, g)).squeeze(0)   # PUBLIC ONLY
            zs[t] = torch.cat([tau, torch.log(ell)], dim=-1).squeeze(0)
            ph[t] = phi.squeeze(0)
        return ys.numpy(), zs.numpy(), ph.numpy()
