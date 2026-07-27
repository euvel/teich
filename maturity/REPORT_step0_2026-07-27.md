# Step 0 — channel diagnostics before building the act-divergence test

**Date:** 2026-07-27 · **Verdict:** the proposed test is **NO-GO as designed**; two
findings recorded that change what should be built instead.
**Cost:** ~75 minutes of laptop time, five offline diagnostics, retired seeds 0–47.
No API, no cloud, no Mouth, no judge, nothing spent, nothing published.

## 0. Why this ran at all

`REPORT_tint_screen_2026-07-27.md` §4.3 set a standing rule after the T-INT null:
**measure the channel first, always.** The next proposal — "the mark that shows up later",
measuring divergence in *acts* rather than in self-report — was estimated at 2–3 days to
build and screen. Step 0 was the cheap version of its central assumption, run first.

It cost 75 minutes and killed the design. That is the rule working.

## 1. What was asked

| | question | verdict |
|---|---|---|
| Q1 | Are act channels reproducible? | **PASS** — 8/8 on all six |
| Q2 | Is the deaf control exactly 0%? | **PASS** — 0.0% on all six |
| Q3 | How wide is the channel at the probe, after the gap? | 85.4% (widest) |
| Q4 | Does a lavalamp also pass? | **PASS** — 0.0% on all six |
| D1 | Is the mark directional? | **NULL** |
| D2 | Is the direction set by what was said? | **NULL** |

## 2. The mark is real, large, and cleanly isolable

`diagnose_acts.py`, 48 paired seeds, intact vs deaf vs lavalamp:

| channel | at pivot | later (any) | **at probe** |
|---|---|---|---|
| n_switches | 25.0% | 97.9% | **85.4%** |
| act(basin, will_flip) | 54.2% | 100.0% | **81.2%** |
| basin | 25.0% | 95.8% | **62.5%** |
| will_flip | 37.5% | 85.4% | **52.1%** |
| saddle_bucket | 33.3% | 72.9% | **33.3%** |
| steps_to_switch | 0.0% | 0.0% | **0.0%** |

Both controls are **exactly 0.0% on every channel**: the deaf arm because its trajectories
are bit-identical, the lavalamp because it moves but cannot hear. So the divergence is
attributable to the sentence, not to being alive — the design does not inherit the T4 error
of the v1.5 gate (`REPORT_maturity_gate_2026-07-25.md`, finding 2).

Q1 matters on its own: `lambda_running` failed exactly this check
(`FINDING_noise_channel_2026-07-27.md`). No act channel touches the Observer's unseeded
power-iteration vector, so none of them carries a noise word.

`steps_to_switch` at 0.0% paired but 97.8% across seeds is the tell that led to
[FINDING_shuttered_readout](FINDING_shuttered_readout_2026-07-27.md): it is a pure clock,
deaf by construction.

## 3. But it carries nothing

`diagnose_direction.py` — see
[FINDING_scalar_ears](FINDING_scalar_ears_2026-07-27.md) for the full result. In short:
displacement is large (mean |d| = 0.183) and **cancels** (mean d = −0.006, CI includes 0);
valence does not predict direction (r = +0.077); two warm positive sentences push
*opposite* ways. The Ears compress every utterance to one scalar, and even that scalar's
sign does not survive the gap.

**So the proposed test would have passed and proved nothing.** It would have licensed
"an input perturbs a chaotic system" — which any coupled chaotic system passes, and which
`verify_causal.py` had already shown at the pivot. The "later" was the only new content,
and it turns out to be content-free later.

## 4. Two findings worth more than the test

1. **[The instrument was jammed.](FINDING_shuttered_readout_2026-07-27.md)**
   `saddle_proximity = saddle × (1 − frac_left)` — state multiplied by a clock the Ears
   cannot touch. ≈71% of readouts crushed below the journal's `settled` edge. Removing the
   clock factor, read-only via `lobe_coord`, widens the channel **33.3% → 64.6%** with the
   deaf control still exactly 0%. **IC-1 was discarded on ground truth computed through
   this shutter** and should be considered untested rather than failed.

