"""Fixed anchor folds for the butterfly problem (iteration 6).

Verified pathology of the stock anchor: τ₀ → rate·τ₀ − T·round(rate·τ₀/T) with
rate = e^{λ* dt} ≈ 1.009 has a thin flip-band attractor: |τ₀| climbs to the fold
boundary in ~130 steps, then alternates sign every ~1.5 steps forever inside
|τ₀| ∈ [0.991, 1.0] (666 sign flips / 1000 steps). λ_max = λ* still holds (the
slope is constant), but the "chaos" lives in a band of width 0.9% of the circle:
with raw features it decodes as lobe flapping, and with periodic features
sin(2πτ₀/T) ≈ const there — the chaotic coordinate becomes invisible and the
free-run collapses to the fiber limit cycle (iteration 5).

Two replacements, both keeping ∂τ₀'/∂τ₀ pinned by construction:

* ``BetaAnchorModel`` — β-transformation fold: τ₀ → rate·τ₀ mod T into [0, T).
  Overflow reinjects near 0 (not at the boundary), giving an ergodic sawtooth
  sweep of the full circle; λ_max = λ* exactly, per step, as before.

* ``SuspensionModel`` — geometric-Lorenz template as a mapping torus: the fiber
  phase φ advances at a FIXED rate (one revolution = T_ORBIT steps = one lobe
  spiral) and the base coordinate x = τ₀/(T/2) ∈ [−1, 1] is FROZEN except once
  per revolution, when the piecewise-expanding Lorenz map
      f(x) = s·x − sign(x)·(s − 1),   s = e^{λ*·dt·T_ORBIT} ≈ 1.96 < 2
  fires. sign(x) is the lobe bit, |x| the spiral radius; the return-map Jacobian
  is s once per T_ORBIT steps, so λ_max = log(s)/(T_ORBIT·dt) = λ* exactly.
  Lobe-switch probability per revolution ≈ (s−1)/s ≈ 0.49 → mean dwell ≈ 2
  revolutions ≈ 150 steps (true Lorenz: ~2.4 revolutions, 179 steps).
"""
from __future__ import annotations

import math

import torch

from periodic_model import PeriodicGrowingModel


class BetaAnchorModel(PeriodicGrowingModel):
    """Periodic-feature model with a β-map (floor-mod) anchor fold."""

    def _fn_step(self, tau, ell, g):
        tau_in = tau
        a, b, c = self._generators(tau, ell, g)
        p, q, r, s = self.proxy.sl2_exp(a, b, c, self.cfg.dt)
        tau, ell = self.proxy.mobius(tau, ell, p, q, r, s)
        if self.gcfg.anchor_expansion:
            rate = math.exp(self.gcfg.lyap_target * self.cfg.dt)
            period = self.gcfg.anchor_period
            nf = self.gcfg.n_fiber
            x = rate * tau_in[..., :1]
            new_tau = [x - period * torch.floor(x / period)]     # β-map fold into [0, T)
            new_ell = [torch.ones_like(ell[..., :1])]
            if nf > 0:
                base = tau_in[..., :1]
                emb = torch.cat([torch.cos(2 * math.pi * base / period),
                                 torch.sin(2 * math.pi * base / period)], dim=-1)
                omega = self.gcfg.fiber_scale * torch.tanh(self.fiber_coupling(emb))
                frate = math.exp(self.gcfg.fiber_anchor_rate * self.cfg.dt)
                for k in range(nf):
                    phi = frate * tau_in[..., 1 + k:2 + k] + omega[..., k:k + 1]
                    new_tau.append(phi - period * torch.floor(phi / period))
                    new_ell.append(torch.ones_like(ell[..., :1]))
            rest = 1 + nf
            tau = torch.cat(new_tau + [tau[..., rest:]], dim=-1)
            ell = torch.cat(new_ell + [ell[..., rest:]], dim=-1)
        return tau, ell


