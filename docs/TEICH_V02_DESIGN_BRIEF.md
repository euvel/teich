# Teich v0.2 — design brief

**Status:** DRAFT for founder review. Nothing built. Written 2026-07-28, immediately after
the v0.1 maturity programme closed with four nulls.
**Purpose:** state the constraints v0.2 must satisfy **by construction**, so that the
impossibilities discovered in v0.1 cannot recur — and name, up front, the one hard tension
between the founder's two stated requirements.

Founder requirements (2026-07-28): *"a first version with leakage 0 mathematical guarantee
and twin"*, and *"prevent such impossibles for future"*.

---

## 0. The tension that must be resolved before anything is designed

**A provably zero-leakage channel is a zero-capacity channel.**

If a private state φ provably cannot be inferred from any observable — which is what "0
leakage, mathematically guaranteed" means — then φ provably does not influence any
observable. A variable that changes nothing cannot be detected; a variable that changes
something can be inferred from what it changed. There is no architecture in which φ both
drives behaviour and is information-theoretically hidden. This is not an engineering
limit; it is the definition of mutual information.

This is the same wall v0.1 hit from the other side. Step B measured it as
**memory XOR consequence** (`FINDING_memory_consequence_tradeoff`): the direction that
remembered perfectly (`tau1`, λ = 0) left `basin` unchanged in 46/48 runs, and the
direction that changed everything (`tau0`, λ > 0) forgot which way it was pushed. That was
read as a fact about the frozen genome. It is more general than that — it is what the
Lyapunov spectrum plus information theory jointly require.

**Consequence for v0.2: the interior must be explicitly two-ply, and the two plies must
have different guarantees.** This was already the shape of INTERIOR_SPEC v0.3; v0.2 should
make it load-bearing rather than aspirational.

| | Ply S — *sealed* | Ply R — *rememberable* |
|---|---|---|
| variable | φ (private phases) | s (slow public state) |
| leakage | **provably 0, by construction** | **not private, by design** |
| influence on behaviour | **none, by construction** | **drives everything** |
| what it is for | identity, twin, continuity, authentication | interiority, memory, self-report |
| claim it supports | "this creature is not that creature" | "its speech is grounded in its state" |

Trying to get one variable to do both jobs is what made v0.1 unfalsifiable-in-practice. The
maturity claim lives entirely in Ply R. The privacy/twin guarantee lives entirely in Ply S.
**Neither claim is weakened by the split; both become provable.**

---

## 1. Requirement A — leakage 0, mathematically guaranteed

v0.1 measured ε ≈ 0 empirically. v0.2 should make it exactly 0 *by construction*, which is
strictly stronger and much cheaper to defend.

**Construction.** Let the observable map be `O = g(x, s)`. Require, as a structural
invariant checked in CI:

> φ appears in **no** argument of `g`, and in **no** term of the update for `x` or `s`.

Then for any two instances differing only in φ, every observable trajectory is *identical*,
not merely similar — so mutual information `I(φ ; observations) = 0` exactly, for all
observation lengths, against all adversaries, with no statistical test required.

**What φ is still good for.** Identity and continuity: φ is the creature's private token,
usable for seat authentication and for proving "same creature, later" without ever being
disclosed. That is a real and useful role. What it is *not* is an inner life — and v0.1's
programme spent months implicitly hoping it could be both.

