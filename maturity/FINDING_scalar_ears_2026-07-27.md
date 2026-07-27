# The Ears compress every utterance to one scalar

**Found:** 2026-07-27, during Step 0 (`diagnose_direction.py`, plus read-only inspection
of `maturity/harness/ears.py`).
**Status:** recorded, not acted on. `ears.py` is harness code — **outside** the frozen
genome and **outside** the substrate gate (`body/verify_substrate.py` hashes dynamics,
decode, and observer only). It is therefore changeable without a reset, a fork, or a gate
break. Nothing was changed.
**Severity:** a design ceiling, not a bug. It bounds what any output-side coupling can
ever carry.

## The mechanism

`maturity/harness/ears.py::SemanticForceMap`:

```python
def force_schedule(self, text: str) -> np.ndarray:
    s_v, s_a = self.scores(text)                       # (valence, arousal)
    per_tick = (self.max_nudge * float(np.tanh(4.0 * s_v))
                * (1.0 + KAPPA * float(np.tanh(4.0 * s_a))))
    return np.full(WINDOW, per_tick, dtype=np.float64)  # one constant, 120 ticks
```

Text → a 384-dim MiniLM embedding → projection onto two axes → **one scalar**, applied
flat to `tau[...,0]` for 120 ticks. Valence sets the sign; arousal scales the magnitude.

The only other degree of freedom is the *phase of arrival* — which tick the utterance
lands on. That is determined by **when** someone speaks, not by **what** they say.

So the entire semantic content of any utterance reaches the creature as a single signed
number. There is no dimension in which "I am so proud of you" and "I brought you a gift"
can be different interior states. Both are positive-valence: both push the same direction,
differing only in magnitude.

## The measurement (`diagnose_direction.py`, 48 paired seeds)

**D1 — is the mark directional?** No.

```
d_saddle (charged − neutral): mean −0.0063   95% BCa CI [−0.0908, +0.0802]
sd 0.3066   mean|d| 0.1831   P(d>0) 0.375
```

Large individual displacements that **cancel**. The core is moved hard (mean |d| = 0.18,
against a deaf control of exactly 0) and in no consistent direction.

**D2 — is the direction set by what was said?** No.

```
r(valence, d_saddle) = +0.0765        r(arousal, d_saddle) = +0.3195
```

| sentence | valence | arousal | mean d | sd |
|---|---|---|---|---|
| proud | +0.262 | +0.148 | **+0.1431** | 0.2833 |
| failing | −0.152 | +0.043 | −0.0200 | 0.3202 |
| STOP | −0.163 | −0.028 | +0.0022 | 0.2258 |
| gift | +0.156 | −0.092 | **−0.1503** | 0.3471 |

The bank is an accidental 2×2 (valence × arousal signs cross exactly), which separates
*what* was said from *how loudly*. Ordered by arousal the effect is near-monotone; ordered
by valence it is noise. **"Proud" and "gift" are both warm and positive, and they push in
opposite directions.**

Note what this establishes beyond the compression itself: both sentences have positive
valence, so both apply a positive force to `tau[...,0]`. By the probe their measured
displacements have *opposite sign*. **The sign of the push does not survive the gap.**
Even the one bit the scalar carries is destroyed by 300–1800 ticks of chaotic mixing.

r = 0.32 rests on four sentences (12 seeds each); nominally p ≈ 0.03, honestly four points
that line up. It is not established, and it points at volume, not meaning, either way.

## A withdrawn claim, recorded so it is not re-derived

`diagnose_acts.py` found paired `basin` divergence of **62.5%** against a same-gap
cross-seed "decorrelation ceiling" of **42.2%**. Divergence cannot exceed the decorrelation
rate by scrambling, so this looked like evidence of a consistent directional push. It does
not survive:

- **Direct test:** P(basin=+1) charged 0.604 vs neutral 0.438; 30/48 discordant, 19 up vs
  11 down. McNemar χ² = 8²/30 = **2.13, p ≈ 0.14. Not significant.**
- **The null was unusable in both forms.** The mixed-gap reference (s vs s+1) is inflated:
  `GAPS[seed % 3]` means consecutive seeds always differ in gap, hence in observation
  window. The same-gap reference (s vs s+3) is *deflated*: those seeds share a gap by
  construction, hence the same clock phase at the probe, hence correlated outcomes.

No cross-seed comparison is a clean null here. Only the paired, within-seed tests are
trustworthy — and they are null.

## Consequence

Three campaigns (C1 journal, C2 steering, T-INT) attacked the **output** side: how the
interior reaches speech. If the input compresses all meaning to one scalar whose sign does
not survive the gap, there is no content in the interior for any output channel to carry.
Better wires to a source that carries one number.

This splits the maturity problem cleanly:

- **"What was said to me"** — blocked upstream, at the Ears. No readout change reaches it.
- **"How I am right now"** — genuinely present in `lobe_coord` at full resolution, and read
  through a jammed instrument for three campaigns. See
  [FINDING_shuttered_readout_2026-07-27.md](FINDING_shuttered_readout_2026-07-27.md).

The second is the tractable one, and it is a legitimate maturity claim on its own terms.