class SuspensionModel(PeriodicGrowingModel):
    """Mapping-torus anchor: fixed-rate fiber phase + once-per-revolution Lorenz fold."""

    T_ORBIT = 75    # steps per fiber revolution ≈ true Lorenz lobe-spiral period

    def __init__(self, cfg, growth_cfg, max_gen: float = 3.0) -> None:
        if growth_cfg.n_fiber != 1:
            raise ValueError("SuspensionModel needs exactly one fiber (the roof phase)")
        super().__init__(cfg, growth_cfg, max_gen)

    def _fn_step(self, tau, ell, g):
        tau_in = tau
        a, b, c = self._generators(tau, ell, g)
        p, q, r, s_m = self.proxy.sl2_exp(a, b, c, self.cfg.dt)
        tau, ell = self.proxy.mobius(tau, ell, p, q, r, s_m)
        if self.gcfg.anchor_expansion:
            period = self.gcfg.anchor_period
            half = 0.5 * period
            slope = math.exp(self.gcfg.lyap_target * self.cfg.dt * self.T_ORBIT)
            # normalize (encoder output is unconstrained; folds are zero-grad shifts a.e.)
            x = tau_in[..., :1] / half
            x = x - 2.0 * torch.round(x / 2.0)               # lobe coordinate in [-1, 1]
            phi = tau_in[..., 1:2]
            phi = phi - period * torch.floor(phi / period)   # roof phase in [0, T)
            phi_new = phi + period / self.T_ORBIT
            wrap = phi_new >= period
            phi_new = torch.where(wrap, phi_new - period, phi_new)
            fx = slope * x - torch.sign(x) * (slope - 1.0)   # Lorenz map, |f| <= 1 for s < 2
            x_new = torch.where(wrap, fx, x)
            new_tau = [half * x_new, phi_new]
            one = torch.ones_like(ell[..., :1])
            tau = torch.cat(new_tau + [tau[..., 2:]], dim=-1)
            ell = torch.cat([one, one, ell[..., 2:]], dim=-1)
        return tau, ell


class VariableSuspensionModel(SuspensionModel):
    """Suspension with a state-dependent roof: T(x) = T0 + T1·min(−log|x|, LOG_CAP).

    The true geometric-Lorenz return time diverges logarithmically at the stable
    manifold (x = 0): passes near the saddle — exactly the ones that precede lobe
    switches — take longest. A fixed roof (T_ORBIT = 75) caps mean dwell at ~140
    steps; a log roof lengthens precisely the switching episodes. λ_max is still
    pinned per return: slope s = e^{λ*·dt·T_BAR} with T_BAR = E_μ[T(x)] under the
    fold map's invariant measure (calibrated offline; s < 2 needs T_BAR < 77).
    """

    T0 = 62.0        # floor of the roof function (steps)
    T1 = 14.0        # log-divergence strength
    LOG_CAP = 3.0    # clamp −log|x| (x within e^{-3} of the cusp)
    T_BAR = 75.0     # E_μ[T(x)] — set by calibration; determines the fold slope

    def _fn_step(self, tau, ell, g):
        tau_in = tau
        a, b, c = self._generators(tau, ell, g)
        p, q, r, s_m = self.proxy.sl2_exp(a, b, c, self.cfg.dt)
        tau, ell = self.proxy.mobius(tau, ell, p, q, r, s_m)
        if self.gcfg.anchor_expansion:
            period = self.gcfg.anchor_period
            half = 0.5 * period
            slope = math.exp(self.gcfg.lyap_target * self.cfg.dt * self.T_BAR)
            x = tau_in[..., :1] / half
            x = x - 2.0 * torch.round(x / 2.0)               # lobe coordinate in [-1, 1]
            phi = tau_in[..., 1:2]
            phi = phi - period * torch.floor(phi / period)   # roof phase in [0, T)
            ax = torch.clamp(x.abs(), min=math.exp(-self.LOG_CAP))
            t_orb = self.T0 - self.T1 * torch.log(ax)        # T(x): long near the cusp
            phi_new = phi + period / t_orb
            wrap = phi_new >= period
            phi_new = torch.where(wrap, phi_new - period, phi_new)
            fx = slope * x - torch.sign(x) * (slope - 1.0)
            x_new = torch.where(wrap, fx, x)
            one = torch.ones_like(ell[..., :1])
            tau = torch.cat([half * x_new, phi_new, tau[..., 2:]], dim=-1)
            ell = torch.cat([one, one, ell[..., 2:]], dim=-1)
        return tau, ell