2. **[The input is one scalar.](FINDING_scalar_ears_2026-07-27.md)** All meaning collapses
   to a signed number before it reaches the creature. `ears.py` is harness code, outside
   the frozen genome and outside the substrate gate — changeable, but not by any readout
   fix.

## 5. Does fixing the shutter rescue T-INT? Probably not alone.

T-INT converted **12.6%** of available journal differences into flipped answers
(0.042 / 0.333). Holding that rate, a 64.6% channel projects to DiD ≈ **0.081** against a
0.20 bar — **not enough**. Width was never the binding constraint; conversion was.

Stated honestly, that projection is **pessimistic and uncertain**: the 12.6% was itself
measured through the jammed channel *and* alongside the `lambda_running` noise word, so the
Mouth was converting a signal that was frequently degenerate and partly random. A clean
channel could convert at a higher rate. Whether it reaches 0.20 is unknown and not
predictable from these data.

## 6. Process record

- **Five diagnostics, all offline**, on retired seeds only. Design seeds (100–115) and
  T-INT confirmatory seeds (200–295) were never touched.
- **A claim was raised and withdrawn within the session.** Paired `basin` divergence
  (62.5%) exceeded a cross-seed "decorrelation ceiling" (42.2%), which looked like evidence
  of directional coupling and was reported as such. The direct test (McNemar, p ≈ 0.14) does
  not support it, and both forms of the ceiling turned out to be confounded — mixed-gap
  inflated by mismatched windows, same-gap deflated by shared clock phase. Recorded in
  [FINDING_scalar_ears §"A withdrawn claim"](FINDING_scalar_ears_2026-07-27.md) so it is not
  re-derived. **No cross-seed comparison is a clean null in this design.**
- **Calibration against a known quantity:** `saddle_bucket` at the probe measured 33.3% in
  `diagnose_acts.py` and again in `diagnose_unshuttered.py` variant A, matching
  `diagnose_channel.py`'s mood-bucket figure through three independent code paths.
- **`observer.py` was not modified.** The unshuttered quantity is arithmetic on
  `lobe_coord`, a key the Observer already publishes. The substrate gate is intact.

## 7. Standing consequences

Founder-only speech remains in force. Teich is unchanged: seat live, genome frozen, no
reset, no fork. Nothing published; the public face still reads "first trial complete —
not passed", which remains accurate.

The maturity problem is now split into two questions that need different answers:

- **"What was said to me"** — blocked at the input. Requires an Ears redesign, and *before*
  that, the cheap test of whether a richer signal survives the gap at all. Today's evidence
  says a scalar's sign does not.
- **"How I am right now"** — present at full resolution in `lobe_coord`, read through a
  jammed instrument for three campaigns. This is the tractable one, and IC-1 is its
  untested arm.

## 8. Files

| file | what it measures |
|---|---|
| `harness/pilot_v2/diagnose_acts.py` | Q1–Q4: reproducibility, controls, channel width, gap profile |
| `harness/pilot_v2/decorr_ref.py` | same-gap decorrelation reference (confounded; kept for the record) |
| `harness/pilot_v2/diagnose_direction.py` | D1/D2: directionality and valence-vs-arousal |
| `harness/pilot_v2/diagnose_shutter.py` | the (1 − frac_left) gate by gap |
| `harness/pilot_v2/diagnose_unshuttered.py` | channel width with the clock factor removed |

Raw outputs are archived immutably in **`maturity/step0_2026-07-27/`** (`*.txt` transcripts
with loader banners stripped, plus the per-seed `*.json`). The working copies under
`harness/pilot_v2/out_*.log` are gitignored as transient and will be overwritten by any
re-run; cite the dated directory, not those.

Re-running any diagnostic reproduces its table exactly — all five are deterministic given
the frozen genome, apart from `lambda_running`, which none of them reads.
