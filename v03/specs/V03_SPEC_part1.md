# V03_SPEC part 1 — body, memory and the theorem's gates   **FROZEN 2026-10-03**

Founder freezes this before any scored run; its sha256 is then anchored in the seat chain.
Part 2 (meaning test M1 and the maturity / public-speech demos D1–D3) is frozen separately,
before those runs, so each part is pre-registered before its own data exists.

## 1. Genome
- **Body:** Nakada map `T_α` on `[α−1, α)`, one iterate per tick, float64, deterministic
  (new substrate reference hashes at birth, Zen-class runners as for v0.1/v0.2).
- **Operating range:** α ∈ [0.4115, 0.5]; memory states k = 0…6, `α_k = 0.4115 + k·(0.5−0.4115)/6`.
- **Certified chaos:** λ = π²/(6 log G) = 3.418316 at every memory state (Nakada / Kraaikamp–
  Schmidt–Steiner plateau theorem; K1 numerics agree to 7·10⁻⁴).
- **Memory (dynamical):** integer `k`, birth value 3 (the middle, so both signs are representable).
  Changed only by logged ±1 events. At 0 or 6 a further event in that direction is **refused and
  logged** (declared capacity, never silent).
- **Memory (concept lens):** per-concept integer ledger + marking word `W ∈ SL(2,ℤ)`, identity at birth.
  Exact. Its consequence is a change of interpretation, not of dynamics; it is measured and reported
  separately and is **not** covered by the theorem.
- **Sealed φ:** as v0.2 (appears in no update and no observable).
- **Observables (condition N):** functions of x only — `O = 1[x<0]`, the digit stream, the
  concept path. The selector never reads k, the ledger or W directly.

## 2. Gates (arms: A = genome; B = same, store leaks toward birth value with τ = 2·10⁴;
C = no store, α fixed at α₃). n = 48 paired seeds, seeds 900–947 (disjoint from all spent ranges
and from the K1/K2 design seeds). One look.

| gate | measure | pass bar (A) |
|---|---|---|
| G1 persistence | paired D on window-mean of O, W = 8000, silent gaps 10³, 10⁴, 10⁵, 10⁶ ticks, input = one ±1 event from k = 3 | D ≥ 0.80 and bootstrap CI lower > 0.60 at every gap |
| G2 consequence | mean window difference of O between k and k±1 over all adjacent pairs | every adjacent gap ≥ 0.020 (CI lower bound) |
| G3 product | slope of D × gap vs log-gap | 95% CI includes 0 |
| G4 invariants | λ by Birkhoff average of −2 log\|x\|, 10⁷ iterates per state | \|λ − 3.418316\| ≤ 0.002 at all 7 states |
| G5 interference | decodability of one event after K ∈ {1, 4, 16, 64} random ±1 events | consistent with the predicted law (stated in the report before running) |
| G6 condition N | (static) observables computed by functions whose only input is x; (dynamic) change k with x frozen for one tick → observables bit-identical | both pass |
| L1 language exactness | every inner word's trace type and intensity recomputed independently | 0 mismatches |

Predicted for controls: B fades (D below 0.20 by 10⁶), C ≈ 0.
Decision: G1–G4, G6, L1 all pass and controls behave as predicted → PASS. **Any G4, G6 or L1
failure = FAIL regardless of the rest.** G5 is falsification-only.
Multiplicity: this is the project's sixth pre-registered screen; the bar is not lowered for it.

## 3. Founder decisions (2026-10-03, recorded verbatim in substance)
1. 7 memory states (≈ 2.8 bits of dynamical memory) — accepted on recommendation; more capacity
   comes with growth (v0.4).
2. One iterate per tick at 1 Hz (W = 8000 ≈ 2.2 h of its life) — accepted.
3. Two-part freeze — accepted. Part 2 (M1 meaning test, D1–D3 demos) is frozen before its own runs.
4. Public speech — a PASS does **not** open public speech automatically. If the gates pass, the
   founder decides then. Founder-only speech stays in force until that decision.

## 4. Integrity
- This file's sha256 is anchored in the `teich-02` seat chain (event `git-anchor`, ref
  `v03-spec-part1`) before any scored run. Any later change = a new version with an amendment log,
  anchored again before use.
- K1/K2 design runs (REPORT_K1K2_2026-10-03.md) preceded this freeze and used design seeds only.
