# V04_SPEC part 2a — Ears v5 gates A2a + R2 (A2b bars fixed here, its data frozen in part 2b)   **FROZEN 2026-10-06 (pending anchor)**

2026-10-06 · private. Bars approved by the founder 10-06. Part 1 (anchored teich-03 ref v04-spec-part1) certified body and mind; its gate A1b failed
(Ears topics 49%), which blocks birth with the v4 Ears. Part 2 replaces the Ears and re-gates them. It is split so
that the public gate can run before the founder set exists:

- **Part 2a** — Ears v5 code (`build/ears_v05.py`, `build/talk_v04.py`), gates A2a + R2; frozen, anchored, run now.
- **Part 2b** — gate A2b on the founder set; frozen and anchored when the founder's file is written.
Birth only after 2a and 2b pass, and only on the founder's word.

## Ears v5 (design: REPORT_ears_v5_design_2026-10-06.md)
Every topic in a sentence (spaCy nouns → our concept if exact, else nearest by MiniLM when cosine ≥ 0.60, else not
heard); one mention per cluster per sentence; self routing as v4; attitude per topic on its own clause, three-way
(positive / negative / neutral) by Qwen2.5-1.5B-Instruct (snapshot 989aa798…), neutral or |log-odds| ≤ 1.0 → no
feeling; questions → no feeling. **Invariance:** the feeling counts only if the clause-alone and whole-sentence
judgements agree. **Whose feeling:** only the speaker's own present attitude (not someone else's, not "you love…", not
under if / unless / whether, not "used to"). Every withheld feeling carries its reason. Veto-only read-back in the
conversation path (founder decisions 10-06).

## Gates
| gate | data | measure | proposed bar | design value (not evidence) |
|---|---|---|---|---|
| **A2a** public | **MAMS test**, all 500 sentences (multi-aspect, multi-sentiment), never opened | recall of gold topics that are our concepts | ≥ 0.90 | 0.953 |
| | | on heard positive/negative gold topics: correct / **opposite** | ≥ 0.62 / **≤ 0.13** | 0.690 / 0.083 |
| | | precision, lower bound | ≥ 0.45 | 0.529 |
| **A2b** founder | founder set (~100, multi-topic, frozen by sha256) | recall of founder topics | ≥ 0.80 | — |
| | | on warm/cold topics: correct / **opposite** | ≥ 0.75 / **≤ 0.08** | — |
| | | precision (heard topics the founder listed) | ≥ 0.70 | — |
| | | self routing ("itself" topics heard as the self cluster) | ≥ 0.90 | 12/12 (v4 design) |
| **R2** regression | "My dog is wonderful." | exactly one mention: animal·dog·pet, warm; creature effects as D1 | exact | pass (probe) |

Rebased 10-06 on the final design (invariance + whose feeling trade correct answers for fewer wrong ones: correct
0.793 → 0.690, opposite 0.148 → 0.083). Bars are looser on MAMS than on the founder set on purpose: MAMS sentences are built to contrast sentiments and its
labels are partly disputable (design inspection); the founder set is how Teich will actually be spoken to.
Gold for A2a as in design: an aspect's head noun (spaCy) → our concept if it is one ("certain"); recall counts certain
gold topics; attitude counts every heard gold topic. One look.

## Scoring harness and environment
`build/gates_v04_part2.py` (a2a, r2; a2b for part 2b). Smoke-checked on 40 MAMS *val* sentences only; MAMS test never
opened. Scored run on Kaggle (CPU, float32) with pinned versions: transformers 4.44.2, sentence-transformers 3.0.1,
tokenizers 0.19.1, spaCy 3.8.16 + en_core_web_sm 3.8.0, Qwen2.5-1.5B-Instruct @989aa7980e4cf806f80c7fef2b1adb7bc71aa306,
all-MiniLM-L6-v2 @1110a243fdf4706b3f48f1d95db1a4f5529b4d41 (the Ears refuse any other snapshot).

## Integrity
Code manifest (Ears v4 base + v5, talk tool, part-2 harness, genome, creature, seat, vocabulary, geometry table, MAMS test
file, this spec) anchored in teich-03's chain before the scored look. Design record: REPORT_ears_v5_design_2026-10-06.md.
