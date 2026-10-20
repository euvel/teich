# Part 2e scored — Ears v7 on strangers' sentences (A2e) and R2e   2026-10-20 (look made 2026-10-10)

Spec: specs/V04_SPEC_part2e.md, anchored teich-03 (procedure b31b29b7, amendment 1 6cbcf528, amendment 2 d7cf0eb8,
labels a0b29d14 + audit e9a38331). Kaggle kernel teich-v04-part2e, pinned Python 3.12, Intel Xeon 2.20 GHz.

## Verdict
**R2e PASS. A2e FAIL on one bar only: self routing** (0.53 vs ≥ 0.90). Every other A2e bar passed.
The failure rule was not pre-registered (founder's choice 10-09). Founder decision afterwards: test self routing alone
in gate S1. **S1 and S1b both stopped at label trust (REPORT_S1_2026-10-20.md), so v0.4 is born with Ears v7's self
routing, disclosed as a known limit.**

| A2e measure (400 sentences, EmpatheticDialogues test, 7 strata) | value | 95% Wilson | bar | |
|---|---|---|---|---|
| recall, topics the mind has a word for (366) | **0.801** | 0.757–0.838 | ≥ 0.80 | pass |
| feelings right (113 warm/cold topics heard) | **0.770** | 0.684–0.838 | ≥ 0.75 | pass |
| **wrong feelings** (opposite sign) | **0.035** | 0.014–0.087 | ≤ 0.08 | pass |
| precision (heard topics that are labelled topics) | **0.855** | 0.818–0.886 | ≥ 0.70 | pass |
| self routing (104 "itself" labels) | **0.529** | 0.434–0.622 | ≥ 0.90 | **fail** |
| reported: self false routes | 19 of 296 non-self sentences (0.064) | | | |
| reported: coverage of all labelled topics (626) | 0.575 | | | |

Parity guard: Kaggle heard the 40 MAMS-val sentences exactly as the laptop (0 of 40 differing, 122 mentions).
R2e: "My dog is wonderful." → the dog cluster +1 warm, one heart step, every other handle identical.

## Findings
1. **The feelings that reach the creature are safe.** Wrong feelings 3.5% (upper bound 8.7%) on strangers' sentences.
   This is the one Ears property that cannot be repaired after birth (the creature keeps what it heard), and it held.
2. **Recall sits exactly at the bar** (0.801; lower bound 0.757). Coverage of *all* labelled topics is 0.575: many
   strangers' topics are words outside the 1,066-concept vocabulary (growth = v0.5).
3. **Self routing failed, and it was mostly a definition problem.** Post-hoc: 30 of 104 "itself" labels sat on
   sentences with no "you" (judge errors), and "about the listener" had no crisp definition. All 55 correct routes and
   all 19 false routes are in the *listener* stratum. Gates S1/S1b then showed that the founder reads nearly every
   listener-"you" as a mirror, while generic "you" divides judges, the founder and the 1.5B organ alike.
4. **Strata.** Feelings were weakest under contrast ("but…": 13 of 24 right) and best in plain sentences (16/17).
   Questions carried almost no feelings, by design.

## Disclosure
- Labels: Mistral-Small-24B (amendment 1, after the NVIDIA free tier throttled GLM-5.3); pronouns removed by a fixed
  list (amendment 2). Non-noun topics stayed in, which costs recall and precision.
- Founder audit (60 sentences): the first submission was unchanged from the generated file and was not accepted; the
  second changed 1 line; the third changed 5 attitudes. Scored TRUSTED by the anchored rule (topic F1 1.00, attitude
  agreement 0.943, itself κ 1.00). A reader should weigh how much this audit vouches for the labels.
- Claude designed Ears v7 before any part 2e sentence was drawn; the sentences and labels were seen afterwards, and the
  instrument was anchored before they existed.
