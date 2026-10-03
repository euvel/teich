# G5 prediction — written and hashed BEFORE any G5 run (2026-10-03)

Design (V03_SPEC_part1 §2, G5): one ±1 event from k = 3, then K i.i.d. fair ±1 events applied identically
to both members of a pair; refusal at the edges {0..6}. The first event stays decodable exactly while the
two memories differ; they merge only when one is refused at an edge and the other moves.
Prediction for the paired D (exact Markov computation, assuming the W = 8000 window separates distinct
states, which K2 measured at 0.99 for the hardest pair):

| K | predicted P(not merged) = predicted D |
|---|---|
| 0 | 1.0000 |
| 1 | 1.0000 |
| 4 | 0.8750 |
| 16 | 0.3267 |
| 64 | 0.0029 |

Pass band: measured D within the 95% binomial band of the prediction for n = 48 pairs at every K,
i.e. |D_measured − D_pred| ≤ 1.96·sqrt(D_pred(1−D_pred)/48) + 0.03 (the 0.03 covers the 1% window error).
Law: decodability decays because a bounded store merges paths at its edges — exponential in K for this
finite store, NOT K^(−1/2) (that law is for an unbounded integer store; the analysis note's statement is
corrected here before any data).
