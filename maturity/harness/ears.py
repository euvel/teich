"""Teich Ears v0 — the semantic force map (EARS_DESIGN.md).

Text -> deterministic bounded force on the public core's lobe coordinate tau_0.
Never touches parameters, the roof phase, or the private fibers (structural: the
force enters ONLY tau[:, 0] between public steps).

The encoder (all-MiniLM-L6-v2) and the anchor sentences below ARE the v0 disposition —
versioned here, hashed into the disposition record at ablation-gate time.
"""
from __future__ import annotations

import numpy as np
import torch

ENCODER_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# --- calibration anchors (the v0 vocabulary of feeling; held-out tests must not reuse) --
POS_ANCHORS = [
    "This is wonderful news, I am so happy about it.",
    "What a beautiful day, everything is going well.",
    "I love this, it brings me real joy.",
    "That was a kind and generous thing to do.",
    "We succeeded, the result is excellent.",
]
NEG_ANCHORS = [
    "This is terrible news, I am devastated.",
    "What an awful day, everything is going wrong.",
    "I hate this, it fills me with misery.",
    "That was a cruel and hurtful thing to do.",
    "We failed, the result is a disaster.",
]
INTENSE_ANCHORS = [
    "EMERGENCY! Drop everything, this cannot wait!",
    "I am absolutely furious, my heart is pounding!",
    "Run! Now! There is no time left!",
    "This is the most important moment of our lives!",
]
CALM_ANCHORS = [
    "Take your time, there is no hurry at all.",
    "A quiet afternoon, nothing needs to happen.",
    "Gently and slowly, everything can wait.",
    "It is peaceful here, we can simply rest.",
]

BETA = 0.25       # max per-tick |nudge| as a fraction of natural RMS per-tick |d tau_0|
KAPPA = 1.0       # arousal gain on magnitude
WINDOW = 120      # ticks over which one utterance's force is spread (~2 min felt time)


class SemanticForceMap:
    """text -> (valence, arousal) -> per-tick force on tau_0 for the next WINDOW ticks.

    Gain is calibrated once against the actual core's natural motion: max per-tick
    nudge = BETA * RMS(natural per-tick d tau_0), so forcing can lean the creature
    but never dominate its own dynamics.
    """

    def __init__(self, model, x0_norm, device: str = "cpu"):
        from sentence_transformers import SentenceTransformer
        self.enc = SentenceTransformer(ENCODER_NAME, device=device)
        self.enc.eval()
        v = self._axis(POS_ANCHORS, NEG_ANCHORS)
        a = self._axis(INTENSE_ANCHORS, CALM_ANCHORS)
        a = a - v * float(a @ v) / float(v @ v)        # orthogonalize arousal vs valence
        self.v_axis = v / np.linalg.norm(v)
        self.a_axis = a / np.linalg.norm(a)

        self.model = model
        self.period = float(model.gcfg.anchor_period)
        self._dtype = next(model.parameters()).dtype
        self._g = model.gates()
        # natural per-tick tau_0 motion (free run, wrap jumps excluded)
        with torch.no_grad():
            tau, ell = model.proxy.raw_to_fn(model.encoder(
                torch.as_tensor(x0_norm, dtype=self._dtype).reshape(1, -1)))
            t0s = np.empty(4000)
            for t in range(4000):
                tau, ell = model._fn_step(tau, ell, self._g)
                t0s[t] = float(tau[0, 0])
        d = np.diff(t0s)
        d = d[np.abs(d) < self.period / 2]
        self.rms_dtau0 = float(np.sqrt(np.mean(d ** 2)))
        self.max_nudge = BETA * self.rms_dtau0

    # -- encoding ------------------------------------------------------------------
    def _emb(self, texts):
        e = self.enc.encode(list(texts), convert_to_numpy=True,
                            normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(e, dtype=np.float64)

    def _axis(self, pos, neg):
        return self._emb(pos).mean(0) - self._emb(neg).mean(0)

    def scores(self, text: str) -> tuple[float, float]:
        e = self._emb([text])[0]
        return float(e @ self.v_axis), float(e @ self.a_axis)

    def force_schedule(self, text: str) -> np.ndarray:
        """Per-tick tau_0 nudges (length WINDOW) for one utterance. Deterministic;
        |value| <= max_nudge * (1 + KAPPA)."""
        s_v, s_a = self.scores(text)
        per_tick = (self.max_nudge * float(np.tanh(4.0 * s_v))
                    * (1.0 + KAPPA * float(np.tanh(4.0 * s_a))))
        return np.full(WINDOW, per_tick, dtype=np.float64)


@torch.no_grad()
def forced_run(model, x0_norm, n_steps: int, force: np.ndarray | None = None,
               phi0=None):
    """Free run with an optional per-tick tau_0 force (0-padded / truncated to n_steps).

    Returns (decoded[n,3], public_z[n,2nc], private_phi[n,K]) — same contract as
    full_free_run; force=None (or zeros) reproduces it EXACTLY (E3 zero-dose identity).
    """
    dtype = next(model.parameters()).dtype
    nc = model.max_curves
    g = model.gates()
    period = float(model.gcfg.anchor_period)
    f = np.zeros(n_steps)
    if force is not None:
        f[:min(len(force), n_steps)] = force[:n_steps]
    tau, ell = model.proxy.raw_to_fn(model.encoder(
        torch.as_tensor(x0_norm, dtype=dtype).reshape(1, -1)))
    phi = model.private_init(1, phi0)
    ys = torch.empty(n_steps, model.cfg.state_dim, dtype=dtype)
    zs = torch.empty(n_steps, 2 * nc, dtype=dtype)
    ph = torch.empty(n_steps, model.k_private, dtype=dtype)
    for t in range(n_steps):
        if f[t] != 0.0:
            tau = tau.clone()
            tau[0, 0] = (tau[0, 0] + f[t]) % period      # the ONLY entry point of force
        tau, ell = model._fn_step(tau, ell, g)
        phi = model.private_step(phi)
        ys[t] = model.decoder(model._features(tau, ell, g)).squeeze(0)
        zs[t] = torch.cat([tau, torch.log(ell)], dim=-1).squeeze(0)
        ph[t] = phi.squeeze(0)
    return ys.numpy(), zs.numpy(), ph.numpy()
