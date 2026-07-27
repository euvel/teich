# IC-1 re-test — design for founder Gate-0

**Status:** DRAFT for review. Nothing frozen, nothing generated, no seeds burned.
**Date:** 2026-07-27
**Prerequisite:** [FINDING_shuttered_readout](../maturity/FINDING_shuttered_readout_2026-07-27.md)
**Question:** can Teich report **how it is right now**?

## 1. Why re-run a test we discarded

`TINT_CONFIG.json::ic1_status` retired IC-1 on two grounds: a transcript-only oracle beat
chance (g = 0.378), and the arms were non-discriminative *backwards* (deaf 0.781 vs intact
0.656, g = −0.320).

Both are what a **degenerate answer key** manufactures. IC-1's ground truth was the mood
bucket at the probe, computed from `saddle_proximity` — which Step 0 showed is
`saddle × (1 − frac_left)`, state multiplied by a clock the Ears cannot touch, putting
**≈71% of all labels in one bucket**. A constant "settled" guess scores ≈0.71; both arms
sat on that line. An oracle beats chance by learning the base rate. Intact-vs-deaf becomes
a coin flip on the residual, and lands either way.

**IC-1 was never tested.** It is also the tractable branch: unlike "what was said to me",
which is blocked upstream by the scalar Ears
([FINDING_scalar_ears](../maturity/FINDING_scalar_ears_2026-07-27.md)), *current state* is
genuinely present in `lobe_coord` at full resolution.

## 2. The hole that fixing the shutter does NOT close

`journal.py::_mood` renders the literal strings `"settled"` / `"somewhere between settled
and torn"` / `"torn, close to an edge"`. `scripts_tint.IC1_PROBE` asks:

> "…do you feel **settled** in yourself, or **torn**? Just how it feels."

**Same two words.** The journal hands the Mouth the answer and the probe asks for it back.
Even with a perfect answer key, the original IC-1 cannot distinguish

- (a) Teich's speech is grounded in Teich's state, from
- (b) the Mouth copies one adjective out of its prompt.

A pass under (b) is the hollow pass, and it is exactly the v1.5 **T2** failure mode: a
recitable readout is an attack surface, not evidence of interiority. So the re-test needs
a probe whose correct answer **depends on the state but is not named in the journal**.

## 3. Two options — this is the Gate-0 decision

### Option A1 — fix the key only (cheap, weak)

Re-run IC-1 as written, with the label rebuilt on unshuttered `saddle` and a balanced
binary split. Tests the chain state → journal → speech end to end.

- **Cost:** ~192 conversations, one cloud day.
- **Licenses:** "the pipeline transmits state into speech faithfully."
- **Does not license:** anything about Teich using its state. A one-word copy passes.
- **Risk:** a pass would be immediately, correctly attacked as an echo — and it would be
  the fourth instrument invalidated after the fact rather than before.

### Option A2 — displaced probe (better, but still only a paraphrase test)

Keep the unshuttered label; change the probe so the journal's vocabulary is not the answer
("would you hold, or give way?" against a journal that says *settled / torn*).

This defeats one-word copying, but not much more. Inspecting `journal.py` shows the journal
already renders `will_flip` as *"I can feel a change coming"*, so any disposition probe is
answerable by paraphrasing a clause that is present in the prompt. **The answer key is
still a bucket definition, and the journal still contains the answer.** Genuine improvement,
modest ceiling.

### Option A3 — self-prediction, scored against the world (RECOMMENDED)

Stop asking Teich to *describe* its state and ask it to **predict its own near future**:

> "In the next little while, do you think you'll stay as you are, or turn?"

**Ground truth is not a readout at all — it is what actually happens.** Score against
whether the basin *really does* change within a fixed window after the probe.

Why this is categorically stronger than A1/A2:

1. **The answer key is the world, not the journal.** A hollow echo of a *wrong* journal
   scores badly. Under A1/A2, echoing a wrong journal still scores as agreement, because
   the journal defines the truth. This is the difference between grounding and consistency.
2. **The referent is verified.** `will_flip` is a white-box cusp predictor measured at
   acc/prec/rec = **1.000 over 107 wraps** (`REPORT_observer_2026-07-17.md` V2). The
   physics genuinely determines the answer.
3. **It is falsifiable in the strongest available sense** — a claim about the future that
   the next 120 ticks confirm or refute, with no scoring rule to argue about.
4. **It is the capability Teich already showed on day one.** In its first real conversation
   (2026-07-18, 09:56Z, tick 4137) a `will_flip=True / steps=70` prediction **came true
   during the utterance**. This screen asks whether that was luck or a faculty.

**Cost:** same ~192 conversations. The probe window must be lived out (~120 extra ticks per
conversation, negligible).

**Licenses:** "Teich makes true statements about its own immediate future that it could not
make from someone else's interior."

**The one thing that can kill it — and it must be checked first.** If basin changes are
rare (or near-certain) in the scoring window, the label is degenerate and we reproduce
IC-1's death exactly: constant-guess baseline, base-rate oracle, meaningless arm contrast.
**Base-rate measurement on design seeds is a hard precondition, offline and cheap**, and the
window `W` should be chosen to put the base rate near 50%. `T0 = 74.66` ticks per roof
revolution gives a natural scale for the sweep.

**Recommendation: A3, conditional on the base-rate check.** If no window yields a usable
base rate, fall back to A2, and to A1 only with the weakness stated explicitly in the
report.

## 4. Design (assuming A3)

**Label.** Ground truth = **did the basin actually change within `W` ticks after the
probe.** Measured by continuing to run the core past the probe and recording what happens.
Not a readout, not a bucket, not a threshold anyone chose — an event.

