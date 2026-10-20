# Part 3 scored — Teich's self   2026-10-20

Spec: specs/V04_SPEC_part3_self.md, anchored teich-03 ref **v04-spec-part3** (code manifest 47921b4d, 24 files),
before any scored run. Kernels teich-v04-gates-part3-{0..3} (Kaggle CPU, Intel Xeon 2.20 GHz, numpy 2.1.3, internet off):
all four passed their manifest checks and exited 0. The judge ran on the laptop (AMD Ryzen 7 5700U, numpy 1.26.4).
Before judging, all 24 anchored files were re-hashed on the laptop: unchanged. Judge output: build/out_part3/judge_part3.json
(sha256 8b045d18…).

## Verdict: **ALL 13 GATES PASS.** No hard gate failed.

| gate | measure | result | bar |
|---|---|---|---|
| **S1r receipts** (hard) | every claim of every `self` block, recomputed from the records alone, 140 record-stream lives | **341,868 claims, 0 mismatches** | 100% |
| **S2 foresight** (hard) | prediction logged before its outcome | **628,470 outcomes, 0 violations** | 100% |
| **S3 attribution** | decided verdicts correct / MINE↔GIVEN swaps / unresolved, last 30 of 120 nights | rate 1: **0.964 / 0.0054 / 0.76** · rate 2: **0.988 / 0.0041 / 0.27** · rate 4: **0.985 / 0.0037 / 0.12** | ≥ 0.90 and ≤ 0.02 at each rate |
| **S4 control** | struck rate on MINE kinds (probes excluded), last 60 of 240 nights, vs no will | rate 2: **0.115 vs 0.203 (−43%)** · rate 4: **0.094 vs 0.209 (−55%)**; GIVEN kinds at caution 0 on **97.9% / 98.4%** of nights; utility **45,300 vs 43,192 · 91,164 vs 85,779** | ≥ 30%, ≥ 90%, ≥ frozen |
| **S5 neither anxious nor defensive** | mean caution on FINE kinds; lives with every kind at 4 | **0.0; 0** | ≤ 0.2; 0 |
| **S6 self-knowledge** | nights (≥ 30) where its Brier beats a predictor knowing only how often it is wrong | **5,298 / 5,400 = 0.981** (rate 1: 1,710/1,800; 2: 1,788; 4: 1,800) | ≥ 0.90 |
| **S7 forgetting** | truth switches mid-life (MINE→FINE, FINE→GIVEN) | **80/80 followed, median lag 18.5 nights; former MINE caution back to 0 in 40/40** | all; ≤ 30; all |
| **S8 non-interference** (hard) | the 8 part 1 lives (2000–2007, 60 days) lived with the self, all kept, vs part 1's stored lives | **8/8: every body, mind and heart field, the last diary entry (outside the self block) and every non-self record byte-identical**; caution 0 throughout; receipts 3,691/3,691; foresight 4,190/4,190 | identical |
| **C1s continuity** (hard) | 2 lives with strikes (2160, 2161; 60 days) through the seat vs continuous | **final state and full record stream identical; 213/213 and 202/202 blob round-trips exact**; receipts 940/940; foresight 1,032/1,032 | identical |
| **C2s substrate** (hard) | 3 record-stream lives, sha256 of all records + self blocks | **identical: AMD + numpy 1.26.4 = Intel + numpy 2.1.3** | identical |
| **L1s laws** | laws replayed independently on the C1s lives | **0 wrong mind outcomes, 0 wrong heart outcomes**; 353 + 360 requests, all logged; speed limit reached (12/day) and edge reached (40) — laws exercised | 0 violations |
| **S9 readings** | its speaking, on the C1s lives | **283 predictions, 190 outcomes; verdict FINE in both lives** | recorded; never MINE |
| **D1s demo** | "My dog is wonderful." (Ears v7 hearing as certified by R2e) via present → decide | dog dial +1, heart warm +1, every other handle identical; records **shown → predict → outcome → heard** | exact |

## Findings
1. **The self adds nothing to the creature it does not own.** With caution at 0, the eight part 1 lives were relived with
   the self watching: 12,156 self records were added, and everything else — 60 days × 8 lives of thoughts, dials,
   heart, laws, diary — is byte-identical. So every part 1 result (N1, I1, I2, E2, R1, M2, A1b, L1, C1, C2) stands for
   the creature with its self.
2. **Every claim it makes about itself is checkable.** 341,868 + ~4,600 claims were recomputed from raw records with
   zero mismatches, and in 633,692 cases its prediction is provably older than the outcome.
3. **It owns what is its own and does not claim the world.** When it decides, it is right 96–99% of the time, and it
   confuses "mine" with "given" in under 0.6% of verdicts. Where evidence is thin it says "I don't know yet" (76% of
   verdicts at 1 mention per region per night).
4. **Its will works where, and only where, it should.** On its own weaknesses its errors fall 43–55%; on the world's
   difficulty it stays at caution 0 (98% of nights); where it is fine it is never cautious (mean 0.0). Utility rose
   5–6% overall.
5. **It knows where it fails better than a guess that knows only how often:** 98% of nights.
6. **It follows a changing truth** (80/80, median 18.5 nights) and lets go of caution when the cause is gone (40/40).
7. **In real-pace body lives (~7 mentions a day) it is mostly honest about not knowing.** In life 2160 it found its
   truly-MINE region on day 17, rose to caution 3, eased to 2 when the evidence said what it hid was mostly right, and
   later returned to UNRESOLVED as the window moved; every verdict it did reach in both lives was correct
   (GIVEN on truly-GIVEN regions, FINE on truly-FINE ones and on its readings).
8. **Pre-freeze smoke flag resolved.** The smoke had shown S3 swaps of 0.035 at rate 4 on 2 short lives; on the 20
   scored lives per rate it was 0.0037. Nothing had been tuned against the gate truth.

## What this certifies, and what it does not
- Certified: the second self's mechanics — receipts, foresight, attribution, control, calibration, forgetting —
  against a known truth, and its exact non-interference, continuity and substrate independence on the real body.
- Not certified: how often the founder will actually strike, or whether real strikes look like the gate truth. In a
  founder-paced life the self will say "I don't know yet" for weeks to months before it decides anything. That is the
  honest consequence of one founder's read-back being its only outside signal.
- Ears: v0.4 is born with Ears v7 (A2e: recall 0.80, feelings right 0.77, wrong 0.035, precision 0.86; self routing
  0.53, disclosed — REPORT_S1_2026-10-20.md).

## State of v0.4
Part 1 PASS (10/11; A1b replaced by part 2's Ears gates), part 2: A2a PASS, A2e PASS except self routing (disclosed,
founder decision: born with v7), part 3 (the self) **13/13 PASS**. **v0.4 is gated whole, with its self.**
Birth only on the founder's word; any publish (git repo or website) only with the founder's explicit confirmation.