class CuspSuspensionModel(SuspensionModel):
    """Suspension over a cusp (geometric-Lorenz) return map instead of a linear fold.

    f(x) = sign(x)·(B·|x|^RHO − 1): |f'| → ∞ at the cusp, f(0±) = ∓1 (deep
    opposite-wing excursions, as in the data), f(±1) = ±(B−1) (non-onto kneading).
    A piecewise-LINEAR fold cannot beat mean dwell ≈ 2 returns at pinned λ (its
    slope is forced by λ*, and the slope forces switch probability ≈ 0.49); the
    cusp map's invariant measure weights the steep region, dropping switch
    probability to 0.416 → pure-map dwell 179.3 steps ≡ true Lorenz 179.3.
    Cost: λ_max is now pinned by MEASURE-CALIBRATED constants (RHO, B, T0, T1
    solved offline so E_μ[log|f'|] = λ*·dt·E_μ[T(x)]), not exact-by-construction.
    Roof as in VariableSuspensionModel: T(x) = T0 + T1·min(−log|x|, LOG_CAP).
    MAP_EPS must be tiny: a larger clamp creates a flat spot at the cusp and the
    dynamics collapses onto superattracting periodic orbits (verified).
    """

    RHO = 0.52
    B = 1.95
    T0 = 55.8        # calibrated with T1, RHO, B against the invariant measure
    T1 = 14.0
    LOG_CAP = 4.0    # roof clamp only
    MAP_EPS = math.exp(-12.0)   # cusp clamp (≈6e-6): gradient bound, no flat spot

    def _fn_step(self, tau, ell, g):
        tau_in = tau
        a, b, c = self._generators(tau, ell, g)
        p, q, r, s_m = self.proxy.sl2_exp(a, b, c, self.cfg.dt)
        tau, ell = self.proxy.mobius(tau, ell, p, q, r, s_m)
        if self.gcfg.anchor_expansion:
            period = self.gcfg.anchor_period
            half = 0.5 * period
            x = tau_in[..., :1] / half
            x = x - 2.0 * torch.round(x / 2.0)               # lobe coordinate in [-1, 1]
            phi = tau_in[..., 1:2]
            phi = phi - period * torch.floor(phi / period)   # roof phase in [0, T)
            ax = x.abs()
            mlog = torch.clamp(-torch.log(torch.clamp(ax, min=self.MAP_EPS)),
                               max=self.LOG_CAP)
            t_orb = self.T0 + self.T1 * mlog
            phi_new = phi + period / t_orb
            wrap = phi_new >= period
            phi_new = torch.where(wrap, phi_new - period, phi_new)
            sgn = torch.sign(x)
            fx = sgn * (self.B * torch.clamp(ax, min=self.MAP_EPS) ** self.RHO - 1.0)
            x_new = torch.where(wrap, fx, x)
            one = torch.ones_like(ell[..., :1])
            tau = torch.cat([half * x_new, phi_new, tau[..., 2:]], dim=-1)
            ell = torch.cat([one, one, ell[..., 2:]], dim=-1)
        return tau, ell


class CuspFixedSuspensionModel(CuspSuspensionModel):
    """Cusp fold with a FIXED roof — the ship candidate.

    Iter-20 finding: the variable roof contributed nothing to dwell (dwell-in-returns
    is a property of the fold map alone) and its non-uniform phase speed fought the
    phase-alignment loss (removing the loss brought back the tube pathology). Fixed
    roof T = E_μ[log|f'|]/(λ*·dt) = 74.66 steps: pure-map dwell 179.0 (true 179.3),
    λ_max = 0.9005 exact under the fold's invariant measure, uniform phase advance
    fully compatible with lam_phase.
    """

    T0 = 74.66
    T1 = 0.0
