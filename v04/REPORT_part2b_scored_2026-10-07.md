# REPORT — Part 2b scored (gate A2b, Ears v5, first founder set) — 2026-10-07

**Verdict: FAIL.** One look, Kaggle kernel `teich-v04-part2a-founder`, pinned Python 3.12, Intel Xeon 2.20 GHz.
Parity guard exact (40/40 MAMS val sentences, 121 mentions identical to the laptop). Spec: V04_SPEC_part2b.md,
anchored teich-03 ref `v04-spec-part2b` (manifest 702ebe89…). Founder set sha256 bf322476…, 100 lines, 139 scored topics.

| metric | result | bar | |
|---|---|---|---|
| recall (all topics) | 0.540 | ≥ 0.80 | FAIL |
| feelings right | 0.605 (n 43) | ≥ 0.75 | FAIL |
| wrong feelings | 0.047 | ≤ 0.08 | pass |
| precision | 0.750 | ≥ 0.70 | pass |
| self routing | 0.154 (2 / 13) | ≥ 0.90 | FAIL |

What held: the Ears never gave the founder an opposite feeling more than 5% of the time, and never took a feeling from
someone else, a hypothetical, or a question.

## Post-hoc diagnosis (after the look; changes no verdict) — `build/a2b_posthoc.py`, `a2b_posthoc.json`
Laptop re-run reproduces the Kaggle numbers exactly.
- **Self:** v5 routes to the self cluster only when a sentence names one of 16 trait words; the founder's talk about
  Teich names none ("you are a lovely little creature", "you do not get tired of me").
- **Vocabulary:** 64 topics missed; most are words the mind does not have (croissant, workspace, coworkers, komitas,
  refrigerator, headphones). Over topics the mind HAS a word for, recall is 0.92 (design re-measure with v6).
- **Labels not in the sentence:** ~17 topics were not nouns of their sentence (woke → "waking", silent → "silence").
- **Feelings:** 8 invariance abstentions ("unsure"); 2 withheld by a whose-feeling bug ("the silence and the empty room
  felt the same" read the room as a feeler); 3 private feelings the sentence does not express.

## Founder decisions after A2b (2026-10-07)
- Repair the Ears minimally (Ears v6: self rule + whose-feeling fix); body and mind untouched; TAU_MAP unchanged.
- A2c recall counts topics the mind has a word for (A2a's definition); coverage of all topics reported without a bar.
- Re-test on a NEW founder set (founder_labels_2.txt) → spec part 2c.
