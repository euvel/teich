# Teich v0.5, step 5: harness smoke and freeze (2026-10-22)

Written before any scored run. Every number below comes from design seeds (3000, 3001, 9000, v0.4's smoke seeds) and short lives. No gate seed has been used.

## What the smoke found

### 1. A creature fault, fixed: a too-stretched day could crash the wake
The N0 smoke life (schedule 3001) died inside a dream with `piece polygon not closed`. After the first fix, a rerun died with `seam pinning failed`.

Both failures come from the same cause. When the day's twists stack on the thinking handle, the shape can need more than the surface can hold exactly:
- its domain may not close at word length 8, or
- its seam may not pin to the pants cuff to machine precision.

The step-2 refusal law covered only the third form of this limit, too many slots, so the other two escaped as crashes. In a live creature, that crash would stop the wake.

**Fix.** `work_v05.rows` now reports all three as the same lawful event, and the day's last thoughts are refused and recorded (`thought-refused`, why "working memory too stretched for its surface"). Spec §3.2's law is reworded to name all three.

**How often.**

| Days tested | Result |
|---|---|
| Random 12-thought days | 1 of 40 did not close at 12 thoughts; none failed at ≤ 11 |
| One region repeated | reaches the limit after 7–12 repeats, depending on the region (regions 1, 3 and the self curve never did in 12) |
| 150 days mixing 1, 2, 3 or 9 regions | 0 escapes; refusals mostly fall on days built from 1–2 regions |

**Effect on claims.**
- A repetitive day thinks fewer of its rehearsals. The refusal is in the record and the THINK prediction is made before the dream.
- The cost is the time of the refused builds.
- Nothing inherited is touched. The main body, dials and heart are proven untouched by N0 and O2.

**Test.** The failing day [2,3,2,1,6,6,8,4,8,4,7,5] now dreams on its first 11 thoughts, and the handle returns to its rest rows bit-exactly.

### 2. Harness fixes (no gate truth involved)
- The judge treated S1r and S2 as soft, while the spec marks them hard. They are now hard (`S_hard`).
- The judge lost O1's "missing" flag when O1's output was absent. Fixed.
- The spec's S-set row said the inherited gates run "on the new kinds". They actually run v0.4's own harness with the v0.5 self, and the new kinds are receipted by F1 and F1 live. The wording is corrected.

### 3. Smoke verdicts (harness check, not evidence)
| Gate | Smoke | Note |
|---|---|---|
| N0 | pass | body, dials, heart and commitments identical; non-self records identical by meaning |
| F1 | pass | 773 acts, 0 flags; sufficiency 0/297; both planted causes caught (44 sufficiency flags / 30 log flags) |
| F1 live | pass | |
| O2 | pass | control handles within 1.1% of rest (bar 2%) |
| L1 | pass | self 0.002% of body; oracle 100% at 1.01× the cost of living, against the cheap self's 55% |
| C1 | pass | seat = continuous; 31/31 round-trips exact; v0.4 laws hold; 5 questions delivered |
| S1r, S2 | pass | |
| G1 body | pass | 0.5.1; twins identical except growth records |
| S3 | fail | swaps 0.035 at rate 4 on 2 short lives. This is the **same** flag v0.4's smoke showed (scored: 0.0037 on 20 lives); the inherited self reproduces it exactly |
| Q1 | fail | 3 seeds is underpowered (the scored run uses 30; the 30-seed design passed at 3/day) |
| C2 | fail | needs the second machine (Kaggle, numpy 2) |
| O1, Q3, G1 Ears, dry run | not run | Kaggle kernels only |

**THINK** stays UNRESOLVED in the short smoke life, as expected: it needs 20 nights.

## Frozen
- Spec `specs/V05_SPEC.md`, with exact bars in §7.1.
- Code manifest `specs/CODE_MANIFEST_v05.sha256`, covering every file the kernels run, the harness, the head-to-head, this report and the step 1–4 reports.
- After the anchor, any change to a manifest file is an amendment, disclosed and anchored before its look.
