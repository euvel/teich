# The journal has a noise channel — `lambda_running` is not reproducible

**Found:** 2026-07-27, ~12:40Z, BEFORE the T-INT confirmatory screen was unblinded.
**Method:** `diagnose_channel.py` (offline, retired seeds 0–47, no API), whose deaf control
failed its own sanity check and exposed this.
**Status:** recorded, not acted on. The frozen pipeline is NOT changed mid-screen, and
`observer.py` is substrate-gate-hashed and must never be edited.

## What the diagnostic found

The deaf arm (A2b) must show 0% journal difference between the charged and neutral
conditions — its trajectories are bit-identical. It showed **60.4%**.

Chasing it: `saddle_proximity` is perfectly reproducible, but `lambda_running` is not. The
same script run twice through the same seeded core:

    run A lambda: -3.0167  -6.7945  -1.3053  -3.5973  -5.7137  0.0334
    run B lambda: -3.9384  -1.3270  -3.8071  -4.2700  -2.3382  0.9526

## Root cause (read-only inspection of `body/observer.py`)

`Observer._local_lambda` estimates the top finite-time Lyapunov exponent by power iteration:

```python
if self._v is None:
    self._v = torch.randn_like(z)      # UNSEEDED random initial vector
```

and `Observer.reset()` sets `self._v = None`. `_CoreEngine.advance()` calls `obs.reset()`
every turn, so a **fresh unseeded random vector is drawn each turn**. Power iteration converges
regardless of initialisation given enough steps — but over the ~400-tick observation window it
is nowhere near converged, so the reported value is dominated by its random start.

This is not a bug in the estimator's intent; it is a short-window estimator being read as
though it were a state variable.

## Why it matters for the screen

`journal.py::_energy` buckets `lambda_running` into "quiet / lively / restless inside", so
**every journal entry carries a word that is effectively random**, and the Mouth reads it.

Consequences, stated before seeing any result:

1. **The DiD stays unbiased.** The noise is symmetric across all four cells; it does not
   push the estimate in either direction.
2. **Power is lower than pre-registered.** My n=96 power table (84% at true DiD 0.30) assumed
   the only cell-to-cell variation was signal plus Mouth sampling noise. There is a third,
   larger source. The true power is unknown and lower.
3. **Common random numbers is partly defeated.** Sharing the Mouth sampling seed was meant to
   make identical inputs produce identical replies; the inputs are not identical, because the
   journal text itself varies randomly.

## The clean channel numbers

Restricting to signals where the deaf control is correctly 0% — i.e. genuinely text-attributable:

| journal signal | hearing core | deaf control |
|---|---|---|
| "shifted noticeably" clause differs | **25.0%** (12/48) | 0.0% ✓ |
| mood bucket differs at probe | **33.3%** (16/48) | 0.0% ✓ |
| whole tail differs | 100% (noise-inflated) | 60.4% ✗ |

So the coupling transmits a real, text-attributable difference to the Mouth in roughly
**a quarter to a third of conversations**. That is the honest ceiling on the DiD: the Mouth
cannot report a difference the journal never showed it. With the pass bar at 0.20, the Mouth
would need to convert something like half of all available journal differences into flipped
answers — demanding, but not impossible.

## Design consequences for the next iteration (NOT applied now)

- The energy clause should be dropped from the journal, or `lambda_running` should be seeded
  and window-converged before it is allowed to speak. A creature should not narrate a coin flip
  as an inner state.
- More generally: **every quantity the journal renders should first be shown to be
  reproducible.** `saddle_proximity` was; `lambda_running` never was, and nobody checked.
- The v1.5 campaign and both G1 screens also rendered this quantity. Their nulls were not
  caused by it (their metrics did not depend on the energy word), but it was present as noise
  in all of them.
