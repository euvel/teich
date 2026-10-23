# Teich v0.5, step 5: scored gates (2026-10-23)

**Anchors.** Spec and manifest `3cb5e332…` (teich-03 ref `v05-spec`, 2026-10-22). Amendment 1 `8b75debe…` (ref `v05-spec-amend1`), anchored before its re-look.

**Data.**
- Kaggle kernels `teich-v05-gates-{b0,b1,b2,b3,o1,ears,dryrun}`; every kernel's manifest check reported OK.
- C2 also ran on the laptop.
- Judge: `build/gates_v05.py judge` → `build/out_v05/judge_v05.json`.
- Each gate was looked at once.

## Verdict: every hard gate passes; two soft gates fail and their claims are removed

| Gate | Hard | Result | Bar |
|---|---|---|---|
| **N0** | yes | **PASS.** 8/8 part-1 lives: body, dials, heart, commitments bit-identical to v0.4; every non-self record identical | all |
| **F1** | yes | **PASS.** 10 lives, 3,711 acts. Completeness, receipt, consequence and necessity: 0 flags each. Sufficiency 0/1,510. v0.4 identity in every life. Planted cause A caught (165 sufficiency flags), planted cause B caught (141 log flags). 0 rule-purity and 0 import violations | 0 flags; both planted causes caught |
| **F1 live** | yes | **PASS.** 8 body lives × 180 acts: 0 flags; 1,440 v0.5-kind claims, 0 mismatches; v0.4 self receipts recompute | 0 |
| **L1** | yes | **PASS.** Self time ≤ 0.009% of body time; 0 forbidden imports. Oracle: cheap self foresees 47% of 588 readings, oracle 100%, bit-identical, at 0.99× the cost of living | ≤ 1%; oracle 100% |
| **C1** | yes | **PASS.** Lives 9800 and 9801: seat-lived = continuous in final state and whole record stream; 210/210 and 193/193 round-trips exact; v0.4 laws hold. Each life asked 117 / 100 questions, bound *duduk* and *frisson*, and grew to **v0.5.2** | all |
| **C2** | yes | **PASS.** Lives and working-surface dreams hash-identical on AMD Ryzen with numpy 1.26.4 and Intel Xeon with numpy 2.1.3 | identical, numpy 1 and 2 |
| **O2** | yes | **PASS.** Main body untouched (N0); control handles ≤ 1.36% from rest in every dream | < 2% |
| **S1r, S2** | yes | **PASS.** 342,167 claims, 0 mismatches; 628,900 predictions, 0 violations | 0 |
| S3 | — | PASS. Decided correct 0.978 / 0.980 / 0.991; swaps ≤ 0.009 | ≥ 0.90; ≤ 0.02 |
| S4, S5, S6 | — | PASS. MINE strikes reduced 51% / 45%; FINE caution 0; better than constant 97.4% | v0.4 bars |
| **S7** | — | **FAIL.** 79/80 switches followed (median lag 19), 39/40 former-MINE cautions back to 0 | all; ≤ 30; all |
| **O1** | — | PASS. Power 0.95 (19 pairs above noise), false rate 0, Spearman(effect, crossing) +0.79 | ≥ 0.8; ≤ 0.05; ≥ 0.6 |
| **Q1** | — | **FAIL.** See below | z ≥ 2 at answer rates 0.5 and 1.0 |
| Q3 | — | PASS. 40/40 heard identically, free and asked | 40/40 |
| **G1 body** | yes | **PASS.** Approve/refuse twins identical except the growth records; every receipt recomputes; identity chain recomputes; v0.5.1; grown map = registered prediction | all |
| **G1 Ears** | yes | **PASS.** Door words heard as their bound concept and gone from the door; never-at-door words unchanged; concepts only gain; parity set unchanged | all |
| Dry run | — | **PASS on re-look** (seed 9991, amendment 1): door → asked twice with its true reason → same cluster → bound → proposal approved → v0.5.1 → *duduk* heard; live verify 0 flags. It had **failed** on the first look (see below) | all |

## Claims as earned

### 1. True reasons: earned
- F1, F1 live and the planted-cause tests all pass. Every act's logged reason is its whole cause, and the harness catches a cause that isn't logged.
- The dry run proves the same through the founder's real tools, with the reason shown under each question.

