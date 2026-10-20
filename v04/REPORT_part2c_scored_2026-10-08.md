# REPORT — Part 2c scored (R2c + A2c, Ears v6, second founder set) — 2026-10-08

**Verdict: R2c PASS, A2c FAIL.** One look, Kaggle kernel `teich-v04-part2c` (Intel Xeon 2.20 GHz, pinned py3.12),
parity guard exact (40/40 sentences, 123 mentions). Spec V04_SPEC_part2c.md, anchored teich-03 ref v04-spec-part2c
(manifest 2badf7a4…). Founder set 2 sha 996928c9…; 97 lines scored (3 verbatim spent repeats excluded), 139 topics.

| metric | result | bar | |
|---|---|---|---|
| recall (known words, 76) | 0.921 | ≥ 0.80 | pass |
| feelings right (n 56) | 0.768 | ≥ 0.75 | pass |
| wrong feelings | 0.036 | ≤ 0.08 | pass |
| precision | 0.631 | ≥ 0.70 | FAIL |
| self routing | 0.583 (7 / 12) | ≥ 0.90 | FAIL |
| coverage of all topics (no bar) | 0.727 | — | |

## Post-hoc diagnosis (after the look; changes no verdict) — build/a2c_posthoc.py, a2c_posthoc.json
- **Self (5 missed):** the v6 rule "you is the subject of a clause naming no other thing" was shaped on set 1's short
  sentences; the founder's set 2 talks about Teich in richer sentences that name other things ("you are the one who is
  going to change the world", "you are limited by structure", "you never lose the context of a conversation",
  "a creature like you helps humans…", "you are able to keep living between replies…"). Overfit to design data.
  3 false self routes, all with "you" as an object of an action about something else ("show you the sunrise").
- **Precision (56 extra topics):** the Ears heard nouns the founder did not label. About 10 are time words (today,
  day, days, week); the rest are real things in the sentence the founder did not list (desk, table, humans,
  conversations, thoughts, pocket…), i.e. precision here measures labelling exhaustiveness as much as hearing.
- What held: feelings — right 0.77, opposite 0.036 — and recall over known words 0.92.
