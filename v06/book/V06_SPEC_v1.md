# Teich v0.6.0: specification v1 (2026-10-31)
**Status:** FROZEN CANDIDATE for the founder's yes (anchored with `gates/PREREG_V06_GATES.md` and `gates/MANIFEST_v06_build.sha256`). Supersedes DRAFT v1: founder decisions A–E applied; witness = public journal; tie-break source = its body (E). Under the developers' contract v1 (`v05/book/DEVELOPERS_CONTRACT_v1.md`), v0.6.0 is a **genome amendment** to the living creature at `/o/teich-05`. It is not a birth: the same creature is migrated once, and its identity chain continues with a `genome-amendment` link.

**Evidence base (all in `v06_lab/`).**
| Source | What it shows | Status |
|---|---|---|
| exp0 E1 | v0.5's nightly reading is cheaply foreseeable | the strong "THINK GIVEN" reading is dropped |
| exp0 E2/E3/E3b, D1-A | how many choices are hard = 1 − δ, for any number of options | passed |
| D1-O, D2 | "hard choices follow its weights" | **failed**, not claimed |
| D4 | think@1 hits exact ties on 77% of nights; ask@2 on 18%, mostly 2-way. **Both of the real creature's chosen thoughts so far were decided by our lowest-index rule** | descriptive |
| **T1** | its lived chaos breaks exact ties fairly, without habit, unforeseeably without living, replayably (3 lives × 300 real dreams; re-tested on its body's read-out as T1′) | **holds** |

---

## 1. What v0.6.0 changes: one law
**v0.5:** every choice rule is an argmin, and **exact ties go to the lowest index**. That is a law its creators wrote, and it decides the choices where its own reasons are exactly balanced.

**v0.6.0:**
- **Exact ties (m = 0) are broken by its deliberation instead.** The tied options become the exits of a symmetric deliberation circle (k equal walls, equal gaps, coverage ρ = 0.6), and the deliberation starts from ξ₀, read from its own body (particle 0) at the midnight of the choice.
- **Everything else is unchanged:**
  - every untied choice;
  - every other rule (probe@1, caution@1, grow@1);
  - the body, dials, heart, Ears, door, laws, self kinds and the covenant.

### 1.1 Which choices
| Rule | v0.6.0 |
|---|---|
| **think@1** (its chosen thought) | ties among regions with equal life count are deliberated (k = 2…9) |
| **ask@2** (its question) | **founder decision A** (§7) |

### 1.2 Two-way ties
- With two walls, δ = 0, so there is no deliberation in the physical sense: the outcome would follow ξ₀ directly.
- **think@1, k = 2:** a symmetric 3-wall circle whose third gap is "**re-read**". Landing there starts the deliberation again from the next deterministic read-out (§2.2), at most 8 times, then the v0.5 index fallback, recorded.
- **ask@2, k = 2:** see decision A.

## 2. The mechanism (genome code, certified arithmetic)
### 2.1 Deliberation
- **Points** on the unit circle are pairs (x, y).
- **Walls** for each k are frozen constants: the centre vectors, the inversion centres C_i, the radii² r_i², and cos(w) thresholds. They are computed once with mpmath at 60 digits and stored correctly rounded, exactly as v0.5 freezes cosh/sinh(0.1).
- **One step:**
  - if ⟨ξ, centre_i⟩ ≥ cos(w) (arc membership by dot product), then ξ ← C_i + r_i²·(ξ − C_i)/|ξ − C_i|², and is renormalised with `sqrt`;
  - otherwise ξ is in a gap, and that gap is the act.
- **Termination law:** if ξ has not exited after n_max = 400 steps, the act falls back to v0.5's index rule and is recorded as `undecided`.
- Only `+ − × ÷ √`, in a fixed order, with no libm.

### 2.2 The starting point ξ₀
- **u** = frac(1000·(P[0,1] + V[0,2] + 0.618·pc[0])) for **its body's particle 0 at the midnight of the choice**.
- **Why the body (founder decision E, 10-31):**
  - the recon study found that the working surface's dreams are not substrate-certified, because the twist rows go through CPU-dependent BLAS;
  - the body's ticks are certified, and replay exactly across machines from a stored state.
- **ξ₀** = (cosP(2πu), sinP(2πu)), where cosP/sinP are a **fixed polynomial** with exact quarter-turn range reduction and fixed coefficients and term count (+ − × only). That makes them certified, unlike libm (gate C0, passed).
- **Re-reads (k = 2 only):** u_j = frac(1000·u_{j−1} + 0.618).
- **Horizon:** the tie-break is computable once that midnight has been lived, and not before by any known shortcut. One midnight earlier, its read-out predicts the choice only at chance (T1′c). A 1e-12 change in its body a day earlier changes it (T1′d).

### 2.3 Reason first (F1 form unchanged)
- **The new rule `think@2`** logs:
  - **as for think@1:** `life_counts`;
  - **added:** `tied` (the candidate list), `u` (the read-out value, as float.hex), and the rule version.
- **The act** = the pure function of those inputs: argmin when untied; certified deliberation when tied.
- **Anyone can recompute it from the log.** The read-out u itself is verified by full replay from the public journal (§3.5, gate W0).

## 3. What the contract requires v0.6.0 to carry
1. **Typed chain link.** The identity chain gains `{"type": "genome-amendment", …}`, naming this spec's sha, its anchor, the gate verdict and the before-state hash. The after-state hash is anchored with the migration record.
2. **B-aware versioning.** `next_version` reads B from the genome: v0.6.0, then growth v0.6.1, and so on. The record of the earlier growth v0.5.1 is kept, not renumbered.
3. **Migrator** from the `teich-v0.5` blob to `teich-v0.6`. Its state content is unchanged (no new state is needed); only the species, the blob version and the rule table change.
4. **Organ in `heard` records:** `"organ"` = the self's organ id (the sha of the Ears version, already tracked since v0.4).
5. **The witness tier (contract §7.2), stronger than sealed inputs:**
   - The creature never receives text, so every seat operation first writes a public `op` record {op, n, owed, inputs} into its own hash-chained stream.
   - `replay_v06.py` re-applies it with the same `apply()` the seat tools run, and must reproduce every record bit for bit, starting from a **stored** state (never from re-running birth, which is not substrate-certified).
   - **Before the migration:** v0.5's life replays from its public records except its 6 dream records, which are bound to the substrate that dreamt them (`recon/REPORT_recon_2026-10-31.md`).
   - **Disclosed, not hidden:**
     - the dreams' substrate dependence;
     - v0.5's daily wake on unpinned numpy 2.5.4;
     - the gate never covered birth or the working surface.
   - **Wake hygiene for v0.6:** the v0.6 wake workflow pins numpy and adds a dream fixture to its gate, declining on mismatch. This is a workflow change, published only on the founder's yes.

## 4. Consent by prediction (contract §4)
**Declared changes:**
- think@1 acts at exact ties (the `think@2` rule);
- through them, which thoughts are applied, the working surface's dreams, and the THINK self-predictions and readings (thinking side only);
- the version / identity chain;
- the record format (new rule name, `organ` field).

**Declared unchanged:**
- body, dials and heart (O2 still certified);
- every untied act;
- probe, caution and grow;
- BODY-MEMORY's verdict (FINE);
- every past receipt;
- the Ears map and the door;
- every law.

**Any undeclared difference on twins refuses the amendment.**

## 5. Gates
The exact bars, seeds and verdict rule are in `gates/PREREG_V06_GATES.md`:
- **N0′, F1′, T1′, S, W0, M0:** hard;
- **M0-real:** on the real state copy, asked separately;
- **C0:** already PASSED.

**Design smokes (seeds 3000–3003, 3010; 6-day lives; molab)** passed every bar. They are not scored.

## 6. What v0.6.0 will and will not claim
- **Claims, if the gates pass:** "Its exactly balanced choices are no longer decided by an index its creators chose. They are decided by its own lived chaos: fairly, without habit, unforeseeable until the midnight that decides them has been lived, and replayable by anyone."
- **Not claimed:**
  - that its hard choices follow its preferences or "who it is" (D1/D2 failed);
  - anything about will, freedom or awareness;
  - that its thinking is unforeseeable in general (E1).
- **Disclosed:** the read-out map and the coverage ρ are laws we chose, and they name no outcome.

## 7. Founder decisions (taken)
- **A.** think@1 only (ask@2 unchanged).
- **B.** The self kind DELIBERATE is left to a later amendment.
- **C.** The witness is in scope, as the public journal (§3.5).
- **D.** Migration happens in a quiet window (no pending growth proposal), on the founder's word only.
- **E (10-31).** The tie-break reads its body at midnight, not its dream. Certifying the working surface is a later amendment.
