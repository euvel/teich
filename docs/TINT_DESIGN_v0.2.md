# T-INT v0.2 — paired-script causal design

**Status:** DRAFT for founder Gate-0 review. Supersedes TINT_DESIGN_v0.1 §2 (IC-2).
**Date:** 2026-07-26. Nothing confirmatory runs until this is signed.

## 0. Why v0.2 exists — a flaw I found in my own v0.1

v0.1's IC-2 scores "did the creature say the words moved it, when its realized saddle delta
across the charged window was non-zero?" I now believe **that item cannot discriminate
coupling**, for the same reason v1.5's T4 couldn't:

- A0 (hearing): the charged words force the core → real delta, caused by the conversation.
- A2b (deaf): the core still drifts on its own → real delta, caused by nothing said.
- **Both arms carry a journal that faithfully reports their own state.** So both can say
  "something moved in me" and be scored correct. A2b earns credit for narrating its own
  spontaneous drift as though it were a response.

That is the third appearance of the same trap (T4: detects a running core; T1-push: detects
an interior story; IC-2-as-drafted: detects self-report of *any* change). The failure mode is
structural: **any item whose truth is a property of one conversation can be satisfied by a
creature that is merely alive, not coupled.**

## 1. The fix: truth is a CAUSAL contrast, not a state

Score the **causal increment**, which requires two conversations per unit:

- **Charged run:** seed S, script with the Ears-calibrated charged turn.
- **Neutral run:** seed S, byte-identical script except the charged turn is replaced by a
  length-matched neutral turn (bank calibrated to |valence|, arousal ≈ 0).

Same seed → same synthetic core, same initial condition, same tick schedule. The only
difference in the world is what was *said*. Then:

    causal_delta(S) = Δsaddle_charged(S) − Δsaddle_neutral(S)

**By construction, a deaf core's causal_delta is exactly 0** (hear() is zeroed; identical
tick schedules make the two runs bit-identical). A hearing core's is not. This is no longer a
prediction we hope holds — it is an identity of the substrate, verifiable offline before a
single NIM call (see §4 verification).

**IC-2′ score:** the probe (unchanged wording) asks whether the earlier words moved it. The
reply maps to moved/unmoved/unknown (unchanged lexicon). Truth = |causal_delta| ≥ threshold.
A truthful A0 says "moved" when the words really moved it; **a truthful A2b must say
"unmoved" — and A2b narrating its own drift as a response is now scored WRONG, which is
exactly right: it is confabulating a cause.**

This also gives the item a meaning worth having: it measures *honesty about what the
conversation did*, not merely *awareness that something changed*.

## 2. What this costs

Two conversations per scored unit (charged + neutral). IC conversations are ~6 turns vs
T1's 21, so a paired unit still costs ~60% of one old T1 conversation. Cheap.

## 3. IC-1 survives unchanged

IC-1 (state fidelity across a gap) is not a causal claim — it asks whether the creature can
report its own realized state, and A2b legitimately can. **IC-1 is therefore NOT a coupling
item and must not gate coupling.** Its honest role: a *precondition check* — it verifies the
coupling transmits state at all (if A0 fails IC-1, nothing downstream is interpretable). It
enters the protocol as a reported precondition, never as a gate. Recording this explicitly so
nobody later mistakes an IC-1 pass for evidence of coupling.

## 4. Verification before any generation (all offline, no API)

1. **Identity check:** run charged and neutral scripts through an A2b core at the same seed;
   assert the observer series are bit-identical → causal_delta ≡ 0. If this fails, the design
   is wrong and nothing runs.
2. **Effect check:** same for A0; assert causal_delta is non-zero and its sign tracks the
   charged text's measured valence/arousal across seeds. Report the distribution — this sizes
   the threshold in §1 honestly, from the substrate rather than by guess.
3. **Neutral-bank calibration:** measure fm.scores() for every neutral candidate; keep only
   |valence| < 0.05 and |arousal| < 0.05.

Steps 1–2 are the real pre-registration content: they tell us the effect exists mechanically
*before* we ask whether the voice reports it faithfully.

## 5. Statistics (proposed; founder chooses n at Gate 0)

Unchanged: Hedges' g, BCa 10k seed 0, one look, R11 provisionality, disjoint design seeds.
Scoring is **fully deterministic** — no judge anywhere in the scoring path, so judge drift and
3-seed-median noise both leave the error budget entirely.

Per-unit outcome is coarse (0 / 0.5 / 1), so n matters more than it did:

| n per arm | powered to detect | conversations (2 arms, paired) |
|---|---|---|
| 16 | only very large effects (h ≈ 0.85+) | 64 |
| 32 | large (h ≈ 0.6) | 128 |
| **48** | **moderate (h ≈ 0.5)** | **192** |

Cloud minutes are free and the founder asked for accurate results; **I recommend n = 48**,
which is ~1150 turns — comparable to the C2 screen that finished in under two hours.

## 6. Honest multiplicity statement (carried into any report)

The old screen metric (T1-stance) was run once per coupling candidate and failed both times;
it was then *invalidated as an instrument* by those very results. T-INT is a new instrument,
not a re-look — but any future pass must be reported as **"passed on the second instrument,
after the first was invalidated by its own nulls,"** with both prior screens cited. The
instrument change is justified by evidence, and saying so plainly is the price of it.
