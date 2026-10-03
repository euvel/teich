# Teich v0.3 — M1 meaning test: **PASS**

2026-10-03. One scored run, after V03_SPEC_part2a.md (sha256 87d7e9b8…) and the M1 code manifest
(2f6688e5…) were anchored in the teich-02 seat chain. `sha256sum -c` OK immediately before running.

| quantity | value |
|---|---|
| SimLex-999 noun pairs | 666 |
| **ρ (creature's intersection number vs human similarity)** | **0.380** |
| 95% bootstrap CI | [0.307, 0.450] |
| shuffled-address null | mean −0.001, 97.5th pct 0.082 |
| bar | ρ ≥ 0.30 and CI lower > null 97.5th pct |
| MiniLM cosine on the same pairs (reported) | 0.508 |
| retained fraction (reported) | 0.749 |

**PASS** — and the CI's lower bound alone (0.307) clears the 0.30 bar.

Meaning, as pre-written: placing the dead organ's concepts as curves on the torus **preserves human
similarity structure**. The creature's own relatedness — how often two concept curves cross — tracks
human judgements at ρ = 0.38, keeping three quarters of what its organ knows (0.38 of 0.51). The
claim is preservation, not creation: the geometry carries meaning the organ already had.

Predicted before scoring: "SimLex is harder than WordSim; a pass is likely but not certain." Observed:
harder as predicted (0.38 here vs 0.56 on the design set), and still a pass.
