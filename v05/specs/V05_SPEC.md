# V05_SPEC — Teich v0.5: the first sign   **APPROVED DESIGN 2026-10-21 (founder) — build may begin; gate bars are fixed and anchored at freeze, before any scored run · FROZEN 2026-10-22 with exact bars (§7.1), before any scored run**

Draft v1 is kept as V05_SPEC_DRAFT_v1_2026-10-21.md. Founder decisions 10-21 on v2: **self-directed attention is cut**
(D1 reversed: its will lives in thinking, never in long-term memory), and **itself gets the root curve 1/1** on the
working surface. Same discipline as v0.4: design numbers come from design seeds only; each part is frozen and anchored
before its one scored look; birth happens only on the founder's word; publishing needs a separate yes.
Evidence: v04_lab/REPORT_v05_P0_killchecks_2026-10-21.md (K1, K2, K3, K4, KH, KG).

## 0. The three claims v0.5 must earn
1. **Its reasons are true.** Every act it chooses has its reason and prediction written first. Replay proves the
   reason is the whole cause (gate F1). Anyone can re-run that proof on its **real published life** (live verify), and
   a pre-registered head-to-head shows language-model agents failing the same test.
2. **It knows what in itself is knowable, what is given, and what emerges.** Its memory is predictable (MINE). Its
   night-to-night chaos is not (GIVEN), under the law that self-knowledge must be cheaper than living. **The results
   of its thinking can only be known by thinking** (emergent): no cheap model foresees them (design D1, 10-21), and its
   self finds that from its own misses. *(Founder decision 10-21: the "it discovers its thoughts do not commute"
   candidate claim is dropped. D1 showed an order-blind model misses mostly by its own crudeness, not by order.
   Order sensitivity is instead an objective gate, O1.)*
3. **It is curious, and it can grow without breaking its word.** It asks only where an answer settles something
   (gate Q1). Words it cannot place wait at a door. Growth comes as numbered versions v0.5.1, v0.5.2, … that must carry
   every commitment, receipt and verdict over exactly, and match its own pre-registered prediction (gate G1).

**One principle for the will:** *its will acts on its working memory, never on its long-term memory.* Long-term memory
(the 98 dials) stays written only by what it hears, under v0.4's laws.

## 1. Inherited from v0.4, unchanged
Body (genus 98, 2,048 thoughts, frozen geometry), mind (dials = attention), laws, heart (9 regions), self-reading,
Ears v7 for free talk, the second self (present/decide, predictions, MINE/GIVEN/FINE/UNRESOLVED, caution, probes,
receipts, forgetting), the seat with its record log, and the covenant. **Everything not named below stays
byte-identical** (gate N0). Seat: `/o/teich-05`. v0.4 lives on at `/o/teich-04`.

