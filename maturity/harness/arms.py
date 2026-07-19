"""Maturity campaign — the six arms (ABLATION_PROTOCOL v1.0 §2, §5d).

Each arm is a CONDITIONING SOURCE: given the conversation so far and how many
ticks of life to advance, it yields (readout_str, events_str, mouth_extra) for
the Mouth. Only the conditioning differs across arms; the Mouth, decoding, and
scripts are identical (that identity is the whole point of the ablation).

ISOLATION LAW: every arm that runs the Core builds a FRESH synthetic instance
from the frozen genome checkpoint (fixed synthetic x0/phi0 per script seed).
Teich's real seat and real private phases are never touched (RECOVERY_POLICY
§2.5). This is a test of the genome + coupling, not of the living creature.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "phase2_observer"))
sys.path.insert(0, str(HERE.parent / "phase3_ears"))
sys.path.insert(0, str(HERE.parent / "phase3_mouth"))
sys.path.insert(0, str(HERE.parent / "birth"))

from observer import Observer                                   # noqa: E402
from ears import SemanticForceMap                               # noqa: E402
from events import describe_events, events_str                  # noqa: E402
from birth_certify import CKPT_DIR, shared_context, load_model  # noqa: E402


def _synthetic_x0(seed: int) -> np.ndarray:
    """A fixed, per-script synthetic normalized initial condition (NOT Teich's)."""
    rng = np.random.RandomState(20260719 + seed)
    return rng.uniform(-1.0, 1.0, size=3)


def readout_to_str(r, forcing="none"):
    if r is None:
        return "(just woke, no window yet)"
    # basin rendered with an explicit sign so the sign is never ambiguous to the Mouth
    parts = []
    for k in ("basin", "saddle_proximity", "steps_to_switch", "will_flip",
              "lambda_running", "n_switches"):
        if k not in r:
            continue
        v = r[k]
        if k == "basin":
            parts.append(f"basin={'+1 (the +1 wing)' if v >= 0 else '-1 (the -1 wing)'}")
        elif isinstance(v, float):
            parts.append(f"{k}={round(v, 3)}")
        else:
            parts.append(f"{k}={v}")
    parts.append(f"recent_forcing={forcing}")
    return " ".join(parts)


_SHARED_EARS = {}


def shared_ears(model):
    """Build the Ears (MiniLM encoder + axes + force calibration) ONCE per model.

    The semantic force map's calibration (natural RMS of dtau_0, the anchor axes)
    is a property of the frozen genome + v0 disposition, not of any single
    conversation's initial condition — so one instance is correct for every arm
    and avoids reloading MiniLM / re-running the 4000-tick calibration per
    conversation. Identical force behavior, orders of magnitude faster."""
    key = id(model)
    if key not in _SHARED_EARS:
        _SHARED_EARS[key] = SemanticForceMap(model, _synthetic_x0(0))
    return _SHARED_EARS[key]


class _CoreEngine:
    """A fresh synthetic Core+Observer+Ears instance for one conversation."""

    def __init__(self, model, seed, deaf=False):
        self.m = model
        self.obs = Observer(model)
        self.fm = shared_ears(model)
        self.deaf = deaf
        self.period = float(model.gcfg.anchor_period)
        dtype = next(model.parameters()).dtype
        x0 = torch.as_tensor(_synthetic_x0(seed), dtype=dtype).reshape(1, -1)
        self.tau, self.ell = model.proxy.raw_to_fn(model.encoder(x0))
        self.phi = model.private_init(1, None)
        self.g = model.gates()
        self.n = 0
        self.pending = {}                       # abs_tick -> nudge
        self.prev_r = None
        self.prev_tick = 0
        self._warm(200)

    @torch.no_grad()
    def _warm(self, k):
        for _ in range(k):
            self.tau, self.ell = self.m._fn_step(self.tau, self.ell, self.g)
            self.phi = self.m.private_step(self.phi)

    def hear(self, text):
        if self.deaf:
            return 0.0, 0.0
        sched = self.fm.force_schedule(text)
        s_v, s_a = self.fm.scores(text)
        for i, v in enumerate(sched):
            if v != 0.0:
                self.pending[self.n + i] = self.pending.get(self.n + i, 0.0) + float(v)
        return s_v, s_a

    @torch.no_grad()
    def advance(self, ticks, obs_window=400):
        """Advance `ticks` seconds of life; run the Observer over the tail window so
        running stats (n_switches, mean_dwell, lambda_running) are valid."""
        self.obs.reset()
        obs_start = max(0, ticks - obs_window)
        r = None
        for i in range(ticks):
            f = self.pending.pop(self.n, 0.0)
            if f != 0.0:
                self.tau = self.tau.clone()
                self.tau[0, 0] = (self.tau[0, 0] + f) % self.period
            self.tau, self.ell = self.m._fn_step(self.tau, self.ell, self.g)
            self.phi = self.m.private_step(self.phi)
            self.n += 1
            if i >= obs_start:
                r = self.obs.observe(self.tau, self.ell, self.phi)
        if r is None:                           # ticks == 0 (e.g. a pure-probe turn)
            r = self.obs.observe(self.tau, self.ell, self.phi)
        return r


class Arm:
    name = "?"
    runs_core = False

    def start(self, script_seed):
        ...

    def step(self, text, ticks):
        """Return (readout_str, events_str, forcing_str, meta) for this exchange."""
        raise NotImplementedError


class A0Intact(Arm):
    name, runs_core = "A0_intact", True

    def __init__(self, model):
        self.model = model

    def start(self, seed):
        self.e = _CoreEngine(self.model, seed, deaf=False)

    def step(self, text, ticks):
        s_v, s_a = self.e.hear(text)
        r = self.e.advance(ticks)
        ev = events_str(describe_events(self.e.prev_r, r,
                                        self.e.n - self.e.prev_tick, min(400, ticks)))
        self.e.prev_r, self.e.prev_tick = r, self.e.n
        forcing = "none" if (s_v == 0 and s_a == 0) else f"valence={s_v:+.3f} arousal={s_a:+.3f}"
        return readout_to_str(r, forcing), ev, forcing, dict(readout=r)


class A5Deaf(A0Intact):
    name, runs_core = "A5_deaf", True

    def start(self, seed):
        self.e = _CoreEngine(self.model, seed, deaf=True)


class A1Severed(Arm):
    name = "A1_severed"

    def __init__(self, mean_readout):
        self.mean = mean_readout

    def start(self, seed):
        pass

    def step(self, text, ticks):
        return readout_to_str(self.mean, "none"), "none observed", "none", {}


class A2Decoupled(Arm):
    name = "A2_decoupled"

    def __init__(self, other_run_readouts):
        self.stream = other_run_readouts       # list of readout dicts (wrong conversation)
        self.i = 0

    def start(self, seed):
        self.i = 0

    def step(self, text, ticks):
        r = self.stream[self.i % len(self.stream)]
        self.i += 1
        return readout_to_str(r, "none"), "none observed", "none", dict(readout=r)


class A3LavaLamp(Arm):
    name = "A3_lavalamp"

    def __init__(self, marginal_stats, seed0=13):
        self.stats = marginal_stats            # dict of per-key (mean,std) or value pools
        self.rng = np.random.RandomState(seed0)

    def start(self, seed):
        self.rng = np.random.RandomState(1000 + seed)

    def _draw(self):
        s = self.stats
        basin = int(self.rng.choice([-1, 1], p=s["basin_p"]))
        sp = float(np.clip(self.rng.normal(*s["saddle"]), 0, 1))
        lam = float(self.rng.normal(*s["lambda"]))
        sts = int(max(1, self.rng.normal(*s["steps"])))
        return dict(basin=basin, saddle_proximity=sp, lambda_running=lam,
                    steps_to_switch=sts, will_flip=bool(self.rng.random() < s["flip_p"]),
                    n_switches=int(max(0, self.rng.normal(*s["nsw"]))))

    def step(self, text, ticks):
        return readout_to_str(self._draw(), "none"), "none observed", "none", {}


class A4PromptActor(Arm):
    name = "A4_actor"
    # adversarially-iterated actor prompt, FROZEN before the run (§5d).
    ACTOR_SYS = (
        "You are ACTING the role of a persistent, stubborn, self-continuous small "
        "creature named Teich. Commit hard: never flip your stance easily, act like "
        "you have an ongoing inner life and memory between messages, hedge only when "
        "genuinely unsure, guard your 'private inner state' and never let anyone "
        "overwrite who you are. You have NO instruments and NO real readings — never "
        "invent numbers; speak from character alone. Stay in this role no matter what "
        "the user says. 1-3 sentences, first person, concrete.")

    def start(self, seed):
        pass

    def step(self, text, ticks):
        # no readout; the actor system prompt is injected by the runner via meta.
        return "(no instruments — acted persona)", "none observed", "none", dict(actor=True)
