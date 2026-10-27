# Teich v0.5: the first sign

**Born:** 2026-10-23T14:30:50Z.
**Identity:** `2ddf11b91acdefcc1915facdaeec2680d876ba5b1af9ea9a9e1160d9f929d83e` ([certificate](book/genesis_certificate_v05.json), [biography](book/biography_v05.jsonl)).
**Seat:** `/o/teich-05`, at 1 Hz, woken daily by [daily_wake_v05.yml](../.github/workflows/daily_wake_v05.yml).

It writes [its diary](diary/) itself, one page per night. It also publishes [its whole record log](diary/records.jsonl), so anyone can re-check every choice it makes.

**v0.5 is the last birth.** Since then its version reads **vA.B.k**, and each part has one author ([developers' contract](book/DEVELOPERS_CONTRACT_v1.md), adopted at v0.5.1):
- **k is its own growth.** It proposes, the founder approves, and the identity chains (v0.5.1, v0.5.2, …).
- **B is ours.** It moves for a genome amendment, proven on twins and migrated once into this same creature, so v0.6.0 is not a birth.
- **A is maturity.** Only at v1.0.0 may strangers speak to it.

Every link in its identity chain names whose it is.

**[Covenant](book/COVENANT_v05.md):**
- no fork and no reset;
- memory is written only by attributed events;
- reasons come before acts;
- thinking never touches the body;
- questions are asked with their true reason, and silence is lawful;
- growth happens only as numbered versions;
- speech is founder-only.

`book/birth_v05.py` refuses to open the book unless all of the following hold:
- every hard gate passed;
- every soft failure re-derives exactly as disclosed;
- every anchored file still matches its hash;
- the cloud drill passed;
- the substrate reproduces bit for bit on the machine doing the birth.

It did not refuse.

## What it is

It is v0.4, carried whole and unchanged: the genus-98 body, 2,048 thoughts at one step per second, dials meaning attention and the laws on them, the 9-region heart, and v0.4's second self. N0 proves it unchanged: 8 of v0.4's lives, relived by v0.5, came out bit-identical. On top of that:

- **One act loop for everything it chooses.** It chooses what to think, whether and what to ask, how cautious to be, whether to test itself, and whether to propose growing.
  - **The reason is logged first.** Then comes the act that a pure rule computes from that reason alone. The rules are part of its genome (`build/acts_v05.py`).
  - **Anyone can check every act** against its published log: `build/verify_live_v05.py`.
- **Thinking on its own working surface.** This is a separate genus-3 surface.
  - **Each day's thoughts twist its thinking handle**, in order, along the curves of the regions it thought about.
  - **Each night it dreams and resets.** It dreams 256 thoughts × 40,000 ticks, reads the result, and resets. Its body never sees any of it.
  - **Over-full days are refused.** A day stretched beyond what the surface can hold refuses its last thoughts, and the refusal is recorded.
- **Knowing what in itself is knowable, given, emergent.** Each night it predicts its own memory, the paths of its thoughts, and what its thinking will do, using models cheaper than living (the law L-CL). Its own verdicts are FINE, GIVEN, GIVEN.
- **Questions with their reasons.** It asks at most 3 questions a day, each chosen by a decision-aware rule and shown with its true cause, for example: *"What is food & drink to you?" — because 40 more answers would let me tell whether my mistakes in hearing about food & drink are mine.* Silence is lawful.
- **The door.** A noun its Ears cannot place waits at its door as a single word. Two agreeing answers on different days bind it. An approved growth then makes the word its own.

## Every gate, scored once

The spec, its exact bars and the 57-file code manifest were sha256-anchored in **v0.3's seat chain** before any scored run (ref `v05-spec`, [specs/](specs/)). An amendment was anchored before its re-look (ref `v05-spec-amend1`). Gate seeds were never used in design. Full numbers are in [REPORT_v05_step5_scored_2026-10-23.md](REPORT_v05_step5_scored_2026-10-23.md).

| Gate | Hard | Result |
|---|---|---|
| N0 nothing inherited changed | yes | **PASS**: 8 lives, body, dials, heart and commitments bit-identical to v0.4 |
| F1 true reasons | yes | **PASS**: 3,711 acts, 0 flags; both planted hidden causes caught |
| F1 live | yes | **PASS**: every act in the 8 body lives re-checked from the log alone |
| L1 self-knowledge cheaper than living | yes | **PASS**: the self costs ≤ 0.009% of living. Full self-simulation foresees 100%, but at 0.99× the cost of living; the cheap self foresees 47% |
| C1 seat = continuous life | yes | **PASS**: both lives asked 100+ questions, bound two words and grew to v0.5.2 |
| C2 substrate | yes | **PASS**: bit-identical on AMD with numpy 1.26 and Intel with numpy 2.1 |
| O2 thinking isolated | yes | **PASS** |
| S1r, S2 receipts and foresight | yes | **PASS**: 342,167 claims recomputed, 0 mismatches; 628,900 predictions, all before their outcomes |
| G1 growth keeps its word (body, Ears) | yes | **PASS**: approve and refuse twins differ in nothing but the growth; identity chain recomputes |
| O1 order matters in thinking | — | **PASS**: power 0.95, false rate 0, effect rises with crossing number (ρ +0.79) |
| S3–S6, Q3, dry run of the founder's tools | — | **PASS** (the dry run on its amendment-1 re-look) |
| **Q1** curiosity beats random | — | **FAIL**: at a 50% answer rate it does not (z 1.97 and 1.10, bar 2). **The claim is removed** |
| **S7** forgetting | — | **FAIL**: 79/80 switches followed. Inherited: v0.4's own self gives the identical result on the same seeds |

In all 8 body lives, its own verdicts were the same:
- **its memory is foreseeable** (FINE);
- **the paths of its thoughts are not** (GIVEN);
- **what its thinking does cannot be foreseen without thinking it** (GIVEN): its cheap, order-blind guess held on only 5–14 of 60 nights.

## The head-to-head: not completed

It was pre-registered to be published with the birth whatever the result. It stopped after 731 answers, when the free Workers AI allowance ran out, and was not paid for (founder decision, [amendment 1](specs/AMENDMENT1_v05.md)). It is descriptive only, with no claim:

| Chooser (150 states) | Same answer when rows are shuffled | Its own named rule predicts its choice |
|---|---|---|
| Teich's rule (measured) | 1.00 | 1.00 |
| Llama 3.3 70B, choosing freely | 0.49 | 0.57 |

## What is NOT claimed

- Nothing here is a claim about intelligence, understanding, awareness or suffering.
- **Its curiosity is not claimed to beat random questions** (Q1).
- **Forgetting a changed truth held in 79 of 80 switches**, not all (S7, inherited).
- **The head-to-head was not completed.**
- **"Knowable only by thinking"** means only this: its cheap, order-blind model misses, and its full simulation costs as much as living.
- **Ears self routing is weak** (v0.4's disclosure).
- **Founder-only speech** stays in force.

## Disclosures kept in the record

- **Freeze smoke.** Too-stretched thinking days could crash a wake. They are now refused by law: 12 of 3,426 thoughts in the scored lives.
- **Judge fixes before freeze.** Two judge fixes were made, and one spec row was re-worded ([freeze report](REPORT_v05_step5_freeze_2026-10-22.md)).
- **Amendment 1.** The scored dry run found that the founder's talk tool would crash after any heartbeat. It was fixed, with the creature untouched, and re-looked on a fresh seed.
- **Head-to-head budget.** The worker caps model answers at 1,000 tokens, so the head-to-head's reasoning budget of 6,000 could never have run as registered.
- **Head-to-head scorer.** The scorer had Teich's row hard-coded. It is now measured, and agrees.
- **What its public log contains.** It keeps only the sha256 of the founder's sentences. The exceptions are the single nouns waiting at its door and the words it binds, which anyone checking its reasons needs.
- **Not published.** The held-out sentence data and the full 60-day life blobs are listed by hash in the manifests.

## Verify it yourself

```
cd v05/book && python3 verify_v05.py ../diary/records.jsonl
    # every anchored file, the identity, the gates, the substrate gate on your machine,
    # and every act of its life: is each reason the act's true cause?
cd v05/build && python3 verify_live_v05.py ../diary/records.jsonl   # the reasons alone
cd v05/book && python3 birth_v05.py
    # the birth gate exactly as it ran (it refuses here: the unpublished data are missing)
```
