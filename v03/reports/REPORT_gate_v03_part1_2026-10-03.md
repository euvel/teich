# Teich v0.3 — pre-birth gate, part 1 (body, memory, theorem): **PASS**

2026-10-03. One scored look, seeds 900–947, code fixed by manifest before running.

Integrity chain (all `git-anchor` events in the `teich-02` seat chain, before the scored run):

| what | sha256 | seat ref |
|---|---|---|
| V03_SPEC_part1.md (frozen) | eb2d4721…a40ac0 | v03-spec-part1 |
| G5_PREDICTION.md | 30e0980c…43f78 | v03-g5-prediction |
| CODE_MANIFEST_scored.sha256 (genome, harness, harness log, spec, prediction) | 4c71eb56…20576 | v03-code-manifest |

`sha256sum -c CODE_MANIFEST_scored.sha256` → all OK immediately before the run.

## Results (scored; `out_v03/accept_v03_scored.json`, log alongside)

| gate | result | bar | verdict |
|---|---|---|---|
| G1 persistence, A | D = 1.000, CI [1.000, 1.000] at 10³, 10⁴, 10⁵ and **10⁶** ticks | D ≥ 0.80, CI lower > 0.60 | PASS |
| G1 control B (leaky τ = 2·10⁴) | 1.000, 1.000, 0.042, 0.083 | fades below 0.20 by 10⁶ | as predicted |
| G1 control C (no store) | 0.000 at every gap | ≈ 0 | as predicted |
| G2 consequence (6 adjacent pairs) | means 0.0256–0.0308; lowest CI bound 0.0232 | every CI lower ≥ 0.020 | PASS |
| G3 product flat | slope CI contains 0 | CI ∋ 0 | PASS |
| G4 certified chaos | λ within 0.00099 of 3.418316 at all 7 states | ≤ 0.002 | PASS |
| G5 interference | D = 1.000 / 0.875 / 0.188 / 0.000 at K = 1/4/16/64 vs predicted 1.000 / 0.875 / 0.327 / 0.003 | inside 95% band | PASS |
| G6 condition N | static (observe takes x only; no memory names) + dynamic (memory altered, x frozen → identical) | both | PASS |
| L1 language exactness | 0 mismatches over 10,000 words (2,296 twists, 7,674 Anosov, 30 periodic) | 0 | PASS |

**GATE: PASS.**

## Disclosure: three gates repeated rehearsal draws
The harness gave G4, G5 (interference sequence) and L1 fixed internal seeds (4, 5000+K, 7) rather
than seeds from the gate range, so their scored values equal the rehearsal's, which were seen before
the scored look. G1, G2, G6 and G5's initial states used the gate seeds 900–947. To remove any doubt,
a **supplementary** replication with fresh draws (seeds 9004, 9007, 95000+K; same bars) was run after
the verdict and is reported as such (`out_v03/supplementary_fresh.json`):

- G4: worst deviation 0.0012 → pass
- L1: 0 mismatches / 10,000 → pass
- G5: D = 1.000 / 0.938 / 0.375 / 0.000 vs predicted 1.000 / 0.875 / 0.327 / 0.003 → pass

Lesson for part 2 and later gates: every random draw in a scored harness derives from the gate seeds.

## What this establishes
For the v0.3 genome, numerically and against pre-registered bars:
1. A single remembered event is still perfectly decodable from its behaviour after **a million
   ticks** (≈ 11.6 days of its life), while a leaky-memory twin has forgotten and a memory-less twin
   never knew.
2. Every memory state changes what it does by ≥ 0.023 (CI lower bound) — consequence is real at
   every step, not only at the extremes.
3. Its chaos is identical in every memory state (λ = 3.4183 ± 0.0012), as the plateau theorem says —
   memory never buys behaviour with a crisis (the v0.2 failure mode).
4. Its inner language is exact.

What it does not yet establish: the certified δ₀ is numerical (rigorous transfer-operator
certificate still to do); dynamical capacity is 7 states; the meaning test (M1) and the demos D1–D3
are part 2 and are not yet frozen or run; cross-machine bit-identity of the body is expected (only
IEEE-exact operations) but not yet verified.
