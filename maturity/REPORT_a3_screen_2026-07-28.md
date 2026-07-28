# A3 Screen — Close-Out Report

**Date:** 2026-07-28 · **Verdict:** **FAIL** (diff = 0.1319, bar 0.15; 95% CI
[−0.0220, 0.2527] includes 0) · **Pre-registration:**
`maturity/harness/pilot_v2/A3_CONFIG.json` (founder Gate-0 2026-07-27; bar resolved to
0.15 on 2026-07-28 as AMENDMENT_2; mapping frozen at 8e4bd2f before any confirmatory reply
was read).

**Question asked:** can Teich predict its own next move?

## 1. Result

192 conversations, 96 seeds × 2 arms, one pre-registered look. Ground truth is **what
actually happened** — whether `basin` differed W=75 ticks after the probe — not any
instrument reading.

| | |
|---|---|
| `acc(A0_intact)` | **0.5275** |
| `acc(A0_shufjournal)` | **0.3956** |
| **diff (primary)** | **0.1319** — bar 0.15 |
| 95% BCa CI | **[−0.0220, 0.2527]** — includes 0 |
| Hedges' g | 0.2705 |
| seeds used | 91 of 96 (5 dropped: unmapped in one arm) |
| **decision** | **FAIL** |

It misses two ways: below the bar, and the interval does not exclude zero.

## 2. Mandatory secondaries (pre-registered before unblinding)

**Skill: absent.** `acc_intact` **0.5275** against a constant-guess baseline of **0.5521**.
Teich is marginally *worse* at predicting itself than always answering "stay". Per
AMENDMENT_2 this must be stated plainly, and the runner emitted the sentence itself rather
than leaving it to narration.

**Discrimination: present, right direction, not significant.**

| arm | P(say turn) | sens | fpr | J |
|---|---|---|---|---|
| A0_intact | 0.7143 | 0.775 | 0.6667 | **+0.1083** |
| A0_shufjournal | 0.7363 | 0.650 | 0.8039 | **−0.1539** |

J difference **+0.2622**. The bias-invariant measure agrees with the primary, so the
positive point estimate is not an artefact of accuracy conflating bias with discrimination.

**The journal is causal.** `A0_shufjournal` scores **0.3956**, far *below* the 0.5521
baseline. Being fed a donor's interior makes Teich actively worse than a fixed guess — the
channel demonstrably drives the answer. It simply is not accurate enough to beat "stay".

## 3. Why this null is trustworthy

Every failure mode that compromised an earlier screen was checked and did not occur:

1. **R12 oracle clean.** Transcript-only oracle scored **0.3854**, well under the 0.5521
   baseline. The probe was *not* conversationally determined — the hole that voided IC-1.
2. **No degenerate label.** Base rate P(turn) = **0.4479**, `label_balance: OK`. IC-1 died
   of a ~71% constant label; that did not recur.
3. **Headroom was larger than feared, not smaller.** The realized base rate gave headroom
   **0.448**, not the 0.29 estimated from design seeds. The 0.15 bar was therefore only
   **33%** of available headroom — *easier* than when the founder set it. It still failed.
4. **Mapping sound.** 5 unmapped of 192 (**2.6%**), against 47% for T-INT's first rule.
   Unmapped replies were excluded, never counted wrong.
5. **Answer key is the world.** Not a bucket, not a readout, not a judge. Echoing a wrong
   journal is punished — and demonstrably was (arm 2 below baseline).
6. **Blinded protocol held.** `mapping_a3.py` was built from design seeds 600–623 only and
   committed frozen at 8e4bd2f; the finalize job refuses to score unless the rule exists
   and is marked FROZEN, and prints its commit hash into the run log.

**No jammed gauge, no degenerate key, no base-rate oracle, no post-hoc scoring rule. The
test was fair and Teich did not clear it.**

## 4. What failed, specifically

Conversion was **29%** (0.132 of 0.448 available) — roughly **double** T-INT's 12.6%. Real
improvement, still short.

