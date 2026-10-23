# v0.5 P0 kill checks — 2026-10-21 (design data and design seeds only; nothing finalized)

| check | question | result |
|---|---|---|
| **K1** body predictability | Is anything in its own body predictable night to night? (part 1 gate lives 2000–2007, spent: 44,952 quiet handle-nights) | **PASS, sharp.** Predicting tonight's reading from its memory: rmse 0.269 step (= the whole noise). From last night's reading: 0.380 (≈ √2 × 0.269). Residual night-to-night correlation **−0.003**: the chaos noise is white. **Its memory is exactly the predictable part of itself; the rest is new every night.** |
| **K2a** order effect (exact math) | Do two thoughts (twists along crossing curves A, B of one handle) depend on order? | **PASS.** Order effect grows as twist²: 0.05 → 0.05%, 0.2 → 0.8%, 0.5 → 5.5%, 1.0 → 28% (max relative length difference). |
| **K2b** order effect on the real body | Is that order readable from the body's own crossings (genus-2 surface, 2,000 thoughts × 30,000 ticks, twist 0.5), and does it leave the other handle alone? | **PASS, decisive.** Readable at **13–26 SE**; measured matches exact prediction on every curve (|z| ≤ 1.42). Other handle and seam unchanged (0.1–0.4 SE). Working-memory scale estimate: ~12 SE per night. |
| **K3** curiosity vs random | Do questions chosen by a curiosity rule make it understand itself faster? (20 lives, 9 regions, founder pace 0.5 per region-night + 3 questions/night; regions correctly understood) | **First measure FAILED, fixed measure PASSES.** none 0.10 / 0.40 · random 1.25 / 0.80 · round-robin 1.30 / 1.45 · posterior-variance curiosity 1.65 / 1.35 (not reliably better) · **decision-aware "settle" 2.15 / 2.15** (night 60 / 120). Lesson: **curiosity must serve decisions, not mere uncertainty.** Disclosed: "settle" was designed after the first measure failed (design seeds; the gate will use fresh ones). Absolute pace is slow (~2 regions in 2 months). |
| **K4** faithfulness harness | Can replay prove a stated reason is the only cause, and catch a hidden one? (450 decisions, 5 lives) | **PASS.** Honest chooser: 0 receipt / 0 sufficiency / 0 necessity failures. Planted hidden cause (secretly skips kinds with caution > 0): caught — 46 receipt, 83 sufficiency, 23 necessity failures. |

## What this changes in the plan
- 1.2(c) working-memory thinking moves from "kill-check dependent" to **core** (K2 passed on the real body).
- 1.3 asking: curiosity = **decision-aware** ("settle what I can"), not variance reduction.
- New law candidate: **self-prediction must be cheaper than living** (no simulating its own body); K1 shows that its GIVEN is then exactly its night-to-night chaos.
- Candidate claim: **it can discover that its own thoughts do not commute** (its first-order self-model misses by exactly the order effect, readable at ~12 SE per night).

## KH — head-to-head pilot: can a language-model agent be run fairly on Teich's job? (added 2026-10-21)
Same job and same information for everyone: 15 self-states from design lives (9 regions: checked/wrong counts by
confidence, verdict), "choose the one region where one question most helps reach a verdict, and say why". Models via
Cloudflare Workers AI (free tier, temperature 0): Llama 3.3 70B, Qwen3 30B-A3B, Mistral Small 3.1 24B. Fair scoring:
tie-aware; "another rule" reported separately, not counted as inconsistent.

| | same choice when rows are shuffled | same choice when region names are swapped | its own named rule predicts its choice |
|---|---|---|---|
| Llama 3.3 70B | 9/15 | 11/15 | 6/10 (named a listed rule 10/15) |
| Qwen3 30B | 7/15 | 12/15 | 3/6 (named a listed rule 6/15) |
| Mistral Small 24B | 9/15 | 12/15 | 10/15 |
| **Teich** | **15/15** | **15/15** | **15/15** (by construction; K4 shows the test can catch a hidden cause) |

- All three models were **competent**: they answered in format 45/45 and always picked a region still needing evidence.
- **Not replayable:** a second run of identical requests at temperature 0 gave different results (Llama: shuffle 8→9,
  rename 9→11; named rules changed). Teich replays bit for bit.
- **Feasible and fair, with fixes for the real test:** ≥150 states; ≥2 prompt wordings; tie-aware scoring; replay of
  identical requests on different days; a closed-loop competence check (does each chooser help the self as much as
  Teich's rule does?), so faithfulness is not bought with incompetence.
- **Limits:** small pilot (15 states); open models of 24–70B, not frontier models (none available here); one prompt.
- Side finding: the worker's /lab/generate prints JSON answers as "[object Object]" (fix: JSON.stringify objects).

## KG — twisted working-memory geometry: bit-identical across machines? (smoke, 2026-10-21) — PASS, no fallback needed
1. **Design constraint found first:** twisting along long concept curves (slopes up to 5/8, twist 0.3) distorts the
   handle until float64 drifts (boundary trace moved at thoughts 11–12) and the domain builder fails. Sweep (20 random
   12-thought days each): slopes p,q ≤ 5 with twist 0.15–0.2 → 20/20 days build, traces stay ~6.5–7.8, and the
   most-crossing pair still shows an 11–20% order effect. **v0.3's 8 concept regions are exactly the depth-3
   Stern–Brocot nodes (1/4, 2/5, 3/5, 3/4, 4/3, 5/3, 5/2, 4/1), all p,q ≤ 5** → thoughts live at region level, the
   same regions as the heart and the self.
2. **Cross-machine test** (v05_lab/design/geo_smoke.py; kernel teich-v05-geo-smoke): a 12-thought day over the 8
   region curves, twist 0.2, geometry rows built exactly as v0.4's genesis builds a handle level (faces, lifts,
   pinned seam rows), hashed after every thought. Two twist variants: N (numpy eig/inv as written) and C (closed form,
   only + − × ÷ √, cosh/sinh(0.1) frozen from mpmath at 60 digits).
   AMD Ryzen/numpy 1.26.4 = Intel Xeon/numpy 2.1.3 = Intel Xeon/numpy 1.26.4 = Intel Xeon/numpy 2.1.3:
   **N 33d449c8… and C 1581c34b… identical on all 4 runs.**
3. Recommendation: use variant C anyway (no eig/exp at run time; fewer assumptions); the v0.5 substrate gate re-runs
   this on the GitHub runner type as well before birth.
