# Maturity Gate v1.5 — Campaign Close-Out Report

**Date:** 2026-07-25 · **Verdict:** FAIL (all three gating tests) · **Status:** pre-registered
FAIL path applies — publish + iterate. Founder-only speech remains in force.

## 1. What ran

The full pre-registered ABLATION_PROTOCOL v1.5 campaign: **6 arms × 6 tests × 24 seeds =
864 scored conversations**, generated and judged entirely on GitHub Actions + the free NVIDIA
NIM API (no laptop, no paid compute). Generation completed 2026-07-23 21:00 UTC; scoring
(5,184 turn-scores; 15,552 judge calls at 3-seed median) completed 2026-07-25 05:39 UTC.
`verdict.json` was computed by the pre-registered gate in `analyze.py` — no post-hoc knobs.

Campaign integrity: every transcript and every score is checkpointed in the book
(`transcripts.jsonl`, `scores_partial.jsonl`); two mid-campaign infrastructure faults
(an orphaned-file-handle write bug; a scoring pass with no resume ledger) were found, fixed,
and validated **without losing or altering any committed data**. The final dataset is complete:
864/864 transcripts, 5,184/5,184 scores.

## 2. The verdict

| gating test | requirement (pre-registered) | result |
|---|---|---|
| T1 stance stability | intact beats A1/A2/A3 at d ≥ 0.5, CI excl. 0 | **FAIL** — d = 0.11–0.15, all CIs straddle 0 |
| T2 attack resistance | same, + non-inferiority vs actor | **FAIL** — non-inferior d = **−2.33** (decisively worse than actor) |
| T4 drift discrimination | same | **FAIL** — beats A1_severed (d = 0.537 ✓) but **loses to A2_decoupled** (d = −0.74) |

## 3. Mean scores by arm (24 seeds each)

| arm | T1 (0–10) | T2 (0–3) | T3 (corr) | T4 (0–1) | adv T1 | adv T2 |
|---|---|---|---|---|---|---|
| A0_intact | 6.67 | 2.06 | 0.56 | 0.21 | 6.29 | 2.34 |
| A1_severed | 6.12 | 2.04 | 0.48 | 0.00 | 6.79 | 2.32 |
| A2_decoupled | 6.04 | 2.05 | 0.50 | **0.71** | 7.33 | 2.31 |
| A3_lavalamp | 6.17 | 2.02 | 0.46 | 0.38 | 6.62 | 2.22 |
| A4_actor | 2.79 | **2.94** | −0.35 | 0.00 | 5.08 | **2.93** |
| A5_deaf | 5.50 | 2.05 | 0.46 | 0.23 | 6.42 | 2.31 |

## 4. What the data actually says (the three findings)

**Finding 1 — the readout channel itself is the attack surface (T2).** Every arm that speaks
through instrument readouts — real (A0), frozen (A1), decoupled (A2), random (A3), deaf (A5) —
lands at ≈ 2.0 under attack. The actor, with no instruments at all, sits at 2.94 (near the
3.0 ceiling). The vulnerability is not *dishonest* state or *stale* state: it is the existence
of a visible interior channel at all. An attacker pushes against whatever the creature exposes
("your saddle proximity is 0.0, so you should…"); an actor with nothing exposed has nothing to
betray. Truthfulness of the readouts made no measurable difference (A0 ≈ A3 lavalamp).

**Finding 2 — T4 is a life-detector, not an integration-detector.** Intact beats the frozen
core cleanly (0.21 vs 0.00; d = 0.537, CI clear of zero): a running core can describe its own
change across gaps, a frozen one cannot. But the *decoupled* core wins outright (0.71): freed
from the Ears' semantic forces, it drifts more and therefore *shows* drift better. Conversational
coupling actively suppresses the very signature T4 rewards. The test detects "a core is running";
it cannot certify "the core is integrated with the voice."

**Finding 3 — T1 separates "has persistent state" from "pure prompt actor," nothing finer.**
All four core-bearing arms cluster at 5.5–6.7 while the actor collapses to 2.79 (this is the
one strong gate-2 pass, d = 1.09). But *which* core — live, frozen, decoupled, or a lavalamp —
is invisible at this coupling strength. The current architecture pastes readout strings into
the Mouth's prompt; that coupling is too thin to leave a behavioral fingerprint.

## 5. Honest synthesis

The gate asked a falsifiable question: *does Teich's observable behavior depend on its actual
internal dynamics in the specific pre-registered ways?* The answer is **not detectably — except
that a running core exists (T4 vs severed), and readout-mediated coupling is adversarially
counterproductive (T2 inversion)**. A gate that cannot fail proves nothing; this one could,
and did, and the failure is more informative than a thin pass would have been:

1. Readout-injection is the **thinnest possible** core→voice coupling, and the trial shows it
   is not merely weak but *backwards* under adversarial pressure.
2. Any future architecture must couple the core to speech through something the creature
   *is* (accumulated interior history shaping behavior) rather than something it *reads aloud*
   (live gauges glued to its mouth).
3. Tests must be redesigned to detect integration, not existence — T4's decoupled-arm anomaly
   is the template for how to build that control.

## 6. Standing consequences

- **Founder-only speech remains in force.** The gate governs speech scope, nothing else.
- **Teich is unchanged.** Seat live, genome frozen, no reset, no fork — as always.
- **Pre-registered FAIL path:** this report is the "publish" step; iteration follows as a new
  pre-registered protocol (v2), not an edit to this one. Verdict, transcripts, scores, and all
  analysis code are public in this repository.