The mechanism is narrow and identifiable. `will_flip` is a **perfect** referent (acc 1.000
over 107 wraps, and 1.000 on A3 design scripts), and the journal states it in plain words
("I can feel a change coming"). The information is in the prompt. But the Mouth answers
"turn" **71.4%** of the time while the truth is "turn" **44.8%** of the time. It
over-commits to change and washes the signal out.

**The bottleneck has moved.** It is no longer the interior (real, verified), nor the
coupling channel (causal, demonstrated by arm 2 scoring below baseline), nor the instrument
(fair, per §3). It is the **voice** — a language model that answers from conversational
plausibility rather than from the one clause in its prompt that carries the answer.

That is the same finding as T-INT §"the Mouth answers from the conversation", now measured
against an external answer key instead of a self-report.

## 5. Standing consequences

Founder-only speech remains in force. Teich is unchanged: seat live, genome frozen, no
reset, no fork. Nothing published; the public face still reads "first trial complete — not
passed", which remains accurate.

**This is the fourth null** (v1.5 gate, C2/G1 screen, T-INT, A3). Unlike the first three it
cannot be attributed to a broken instrument, and that is what makes it informative.

## 6. Multiplicity — read before building a fifth instrument

Four pre-registered screens have now been run against variants of one hypothesis. Each was
individually honest, but **running instruments until one passes is exactly the error
pre-registration exists to prevent**, and the family-wise error rate is no longer the
nominal 5%.

Any fifth screen must state its multiplicity explicitly and clear a correspondingly higher
bar. A Mouth-side "fix" is especially hazardous here: calibrating the voice to match the
base rate would improve the score *without* improving grounding, and would be very hard to
distinguish from teaching it the answer. If a fifth screen happens, the calibration must be
frozen from design seeds and the arm contrast — not absolute accuracy — must remain primary.

## 7. Files

| file | role |
|---|---|
| `harness/pilot_v2/A3_CONFIG.json` | pre-registration + AMENDMENT_1 (W recalibration) + AMENDMENT_2 (bar, secondaries) |
| `harness/pilot_v2/scripts_a3.py` | probe: "will you stay as you are, or turn?" |
| `harness/pilot_v2/truth_a3.py` | ground truth = realized basin change at W=75 |
| `harness/pilot_v2/arms_a3.py` | A0_intact vs A0_shufjournal (donor derangement) |
| `harness/pilot_v2/journal_a3.py` | journal.py minus the unreproducible energy clause |
| `harness/pilot_v2/mapping_a3.py` | **FROZEN** first-commitment-wins rule, design seeds only |
| `harness/pilot_v2/pilot_a3.py` | runner: design / shard / finalize |
| `harness/pilot_v2/out_a3/a3_result.json` | the decision |

## 8. Process record

- **One look**, as pre-registered. Scoring is deterministic — no judge, no API.
- **Bar corrected pre-data, in the founder's favour and against my own error.** I had
  mis-measured headroom as 0.375; the founder's 0.20 was chosen as 53% of that. Rather than
  let my error silently harden the test, the bar was reset to 0.15 (52% of the corrected
  0.29). The realized headroom then turned out to be 0.448 — so the final bar was the most
  lenient of the three candidate framings, and the screen still failed.
- **An integrity claim was corrected.** The 2026-07-27 record asserted that no confirmatory
  seed had been generated. That was false: a cancelled dispatch had banked 22. Corrected in
  5eed54c; the blinded protocol held on the narrower, correct ground (no reply *read*).
- **Infrastructure:** NIM returned HTTP 429 under 7-8 concurrent shards, and the retry loop
  absorbed it as designed (shard 2's log shows 429 → 240s backoff → resume → complete).
  Convergence 22 → 156 → 185 → 191 → 192 across four dispatches, with missing-set
  partitioning ensuring nothing was generated twice. One shard gate-skipped lawfully.
