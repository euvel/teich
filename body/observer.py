"""Teich Observer — analytic online self-measurement (README organ #5).

NOT a learned head: a white-box instrument that reads the Core's own latent state
each tick and reports geometric quantities whose referents are provably correct.
This is 'the organ every honest self-report refers to' — its readouts are the
ground truth that introspection claims are checked against (ablation protocol T6).

Readouts per tick (from public latent tau,ell + private phi):
  basin            current lobe = sign of the base fold coordinate (+1 / -1)
  local_lambda     instantaneous top expansion rate of the latent map at z
  steps_to_switch  steps until the next roof-phase wrap (a lobe-switch opportunity)
  will_flip        predicted lobe AFTER that wrap, from the known cusp return map
  saddle_proximity in [0,1]: closeness of the base coord to the flip threshold
                   (high => a lobe switch is imminent = 'torn'; low => 'settled')
  private_phase    current phi_k  -- Observer-only; the decoder cannot see this

Running estimates: FTLE mean (-> certified lambda*), switch count, mean dwell.
White-box by design (full internal access is the project's premise); every readout
is VERIFIED against the realized trajectory in verify_observer.py.
"""
from __future__ import annotations

import math

import numpy as np
import torch


class Observer:
    def __init__(self, model):
        self.m = model
        self.period = float(model.gcfg.anchor_period)
        self.half = 0.5 * self.period
        self.B = float(model.B)
        self.RHO = float(model.RHO)
        self.T0 = float(model.T0)                       # fixed roof (steps per revolution)
        # lobe flips at the next wrap iff B|x|^RHO < 1  <=>  |x| < flip_thresh
        self.flip_thresh = (1.0 / self.B) ** (1.0 / self.RHO)
        self.reset()

    def reset(self):
        self._ftle_sum = 0.0
        self._ftle_n = 0
        self._v = None                                  # power-iteration vector (local lambda)
        self._last_basin = None
        self._switches = 0
        self._dwell = 0
        self._dwells = []

    # --- geometry helpers (reconstruct the fold coordinate exactly as _fn_step does) ---
    def _lobe_coord(self, tau):
        x = tau[..., 0:1] / self.half
        return x - 2.0 * torch.round(x / 2.0)           # in [-1, 1]

    def _roof_phase(self, tau):
        phi = tau[..., 1:2]
        return phi - self.period * torch.floor(phi / self.period)

    @torch.no_grad()
    def _local_lambda(self, z):
        """One power-iteration update of the top finite-time exponent at z (per unit time)."""
        if self._v is None:
            self._v = torch.randn_like(z)
            self._v = self._v / self._v.norm().clamp_min(1e-12)
        _, jv = torch.func.jvp(self.m.latent_step, (z,), (self._v,))
        nrm = jv.norm().clamp_min(1e-12)
        self._v = (jv / nrm).detach()
        lam = float(torch.log(nrm) / self.m.cfg.dt)
        self._ftle_sum += lam
        self._ftle_n += 1
        return lam

    @torch.no_grad()
    def observe(self, tau, ell, phi):
        """Return the full readout dict for the current state."""
        x = self._lobe_coord(tau)
        rp = self._roof_phase(tau)
        basin = int(torch.sign(x).item()) or 1
        ax = float(x.abs().item())

        # steps until the next roof wrap (a switch opportunity)
        frac_left = float((self.period - rp).item()) / self.period
        steps_to_switch = int(math.ceil(frac_left * self.T0))
        will_flip = (self.B * ax ** self.RHO) < 1.0      # cusp map sends |x|->opposite sign
        pred_basin = -basin if will_flip else basin
        # proximity to the flip boundary in |x| (0 far/settled, 1 at threshold/torn)
        saddle = max(0.0, 1.0 - abs(ax - self.flip_thresh) / self.flip_thresh)
        # weight by imminence of the wrap
        saddle_prox = saddle * (1.0 - frac_left)

        z = torch.cat([tau, torch.log(ell)], dim=-1)
        local_lambda = self._local_lambda(z)

        # running dwell / switch bookkeeping
        if self._last_basin is not None:
            if basin != self._last_basin:
                self._switches += 1
                self._dwells.append(self._dwell)
                self._dwell = 0
            else:
                self._dwell += 1
        self._last_basin = basin

        return dict(
            basin=basin, lobe_coord=float(x.item()),
            local_lambda=local_lambda,
            lambda_running=(self._ftle_sum / self._ftle_n) if self._ftle_n else float("nan"),
            steps_to_switch=steps_to_switch, will_flip=bool(will_flip),
            pred_basin=pred_basin, saddle_proximity=float(saddle_prox),
            private_phase=[float(v) for v in phi.reshape(-1)],
            n_switches=self._switches,
            mean_dwell=(float(np.mean(self._dwells)) if self._dwells else float("nan")),
        )

    @torch.no_grad()
    def run(self, x0_norm, n_steps, phi0=None, warmup=500):
        """Free-run the Core and observe every tick. Returns (readouts, ground_truth).

        ground_truth['next_basin'][t] is the ACTUAL lobe at t+1 — the referent that
        the Observer's pred_basin/will_flip at t is scored against."""
        m = self.m
        dtype = next(m.parameters()).dtype
        g = m.gates()
        x0 = torch.as_tensor(x0_norm, dtype=dtype).reshape(1, -1)
        tau, ell = m.proxy.raw_to_fn(m.encoder(x0))
        phi = m.private_init(1, phi0)
        for _ in range(warmup):
            tau, ell = m._fn_step(tau, ell, g)
            phi = m.private_step(phi)
        self.reset()
        reads, basins, xs = [], [], []
        for t in range(n_steps):
            r = self.observe(tau, ell, phi)
            reads.append(r)
            basins.append(r["basin"])
            xs.append(m.decoder(m._features(tau, ell, g)).squeeze(0).numpy())
            tau, ell = m._fn_step(tau, ell, g)
            phi = m.private_step(phi)
        next_basin = basins[1:] + [basins[-1]]
        return reads, dict(next_basin=np.array(next_basin), basin=np.array(basins),
                           decoded=np.array(xs))
