# V04_SPEC part 2b — gate A2b (founder set)   **FROZEN 2026-10-07 (pending anchor)**

Bars as approved by the founder 10-06 and anchored in part 2a (V04_SPEC_part2a.md): recall ≥ 0.80, feelings right
≥ 0.75, **wrong feelings ≤ 0.08**, precision ≥ 0.70, self routing ≥ 0.90. One look.

## Data
`ears_founder_set/founder_labels.txt` — 100 lines, 143 topics (warm 45, cold 31, neutral 67; itself 13), written and
labelled by the founder 2026-10-07 in 10 groups (plain, several topics, mixed, about itself, to it about something else,
someone else's feeling, hypothetical / used-to, questions, neutral facts, negation). sha256 bf322476487d51af6cc430efb8bbb2f0087947aa18a07131a5272ce5b3bc2e5f.

## Instrument
Ears v5 exactly as anchored in part 2a (ears_v04.py, ears_v05.py unchanged). Harness `gates_v04_part2.py` with ONE
announced amendment (2026-10-07, made before the founder file existed): the A2b pass flag now encodes the approved bars
(0.75 / 0.08) instead of the pre-rebase draft (0.80 / 0.10) — see the erratum in REPORT_part2a_scored_2026-10-07.md.
Run on Kaggle in the pinned Python 3.12 environment, behind the same 40-sentence parity guard as part 2a.

## Disclosure
The founder's sentences and labels were displayed to Claude by the editing environment's automatic change notice when
the file was saved (Claude did not open the file). The instrument was already frozen and anchored (part 2a) and the
only later change (the bar amendment above) predates the file. No change to the Ears was made after the exposure.