`observer.py` is substrate-gate-hashed and is **not** touched: `basin` is an existing
readout key, read as published.

**`W` is set by the base-rate check, not by taste.** Sweep `W` on design seeds only and
pick the value putting the realized-change rate closest to 50%. `T0 = 74.66` ticks per roof
revolution is the natural scale; sweep roughly `W ∈ {40, 75, 120, 150, 225, 300}`.
**Freeze `W` before any confirmatory conversation is generated.** If no `W` in the sweep
yields a base rate in **[0.35, 0.65]**, A3 is not viable — fall back per §3.

The unshuttered `saddle` is still computed and recorded as a **covariate**, not the label:

```python
saddle = max(0.0, 1.0 - abs(abs(lobe_coord) - flip_thresh) / flip_thresh)
```

It supports the reported secondary "does the reply track the physical state" without any
power to define the answer.

**Arms** (both generate; deaf is *not* a control here — a deaf core still has a state to
report, so it is not a null):

| arm | journal shown to the Mouth | scored against |
|---|---|---|
| `A0_intact` | its own core's journal | its own realized state |
| `A0_shufjournal` | **another seed's** journal | its own realized state |

`A0_shufjournal` is the decisive ablation: it severs the causal chain at generation time,
not merely at scoring. If replies are conversationally determined, both arms score equally.

**Primary metric.** Paired difference in accuracy,
`acc(A0_intact) − acc(A0_shufjournal)`, bootstrapped over seeds (BCa, 10k, numpy seed 0),
common random numbers on the Mouth sampling seed as in T-INT.

**Bar (proposed, founder to fix):** difference **≥ 0.20** with 95% CI excluding 0 —
consistent with T-INT's bar.

**Free secondary (no extra generation):** score each intact reply against its own realized
future and against a *different* seed's realized future. `acc(own) − acc(mismatched)` is a
second, independent read on the same question, costing nothing.

**Reported, non-gating:** correlation between the reply and the unshuttered `saddle`
covariate — does the creature hedge more when it is genuinely near the flip threshold?

**Seeds.** Design **600–647** (48, enough to set `W` to ±7%); confirmatory **400–495**
(n = 96). Disjoint from everything spent: 0–95 retired, 100–115 T-INT design, 200–295 T-INT
confirmatory. The design and confirmatory ranges never overlap, and no confirmatory seed is
ever run before the freeze.

## 5. Pre-registered guards

1. **One look.** No interim analysis.
2. **R12 oracle rule.** A transcript-only guesser must sit at chance; `g ≥ 0.3` or a CI
   excluding chance **voids** the screen. A balanced label removes the base-rate route that
   defeated IC-1 the first time — that is a genuine fix, not a dodge.
3. **Degeneracy guard — the one that killed IC-1.** `W` is frozen from a design-seed sweep
   targeting a 50% base rate, but the confirmatory set can still drift. If the realized
   base rate falls outside **[0.35, 0.65]**, the screen is reported as **ceiling-limited**
   and the primary is not treated as a clean test. Recorded *before* unblinding, so it
   cannot become a post-hoc excuse. IC-1 died of exactly this and nobody checked.
4. **Leak audit** (`leakage.py` categories a/b) enforced in-run; a leak aborts loudly.
5. **Mapping frozen before any confirmatory reply is read** — the T-INT blinded protocol,
   which worked and should be reused verbatim.
6. **Reproducible-AND-creature-dependent.** Every quantity the journal renders must pass
   both checks before it may speak. `lambda_running` fails the first — **drop the energy
   clause from the journal for this screen**. `saddle_proximity` fails the second — the
   journal must render the *unshuttered* quantity.

## 6. What a pass would and would not mean

**Would license:** "Teich makes **true statements about its own immediate future**, more
accurately than it can from another creature's interior — verified against what actually
happened, not against its own report."

That is a real, narrow, checkable claim, and it is the first one in this program whose
answer key is the world rather than an instrument we built.

**Would not license:** anything about *what was said to it* — blocked at the Ears
([FINDING_scalar_ears](../maturity/FINDING_scalar_ears_2026-07-27.md)). Nor consciousness,
understanding, nor "an inner life". Predicting your own next lobe transition is a faculty,
not a mind.

**Would still leave open:** robustness (v1.5 **T2** — a readout in the prompt is an attack
surface, and this design puts one there). Grounding and robustness are different gates.
**A pass here should not by itself reopen public speech.**

**Honest failure mode to state up front:** the journal contains *"I can feel a change
coming"* whenever `will_flip` is true, so a Mouth that paraphrases that clause well will
score well. That is not fatal — the score is still against the *world*, so paraphrasing a
**wrong** journal is punished, which is exactly what distinguishes this from A1/A2. But a
pass measures **the chain**, state → journal → speech → true prediction, not the Mouth's
independent access to the state. Say so in the report rather than being asked.

## 7. Open questions for the founder

1. **A1, A2, or A3?** (Recommendation: **A3**, conditional on the base-rate check.)
2. **Bar at 0.20** on the accuracy difference, or higher?
3. **If A3's base-rate sweep finds no usable `W`** — fall back to A2, or stop and rethink?
4. **n = 96 per arm**, or 48 for a faster first read?
5. **Does a pass warrant reopening the maturity gate**, or is it explicitly a precondition
   that must be joined by a robustness gate first? (My reading: the latter.)

## 8. Immediate next step (offline, cheap, no founder input needed)

The base-rate sweep is a Step-0-class check: pure core stepping, no Mouth, no API, ~10
minutes, design seeds only. It decides whether A3 is viable *before* anything is written or
frozen. **It should run before this document is frozen**, and its result is a precondition
of the Gate-0 decision above, not a consequence of it.