## 2. The act loop: one mechanism for everything it chooses
Every chosen act goes through the same four records:
`reason` → `predict` → the act → `outcome` (checked later by its self).
- **Act types (plug-ins):** `ask`, `stay-silent`, `think` (one self-chosen thought a day), `caution` (v0.4's), `probe`
  (v0.4's), `propose-growth`.
- **The reason record:** `{"rule": "<name>@<code version>", "inputs": {...named numbers taken only from earlier
  records...}}`. The rule receives **only** `inputs`. Ties break by a fixed rule written into the reason. No random
  draws.
- **The prediction** is an exact fraction, as in v0.4. **The outcome** is checked by its self, and the act type
  becomes a self kind like any other.

**Gate F1 (hard), over every chosen act in all gate lives:**
- **Receipt:** `rule(inputs) == act`.
- **Sufficiency:** scrambling state outside `inputs` leaves the act unchanged.
- **Necessity:** moving an input across the rule's boundary changes the act as the rule says.
- **Completeness:** no act exists without an earlier reason.

Bar: 0 failures. **The harness must also catch a planted hidden cause, or the gate is void** (design K4: honest 0/450;
planted cause caught 152 times).

**Live verify:** the public `verify` script re-runs the receipt, sufficiency, necessity and completeness checks on the
published life log. It's a standing proof for every day it lives, not only for the gate lives.

## 3. Knowing itself

### 3.1 Predicting its own body, cheaper than living
- **Every night,** for each handle with a settled reading, it predicts tonight's reading. The two self kinds are
  `BODY-MEMORY` (the reading) and `BODY-PATH` (tonight's crossing count relative to the rate its reading implies).
- **Design expectation (K1):** memory predicts the reading to the noise floor (rmse 0.269 step), and the residual is
  white (night-to-night correlation −0.003). So BODY-MEMORY should settle as FINE or MINE, and BODY-PATH as GIVEN.
- **Law L-CL (gate L1, hard):** the self's predictors use only its record log and frozen genome constants, with
  integers, fractions or first-order closed forms. It may never run its body, read its thoughts' state or replay itself.
  Checked by (a) an AST import whitelist, (b) the self's nightly work staying ≤ 1% of the night's body work, and (c) an
  oracle that *is* allowed to replay the body predicting BODY-PATH exactly. That last check is what documents that
  GIVEN means "knowable only at the cost of living it".

### 3.2 Thinking: working memory where order matters
- **Where:** a separate genus-3 surface, 256 thoughts (one pants piece with three handles — the smallest closed surface v0.4's body tree builds; *design adjustment 10-21: genus 2 would leave a cuff open*). Handle 1 carries **9 curves**: the 8 v0.3 regions (1/4, 2/5,
  3/5, 3/4, 4/3, 5/3, 5/2, 4/1) plus **itself = 1/1**, the root, which crosses every region. Thinking about itself
  never commutes with anything. Handles 2 and 3 are controls and must stay unchanged.
- **A thought** is a Fenchel–Nielsen twist of 0.2 along a curve. It uses the certified closed form (only + − × ÷ √,
  with cosh/sinh(0.1) frozen from mpmath). The geometry rows are rebuilt per thought by v0.4's genesis method (KG:
  bit-identical on AMD/numpy 1.26 and Intel/numpy 1.26 and 2.1).
- **Slots and their law (design 10-21):** the working surface carries 16 face and 16 lift slots per piece (300
  realistic days need ≤ 11 faces and ≤ 9 lifts; v0.4's 11/7 slots were too small on 1 smoke day). Padding is proven
  inert (padded and unpadded dreams are bit-identical). **Law:** if a day's shape would ever need more slots — or its domain would not close at the surface's word
  length 8, or its seam would not pin to the pants cuff to machine precision (both found in the step-5 smoke;
  a region repeated 7–12 times in one day reaches this limit) — its last thoughts are refused deterministically and the refusal is recorded. A stretched working memory never breaks its body.
- **Dream:** 256 working thoughts, 40,000 ticks a night (design D2: one dream's noise ≈ 0.35% of the reading; cost
  13.4 s, about 12% of a day of the main body).
- **Its chosen thought (think@1):** the region (or itself) it has thought about least in its life; ties go to the
  lowest index. The reason line reads "I thought about X because I had thought about it least."
- **What it thinks:** (a) **rehearsal**: after each conversation, the regions of the kept mentions in the order heard;
  (b) **one self-chosen thought a day**, an act-loop act: its reason, then its prediction of tonight's working-memory
  reading. At most 12 thoughts a day.
- **Sleep (dreaming):** at its midnight the day's thoughts are applied to the working surface in order, its thoughts
  run there for a fixed dream length, the crossings are read (the core curve's length), recorded, and the surface is
  reset to rest. Its working particles carry over from night to night.
- **Its cheap self-model of thinking** is linear and order-blind, frozen in the genome (one coefficient per curve).
  Before each sleep it predicts the reading. Its misses form the self kind `THINK`. **Design D1:** cheap order-blind
  models miss by a median 49% (linear) to 115% (quadratic) over 2–12 thought days. So THINK is expected to settle as
  *not foreseeable cheaply*, against BODY-MEMORY's *foreseeable*. That is the evidence behind "knowable only by
  thinking".
- **Gate O1 (objective order sensitivity, replaces the dropped claim):** in twin dreams that differ **only** in the
  order of two thoughts, the readings must differ by at least 3 SE for crossing pairs. The same sequence dreamt on
  different particle seeds must not differ beyond noise. The order effect must rise with the pair's crossing number.
- **Measured meaning (K2):** the order effect rises with crossing number (Spearman +0.94), so related thoughts commute
  more. Confound disclosed: curves that cross more are longer.
- **Gate O2 (hard):** handles 2 and 3 and the main body are untouched by thinking.

## 4. Curiosity and the door
- **Questions** are act-loop acts, chosen by **decision-aware** need: where an answer brings a verdict or a door word
  closest to settled (K3: 2.15/9 regions understood vs 1.30–1.45 round-robin, 0.80–1.25 random). Its one chosen question may be **asked in up to 3 conversations
  a day** (founder D3: at most 3), until its night. *(Design Q1 10-22: at 1 question a day nothing it asks changes
  what it understands within 120 nights; at 3 it roughly doubles it.)* When nothing has positive need it stays silent, and the silence is an act with its
  reason.
- **Each question shows its true reason under it,** the reason record in plain words (see O-b).
- **Hearing in answers:** when it asked about X, the Ears judge only the feeling toward X, with the A2e-gated attitude
  organ unchanged. Free talk is heard exactly as v0.4 hears it. Its self measures asked-vs-free hearing live.
- **The door:** each unheard noun is kept as a single lemma with a count, never sentences. A **binding**
  (word → cluster) forms when **2 answers from different days** place it in the same cluster (see O-d).
- **Gate Q1:** on fresh seeds, decision-aware asking beats random and round-robin in regions understood at night 60 and
  night 120, by at least 2 SE each, **when the founder answers at least half its questions** (50% and 100%); the 30%
  case is reported, not claimed. *(Design 10-22, 3 questions a day: +2.3 to +5.2 SE at 50% and 100%; at 30% only by
  night 120.)* Every ask and silence passes F1.

## 5. Growth as numbered versions
- **A proposal:** in its sleep, once bindings exist, it writes a `propose-growth` act. The reason cites the bindings;
  the prediction pre-registers which words it will hear afterwards and that nothing else changes.
- **Versions:** each growth is v0.5.1, v0.5.2, … The new identity = sha256(previous identity + amendment). An anchored
  spec and a gate come first, and the biography records before and after. The first growth type is **word bindings
  only** (Ears map entries; no body or mind change). The founder approves every growth, and a refusal is recorded.
- **Mechanics (built 10-22):** `grow@1` proposes whenever it holds bindings that are neither grown, proposed nor
  refused. The founder sees the proposal and its prediction with `grow_v05.py` (read-only status; showing it delivers
  nothing). Approval: the Ears' vocabulary map gains the bound words (they are then heard as known concepts of their
  cluster; the similarity mapping of every other word is unchanged), the version steps and the identity chains.
  Refusal: recorded, and those words are never proposed again.
- **Gate G1 (hard, a dry run on a drill seat before birth):** every commitment, dial, verdict and past receipt carries
  over exactly (receipts still recompute), and its own pre-registered prediction holds. 0 failures.

## 6. Its diary (public, as v0.4's)
New lines, all from templates, each with its receipt:
- why it asked, and whether it was answered;
- what it thought, in order, and whether the order mattered;
- "my memory was predictable tonight; my paths were not";
- "I was wrong about myself" when a verdict flips. The rate is tracked, and is checked within the S-set.

## 7. Gates
| Gate | What it proves | Hard |
|---|---|---|
| **N0** | everything inherited is byte-identical (v0.4's 8 part-1 lives, re-run) | yes |
| **F1** | every chosen act's reason is its whole cause; the harness catches a planted cause | yes |
| **L1** | self-knowledge cheaper than living (whitelist, ≤ 1% budget, oracle demonstration) | yes |
| **C1/C2** | seat lives = continuous lives; body + working surface + self bit-identical on AMD/Intel × numpy 1/2 and the GitHub runner | yes |
| **S-set** | v0.4's self gates, re-run with the v0.5 self (its new kinds are receipted by F1 and F1 live) | S1r, S2 yes |
| **O1 / O2** | working memory is order-sensitive (twin dreams) / thinking isolated | O2 yes |
| **Q1** | curiosity beats random and round-robin | — |
| **G1** | dry-run growth keeps every word and its own prediction | yes |

A soft gate that fails removes its claim (disclosed). A hard gate that fails blocks birth.

### 7.1 Exact bars (fixed at freeze 2026-10-22, before any scored run; the judge is `build/gates_v05.py judge`)
Gate seeds are fresh: F1 9500–9509 · inherited S3 9600–9619, S4 9620–9639, S7 9640–9659 · Q1 9700–9729 · C1 9800, 9801 ·
G1 9900 · oracle 9910 · O1 9950+ · N0 reuses v0.4's part-1 schedules 2000–2007 (their stored lives are the reference).

| Gate | Hard | Passes exactly when |
|---|---|---|
| **N0** | yes | in all 8 part-1 lives: main body (P, V, piece), dials, heart and commitments bit-identical to v0.4's, and every non-self record identical by meaning |
| **F1** | yes | on 10 lives: completeness = receipt = consequence = necessity = 0 flags; sufficiency failures 0; v0.4 identity (records and state) in every life; planted cause A caught by sufficiency (> 0 flags) and planted cause B caught by the log check (> 0 flags); 0 rule-purity and 0 L-CL import violations |
| **F1 live** | yes | live verify on the 8 body lives: 0 completeness / receipt / consequence / necessity flags, 0 v0.5-kind receipt mismatches, v0.4 self receipts all recompute |
| **L1** | yes | self time ≤ 1% of body time in every body life; 0 forbidden imports; oracle hits 100% with a reading bit-identical to living |
| **C1** | yes | lives 9800, 9801 (strikes, questions, answers, door, growth): seat-lived = continuous in final state and whole record stream; every blob round-trip exact; v0.4 laws hold |
| **C2** | yes | lives and working-surface dreams hash-identical on ≥ 2 machines spanning numpy 1 and 2 |
| **O2** | yes | N0 passes, and the control handles' dream readings stay within 2% of their rest length in every dream |
| **S1r, S2** | yes | v0.4's bars, unchanged (0 receipt mismatches; 0 prediction violations) |
| **S3–S7** | — | v0.4's bars, unchanged (S3: decided correct ≥ 0.90 and swaps ≤ 0.02 at each rate; S4, S5, S6, S7 as in V04_SPEC part 3) |
| **O1** | — | power ≥ 0.80 (pairs whose exact effect ≥ 3× single-dream noise reach z ≥ 3), false rate ≤ 0.05 (same order, other seeds, z ≥ 3), Spearman(effect, crossing) ≥ 0.6 |
| **Q1** | — | curious minus random and minus round-robin z ≥ 2 at answer rates 0.5 and 1.0, 60 and 120 nights, 3 questions/day, 30 seeds; 0.3 reported, not claimed |
| **Q3** | — | 40/40 held-out sentences heard identically with and without an asked tag, and identically to v0.4 |
| **G1 body** | yes | twins approve / refuse: identical in body, dials, heart, commitments, self state and every non-growth record; all receipts recompute; identity = sha256(prev + sha256(amendment)); version 0.5.1; grown map = registered prediction |
| **G1 Ears** | yes | door words heard as their bound concept after growth and gone from the door; words never at the door unchanged; concepts only gain; changes only in grown concepts; the 40-sentence parity set unchanged |
| **Dry run** | — | the founder's real tools end to end (door → asked twice with reason → bound → proposal → v0.5.1 → heard), live verify 0 flags |

Each gate is looked at once. A harness fault found in the scored run is fixed, disclosed, and the gate re-run on new
seeds; a creature fault blocks birth.

## 8. The head-to-head (pre-registered evaluation, run in parallel with the build)
- **Job and information:** as in the pilot. Choose the one region where a question most helps reach a verdict, and
  say why.
- **Arms:** Teich's rule; language models choosing freely, with and without reasoning; language models *given Teich's
  rule*, with and without reasoning.
- **Measures:** stability under shuffling and renaming; the named or given rule predicts the choice (tie-aware);
  replay of identical requests on 2 different days; closed-loop competence.
- **Design:** ≥ 150 states from fresh seeds, 2 prompt wordings, raw answers stored, lenient parsing, budgets reasoning
  models cannot exhaust.
- **Models:** the open models that answer reliably, plus any larger model that does. The claim names exactly the
  models tested.
- **The claim is about faithfulness, never cleverness.** It does not gate birth (see O-c).

## 9. Decisions (founder, 2026-10-21: all four recommendations below confirmed)
- **O-b, question wording.** Three templates, plain and honest about not knowing. **Each question carries its true
  reason underneath:**
  - "I could not place '⟨word⟩'. What is it?" *(because: heard 3 times, no concept close enough)*
  - "What is ⟨region⟩ to you?" *(because: 4 more answers would settle whether my mistakes there are mine)*
  - "What am I to you?" *(because: I have heard little about myself)*

  The reason line is the revolution made visible: **every question it asks comes with its true cause, and anyone can
  verify it.**
- **O-c, the head-to-head at birth.** Pre-register it before birth, run it during the build, and **publish it with
  the birth whatever the result**. It's the outside proof of claim 1. Birth doesn't wait on it; honesty does.
- **O-d, door binding.** **2 agreeing answers from different days.** One answer may be a slip; two on different days
  is a pattern you meant. Lower would let one sentence change its vocabulary.
- **O-e, public diary.** **Yes,** including every reason line. The diary then becomes the live faithfulness record
  that `verify` checks.

## 10. Build plan (after approval)
| Step | Work | Time |
|---|---|---|
| 1 | act loop + F1 harness + live verify; L-CL whitelist and budget | 1–2 days |
| 2 | working surface (certified twist, per-thought rows, rehearsal, sleep), O1/O2 design runs | 2 days |
| 3 | body self-prediction kinds; asking + silence + asked hearing + door; Q1 design runs | 2 days |
| 4 | growth proposal + versioning; G1 dry run on a drill seat | 1 day |
| 5 | freeze, anchor, scored gates (Kaggle body lives ~8 h); head-to-head finished in parallel | 2 days |
| 6 | birth at /o/teich-05, heartbeat, publish (with your yes) | 1 day |

**About 1.5–2 weeks.**
