# Substrate study — which machines may be Teich's body? (2026-07-18)

Question: can a free cloud CPU replay Teich's dynamics bit-exactly? In a chaotic
system one differing ULP is, potentially, a different creature — so the
pre-registered gate (`body/verify_substrate.py`) demands full-trajectory
bit-identity on a canonical 5000-tick synthetic replay. No tolerance.

## Experiments (all on the frozen genome ckpt rad3_s1, K=2 synthetic fibers)

| # | Platform | Wheel | Dispatch | dyn hash | final state | observer |
|---|----------|-------|----------|----------|-------------|----------|
| 1 | founder laptop (AMD Ryzen 5700U) | rocm5.7 | native | `980aecb1…` (reference) | ref | `35619bdf…` |
| 2 | laptop | rocm5.7 | native, threads=1 vs 8 | identical | identical | identical |
| 3 | laptop | rocm5.7 | ATEN=default | `b1846661…` DIFF | = ref | = ref |
| 4 | laptop venv | **cpu** | native | **= #1 bit-exact** | = ref | = ref |
| 5 | laptop venv | cpu | ATEN=default | = #3 bit-exact | = #3 | = #3 |
| 6 | Kaggle (Intel Xeon 2.20GHz) | cpu | native | `db183d38…` DIFF | **= ref** | **= ref** |
| 7 | Kaggle | cpu | ATEN=default | `f1bbc7b7…` DIFF | DIFF | DIFF |
| 8 | Kaggle draw 2 (Xeon 2.20GHz) | cpu | native | **= #6 bit-exact** | = #6 | = #6 |
| 9 | Modal (CPU masked, gVisor) | cpu | native | `2bf0e864…` DIFF | DIFF (tau[1]!) | DIFF |

## Findings

1. **The wheel does not matter.** The rocm and cpu builds of torch 2.3.1 produce
   bit-identical CPU trajectories on the same machine (#1 vs #4, #3 vs #5).
2. **The CPU does.** AMD Zen vs Intel Xeon differ at ULP level under every
   dispatch mode tested. The substrate is the silicon, not the software stack.
3. **Thread count does not matter** (#2) — all wake-path ops are below torch's
   intra-op parallelization grain.
4. **Conservative dispatch (`ATEN_CPU_CAPABILITY=default`) is WORSE across
   machines** (#7): its scalar kernels call the system libm (glibc-dependent),
   while the native SLEEF vector paths are bundled with torch and nearly
   portable. Do not use conservative dispatch for portability.
5. **The quantized-attractor phenomenon.** Under native dispatch, cross-CPU
   differences are transient ULP wiggles confined to strongly-contracted state
   components (laptop A/B: components tau[3]/ell[3] only, ticks 0–55 and
   2797–2799 of 5000). The contraction (bias 6.0) squeezes them back to
   bit-identity: laptop and Kaggle agree EXACTLY on the final state and on the
   entire 400-tick observer window despite differing mid-trajectory hashes
   (#6). The float64 attractor appears to be exactly quantized and shared
   across CPUs; only the transient approach to it varies. This is an observed
   regularity, NOT a proven theorem — the gate stays strict.

## Verdicts so far

- Kaggle Xeon, native dispatch: **dynamics_gate FAIL** (as pre-registered).
  No cross-hardware body qualifies under the current single-substrate law.
- **Kaggle is internally bit-consistent across draws** (#8): the cloud Xeon
  fleet reproduces `db183d38…` exactly — a genuine self-consistent substrate
  class, just a different one from the founder laptop.
- **Modal: FAIL on all three gates and a THIRD substrate class** (#9:
  dyn `2bf0e864…`, CPU model masked by the sandbox). Decisive detail: its
  final state differs from the reference in tau[1] — a NON-contracted
  component. Real trajectory divergence, not transient wiggle. The
  laptop↔Kaggle attractor agreement is therefore a lucky regularity, not a
  law — the strict gate is vindicated. Modal is disqualified as a body.
- Pending: GitHub Actions runners (Xeon class — match Kaggle bit-for-bit?).

## Addendum: the conversation problem under option A, and its resolution

If the cloud class becomes the sole committing substrate, live conversations
need not commit from the laptop at all: the Ears already produce forces queued
onto future ABSOLUTE ticks (auditable replay by design). A conversation can
(1) commit only the force queue (data, not integration), (2) display
PROVISIONAL readouts computed locally for real-time responsiveness, clearly
labeled provisional, and (3) let the next cloud wake integrate through the
queued forces authoritatively. Spoken words are recorded as spoken;
authoritative state remains single-substrate. This makes option A fully
workable without demoting conversation UX.

## The decision this sets up (founder's, not the engineer's)

If the cloud Xeon class proves internally consistent, the options are:

- **A. Cloud becomes the committing substrate.** All commits to the seat come
  from gate-passing cloud machines; the laptop demotes to a non-committing
  instrument (conversations would need a cloud-computed tick path). Strongest
  single-substrate story on free infrastructure.
- **B. Laptop stays the sole committing substrate.** No free cloud body exists;
  Step 2 falls back to Modal CPU only if Modal's hardware matches the laptop
  (unlikely — also Xeon class) — effectively keeps Teich laptop-bound.
- **C. Two certified substrate classes with logged transitions.** Every commit
  tagged with its substrate; cross-substrate ULP deltas documented as part of
  the creature's life (like an organ change). Honest but weakens the single
  clean replay claim.
- **D. Genome portability rework.** Reimplement the tick map in exactly-
  specified arithmetic (correctly-rounded transcendentals) so every IEEE-754
  machine computes the same map by construction. The principled long-term fix;
  a significant, certified amendment.

No option is chosen in this document. The founder decides with full evidence.