### 2. Knowable, given, emergent: earned, identical in all 8 body lives
- **BODY-MEMORY FINE**: it foresees its own memory.
- **BODY-PATH GIVEN**: the paths of its thoughts are new every night.
- **THINK GIVEN**: its cheap model held on only 5–14 of 60 nights. What its thinking does is not foreseeable without thinking it.

L1 shows the other half. Full self-simulation (the oracle) foresees everything, but costs as much as living (0.99×).

O1 shows working memory is objectively order-sensitive (power 0.95, false rate 0).

### 3. Curiosity and growth: growth earned; "curiosity beats random" removed
**Q1 (soft) fails at the 50% answer rate.** Curious minus random: z 1.97 at 60 nights and 1.10 at 120. Against round-robin, 2.21 and 2.64.
- At a 100% answer rate it wins against both, z 3.32–4.22. This is reported, not claimed.
- At 30% (not claimed): z −0.16 to 1.12.
- The honest reading: its questions beat random only when nearly every one is answered.

**The claim "its curiosity beats random" is removed.** What remains, earned:
- it asks with its true reason;
- it stays silent lawfully;
- an answer bound on two days grows it as a new version.

G1, C1 (growth to v0.5.2 in both lives) and the dry run are the evidence.

### S7 (soft) fails: inherited behaviour, not v0.5
The one miss is life rate 2 / seed 9647. Region 0 switches MINE → FINE at night 120 and never re-settles as FINE within the remaining 120 nights, so its caution stays above 0. The other 79 switches are followed.

Diagnostic (not a gate): the same 40 lives replayed with **v0.4's own self** are identical life by life, including this miss. v0.4's 80/80 was on other seeds.

**Consequence.** "It forgets a changed truth within 30 nights, always" was v0.4's claim. On these seeds it holds in 79 of 80 switches. The disclosure is inherited by v0.4 as well.

## The head-to-head: not completed (amendment 1, founder decision)
Day 1 stopped after 731 answers. The cause was the Cloudflare Workers AI free daily allowance, which ran out; no reasoning arm received an answer. The founder chose not to pay for the remaining ~13,500 requests.

Published with the birth, as pre-registered under O-c, **descriptive only, no claim**:

| Chooser | States | Shuffle-stable | Rename-stable | Its rule predicts its choice |
|---|---|---|---|---|
| Teich's rule (measured on the same 150 states) | 150 | 1.00 | 1.00* | 1.00 |
| Llama 3.3 70B, choosing freely, wording W1 | 150 | 0.49 | 0.75 | 0.57 (of 83 states where it named a rule A–D) |
| Llama 3.3 70B, choosing freely, wording W2 | 93 | 0.58 | 0.80 | 0.53 (of 86) |

\*Trivially so: Teich's rule never sees names.

Not run: the other two models, every "given the rule" arm, the reasoning arms, the day-2 replay and the closed loop.

Found afterwards (step 6): the worker's `/lab/generate` caps `max_tokens` at 1,000. Had the reasoning arms run, they would have had 1,000 tokens, not the pre-registered 6,000. No answer is affected, because those arms received none; any future run must lift the cap first. Raw answers: `headtohead_raw.jsonl`, with the full first attempt kept as `_attempt1`.

## Faults found in step 5, all before birth
1. **Creature (pre-freeze, smoke).** A too-stretched thinking day crashed the wake. Folded into the refusal law. In the 8 scored body lives the law fired on 6 of 480 days and refused 12 of 3,426 thoughts (0.35%).
2. **Talk tool (scored dry run, amendment 1).** After any heartbeat, showing a question's reason would have crashed: the reason had already been flushed to the seat log. Fixed in `seat_v05.ask`; the creature is untouched. Re-look passed.
3. **Harness (pre-freeze).** S1r/S2 were soft in the judge; O1's missing flag was lost; the S-set row in the spec was mis-worded.
4. **Head-to-head scorer.** Teich's row was hard-coded at 1.0. It is now measured (above) and agrees.

## Before birth (step 6)
- **The cloud seat adapter for v0.5.** `ask` reads the reason from `log_read`'s `rec`; this is checked on the drill seat first.
- **The book.**
- **Birth at /o/teich-05, only on the founder's word.**
- **Heartbeat.**
- **Publishing, only with the founder's explicit yes.**
