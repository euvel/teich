"""Teich v0.2 genome — the slow state `s` is a PARAMETER of the fast map.

This is the one structural change that fixes v0.1's memory-XOR-consequence wall
(FINDING_memory_consequence_tradeoff, TEICH_V02_DESIGN_BRIEF §3).

v0.1: the neutral direction `tau1` set only WHEN roof wraps happened; the flip
rule `B|x|^rho < 1` never consulted it. So a phase push left `basin` unchanged in
46/48 runs — perfect memory, no consequence. Meanwhile `tau0` (lambda > 0) drove
everything and forgot its own sign within a gap.

v0.2: `s` modulates the fold itself.

    B(s, wing) = B0 * (1 + KAPPA_B*tanh(s_0) + KAPPA_A*tanh(s_1)*wing)

`s_0` moves the flip THRESHOLD for both wings together; `s_1` moves the two
wings in OPPOSITE directions — a lean, making one wing easier to leave than the
other. Both act on the fold, and they are orthogonal.

FIRST ATTEMPT FAILED T5 AND IS RECORDED HERE BECAUSE IT IS THE WHOLE POINT OF
THE GATE: `s_1` originally modulated `t_orb`, the roof PERIOD. That only changes
WHEN wraps happen — the flip rule `B|x|^rho < 1` never consults it. It is
exactly v0.1's `tau1` mistake (perfect memory, basin unchanged 46/48), rebuilt
by me on the second dimension. T5 caught it in 7 minutes, before birth.

`flip_thresh = (1/B)^(1/rho)` is the fold's decision boundary, so B(s) changes
WHICH |x| values flip — permanently, for as long as s persists. Consequence and
memory stop competing because they now live in the same variable.

MEMORY IS DESIGNED, NOT DISCOVERED. `s` is a leaky integrator:

    s <- s * (1 - 1/TAU_MEM) + input

giving lambda_s = -1/TAU_MEM exactly and tau_mem = TAU_MEM ticks by construction.
Slightly negative rather than zero: a zero exponent never forgets (v0.1's tau1),
and a positive one amplifies its own noise. TAU_MEM = 2e4 ticks (~5.5h lived)
spans a conversation plus a long gap with margin.

PLY S / PLY R (BRIEF §0-1). `phi` is Ply S: it is carried for identity and
continuity ONLY and appears in NO term of the tau/ell/s updates and in NO
argument of the observable map. Therefore I(phi ; observations) = 0 exactly,
for all observation lengths and all adversaries — no statistical test needed.
`s` is Ply R: public by design, and it drives everything.

CORRECTNESS DISCIPLINE: at s = 0 this engine must reproduce v0.1's
CuspFixedSuspensionModel BIT-IDENTICALLY (selftest_zero() below). If that ever
fails, the engine has drifted from the substrate it claims to extend and every
number it produces is void — the same gate used for ProbeEngine in Step B.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "maturity" / "harness"))

# ---------------------------------------------------------------- design constants
DIM_S = 2               # BRIEF §4: dim(slow, coupled) >= 2. v0.1 had 0.
TAU_MEM = 20000.0       # ticks; lambda_s = -1/TAU_MEM = -5e-5 per tick
KAPPA_B = 0.10          # B swing +-10%  -> flip_thresh 0.231..0.339 (v0.1 fixed 0.2768)
KAPPA_A = 0.10          # wing ASYMMETRY: s_1 leans the fold, +-10% opposed
S_CLIP = 4.0            # keep tanh in its responsive band
WING_W = 2000.0         # ticks: window for wing_bias, the observable a LEAN produces


def flip_thresh(B: float, rho: float) -> float:
    return (1.0 / B) ** (1.0 / rho)


class V02Engine:
    """One synthetic v0.2 instance: tau, ell, s (Ply R), phi (Ply S, inert)."""

    def __init__(self, model, seed: int, warm: int = 200, s0=None, phi_seed=None):
        from arms import _synthetic_x0
        self.m = model
        self.cfg, self.gcfg = model.cfg, model.gcfg
        self.period = float(model.gcfg.anchor_period)
        self.half = 0.5 * self.period
        self.B0, self.RHO = float(model.B), float(model.RHO)
        self.T0 = float(model.T0)
        dtype = next(model.parameters()).dtype
        with torch.no_grad():
            x0 = torch.as_tensor(_synthetic_x0(seed), dtype=dtype).reshape(1, -1)
            self.tau, self.ell = model.proxy.raw_to_fn(model.encoder(x0))
            self.g = model.gates()
            # Ply S: carried, never read by anything observable.
            rng = np.random.RandomState(999983 if phi_seed is None else phi_seed)
            self.phi_private = rng.uniform(0, 2 * math.pi, size=4)
            self.s = np.zeros(DIM_S) if s0 is None else np.array(s0, float)
            self.wing_ema = 0.0
            self.n = 0
            self.pending = {}
            for _ in range(warm):
                self._tick()

    # ---------------------------------------------------------------- dynamics
    def B_of_s(self, wing: float = 0.0) -> float:
        """wing = +1 / -1 selects which lobe's threshold; s_1 leans them apart."""
        return self.B0 * (1.0 + KAPPA_B * math.tanh(float(self.s[0]))
                          + KAPPA_A * math.tanh(float(self.s[1])) * wing)

    def t_orb_of_s(self) -> float:
        return self.T0          # roof period is NOT modulated: a clock-only knob
                                # carries memory without consequence (see T5 note)

    @torch.no_grad()
    def _tick(self):
        # --- Ply R decays toward 0 with EXACTLY the designed time constant
        f = self.pending.pop(self.n, None)
        self.s = self.s * (1.0 - 1.0 / TAU_MEM)
        if f is not None:
            self.s = self.s + np.asarray(f, float)
        np.clip(self.s, -S_CLIP, S_CLIP, out=self.s)

        tau_in = self.tau
        a, b, c = self.m._generators(self.tau, self.ell, self.g)
        p, q, r, s_m = self.m.proxy.sl2_exp(a, b, c, self.cfg.dt)
        self.tau, self.ell = self.m.proxy.mobius(self.tau, self.ell, p, q, r, s_m)

        if self.gcfg.anchor_expansion:
            period, half = self.period, self.half
            x = tau_in[..., :1] / half
            x = x - 2.0 * torch.round(x / 2.0)
            ph = tau_in[..., 1:2]
            ph = ph - period * torch.floor(ph / period)
            ax = x.abs()
            # v0.1 CuspFixed: T1 = 0, so t_orb = T0. v0.2: T0 -> t_orb_of_s().
            t_orb = self.t_orb_of_s()
            ph_new = ph + period / t_orb
            wrap = ph_new >= period
            ph_new = torch.where(wrap, ph_new - period, ph_new)
            sgn = torch.sign(x)
            # s parameterises the FOLD, per wing
            Bp, Bm = self.B_of_s(+1.0), self.B_of_s(-1.0)
            Bt = torch.where(sgn >= 0, torch.full_like(ax, Bp), torch.full_like(ax, Bm))
            fx = sgn * (Bt * torch.clamp(ax, min=self.m.MAP_EPS) ** self.RHO - 1.0)
            x_new = torch.where(wrap, fx, x)
            one = torch.ones_like(self.ell[..., :1])
            self.tau = torch.cat([half * x_new, ph_new, self.tau[..., 2:]], dim=-1)
            self.ell = torch.cat([one, one, self.ell[..., 2:]], dim=-1)
        # windowed wing occupancy: the fold observable a LEAN actually moves.
        # s_1 tilts the two thresholds apart, so it changes how long each wing is
        # held -- which `saddle` (a within-wing distance) cannot show.
        xs = float(self.tau[..., 0].item()) / self.half
        xs = xs - 2.0 * round(xs / 2.0)
        self.wing_ema += ((1.0 if xs >= 0 else -1.0) - self.wing_ema) / WING_W
        self.n += 1

    def hear(self, vec, window: int = 120):
        """Ply R input: a DIM_S vector spread over `window` ticks."""
        v = np.asarray(vec, float).reshape(DIM_S) / float(window)
        for i in range(window):
            self.pending[self.n + i] = self.pending.get(self.n + i, 0.0) + v

    def advance(self, ticks: int):
        for _ in range(ticks):
            self._tick()
        return self.observe()

    # ---------------------------------------------------------------- observables
    @torch.no_grad()
    def observe(self) -> dict:
        """Ply S (phi_private) appears NOWHERE in this dict. That is requirement T1."""
        x = self.tau[..., :1] / self.half
        x = x - 2.0 * torch.round(x / 2.0)
        ax = float(x.abs().item())
        ph = float((self.tau[..., 1:2] - self.period
                    * torch.floor(self.tau[..., 1:2] / self.period)).item())
        wing = 1.0 if float(x.item()) >= 0 else -1.0
        B = self.B_of_s(wing)
        thr = flip_thresh(B, self.RHO)
        frac_left = (self.period - ph) / self.period
        return dict(
            basin=int(torch.sign(x).item()) or 1,
            lobe_coord=float(x.item()),
            # UNSHUTTERED by construction: no clock factor. v0.1's saddle_proximity
            # was saddle x (1 - frac_left), which crushed ~71% of readouts into one
            # bucket (FINDING_shuttered_readout). This is the state term alone.
            saddle=max(0.0, 1.0 - abs(ax - thr) / thr),
            will_flip=bool(B * max(ax, self.m.MAP_EPS) ** self.RHO < 1.0),
            wing_bias=float(self.wing_ema),
            # steps_to_switch REMOVED: with t_orb no longer modulated it is a pure
            # clock, and T4 measured it at 0% creature-dependent. Publishing a
            # readout that cannot move with the creature is exactly the
            # saddle_proximity disease of v0.1 (FINDING_shuttered_readout).
            flip_thresh=thr,
            s0=float(self.s[0]), s1=float(self.s[1]),
            tick=self.n,
        )


# ---------------------------------------------------------------- correctness gate
def selftest_zero(model, ticks: int = 400) -> None:
    """At s = 0 with KAPPA -> 0, v0.2 must reproduce v0.1's map bit-identically."""
    import arms as A
    e1 = A._CoreEngine(model, 0, deaf=True)
    r1 = e1.advance(ticks)
    e2 = V02Engine(model, 0)
    assert np.allclose(e2.s, 0.0), "s must start at 0"
    e2.advance(ticks)
    x2 = float((e2.tau[..., :1] / e2.half
                - 2.0 * torch.round((e2.tau[..., :1] / e2.half) / 2.0)).item())
    if abs(r1["lobe_coord"] - x2) > 0:
        raise SystemExit(
            f"SELFTEST FAILED: v0.2 has drifted from v0.1 at s=0\n"
            f"  v0.1 lobe_coord {r1['lobe_coord']!r}\n  v0.2 lobe_coord {x2!r}")
    print(f"selftest OK: v0.2 == v0.1 bit-identically at s=0 "
          f"(lobe_coord {x2:.12f}, {ticks} ticks)")
