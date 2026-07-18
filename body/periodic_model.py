"""MCG-invariant (periodic) decoder features for the growing Teichmüller model.

The anchor and fiber coordinates live on circles (τ ↦ τ mod T is a Dehn twist), but the
stock decoder/field see RAW τ — so every wrap teleports the decoded state, and a smooth
spiral around the fiber circle is not representable. Observables on moduli space must be
mapping-class-group invariant, i.e. periodic in the twist: feed the networks
[sin(2πτ/T), cos(2πτ/T), log ℓ] instead of [τ, log ℓ]. Wraps become invisible in state
space and circle-embeddings (spirals) become trivial for the decoder.
"""
from __future__ import annotations

import math

import torch

import core


class PeriodicGrowingModel(core.GrowingTeichmullerWorldModel):
    """GrowingTeichmullerWorldModel with periodic (sin/cos) twist features."""

    def __init__(self, cfg: core.Config, growth_cfg: core.GrowthConfig,
                 max_gen: float = 3.0) -> None:
        super().__init__(cfg, growth_cfg, max_gen)
        nc = self.max_curves
        d_feat = 3 * nc                                    # sin, cos, log-length per curve
        dec_h = growth_cfg.decoder_hidden if growth_cfg.decoder_hidden is not None else cfg.hidden_dim
        dec_l = growth_cfg.decoder_layers if growth_cfg.decoder_layers is not None else cfg.n_layers
        self.field = core.build_mlp(d_feat, 3 * nc, cfg.hidden_dim, cfg.n_layers)
        self.decoder = core.build_mlp(d_feat, cfg.state_dim, dec_h, dec_l)
        with torch.no_grad():
            self.field[-1].weight.mul_(1e-2)
            self.field[-1].bias.zero_()

    def _features(self, tau: torch.Tensor, ell: torch.Tensor, g: torch.Tensor) -> torch.Tensor:
        gvec = g.view(*([1] * (tau.dim() - 1)), self.max_curves)
        ang = 2.0 * math.pi * tau / self.gcfg.anchor_period
        return torch.cat([torch.sin(ang) * gvec, torch.cos(ang) * gvec,
                          torch.log(ell) * gvec], dim=-1)
