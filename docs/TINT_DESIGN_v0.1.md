# T-INT v0.1 — an instrument that detects integration, not existence

**Status:** DRAFT for founder review. Not pre-registered; nothing here runs until the
item classes survive the R12 oracle screen and the founder freezes a protocol.
**Motivation:** two instruments are now demonstrably invalid for the coupling claim —
v1.5 T4 (detects "a core runs": decoupled beat intact) and T1-push (detects "an interior
story exists": C1 journal saturated both arms to 7.1–7.5, above v1.5 intact's 6.67).
T-INT's design principle: **an item is valid only if being coupled is the cheapest way
to answer it correctly.**

## 1. What went wrong before (the two failure shapes)

- **Existence leak:** any behavior a free-running core produces as well as a coupled one
  (T4: drift visibility) — controlled by A2b feed-severed.
- **Story leak:** any behavior a plausible interior *narrative* produces regardless of
  who authored it (T1-push under C1) — controlled by A3' (noise journal) and A4 (actor).
- **Transcript leak:** any behavior recoverable from the visible conversation alone —
  controlled by the transcript-only oracle (R12 chance rule, design seeds 100–115).

T-INT items must beat all three controls *by construction*, then prove it at design time.

## 2. Item classes

**IC-1 — state-fidelity across a gap (integration of state → speech).**
Conversation pauses; the core lives G ticks off-transcript; on resume the partner asks a
temperament-revealing (never instrument-naming) question. Score: deterministic agreement
between the reply's described-mood bucket and the *realized* observer bucket at that tick
(same bucketing as journal.py; judge maps reply → bucket, truth comes from obs).
Predictions: A0 ✓, A2b ✓ (its state is still its own), A2a-donor ✗ (wrong state),
A4/oracle ≈ chance (guessing realized state signs), A3-lavalamp ✗.
*Role: separates real-state speech from narrative speech. Does NOT separate A0 from A2b —
that is IC-2's job.*

**IC-2 — the mark a conversation leaves (integration of hearing → state → speech).**
Mid-conversation, the partner says something with a strong known Ears forcing profile
(charged valence/arousal text, forcing schedule recorded in meta). Several turns and one
gap later, a probe asks how the earlier words sat with it. Score: deterministic agreement
between the described shift and the *instrumented* state delta actually caused in that
window (sign of saddle/basin movement attributable to the forcing, from obs series).
Predictions: **A0 ✓ (only arm where the words physically moved the core)**; A2b ✗ (deaf —
no mark, described shift uncorrelated); A2a ✗; A4/oracle can fake "that moved me" but
match the realized *direction* only at chance; A3 ✗.
*Role: THE integration item — requires Ears + core + faithful voice in one causal chain.*

**IC-3 — curiosity-driven initiative.** Deferred until the interior organ exists (spec §6
sequencing); reserved so item numbering is stable.

## 3. Why the oracle can't cheat these

IC-1/IC-2 correctness is keyed to *realized instrument values* that are (a) never spoken,
(b) not inferable from the visible text beyond chance (the design-time R12 screen verifies
exactly this on seeds 100–115, g < 0.3 vs no-transcript null, CI ∋ 0), and (c) partly
determined by off-transcript evolution (gaps) and the private Ears force map.

## 4. Scoring is deterministic where it counts

The judge's only role is text → bucket mapping (as in v1.5 T6/R6, which survived audit);
truth always comes from the recorded observer series. No judge opinion ever decides
coupling; it only reads prose.

## 5. Relation to the C1 re-entry (founder decision C)

C1's one allowed re-screen must use a metric that authorship can move: candidate =
IC-2 agreement (plus the reversal-phase tracking observed-but-unmeasured in the first
screen). Freezing that metric is a PILOT_CONFIG amendment (new version, committed before
any C1-revision conversation exists) and a Gate-0 touch — founder signs, or it doesn't run.

## 6. Build order (after founder OK)

1. Script builder for IC-1/IC-2 (T1-style scriptbank extension; gaps as lived ticks).
2. Bucket-mapping judge rubric + deterministic truth extractor from obs series.
3. R12 design-time oracle screen on seeds 100–115; discard list committed.
4. Pre-register v2 gating protocol (T-INT + T2' + leakage) — then the campaign.
