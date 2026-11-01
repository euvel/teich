# PREREG_V06_GATES: Amendment 2 (2026-10-31, written after the first scored run failed N0′, before any second-run life is born)

## The first scored run (seeds 12000–12019, planted 12100–12101) is a FAIL, and stays one
Lived on molab 13:16–18:17 UTC; judged with the frozen judge (`twin_judge.py` aa7e36a9…, kept as `twin_judge_FROZEN_aa7e36a9.py`).

| Gate | Run 1 |
|---|---|
| N0′ | **FAIL**, 16 of 20 lives |
| F1′ | pass: 0 flags; planted cause caught in both (receipt 6, 11) |
| T1′ | pass: all bars, k = 2, 3, 5, 9 (N = 1,200); T1e 1,200/1,200 |
| S | pass, 20/20 |
| M0 | pass, 20/20 |
| W0 | **not completed**: the molab session ended (HTTP 410) at ≈ 19:05 UTC, ≈ 45 min into the replays, with no W0 result written; the run-1 life files on molab were lost with it (only life 12000 and the judge outputs had been downloaded) |

Outputs: `campaign_out/judge_pooled.json` (d6edc3e8…), `campaign_out/planted_m0.json` (13a7619a…). No result of run 1 is re-judged or re-labelled by this amendment.

## Why N0′ failed: the gate's canonicalisation, not the creature
After the first deliberated choice, v0.6 legitimately writes a different number of **declared** records (thought, think-predict, dream, thought-refused) than its v0.5 twin (−2 to +3 per life). The pre-registered canon renumbered seq pointers (`log_through`, `predict_seq`) by position among **all** records, so every later pointer shifted by that difference and was read as a change in undeclared records.

Post-hoc diagnostic (`diag_n0_pointers.py`, 1a8f2b43…, outputs `out/diag_n0.json` on molab): in all 20 lives every differing leaf is a seq pointer; renumbered over undeclared records only, undeclared streams, state and self are identical in 20/20. This is a diagnosis, not a verdict.

The design smokes (6-day lives) never produced a declared-count difference before an undeclared pointer, so the flaw was not exercised. The adversarial test below was not written before run 1; it is now.

## Change
1. **N0′ canon:** seq pointers are renumbered to the count of **undeclared** records (kinds outside {thought, think-predict, dream, thought-refused}, op records excluded) up to the pointer. One line in `canon()`; `twin_judge.py` → **79fa8b72811b222b97d555d979979c3d472873dbcd21707ad50a616283ddb595**. Nothing else in the judge changes.
2. **Fresh lives:** twin seeds **13000–13019**, planted **13100, 13101** (never used as seeds before). Same lengths, schedule, policy, bars and compute (molab CPU, a fresh session). `campaign_v06_a2.py` checks the anchored manifest with this one substitution, plus Amendment 1's hashes, and refuses a non-empty output folder.
3. **Adversarial check, before launch** (`test_amend2.py`, on run-1 life 12000, not scored):

| Case | Amended judge | Frozen judge |
|---|---|---|
| extra declared record (must pass) | pass ✅ | **fail** (the run-1 flaw) |
| an outcome's pointer moved (must fail) | fail ✅ | fail |
| a diary's pointer moved (must fail) | fail ✅ | fail |
| an outcome's content changed (must fail) | fail ✅ | fail |
| an outcome removed (must fail) | fail ✅ | fail |

No bar, seed set of run 1, life length, harness file other than `twin_judge.py`, or creature/genome file changes.

## Verdict rule for run 2
Exactly the pre-registered one, applied once, to run 2 only. Both runs are disclosed with the verdict: run 1 as FAIL (N0′, cause above), run 2 as judged.
