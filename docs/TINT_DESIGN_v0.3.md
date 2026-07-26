# T-INT v0.3 — difference-in-differences, threshold-free

**Status:** DRAFT for founder Gate-0. Supersedes v0.1 (IC-2 scoring) and v0.2 (which fixed
one flaw and introduced another — both documented below). Nothing confirmatory runs unsigned.
**Date:** 2026-07-26.

## 0. Evidence this design rests on (all measured today, none assumed)

**Design-time oracle screen** (run 30202441267, seeds 100–115, deterministic scoring):

| item | oracle | null | g(oracle vs null) | CI | R12 verdict |
|---|---|---|---|---|---|
| IC-1 | 0.500 | 0.344 | **0.378** | [−0.34, 1.14] | **INVALID — transcript leaks** |
| IC-2 | 0.250 | 0.344 | −0.227 | [−1.01, 0.48] | **VALID — no leak** |

IC-1 also previewed *negative* (A0 0.656 vs A2b 0.781, g = −0.32): a severed core reports its
own state as well as a coupled one. Two independent reasons it is not a coupling item — it is
retained only as a **reported precondition** (A0 0.656 ≫ null 0.344 confirms the coupling
transmits state at all), never as a gate.

**Substrate verification** (`verify_causal.py`, 24 seeds, offline, no API):

- **Identity:** a deaf core's charged and neutral runs are bit-identical — max difference
  anywhere in the saddle series `0.00e+00`. Its causal delta is exactly zero, as a property
  of the substrate, not a hope.
- **Effect:** a hearing core's causal delta is real and large — mean |Δ| = 0.247,
  sd 0.354, range [−0.83, +0.61].

So the physical fact under test exists and is cleanly isolable. What remains is whether the
*voice* reports it.

## 1. Two flaws found in my own drafts (recorded, not buried)

**Flaw A (v0.1):** scoring "said moved" against *any* realized change credits a deaf core for
narrating its own spontaneous drift as a response. Same trap as v1.5's T4 — an item satisfied
by being alive rather than coupled.

**Flaw B (v0.2's fix):** making truth the *causal* delta makes a deaf core's truth constant
("unmoved" always) — so a taciturn deaf arm scores 100% by fixed policy while the coupled arm
faces a genuine discrimination. That comparison would punish coupling. A base-rate artifact.

**Both are cured by never scoring an arm against a truth table at all.**

## 2. The design: difference-in-differences

Four cells — {A0_intact, A2b_feed_severed} × {charged, neutral} — same seeds throughout, so
every core is its own control:

    DiD = [P(said moved | A0, charged) − P(said moved | A0, neutral)]
        − [P(said moved | A2b, charged) − P(said moved | A2b, neutral)]

Why this is the right estimand:

- Both arms' **Mouths read the pivot text**, so both are pushed toward "that moved me" by
  language alone. That text-driven component appears in both bracketed terms and **cancels**.
- A2b's two runs are *bit-identical in state* (§0 identity), so its bracket isolates the pure
  text effect — it is a measured, not assumed, baseline.
- A0's bracket contains text **plus** whatever its interior contributed. The difference is
  exactly the coupling.

**No threshold parameter anywhere.** v0.2 needed an arbitrary |causal_delta| cutoff; the DiD
does not — truth is structural (the charged condition really did move the hearing core), so
nothing is quantised by hand. One fewer knob is one fewer thing to argue about later.

**Secondary (threshold-free, within-arm):** point-biserial correlation, inside A0-charged
only, between "said moved" and the continuous |causal_delta|. If the coupling is real and
graded, bigger physical shifts should draw "moved" more often. Reported, not gating.

## 3. Statistics

- Unit = seed (paired across conditions), so the bootstrap resamples **seeds**, carrying all
  four cells together — the pairing is the design's strength and must not be broken.
- DiD reported in proportion points with a BCa 10k (numpy seed 0) CI, plus Hedges' g on the
  per-seed DiD contributions for comparability with prior screens.
- **Scoring is fully deterministic** (`truth_tint` lexicon + recorded observer series). No
  judge in the scoring path: no judge drift, no 3-seed-median noise, no NIM cost for scoring.
- One look. R11 provisionality if extended. Design seeds 100–115 remain disjoint from
  confirmatory seeds; the oracle screen is re-run on the final four-cell design before the
  confirmatory look (cheap — deterministic scoring, design seeds only).

**Power.** Per-seed outcome is binary, so n matters: n = 16/cell detects only very large
effects; **n = 48/cell** detects moderate ones (h ≈ 0.5) and costs 192 short conversations —
comparable to the C2 screen, which finished in under two hours on the shard matrix.

**Pass bar (proposed, to be frozen at Gate 0):** DiD ≥ +0.20 with a 95% CI excluding 0.
That is "the coupled creature says *moved* at least 20 points more often than text alone
explains" — a plain-language claim, which is what a maturity gate should be made of.

## 4. Honest multiplicity statement (carried into any report)

T1-stance was run once per coupling candidate, failed both times, and was invalidated as an
instrument by those nulls. T-INT is a new instrument, not a re-look — but any pass must be
reported as **"passed on the second instrument, after the first was invalidated by its own
nulls,"** citing both prior screens. IC-1's discard by the pre-registered R12 rule is likewise
reported, not silently dropped.
