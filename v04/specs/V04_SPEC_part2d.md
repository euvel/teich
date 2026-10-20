# V04_SPEC part 2d — gates R2d + A2d (Ears v7, third founder set)   **DRAFT 2026-10-08 (freeze after the set exists)**

## Why there is a part 2d
A2c (Ears v6, founder set 2, one look on Kaggle) **FAILED** self routing 0.58 and precision 0.63, while it PASSED
recall over known words 0.92, feelings right 0.77 and wrong feelings 0.036. See REPORT_part2c_scored_2026-10-08.md.
Founder sets 1 and 2 are spent and were used afterwards as design data only.

## Instrument: Ears v7 (`ears_v07.py`), two changes to Ears v6, nothing else
1. **Self = rule OR organ.** A sentence addressing the creature ("you", "your", "Teich") reaches the self cluster when
   the v5/v6 rules fire, OR when the pinned organ (same Qwen2.5-1.5B snapshot, log-probs, no sampling), asked whether
   the sentence is mainly about the listener (A) or something else (B), gives log P(A) − log P(B) > SELF_THETA = 4.0.
2. **A time expression used as an adverb is not a topic**: spaCy npadvmod AND (DATE/TIME entity or a time-unit lemma)
   — "today", "this week", "one day", "these days", "10 minutes into". Other adverb-nouns stay topics ("worth the prices").
Body, mind, genome, vocabulary, organ, encoder, tagger, TAU_MAP 0.60, invariance, whose-feeling rules: unchanged.

Design (both spent founder sets, 25 self sentences; MAMS val generic "you"): self caught — rule alone 18/25, organ alone
at best 20/25, rule OR organ 24/25 with 4 false routes on 24 founder non-self addressed sentences. Four ways of asking
the organ were compared (build/e7_probe.py, e7_probe.json); the A/B question separated best. **SELF_THETA was chosen on
this design data**, so the design 0.96 is optimistic; A2d is its test. Known cost: generic "you" in reviews reaches the
self cluster via the v6 rule (~6%); accepted — speech to Teich addresses Teich, and the veto read-back strikes it.
**Design verification** (the A2d harness itself on the spent sets, build/e7_verify.py; optimistic — tuned on them):

| spent set | recall (known) | feelings right | wrong | precision | self routing |
|---|---|---|---|---|---|
| set 1 (v5 scored FAIL) | 0.912 | 0.660 | 0.038 | 0.808 | 0.923 |
| set 2 (v6 scored FAIL) | 0.987 | 0.787 | 0.033 | 0.675 | 1.000 |

Set 1's "feelings right" carries private-feeling labels (fixed in the set 2+ worksheet); set 2's precision is lowered
by nouns the founder did not label (fixed in the set 3 worksheet: label every noun).
Laptop parity reference (build/out_smoke/A2d_smoke.json): 40 MAMS val sentences, 122 mentions; differs from v6 in one
sentence ("10 minutes into our appetizer": time adverb no longer a topic).

## Gates (one look each, Kaggle, pinned Python 3.12, behind the 40-sentence MAMS-val parity guard vs the laptop)
- **R2d** — "My dog is wonderful." moves exactly the dog cluster by one warm step and one heart count; nothing else.
- **A2d** — third founder set `ears_founder_set/founder_labels_3.txt` (sha256 fixed at freeze). Bars unchanged from
  A2b/A2c: recall ≥ 0.80 (topics the mind has a word for, as in A2a/A2c), feelings right ≥ 0.75, wrong feelings ≤ 0.08,
  precision ≥ 0.70, self routing ≥ 0.90. Coverage of all topics reported without a bar. Exact repeats of any sentence
  of sets 1–2 are not scored (count reported).
- Worksheet change for set 3 (before it was written): label EVERY noun the sentence names except time adverbs; use
  `itself` whenever the sentence is about Teich (what it is, does, can do, is like). The founder writes in a copy of
  TEMPLATE_set3.txt that Claude never opened, so no editor change notice can show its content to Claude.

## Disclosure
Claude designed v7 on founder sets 1 and 2 (whose content Claude has read, after their scored looks) and MAMS val.
