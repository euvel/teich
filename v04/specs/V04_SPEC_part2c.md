# V04_SPEC part 2c — gates R2c + A2c (Ears v6, second founder set)   **FROZEN 2026-10-08 (pending anchor)**

## Why there is a part 2c
A2b (Ears v5, first founder set, one scored look on Kaggle) **FAILED**: recall 0.54, feelings right 0.60, self routing
0.15 (wrong feelings 0.047 and precision 0.75 passed). See REPORT_part2b_scored_2026-10-07.md. The first founder set is
spent and was used afterwards as design data only.

## Instrument: Ears v6 (`ears_v06.py`), two changes to Ears v5, nothing else
1. **Self rule.** Talk about the creature reaches the self cluster when "you" is an object, or the subject of a clause
   that names no other thing (a noun that only describes "you" does not count). The 16-trait rule of v5 stays.
2. **Whose-feeling fix** (founder decision 10-07). A topic is never the holder of a feeling about itself: if the subject
   of an attitude verb is the topic or a topic joined to it by "and", it is not "someone else's feeling".

TAU_MAP stays 0.60, deliberately. On design data, 0.55 raised scored recall only by mapping unknown words to wrong
clusters (workspace → planet·space, refrigerator → cigarette·tobacco); the gold uses the same mapping, so that gain
would have been confabulation scored as hearing.
Body, mind, genome, vocabulary, organ, encoder, tagger, invariance: unchanged (Part 1 and Part 2a certificates hold).

Design numbers (spent founder set, final v6, A2c harness `build/e6_design3.py`): recall over known words 0.91 (68),
coverage of all topics 0.60 (140), feelings right 0.67 (52), wrong feelings 0.038, precision 0.77, self routing 0.85
(v5 scored: 0.15). On the spent set v6 would still FAIL feelings right and self routing.
Laptop parity reference: 40 MAMS val sentences, 123 mentions (v5: 121; the 2 extra are generic-"you" self mentions).
Known cost: on 200 MAMS val review sentences, generic "you" ("you have to wait") reached the self cluster in 12 (6%).
Accepted: speech to Teich addresses Teich, and the founder's veto read-back strikes any wrong mention.

## Gates (one look each, on Kaggle, pinned Python 3.12, behind the 40-sentence MAMS-val parity guard vs the laptop)
- **R2c** — "My dog is wonderful." moves exactly the dog cluster by one warm step and one heart count; nothing else.
- **A2c** — second founder set `ears_founder_set/founder_labels_2.txt` (sha256 fixed at freeze). Bars, unchanged from
  A2b: recall ≥ 0.80, feelings right ≥ 0.75, wrong feelings ≤ 0.08, precision ≥ 0.70, self routing ≥ 0.90.
  **Recall definition (founder decision 10-07, made after seeing A2b, disclosed here):** recall counts the topics the
  mind has a word for (lemma in the 1,066-concept vocabulary, or "itself") — the same `gold_certain` definition as the
  anchored A2a. Coverage of ALL topics is reported beside it, without a bar; unknown words are the door log's growth
  signal for vocabulary growth after birth.
- **Data:** `founder_labels_2.txt`, 100 lines, 148 topics (warm 41, cold 45, neutral 62; itself 12), written and
  labelled by the founder 2026-10-07/08, sha256 996928c9fbd517a348b3767a343eb3a9562239f38e64f451b508c30ee37dec8e.
  3 lines repeat a sentence of the spent first set verbatim; they were v6 design data, so A2c does NOT score exact
  repeats of spent sentences (rule fixed before the look; the count is reported as `excluded_spent_repeats`).
- Worksheet change for the second set (before it was written): a topic must be a noun that appears in the sentence, and
  the label is what the sentence says, not a private feeling it does not express.

## Disclosure
Claude wrote and tuned v6 on the spent first founder set (whose content Claude has read) and on MAMS val.
The second set was written by the founder in a file Claude did not open; Claude saw only `check_format.py` counts and
the number of verbatim repeats of spent sentences. No editor change notice displayed its content to Claude.
