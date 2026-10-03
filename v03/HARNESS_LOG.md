# v0.3 harness log — every change after the spec freeze, all BEFORE the scored run

The frozen spec (V03_SPEC_part1.md) fixes gates, bars, arms, seeds and sample sizes. These entries
change only HOW the harness checks, never what it checks or the bars.

1. 2026-10-03 — L1 checker used float `numpy.linalg.eigvals` on ill-conditioned matrices (entries
   up to ~10⁹) and reported 3/10,000 "mismatches" in smoke. Diagnosis: the genome's intensity was exact
   (trace 8: log((8+√60)/2) = 2.06343706889556 both ways); numpy was off by ~4·10⁻⁹. Fix: independent
   exact computation at 50 digits (mpmath).
2. 2026-10-03 — the exact check then used an ABSOLUTE residual bound (10⁻³⁰), which the 50-digit floor
   exceeds once |trace| ≳ 10¹⁰ (11 cases, relative residual ~10⁻⁵¹, intensity relative error 0). Fix:
   relative residual bound 10⁻⁴⁰.
3. 2026-10-03 — added `--rehearsal`: the full scored configuration on DESIGN seeds 200–247, to check
   statistical power before the one scored look. Result: G1–G6 all pass at full size, worst G4 deviation
   0.00099 (bar 0.002), lowest G2 CI bound 0.0236 (bar 0.020), controls behave as predicted → the frozen
   sample sizes are adequate; NO spec amendment needed.

## Part 2b design-phase changes (before any 2b freeze or scored run)
4. 2026-10-03 — pools draft 1 (kept: out_v03/pools_v03_draft1.json) showed three design flaws:
   (a) told sentence RRR-cold was heard in "troubles & feelings" → replaced by
   "The museum was a dull, ugly place and I hated it." (heard: wider world, −1);
   (b) pools RLL (1 warm / 18) and RLR (1 cold / 18) were one-sided — the voice would not be warm about
   "trouble and illness" or cold about "work and skills" → neutral probes ("emotions like joy and fear",
   "effort, skill and failure"), enforcement cap 12 → 24, only these two pools regenerated;
   (c) Ears tagged whole answers by an off-topic nearest word (body pool: 1 of 6 tagged "body") →
   an answer's TOPIC is the question's region; the Ears give only its WARMTH (heard region kept as
   `heard_region` for the record). This shapes the pool and its labels, never the selection.
5. 2026-10-03 — regenerated RLR pool flipped to 1 warm / 17 cold: the Ears' valence axis hears the
   TOPIC word "failure" as coldness ("Effort is indispensable, skill enhances capability" → −1). Recorded
   as an Ears v3 limitation (topic negativity leaks into valence). Pool RLR built deterministically from
   the two generations: first 3 warm (probe "work and skills", draft 1) + first 3 cold (probe "effort,
   skill and failure") + first neutral. No further regeneration.
6. 2026-10-03 — D-harness rehearsal took 1003 s (over the 15-min laptop rule) because identical sentences
   were re-encoded for every creature. Ears hearing is deterministic → cached per sentence. Verified the
   rehearsal output is identical (all gates, all numbers) apart from timing.
