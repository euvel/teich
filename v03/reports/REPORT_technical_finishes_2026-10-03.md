# Teich v0.3 — technical finishes before birth (2026-10-03)

Still private, unborn, unpublished. The Kaggle kernel used is PRIVATE (CPU, no internet).

## 1. Substrate reference — DONE
`verify_substrate_v03.py` replays a fixed scripted life (4 creatures × 8 bodies, 200,000 ticks, six
memory events across conversations, one lawful commitment, a selection every 8,000 ticks, 200 language
words) from a PINNED start (`x0_hex`, so random-generator versions cannot matter) and hashes everything.
Reference: `substrate_reference_v03.json` — dynamics ce38030c…, observables 44da874d…,
decisions 4738e921…. Runtime 2.7 s. The Ears are an organ, not substrate: their output (region, sign)
is logged with each event, so replay never needs them.

## 2. Cross-machine bit-identity — MATCH
| | laptop (reference) | Kaggle private kernel |
|---|---|---|
| CPU | AMD Ryzen 7 5700U | Intel Xeon @ 2.20 GHz |
| Python / numpy | 3.12 / 1.26.4 | 3.13.15 / 2.1.3 |
| dynamics, observables, decisions, ledger, language, final state | — | **all identical** |
The exact lab files were embedded and their sha256 checked inside the kernel before running.
v0.1 and v0.2 failed this on Intel (transcendental functions in torch/libm); v0.3's body uses only
IEEE-exact operations (abs, division, floor, add, subtract), and the result now holds across CPU
vendors and numpy major versions.

## 3. δ₀ — deterministic certificate (Ulam transfer operator), NOT yet an interval proof
`delta0_ulam.py`: invariant density of each memory state's map by Ulam's method (bins + dense
quadrature, no random orbits), resolution doubled to show convergence.
| resolution | min adjacent gap of P(x<0) |
|---|---|
| 1024 × 64 | 0.02415 |
| 4096 × 64 | 0.02440 |
| 8192 × 256 | 0.02457 |
| **16384 × 256** | **0.02442** |
Last doubling changed no state by more than 0.0004; agreement with the independent Monte Carlo
calibration: max difference **0.00024** at every state. **δ₀ = 0.0244** (scored gate floor 0.020;
scored G2 lowest mean gap 0.0256).
What would make it a proof: interval arithmetic for the quadrature and the infinite branches near 0,
plus the Galatolo–Nisoli a-posteriori bound on the Ulam error. The map is uniformly expanding here
(|T′| ≥ 1/(1−α)² > 2.8), which is the setting those bounds cover. Estimated effort: days, not hours.
