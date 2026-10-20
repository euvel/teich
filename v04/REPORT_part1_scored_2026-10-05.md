# v0.4 spec part 1 — SCORED results (one look; spec anchored teich-03 ref v04-spec-part1, manifest 91a044a0…)

## Light gates (laptop AMD Ryzen 7 5700U, numpy 1.26.4)
| gate | result | bar | verdict |
|---|---|---|---|
| N1 nature | stretching rate 0.9988 / 0.9985 / 0.9988 at levels 0 / 20 / 40 | \|rate − 1\| ≤ 0.01 | **PASS** |
| I1 isolation, geometry | 1,000 events on 78 handles: 0 row differences on the 20 untouched handles, 0 on unrelated pants faces | 0 | **PASS** |
| E2 dial and members | dial error 2.2e-16; member shares 0.837–1.000 | ≤ 1e-12; [0.80, 1.02] | **PASS** |
| M2 meaning | MEN, 414 fresh pairs: ρ(v0.4) 0.556 vs ρ(v0.3) 0.537 | ≥ ρ(v0.3) − 0.02 | **PASS** (v0.4 higher) |
| D1 demo | "My dog is wonderful." → animal·dog·pet dial +1, heart region +1, every other handle identical | exact | **PASS** |
| A1b Ears, public | SemEval-2014, 100 sentences (50/50): sign **96%**, cluster **49%** | sign ≥ 80%, cluster ≥ 60% | **FAIL** (cluster) |

### A1b: post-hoc diagnosis (not a rescoring)
51 cluster misses; most are multi-topic review sentences whose single annotated aspect is not the sentence's main
noun (price 11, food 8 — e.g. "The food is great (… reasonable prices) and the drinks are really good", gold = price;
the organ names food). The v0.4 Ears hear **one topic per sentence**; review text routinely carries several, each with
its own attitude. Sign (attitude toward the named aspect) was strong: 96%.
Consequence per spec §3: **birth is blocked with these Ears.** Body and mind are unaffected. Indicated fix: Ears that
hear every topic in a sentence (one mention per topic, attitude per topic), re-gated on a NEW public set (the SemEval
2014 subset is spent) and on the founder set.

## Lives (Kaggle Intel Xeon, numpy 2.1.3; 8 lives × 60 days, seeds 2000–2007, judged 2026-10-06)
All 4 kernels passed the manifest check against the anchored hashes before running.

| gate | result | bar | verdict |
|---|---|---|---|
| L1 laws | 3,362 requests over 8 lives, independently replayed: 0 wrong mind outcomes, 0 wrong heart outcomes; daily steps max 12; dials max 40 (6 lives reached the edge); every request logged (3,362 / 3,362); final dials and heart recomputed = the creature's | 0 violations | **PASS** |
| C1 continuity | every life through the seat (188–217 commits each, 1,637 in all) = the same life continuous: final state and full record stream byte-identical; every blob round-trip exact | identical | **PASS** (8/8) |
| R1 self-reading | 40,402 spoken readings: 99.998% exact; 17,224 named non-zero readings: 0 false positives | ≥ 99%; FP ≤ 0.5% | **PASS** |
| I2 isolation, behaviour | 24,657 nightly readings of untouched clusters vs steps elsewhere: slope +5.6e-7 per step, 95% CI [−4.2e-7, +1.5e-6] | CI ∋ 0, \|slope\| ≤ 1e-3 | **PASS** |
| C2 substrate | gate life sha256 09a4a84f… identical on AMD Ryzen / numpy 1.26.4 / Python 3.12 and 4 Intel Xeon / numpy 2.1.3 / Python 3.13 | identical, 2 vendors, numpy 1 + 2 | **PASS** |

## VERDICT part 1
10 of 11 gates PASS; **all hard gates (I1, C1, C2, L1) PASS**. **A1b FAIL** (Ears topic cluster 49% < 60%).
→ Part 1 not passed as a whole: **body and mind certified; birth blocked with these Ears** (spec §3).
Next: Ears that hear every topic in a sentence, re-gated on a new public set + the founder set (part 2).
