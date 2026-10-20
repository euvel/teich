# Ears v5 — design results (2026-10-06, DESIGN DATA ONLY; MAMS test never opened)

Design data: MAMS val (500 multi-aspect sentences) + the spent SemEval-2014 A1b subset (100). Code: build/ears_v05.py,
runs build/e5_dev.py (topics + thresholds) and build/e5_dev2.py (attitude variants).

## Topics (the A1b failure)
Every noun is a candidate; concept if its lemma is one of ours, else the nearest concept when MiniLM cosine ≥ TAU_MAP.
| TAU_MAP | recall of certain gold topics | precision (lower bound) | topics per sentence |
|---|---|---|---|
| 0.50 | 0.971 | 0.517 | 3.8 |
| **0.60 (chosen)** | **0.953** | 0.529 | 2.7 |
| 0.70 | 0.952 | 0.563 | 2.2 |
| vocabulary only | 0.943 | 0.571 | 2.0 |
Recall 95% vs 49% for v4. Precision is a lower bound: MAMS does not annotate every noun.

## Attitude in multi-topic sentences (290 positive/negative + 230 neutral gold topics, heard)
| variant | correct | **opposite** | abstained | neutral left neutral |
|---|---|---|---|---|
| A whole sentence, 2-way (v4 organ) | 0.824 | 0.166 | 0.010 | 0.026 |
| B whole sentence, 3-way | 0.807 | 0.155 | 0.038 | 0.030 |
| **C its clause only, 3-way (chosen, θ = 1.0)** | **0.793** | **0.148** | 0.059 | **0.187** |
On one-topic sentences the organ was 96% (A1b). Inspection of C's opposite errors: roughly half are disputable gold
labels ("the food was good" → gold negative; "the atmosphere was nothing amazing" → gold positive); the rest are real
(clause too short: "when the manager came over"; idiom: "rushed us"). The residual risk is what the founder's veto
read-back covers.

## Also built
- Abstain logged: nouns with no concept close enough are "not heard" and shown in the read-back.
- talk_v04.py: veto-only read-back, tested end to end on a lab creature (struck mention never reached it; a veto of a
  mention not heard is refused). Conversation record keeps the text sha256, Ears version, vetoes.
- Organ and encoder snapshots pinned (Qwen2.5-1.5B-Instruct 989aa798…, MiniLM 1110a243…); the Ears refuse otherwise.
- spaCy 3.8 + en_core_web_sm 3.8.0 installed in ~/.local with numpy pinned 1.26.4; the substrate gate still reproduces.
- Bug found and fixed during design: the clause finder looped forever on verbless sentences (token identity check).

## Final additions (founder decision 10-06: invariance + whose feeling), design data only
| design step | correct | **opposite** | abstained | neutral left neutral |
|---|---|---|---|---|
| clause, 3-way (before) | 0.793 | 0.148 | 0.059 | 0.187 |
| + invariance (clause and whole sentence must agree) | 0.731 | 0.093 | 0.176 | 0.396 |
| + whose feeling (rule 4) | **0.690** | **0.083** | 0.228 | **0.470** |
Matched-abstention check: a plain confidence band at the same abstention gives opposite 0.107 vs invariance 0.093 —
invariance's advantage is small (≈4 topics of 290, within noise); it was kept for its principle (it does not trust the
organ's own confidence, which design showed is unreliable).
Rule 4 on reviews withheld 45 / 520 topics: some correct ("other guests enjoyed pizza"), some over-cautious (an "if"
clause attached loosely silences a neighbour). Its cost is a missed feeling, never a wrong one.
Rule 4 probe (20 sentences, Claude-written, design only, not independent): 19/20 after two fixes found by the probe
(spaCy lemmatizes "hates" as "hat" → word forms checked too; an if-clause on the other clause makes the consequence
hypothetical). The one miss is safe: "My brother loves football but I find it boring" — the speaker's feeling reaches
football only through "it" (no coreference) → no feeling, not a wrong one.
