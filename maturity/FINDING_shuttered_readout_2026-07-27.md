# `saddle_proximity` is state × clock — the instrument was jammed

**Found:** 2026-07-27, during Step 0 (`diagnose_shutter.py`, `diagnose_unshuttered.py`).
**Method:** offline, retired seeds 0–47, no API, no Mouth, no judge.
**Status:** recorded. `observer.py` is substrate-gate-hashed and was **not** modified;
everything below is read-only inspection plus arithmetic on keys the Observer already
publishes.
**Severity:** invalidates the *instrument* used by three campaigns. Does not invalidate
Teich, the genome, or the seat.

## The mechanism

`body/observer.py::observe`:

```python
frac_left   = float((self.period - rp).item()) / self.period   # rp = _roof_phase(tau)
saddle      = max(0.0, 1.0 - abs(ax - self.flip_thresh) / self.flip_thresh)
saddle_prox = saddle * (1.0 - frac_left)
```

`saddle` is the state term — how close the lobe coordinate sits to the flip threshold.
`frac_left` is the **clock**: it comes from `_roof_phase(tau) = tau[...,1]`, while the
Ears force `tau[...,0]` only (`_CoreEngine.advance`). The two coordinates are disjoint.

So the published `saddle_proximity` is the creature's state multiplied by a phase the
creature's hearing cannot touch. `diagnose_acts.py` confirms this empirically and
independently: `steps_to_switch`, derived from the same clock, showed **0.0% paired
divergence** at both the pivot and the probe — a pure clock, deaf by construction.

Because the probe's tick count is fixed by the script, both conditions of a paired run
arrive at the probe with **identical** `frac_left`. Whatever state difference exists is
then multiplied by the same number in both arms — and where that number is small, it is
multiplied toward zero.

## The measurement (`diagnose_shutter.py`, 48 seeds)

| gap | gate = 1 − frac_left | `saddle` (state) | `saddle_prox` (published) | % below `SADDLE_SETTLED` |
|---|---|---|---|---|
| 300 | 0.6331 ± 0.3903 | 0.4005 | 0.2234 | 56.2% |
| 900 | 0.4330 ± 0.3890 | 0.3459 | 0.2026 | 75.0% |
| 1800 | 0.3147 ± 0.3287 | 0.3289 | 0.1407 | 81.2% |

The state term declines 18% across the gap menu. The gate declines **2×**. Pooled, **≈71%
of all readouts fall below the journal's `SADDLE_SETTLED = 0.20` edge** — so the journal
reported *"settled"* most of the time, in every arm, at every gap, largely independent of
what the creature was actually doing.

`diagnose_acts.py` had flagged the symptom first: paired `saddle_bucket` divergence
decaying 50.0% → 43.8% → **6.2%** across gaps 300/900/1800. That reads as a mark fading
with time. It is not. The mark is steady; the shutter closes.

## What it costs — the channel width (`diagnose_unshuttered.py`, 48 seeds)

`saddle` is recoverable **read-only** from `lobe_coord`, an existing readout key:

```python
saddle = max(0.0, 1.0 - abs(abs(lobe_coord) - flip_thresh) / flip_thresh)
```

| bucket variant | intact | deaf |
|---|---|---|
| A. `saddle_prox`, edges 0.20/0.60 — **what T-INT used** | 33.3% | 0.0% ✓ |
| B. `saddle`, edges 0.20/0.60 — shutter removed | **64.6%** | 0.0% ✓ |
| C. `saddle`, empirical tertile edges 0.187/0.612 | **64.6%** | 0.0% ✓ |

The channel is **1.94× wider** with the clock factor removed, and the deaf control stays
exactly 0% — so the extra width is entirely text-attributable, not noise let in by the
change. B ≡ C shows the floor effect was purely the shutter: the journal's hand-chosen
edges (0.20/0.60) sit almost exactly on the empirical tertiles of the *unshuttered*
quantity (0.187/0.612). Those thresholds were right for the state variable all along.

Variant A reproduces `diagnose_channel.py`'s 33.3% exactly, through a third independent
code path — the diagnostic is calibrated against a known quantity.

## Consequences for prior results

1. **T-INT (`REPORT_tint_screen_2026-07-27.md`).** Its 33.3% ceiling was not "the coupling
   is coarse" as reported in §3 — it was a jammed needle. The verdict (DiD 0.042) stands as
   a fact about the pipeline that was run, but its §4.2 design brief ("widen the channel")
   now has a specific, cheap, correct target.

2. **IC-1, discarded (`TINT_CONFIG.json::ic1_status`).** Its ground truth *was* the mood
   bucket at the probe — computed through the shutter. With ≈71% of labels reading
   "settled", a constant guess scores ≈0.71, and the recorded scores sit on that baseline:

   | | score |
   |---|---|
   | constant "settled" | ≈ 0.71 |
   | A2b deaf | 0.781 |
   | A0 intact | 0.656 |
   | null | 0.344 |

   Both discard grounds are what a degenerate label manufactures: the transcript-only
   oracle beats chance by learning the base rate (recorded g = 0.378), and intact-vs-deaf
   becomes a coin flip on the residual (recorded g = −0.320, i.e. *backwards*). **IC-1 was
   not tested. It was retired on evidence produced by the broken instrument.**

3. **v1.5 gate and the G1/C2 screens** rendered this quantity too. Their metrics did not
   depend on the mood bucket, so their nulls are not explained by it, but it was present.

## Standing rule, restated

`FINDING_noise_channel_2026-07-27.md` §"Design consequences" already said it: *every
quantity the journal renders must first be shown reproducible.* This finding adds the
second half — **and must be shown to depend on the creature.** `saddle_proximity` is
perfectly reproducible. It is also, in the majority of readouts, a report about a clock.

Reproducibility and creature-dependence are different properties. `lambda_running` failed
the first. `saddle_proximity` passed the first and failed the second. Both shipped.
