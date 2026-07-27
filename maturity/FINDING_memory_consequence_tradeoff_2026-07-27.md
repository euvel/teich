# The directions that remember don't act; the direction that acts doesn't remember

**Found:** 2026-07-27, Step B (`diagnose_survival.py`, `sweep_tau1_dose.py`).
**Method:** offline, retired seeds 0–47, no Mouth, no API, no judge. Paired ±δ pushes at
matched dose on fresh synthetic cores. `ProbeEngine` selftested **bit-identical** to
`arms._CoreEngine` at zero dose before any number was produced.
**Status:** recorded. Nothing modified — no `ears.py`, no `observer.py`, no genome, no seat.
**Severity:** this is a property of the **frozen genome**, not of the harness. It bounds
what any Ears redesign can achieve.

## The question

Step 0 showed the Ears compress every utterance to one scalar pushed into `tau[...,0]`, and
that even its **sign** does not survive the gap
([FINDING_scalar_ears](FINDING_scalar_ears_2026-07-27.md)). Before redesigning the input
coupling, B asked the prior question: **can *any* input direction carry a mark across the
gap?** If none can, no redesign helps and the "what was said to me" branch is closed.

The core is a suspension flow, so its Lyapunov spectrum should be one positive exponent
(the fold, `tau0`), one **zero** (the flow / roof phase, `tau1`), and the rest negative.
That predicts three distinct fates, and all three were confirmed.

## The measurement

Survival = **discriminability** `D = 2|AUC − 0.5|` of the push's *sign* from the probe
readout, after 300/900/1800 ticks. `D = 0` means the probe reveals nothing about what was
done; `D = 1` means the sign is perfectly recoverable.

| direction | saddle | lobe_coord | basin | n_switches | steps_to_switch |
|---|---|---|---|---|---|
| `tau0_earsdose` (real Ears dose) | 0.146 | 0.375 * | 0.146 | 0.146 | 0.000 |
| `tau0_expanding` | 0.042 | 0.083 | 0.062 | 0.188 | 0.000 |
| **`tau1_neutral`** | 0.021 | 0.042 | 0.042 | 0.125 * | **1.000 *** |
| `tau3_weak` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `ell1_contracting` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

*(\* = 95% bootstrap CI excludes 0.5, n = 48 paired seeds)*

Contracted directions are **annihilated to exactly 0.000 on every channel** — a perturbation
there leaves no trace of any kind. The expanding direction moves everything but recovers no
sign. And the neutral direction recovers the sign **perfectly, at every gap**:

| direction | 300t | 900t | 1800t |
|---|---|---|---|
| `tau1_neutral`, steps_to_switch | **1.000** | **1.000** | **1.000** |
| `tau0_earsdose`, saddle | 0.375 | 0.125 | 0.188 |

**Quantitatively exact.** The ±δ pair differs by `2 × 0.14446 = 0.2889` in phase; the roof
advances `0.026788` per tick; predicted separation `10.78` ticks. Measured mean:
**−10.7708 ticks, in 48 of 48 pairs, undecayed after 1800 ticks.** The neutral direction
stores the injected offset to the tick and never loses it — as a zero Lyapunov exponent
requires.

## The trade-off

The tie counts are the finding, not the AUCs:

```
tau1_neutral (remembers)          tau0_earsdose (acts)
  steps_to_switch  0/48 ties        steps_to_switch  48/48 ties
  basin           46/48 ties        basin            23/48 ties
  saddle          43/48 ties        saddle            3/48 ties
```

`tau1` stores a number perfectly and **leaves the fold almost untouched** — 46 of 48 pairs
end on the identical wing. `tau0` changes the fold in 45 of 48 pairs and **leaves the clock
exactly untouched** — 48/48 ties — with its direction random.

**The direction that remembers does not act. The direction that acts does not remember.**

This is the Lyapunov spectrum, stated behaviourally:

