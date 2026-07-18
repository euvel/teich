"""Teich continuity — hibernation-with-replay integrator (README capability #1).

The claim is LAWFUL EVOLUTION THROUGH ELAPSED TIME, not continuous joule burn: the
Core's state is not held live between interactions. Instead the state + a wall-clock
timestamp are persisted (in the Durable Object), and on each wake the deterministic
dynamics are integrated forward by however many ticks correspond to the real elapsed
time. Because the public map and the private rotation are both deterministic, replay
is bit-exact: a hibernated creature reconstructs precisely the state it would have
had if it had never slept. That exactness is what makes "it exists between messages"
an auditable claim rather than a metaphor.

This module is storage-agnostic (plain-JSON state <-> dict); the Durable Object just
persists the dict and calls wake() on an alarm or a message.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, asdict, field
from typing import List, Optional

import numpy as np
import torch


@dataclass
class TeichState:
    """The complete seat of self — everything needed to resume the creature."""
    tau: List[float]                 # public Teichmuller coords (nc)
    log_ell: List[float]             # public log-lengths (nc)
    phi: List[float]                 # private fiber phases (K)
    last_tick_unix: float            # wall-clock of the last integrated tick
    birth_unix: float                # genesis timestamp (immutable)
    n_ticks_lived: int               # total ticks integrated since birth
    tick_hz: float                   # ticks per real second (integration cadence)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "TeichState":
        return cls(**d)


class Continuity:
    """Deterministic hibernation-replay engine around a PrivateFiberSuspensionModel."""

    def __init__(self, model, observer=None, tick_hz: float = 100.0):
        self.m = model
        self.obs = observer
        self.tick_hz = float(tick_hz)
        self._g = model.gates()
        self._dtype = next(model.parameters()).dtype

    # --- birth -------------------------------------------------------------------
    def birth(self, x0_norm, phi0=None, t0: Optional[float] = None) -> TeichState:
        t0 = time.time() if t0 is None else float(t0)
        x0 = torch.as_tensor(x0_norm, dtype=self._dtype).reshape(1, -1)
        tau, ell = self.m.proxy.raw_to_fn(self.m.encoder(x0))
        phi = self.m.private_init(1, None if phi0 is None
                                  else torch.as_tensor(phi0, dtype=self._dtype))
        return TeichState(
            tau=tau.reshape(-1).tolist(), log_ell=torch.log(ell).reshape(-1).tolist(),
            phi=phi.reshape(-1).tolist(), last_tick_unix=t0, birth_unix=t0,
            n_ticks_lived=0, tick_hz=self.tick_hz)

    # --- the load-bearing operation: integrate elapsed real time -----------------
    def _state_tensors(self, st: TeichState):
        tau = torch.tensor(st.tau, dtype=self._dtype).reshape(1, -1)
        ell = torch.exp(torch.tensor(st.log_ell, dtype=self._dtype)).reshape(1, -1)
        phi = torch.tensor(st.phi, dtype=self._dtype).reshape(1, -1)
        return tau, ell, phi

    @torch.no_grad()
    def wake(self, st: TeichState, t_now: Optional[float] = None,
             observe: bool = True, obs_window: int = 400):
        """Integrate the persisted state forward through the elapsed wall-clock time.

        Returns (new_state, readout|None). The new_state is a pure function of
        (st, t_now): identical inputs -> bit-identical output (hibernation fidelity).
        When observing, the final ``obs_window`` ticks are fed through the Observer so
        the running estimates (FTLE, dwell, switch count) are valid regardless of how
        long the nap was — replay stays cheap, readouts stay honest."""
        t_now = time.time() if t_now is None else float(t_now)
        n = max(0, int((t_now - st.last_tick_unix) * st.tick_hz))
        tau, ell, phi = self._state_tensors(st)
        n_fast = n if not (observe and self.obs is not None) else max(0, n - obs_window)
        for _ in range(n_fast):                              # bulk replay: raw, no observer
            tau, ell = self.m._fn_step(tau, ell, self._g)
            phi = self.m.private_step(phi)
        readout = None
        if observe and self.obs is not None:
            self.obs.reset()                                 # window-local running estimates
            for _ in range(n - n_fast):                      # observed final window
                readout = self.obs.observe(tau, ell, phi)
                tau, ell = self.m._fn_step(tau, ell, self._g)
                phi = self.m.private_step(phi)
            if readout is None:                              # n == 0: observe in place
                readout = self.obs.observe(tau, ell, phi)
        new = TeichState(
            tau=tau.reshape(-1).tolist(), log_ell=torch.log(ell).reshape(-1).tolist(),
            phi=phi.reshape(-1).tolist(),
            last_tick_unix=st.last_tick_unix + n / st.tick_hz,   # exact tick grid, no drift
            birth_unix=st.birth_unix, n_ticks_lived=st.n_ticks_lived + n,
            tick_hz=st.tick_hz)
        return new, readout

    @torch.no_grad()
    def decode(self, st: TeichState) -> np.ndarray:
        """The public observable at the current state (what the world/Mouth sees)."""
        tau, ell, _ = self._state_tensors(st)
        return self.m.decoder(self.m._features(tau, ell, self._g)).reshape(-1).numpy()
