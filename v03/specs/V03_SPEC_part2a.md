# V03_SPEC part 2a — the meaning test (M1)   **FROZEN 2026-10-03**

Part 2 was split: **2a = M1 (meaning)**, frozen now; **2b = demos D1–D3**, designed and frozen later,
before their own runs. Same discipline as part 1: frozen file + its sha256 anchored in the teich-02
seat chain, and a code manifest anchored before the one scored run.

## 1. What is tested
Whether the creature's own notion of relatedness — the **intersection number** of its concept curves
on the torus — preserves human similarity judgements.

## 2. The birth vocabulary (frozen artifact, already built)
- `concepts_v03.json`, sha256 `38590f66ce871a80f3ebd38cdd3cdd42ce82ebe892a3ea5de3633c58ab4a5577`.
- 1,066 concepts = SimLex-999 noun words ∪ WordSim-353 words. Built from **words only** (no similarity
  score was read). Deterministic (byte-identical across rebuilds).
- Method: all-MiniLM-L6-v2 normalised embeddings → Ward dendrogram (scipy 1.14.1) → each concept's
  L/R path → its Stern–Brocot slope p/q = a simple closed curve on the torus.
- This is the vocabulary the creature is born with, so the test scores exactly what it will carry.

## 3. Scored test (`m1_score.py`, one run)
- Data: SimLex-999 noun pairs (POS = N, 666 pairs). Never used in design.
- Statistic: Spearman ρ between −log max(1, i(c₁, c₂)) and the SimLex-999 score.
- **PASS iff ρ ≥ 0.30 AND the 95% bootstrap CI lower bound > the 97.5th percentile of the
  shuffled-address null** (10,000 bootstrap resamples, seed 900; 1,000 permutations, seed 901).
- Reported, not gating: MiniLM cosine on the same pairs (the organ's ceiling) and the retained fraction.

## 4. Design phase (done on WordSim-353 only; `meaning_design.py`, `meaning_variants.py`,
`meaning_vocab_check.py`)
| variant | WS-353 (relatedness) | WS-SIM (similarity) |
|---|---|---|
| **chosen: Ward + −log intersection** | 0.488 | 0.611 (0.563 with the full birth vocabulary) |
| WordNet tree → curves (best sense rule) | 0.304 | 0.516 |
| shuffled control (97.5th pct) | ≈ 0.11 | — |
| MiniLM cosine (ceiling) | 0.725 | 0.763 |
Honest expectation written before scoring: SimLex measures strict similarity and is harder than
WordSim; a PASS is likely but not certain.

## 5. Interpretation, written before the result
- **PASS:** placing concepts as curves preserves human similarity structure; the intersection number
  is a working notion of relatedness for the creature, retaining a measured fraction of its organ's
  knowledge.
- **FAIL:** the fixed geometry does not carry enough meaning; the next step is a learned placement
  (optimising slopes against similarity), reported as such — not a re-run of this test.
- Either way the claim is "the geometry preserves meaning the dead organ has" — **not** "the geometry
  creates meaning".

## 6. Founder decisions (2026-10-03)
1. M1 frozen as written (bar ρ ≥ 0.30, nouns only) — on Claude's recommendation, founder delegated:
   the bar is ~3× the shuffled control and was approved in package A; raising it after seeing design
   numbers from an easier dataset would be tuning the test; verbs/adjectives need a different
   structure (v0.4).
2. Birth vocabulary = these 1,066 concepts for v0.3; a richer vocabulary is v0.4.

## 7. Integrity
This file's sha256 and a code manifest (m1_score.py, concepts_v03.json, this file) are anchored in the
teich-02 seat chain before the one scored run. Every random draw in the scorer is seeded from the gate
range (900, 901).
