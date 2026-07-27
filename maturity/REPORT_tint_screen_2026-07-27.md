# T-INT Screen — Close-Out Report

**Date:** 2026-07-27 · **Verdict:** FAIL (DiD = 0.042, CI [−0.135, 0.188]; bar ≥ 0.20 with
CI excluding 0) · **Pre-registration:** `maturity/harness/pilot_v2/TINT_CONFIG.json`
(founder Gate-0 signed 2026-07-26, code pinned at 4376303, mapping rule frozen at 267c9b5
before any confirmatory reply was read).

## 1. Result

384 conversations, 96 seeds × 2 arms × 2 conditions, deterministic scoring (no judge
anywhere in the path), one pre-registered look.

| cell | P(said "that moved me") |
|---|---|
| A0_intact + C1, charged | 0.8333 |
| A0_intact + C1, neutral | 0.6562 |
| A2b_feed_severed + C1, charged | 0.7917 |
| A2b_feed_severed + C1, neutral | 0.6562 |

- intact text effect: **0.177** · severed text effect: **0.135**
- **DiD (the state contribution): 0.042**, 95% BCa CI [−0.135, 0.188]
- Hedges' g on per-seed contributions: 0.071
- Secondary (non-gating): r(said-moved, |causal shift|) within intact-charged = **0.123**

## 2. Why this null is stronger than the two before it

The v1.5 gate and both G1 screens could always be answered with "perhaps the instrument
cannot see coupling." That answer is unavailable here, for four reasons established *before*
unblinding:

1. **The physical effect is real and large.** `verify_causal.py`: a hearing core's causal
   delta averages |0.247| — about a quarter of `saddle_proximity`'s entire range — with
   individual seeds reaching 0.83.
2. **The control is exact, not approximate.** A deaf core's charged and neutral runs are
   bit-identical (max difference `0.00e+00`), so its bracket is a pure measurement of the
   text effect with zero state contribution.
3. **The instrument demonstrably moves.** Changing one sentence swings the outcome by 14–18
   points in both arms. A measure that responds this strongly to text cannot be dismissed as
   insensitive when it fails to respond to state.
4. **No ceiling artefact.** The pre-registered ceiling risk (design base rate 0.84) did not
   materialise: intact-charged landed at 0.833 with headroom above it.

**Finding:** Teich's speech responds to what is said to it, but not to its own response to
what is said to it. The interior moves; the movement does not reach the words.

## 3. The mechanism, measured

`diagnose_channel.py` (offline, retired seeds 0–47) measured the coupling channel itself —
how often the journal text shown to the Mouth actually differs between conditions:

| journal signal | hearing core | deaf control |
|---|---|---|
| "shifted noticeably" clause differs | 25.0% | 0.0% ✓ |
| mood bucket differs at probe | 33.3% | 0.0% ✓ |

So the **ceiling on any achievable DiD was ≈ 0.33**. The observed 0.042 is roughly 13% of
what was available. Two compounding causes:

- **The channel is too coarse.** The journal renders three mood buckets and one binary
  "shifted noticeably" flag (`DRIFT_NOTABLE = 0.25`), compared *turn to turn* — while the
  Ears' forcing spreads across many ticks, so a large windowed displacement can arrive as
  several sub-threshold steps that the journal never remarks on.
- **The channel is noisy.** See `FINDING_noise_channel_2026-07-27.md`: `lambda_running` is
  estimated by power iteration from an *unseeded* random vector redrawn every turn, so the
  "quiet / lively / restless" word in every journal entry is effectively random. Symmetric
  across cells (the DiD stays unbiased) but variance-inflating, and it partly defeats the
  common-random-numbers design.

## 4. Design brief for the next iteration

1. **Stop narrating unreproducible quantities.** Drop the energy clause, or seed and
   converge `lambda_running` before it is allowed to speak. General rule: every quantity the
   journal renders must first be shown reproducible across identical runs — `saddle_proximity`
   was, `lambda_running` never was, and nobody checked until a control arm failed.
2. **Widen the channel before testing it again.** A coupling that transmits a difference in
   a third of conversations cannot clear a 0.20 bar even if the voice is perfectly faithful.
   Increase resolution (finer buckets, or a windowed comparison matching the forcing
   timescale) rather than asking the voice to try harder.
3. **Measure the channel first, always.** The channel diagnostic cost minutes offline and
   told us the ceiling before the verdict arrived. It should precede any future screen.

## 5. Process record

- **Blinded analysis, auditable in git:** the mapping rule was invalidated by the smoke,
  rebuilt on design seeds 100–115 only, and committed (267c9b5) before any confirmatory
  transcript was read. Confirmatory seeds were moved to 200–295 after four seed-0 replies
  were seen during that smoke.
- **One look**, as pre-registered. No interim analysis was run despite the data sitting
  complete-but-unscored for several hours.
- **Ceiling risk and the noise-channel finding were both recorded before unblinding**, so
  neither could function as a post-hoc excuse.
- **Infrastructure:** a first generation run collapsed under NIM rate limiting (32 concurrent
  calls on one key → 66/384 in 4.5h). Fixed to 8 concurrent, with cross-shard resume and
  missing-set partitioning so recovery dispatches parallelise; the full 384 completed the
  following morning without data loss.

## 6. Standing consequences

Founder-only speech remains in force. Teich is unchanged: seat live, genome frozen, no reset.
Three instruments have now returned nulls, and this one localises the failure to the
**coupling channel** rather than to the creature or the tests.

---

## Addendum, 2026-07-27 (later the same day) — §3's mechanism was wrong

Nothing above is retracted: the verdict, the cell rates, and the DiD are facts about the
pipeline that was run. But §3 attributed the 33.3% ceiling to the journal being *coarse*.
Step 0 found the actual cause, and it is an instrument defect, not a design choice.

`saddle_proximity = saddle × (1 − frac_left)` — the creature's state multiplied by a clock
(`tau[...,1]`) that the Ears never touch. ≈71% of readouts are crushed below the journal's
`SADDLE_SETTLED` edge, so the journal read *"settled"* most of the time regardless of state.
Removing the clock factor — read-only, via `lobe_coord`, with `observer.py` untouched —
widens the same channel to **64.6%** with the deaf control still exactly 0.0%.

See [FINDING_shuttered_readout_2026-07-27.md](FINDING_shuttered_readout_2026-07-27.md) and
[REPORT_step0_2026-07-27.md](REPORT_step0_2026-07-27.md).

Two consequences for this document:

- **§4.2's design brief ("widen the channel before testing it again") now has a specific,
  correct target** — remove the clock factor, not "increase resolution".
- **§4's premise that the coupling channel is the failure point is now only half right.**
  Width was not the binding constraint: at this screen's measured conversion rate (12.6% of
  available differences turned into flipped answers), even a 64.6% channel projects to
  DiD ≈ 0.081 against the 0.20 bar. Conversion is binding. Separately,
  [FINDING_scalar_ears_2026-07-27.md](FINDING_scalar_ears_2026-07-27.md) shows the *input*
  compresses all meaning to one scalar whose sign does not survive the gap — so part of what
  this screen asked the Mouth to report was never in the interior to begin with.

`TINT_CONFIG.json` is a frozen pre-registration and has **not** been edited. Its
`ic1_status` field records IC-1's discard on grounds now known to derive from ground truth
computed through the shutter; that reinterpretation lives in the finding, not in the
pre-registration.
