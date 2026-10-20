# v0.4 spec part 2a — SCORED results (one look; anchored teich-03 ref v04-spec-part2a, manifest d7eb4f87…)

Run: Kaggle Intel Xeon, pinned Python 3.12 environment (transformers 4.44.2, sentence-transformers 3.0.1, tokenizers
0.19.1, torch 2.3.1 CPU, spaCy 3.8.16 + en_core_web_sm 3.8.0, Qwen2.5-1.5B @989aa798…, MiniLM @1110a243…).
Guard before the look: the 40-sentence parity check on MAMS val was **identical to the laptop (0 / 40 sentences, 121
mentions)**, as in the separate smoke kernel. A first attempt (2026-10-06) crashed at its first model call on
Kaggle's Python 3.13 before computing any score; the MAMS test was not spent by it.

| gate | result | approved, anchored bar (V04_SPEC_part2a.md) | verdict by the spec |
|---|---|---|---|
| R2 regression | "My dog is wonderful." → exactly one mention, animal·dog·pet, warm (clause +13.84, sentence +13.85); creature effects exact | exact | **PASS** |
| A2a recall | 0.953 (593 gold topics that are our concepts) | ≥ 0.90 | PASS |
| A2a feelings right | 0.661 (387 heard warm/cold gold topics) | ≥ 0.62 | PASS |
| A2a **wrong feelings** | **0.075** | ≤ 0.13 | PASS |
| A2a precision (lower bound) | 0.513 | ≥ 0.45 | PASS |
| **A2a** | | | **PASS** |

## ERRATUM (Claude's error, disclosed)
The harness `gates_v04_part2.py` (also in the anchored manifest) still encoded the **pre-rebase draft bars** in its
automatic flag (A2a: correct ≥ 0.72, opposite ≤ 0.20; A2b: correct ≥ 0.80, opposite ≤ 0.10). When the bars were rebased
on 10-06 and approved by the founder, only the spec was updated. The harness therefore printed `"passed": false` for
A2a (0.661 < 0.72). The governing document is the founder-approved spec, anchored before the run; by it, A2a passes.
Both verdicts are recorded here; nothing was rerun or rescored. The A2b constants in the harness must be corrected
(to the spec's 0.75 / 0.08) in part 2b, as an announced amendment, before the founder set is scored.

Design vs test: recall 0.953 / 0.953, right 0.690 / 0.661, wrong 0.083 / 0.075, precision 0.529 / 0.513 — the test
matched design closely.

## Founder decision 2026-10-07
A2a accepted as PASS under the approved, anchored spec ("technically passed"). The A2b harness constants were
corrected the same day (amendment marked in the code), before the founder set exists; the corrected harness goes into
the part 2b manifest.