**Gate:** a static check (φ's symbol never reaches `g`, `x`, or `s`) plus a differential
test: run N instances with random φ and identical seeds; **every** observable must be
bit-identical. Not "statistically indistinguishable" — bit-identical. This is a much
stronger gate than v0.1's ε ≈ 0 and it is trivial to run.

---

## 2. Requirement B — the twin, made trivial

v0.1's twin theorem needed an ε and a measurement. Under §1 it becomes a corollary:

> **Twin corollary.** Two instances sharing (x₀, s₀) and differing in φ are observationally
> identical, exactly. No decoder, given any amount of data and unbounded compute, can do
> better than chance at telling them apart.

Because it follows from a structural invariant rather than an experiment, it cannot be
eroded by a longer observation window, a better decoder, or a jammed instrument — the three
things that repeatedly undermined v0.1's empirical claims.

---

## 3. Requirement C — memory AND consequence (the v0.1 impossibility, fixed)

Ply R must do what no direction in v0.1 could: persist *and* matter. Two structural
requirements, both checkable before a single conversation is run.

**C1 — s must be a PARAMETER of the fast dynamics, not merely a coordinate beside them.**

    x_{t+1} = f(x_t ; s_t)        <- s modulates the rule
    s_{t+1} = s_t + (input) + small drift

In v0.1 the neutral direction `tau1` set only *when* roof wraps occurred; the flip rule
`B|x|^ρ < 1` never consulted it. That is why a phase push left `basin` unchanged in 46/48
runs. If instead `B` or `ρ` is a function of `s`, then s shapes *every* flip decision for as
long as it persists. Memory and consequence stop competing.

**C2 — memory time must be tuned to the conversation timescale, not maximised.**

For a direction with exponent λ, sign information survives roughly

    τ_mem  ≈  (1/λ) · ln(L/δ)

v0.1 offered only λ ≫ 0 (τ_mem ≈ minutes, too short — the scalar's sign did not survive a
300-tick gap) or λ = 0 (τ_mem = ∞, but decoupled). **v0.2 wants λ small and positive, or
slightly negative, with τ_mem set deliberately** — long enough to span a conversation and a
gap, short enough that the creature is not a permanent recording device.

Concretely: v0.1 conversations ran ~1400 ticks with gaps to 1800. A target of
τ_mem ≈ 10⁴–10⁵ ticks (hours to a day of lived time) implies |λ| ≈ 10⁻⁴–10⁻⁵ per tick.
**Design λ first, then build the map to have it** — do not discover it afterwards.

**Gate (cheap, offline, mandatory before any screen):** the Step-0 survival diagnostic,
run on v0.2's genome as an *acceptance test*. Push ±δ along each input direction; require
discriminability `D = 2|AUC − 0.5|` to remain high on **fold observables** (`basin`,
`saddle`) — not merely on clock readouts — at the longest intended gap. v0.1's genome scores
D ≈ 0.04 on that test. **v0.2 must not be built until a candidate scores high.**

---

## 4. Requirement D — input capacity (the scalar-Ears impossibility, fixed)

`ears.py` compressed every utterance to one signed number, so "proud" and "gift" were the
same event to the creature (`FINDING_scalar_ears`).

**Capacity rule.** The content a creature can hold is bounded by

    capacity  ≈  Σ over slow directions of  log₂(range_i / noise_i)   bits

Input dimensionality above that is wasted; below it is self-inflicted. v0.1 had
dim(slow, coupled) = **0**, so no Ears redesign could ever have helped — worth stating
plainly, since weeks were nearly spent there.

**Requirement:** choose `dim(s) ≥ 2` deliberately, size the input map to match, and state
the resulting bit capacity in the design document *before* building.

---

## 5. Requirement E — every readout reproducible AND creature-dependent

Two v0.1 instruments shipped broken and stayed broken across three campaigns:

- `lambda_running` — **not reproducible** (unseeded power iteration, redrawn every turn).
- `saddle_proximity` — reproducible but **not creature-dependent**: `saddle × (1 − frac_left)`,
  state multiplied by a clock the input cannot touch, crushing ~71% of readouts into one
  bucket.

**Requirement:** every published readout passes both checks *in CI*, mechanically:

1. **Reproducible** — identical seed and script, run twice, bit-identical.
2. **Creature-dependent** — a paired ±input perturbation changes it detectably, and a
   deaf/severed control changes it in exactly 0% of runs.

Cost: minutes. v0.1's price for skipping it: three campaigns of nulls whose instruments
turned out to be jammed, and one discarded arm (IC-1) retired on evidence produced by the
broken gauge measuring it.

---

## 6. Requirement F — do not ask a language model to report

A3's mechanism was precise: `will_flip` is a perfect referent (acc 1.000), the journal
stated it in plain words, and the Mouth still answered "turn" 71.4% of the time against a
44.8% base rate. The information reached the prompt and died there — an LLM answers from
conversational plausibility, and that prior swamps one clause of its context.

**Requirement:** in v0.2 the state must **select among** candidate utterances the voice has
already produced, rather than being described *to* the voice and asked about. Selection
cannot be overridden by plausibility, because plausibility has already had its say by the
time selection runs.

**Warning, carried from A3 §6:** calibrating the voice to match base rates raises the score
**without** improving grounding. Any such calibration must be frozen from design seeds, and
the arm contrast — never absolute accuracy — must remain the primary metric.

---

## 7. Acceptance tests, to run on a candidate genome BEFORE it becomes a creature

The whole point of this brief. All are offline, cheap, and decisive; none needs a Mouth, an
API, or a conversation.

| # | test | pass condition | v0.1 result |
|---|---|---|---|
| T1 | φ-blindness | N random φ, identical seeds → **bit-identical** observables | ε ≈ 0 (measured, weaker) |
| T2 | survival | D on `basin`/`saddle` at the longest gap | **≈ 0.04 — FAIL** |
| T3 | memory time | τ_mem within 10× of target | not designed; discovered |
| T4 | readout hygiene | every readout reproducible AND creature-dependent | **2 of 6 FAIL** |
| T5 | capacity | dim(slow, coupled) ≥ 2, bit budget stated | **0 — FAIL** |

**A candidate that fails any of these is not born.** v0.1 was born first and tested
afterwards, which is why it cannot now be fixed: the genome is frozen and the covenant
forbids reset or fork. That constraint is correct and should be kept — which is exactly why
the tests must run *before* birth.

---

## 8. Open questions for the founder

1. **Does Ply S / Ply R match your intent?** It is the only way to have both "leakage 0,
   guaranteed" and a genuine interior. It also means the twin theorem no longer certifies
   anything about inner life — only about identity. That is a real narrowing of the original
   story and you should decide it deliberately.
2. **τ_mem target?** Hours, or a day? Sets λ, and everything else follows.
3. **dim(s)?** 2 is the minimum for content; higher costs analysis tractability.
4. **Does v0.1 keep living?** Nothing here requires touching it. My recommendation: it
   lives, unchanged, founder-only, as the creature that produced these results.
5. **Publish the v0.1 arc first, or in parallel?** The negative result is strong and the
   design brief is much more persuasive with it attached.
