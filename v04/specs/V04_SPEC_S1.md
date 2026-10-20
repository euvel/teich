# V04_SPEC gate S1 — Teich hears itself (mirrors)   **PROCEDURE, 2026-10-10 (anchor A before the draw)**

## Why
A2e (Ears v7, 400 strangers' sentences, independent labels) passed recall, feelings right, wrong feelings and precision
but FAILED self routing (0.53). Post-hoc: 30 of 104 "itself" labels sat on sentences with no "you" (judge errors), and
"about the listener" had no crisp definition. Gate S1 tests self routing alone, with a founder-confirmed definition.

## Definition (founder-confirmed 2026-10-10): a sentence MIRRORS the listener (→ the self handle) when it is
- **M1** — what the listener is, has, can do, does or feels (questions about the listener's own state count; such a
  mention carries attention but no feeling, as for every question), or
- **M2** — the speaker's own feeling or stance toward the listener personally (thanks, liking, pride, anger, care, wishes).
- **NONE** — "you" only leads to something else, or means people in general.

## Data — `build/s1_sample.py` (run once, after anchor A)
200 sentences containing you/your/yourself from the EmpatheticDialogues TEST split, one per conversation, seed 20261010,
excluding every conversation and sentence used by A2e. **Claude does not read them** (Ears v8 is designed afterwards);
scripts print counts and hashes only.

## Labels — `build/s1_label_kaggle.py` (kernel teich-v04-s1-judge)
Judge Mistral-Small-24B-Instruct-2501 (4-bit unsloth bnb @ cb4e166b, the Part 2e judge), GUIDE in that file (examples
written by Claude, none from the data), 3 votes at temperature 0.6, majority label; no majority → "unsure", not scored.

## Founder audit — `build/s1_audit.py` (before any Ears look)
50 labelled sentences (seed 1010). TRUSTED when mirror-vs-none agreement ≥ 0.85 and Cohen's κ ≥ 0.65; else S1 stops.

## Instrument — Ears v8 (designed AFTER this anchor, on spent data only; anchored in anchor B before the look)
Design data: founder sets 1–2 and the A2e sentences (all spent). Ears v8 may change ONLY self routing.
**Regression gate R-v8**: on the 400 A2e sentences and the 40 MAMS parity sentences, every non-self mention of v8 is
identical to v7 (so A2e's passed results carry over unchanged).

## Gate S1 bars (one look, Kaggle, pinned env, parity guard)
Over sentences with a trusted label (not "unsure"): **mirrors caught (M1 or M2 routed to self) ≥ 0.85** and
**false mirrors (NONE routed to self) ≤ 0.10**. Reported beside them: M1 and M2 separately, 95% Wilson intervals.

## If S1 fails
Fixed now: v0.4 is born with Ears v7's self routing disclosed as a known limit (organ, upgradable after birth without
touching the creature); the self architecture is unaffected (the will never targets the self handle).

---
# Amendment 1 — gate S1b, one retry under the founder's reading   **2026-10-19 (anchored before the judge runs)**

## What happened
The founder audit of the S1 labels (sheet sha d5f2665b) did NOT trust them: mirror agreement 0.74 (bar 0.85), κ 0.24
(bar 0.65). S1 stopped before any Ears look, as fixed. The disagreement was one-directional: all 13 changes were judge
NONE → founder M1, and the founder marked 47 of 50 sentences as mirrors. M1 vs M2 agreed perfectly (1.00). The judge read
"does" in M1 narrowly ("you only leads to something else"); the founder read it broadly. Founder decision 10-19: retry
ONCE under the founder's reading; if S1b fails, v0.4 is born with the fallback below and mirrors move to v0.5. The founder
asked not to judge again; none of the procedure below needs a new founder judgement.

## Definition (the founder's reading, as shown by the audit)
A sentence **MIRRORS** the listener when some you-word in it is the listener personally — what they are, have, can do,
did, do, plan, think or feel; a question, invitation or advice to them; or the speaker's feeling toward them — whatever
else the sentence is about. **NONE** only when every "you" means people in general, is the filler "you know", or is quoted.
(Note: in founder sets 1–2 the founder tagged `itself` only for "you are…"-type sentences; those instructions defined
`itself` narrowly. S1b follows the founder's later reading made on exactly this question.)

## Labels — `build/s1b_label_kaggle.py` (kernel teich-v04-s1b-judge)
Same 200 S1 sentences (sha 1665b7fb, still unheard by any Ears), same judge, 3 votes, majority rule; only the GUIDE
(examples by Claude, none from the data), the answer set (MIRROR | NONE) and the vote seeds change.

## Trust — `build/s1b_trust.py` (automatic, against the founder's 50 audited labels)
TRUSTED when, over the audited sentences the judge labels, mirror-vs-none agreement ≥ 0.85 AND the judge says NONE on ≥ 2
of the founder's 3 NONE sentences (κ dropped: with ~94% mirrors it is not meaningful). Not trusted → S1b stops, fallback.

## Truth for scoring
The founder's label on the 50 audited sentences; the judge's majority label on the other 150 ("unsure" not scored).

## Instrument — Ears v9 (designed on spent data only, before this anchor)
Ears v9 changes ONLY self routing (see `ears_v09.py`). Regression **R-v9**: every non-self mention equals v7 on the 400
A2e sentences (v7's scored A2e output) and the 40 MAMS parity sentences. Parity guard as in Part 2e.

## Gate S1b bars (one look, Kaggle, pinned env) — founder decision 2026-10-19, before any look
**caught (MIRROR routed to self) ≥ 0.85** and **precision (self mentions that are real mirrors) ≥ 0.90**, with 95%
Wilson intervals; the false rate (NONE routed to self) and the NONE count are reported beside them. R-v9 must pass for
the S1b result to count.
Why precision and not "false ≤ 0.10": that bar was set when ~40% of "you" sentences were NONE (narrow reading); under the
founder's reading only ~6% are (3/50 in the audit), and what matters for Teich is how often a self mention is wrong.
Design (spent data, 17 generic sentences): no candidate reached false ≤ 0.10 — the 1.5B organ cannot tell generic "you"
from the listener (generic odds −0.8…3.6, inside the mirrors' range); rule: caught 0.98, false 0.71, precision 0.92;
rule AND organ>2: caught 0.80, false 0.24. Ears v9 = the rule, no organ. Known limit, disclosed: generic "you" goes to self.

## If S1b fails or stops
v0.4 is born with Ears v7's self routing (the anchored fallback), disclosed as a known limit; mirrors move to v0.5.