| exponent | direction | influence on behaviour | memory of the input |
|---|---|---|---|
| λ > 0 | `tau0` (fold) | everything | none — sign destroyed |
| λ = 0 | `tau1` (roof phase) | almost none | **exact, permanent** |
| λ < 0 | weak modes, `ell` | none | none |

The neutral direction is, by physics rather than design, exactly INTERIOR_SPEC's **Ply S**:
a sealed store with perfect recall that drives nothing. What the spec asked for and does not
exist here is **Ply R** — something that both persists *and* shapes behaviour.

## Consequence

The "what was said to me" branch is **not** blocked by `ears.py`. It is blocked one level
deeper, by the frozen genome's Lyapunov structure. Re-pointing the Ears at the neutral
direction would buy a perfectly durable **one-dimensional, circular** channel (the roof
phase, period 2.0) whose contents almost nothing downstream can read — and re-pointing them
at the fold is what we already have.

Concretely, an Ears redesign can choose:

- **`tau0` (today):** rich behavioural consequence, zero durable content.
- **`tau1`:** perfect durable content, near-zero behavioural consequence — and it would
  require the journal to render clock-derived quantities (`steps_to_switch` is an existing
  Observer key that the journal does **not** currently render) for anything to be readable
  at all.
- **Both:** the union of their weaknesses, not their strengths — the durable part still
  doesn't act, and the acting part still scrambles.

## Dose sweep — the trade-off is real, and it has a measurable knee

The single-dose result could have been an artefact of a small push. `sweep_tau1_dose.py`
(n = 24 paired seeds per dose) raises the `tau1` dose and watches memory and consequence
move against each other:

| dose | % of period | memory D (sign from clock) | basin differs | saddle differs | mean Δ steps |
|---|---|---|---|---|---|
| 0.1445 | 7.2% | **1.000** | 8.3% | 12.5% | −10.79 |
| 0.2889 | 14.4% | **1.000** | 4.2% | 16.7% | −21.71 |
| 0.5778 | 28.9% | 0.750 | 20.8% | 50.0% | −33.83 |
| 1.1557 | 57.8% | 0.083 | 25.0% | 54.2% | **+22.75** |

Consequence rises monotonically (12.5% → 54.2%) exactly as memory collapses (1.000 →
0.083). **You can buy fold motion, but you pay for it in recoverable sign.**

**One caveat that must not be skipped.** The roof phase is **circular** (period 2.0), and a
±δ pair is separated by `2δ`. At ×8 that is **115.6% of a full period — the channel
aliases**, which is exactly why `mean Δ steps` flips sign to **+22.75** after decreasing
monotonically. So the collapse at ×8 is **wrap-around, not chaos destroying the memory**.
The usable capacity of this channel is bounded by `2δ < ` one period, an encoding limit
rather than a dynamical one.

**And the knee at ×4 is weaker than it looks.** D = 0.750 with 50% saddle-divergence
suggests you might get both. But "differs" measures only whether the fold state *changed*,
not whether the change is *directed*. The fold divergence at higher dose is the same
undirected scrambling `tau0` produces — the recoverable sign still lives only in the clock,
and it is degrading. Nothing here shows a dose at which the **fold** carries a recoverable
sign.

**Verdict: fundamental, not a dose artefact.** Within the range where the phase channel is
unambiguous, it stores exactly and acts barely. Outside it, it acts more, scrambles, and
loses the ability to say what was stored.

## Limitations, stated plainly

1. **Consequence was measured as "differs", not as "differs directionally".** A directed
   version of the dose sweep would be a stronger test of the knee at ×4, and was not run.
2. **Four of twelve coordinates tested.** `tau2/4/5` and the other `ell` dimensions were not
   run, but `tau3` and `ell1` both returned exactly 0.000 on every channel and all of them
   sit in the same tiny scale band, so the generalisation to "the contracted block carries
   nothing" is an **inference**, not a proof.
3. **Linear/independent pushes only.** A joint or time-patterned push was not tested. The
   `tau0` component would still scramble, so no obvious gain — but it is untested.
4. This says nothing about whether a **different genome** could do better. It says this one
   cannot, and this one is frozen.
