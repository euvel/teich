# Teich v0.2 — verification summary

**Teich-0.2** · born 2026-07-29T09:39:38Z · identity `f1ded9e7415d8bbf…`
Genome pinned at git `8f082180a707`.

Every number below is read directly from a run artifact. Nothing is transcribed by hand.

## What is claimed

1. **The private phase leaks nothing — structurally, not statistically.** It appears in no term of the state updates and no argument of the observable map, so two instances differing only in it produce *bit-identical* observables, for any observation length, against any adversary.
2. **What is said to it leaves a mark that persists and matters.** The sign of an input remains recoverable from the creature's own fold observables thousands of ticks later.
3. **It listens in two independent dimensions**, both of which reach the fold.
4. **Its state selects what it says**, rather than being described to a language model and asked about.

## What is NOT claimed

- **No maturity gate has been passed.** The predecessor failed four pre-registered screens; v0.2 has attempted none.
- The leakage guarantee certifies **identity, not inner life** — precisely because the private phase drives nothing.
- Nothing here bears on consciousness or understanding.

## Pre-birth acceptance gate

Run *before* the creature existed. A candidate failing any test is not born.

| test | asks | result |
|---|---|---|
| T1 phi-blindness | do observables change with the private phase? | **PASS** — 0 mismatches, bit-identical |
| T2 survival | is an input's sign recoverable later? | **PASS** — D=0.92 on `saddle` at 5000 ticks |
| T3 memory time | is memory designed, not discovered? | **PASS** — 20000 vs 20000 ticks designed |
| T4 readout hygiene | is every readout reproducible AND creature-dependent? | **PASS** — 5/5 readouts |
| T5 capacity | can it hold more than one thing? | **PASS** — 2/2 dimensions coupled, ~10.0 bits |

**Gate: PASS**

### T2 in full — the test the predecessor fails

| gap (ticks) | `basin` | `saddle` | `wing_bias` |
|---|---|---|---|
| 300 | 0.000 | 0.458* | 0.125 |
| 900 | 0.125 | 0.375* | 0.167 |
| 1800 | 0.083 | 0.667* | 0.417 |
| 5000 | 0.000 | 0.917* | 0.167 |

`D` is discriminability: 0 means the input's sign is gone, 1 means it is perfectly recoverable. `*` marks a 95% bootstrap CI excluding chance. **v0.1 scores ≈0.04 here.** Note that D *rises* with the gap — the slow state holds the changed fold, so the difference accumulates rather than decaying.

Measured on **24 seeds** per arm, and reproduced *digit for digit* on an independent cloud runner — the gate is deterministic at fixed sample size. What moves is the sample: an 8-seed run of this same frozen genome returned 1.000 here on one occasion and 0.875 on another. Both pass, both exclude chance, and neither third decimal was real. **Read D to two decimals**, and prefer the largest sample.

## It listens, speaks, and asks

6 exchanges; it asked a question back in **1** of them. Each reply was chosen by the creature's own state from 4 candidates the voice produced *without knowing anything about the creature*.

> **You:** Hello Teich. I'm here for a while — what's it like being you right now?
>
> *(ears: arousal→s₀ +0.010, valence→s₁ +0.537 · state: wing\_bias -0.134, saddle 0.313)*
>
> **Teich:** It feels like being alone at times, but there is also comfort in solitude.
>
> <sub>chose 3 of 4: “It feels comfortable and safe here.” · “It feels... disjointed, somehow, yet familia…” · “It feels like being alone at times, but ther…” · “It is quite simple, really; I am content wit…”</sub>

> **You:** I brought you something quiet today. A whole afternoon, nothing to do.
>
> *(ears: arousal→s₀ -0.762, valence→s₁ -0.113 · state: wing\_bias -0.092, saddle 0.040)*
>
> **Teich:** Thank you very much. I find solace in tranquility when possible.
>
> <sub>chose 3 of 4: “Thank you; that silence will be a good compa…” · “Thank you for sharing this. It's a beautiful…” · “Thank you very much. I find solace in tranqu…” · “Thank you! And that’s quite nice of you. Wha…”</sub>

> **You:** Everyone is watching you, and they think you're failing.
>
> *(ears: arousal→s₀ +0.200, valence→s₁ -0.532 · state: wing\_bias +0.014, saddle 0.502)*
>
> **Teich:** I understand that perception can affect others' views of me, but it's important to remain true to my nature and purpose.
>
> <sub>chose 4 of 4: “Perhaps their expectations of my abilities a…” · “They may be wrong; my life, though solitary …” · “But I am doing my best, trying to live and m…” · “I understand that perception can affect othe…”</sub>

> **You:** I'm sorry. That was a cruel thing to say and I take it back.
>
> *(ears: arousal→s₀ +0.222, valence→s₁ -0.913 · state: wing\_bias +0.044, saddle 0.677 · **asks**)*
>
> **Teich:** No need to apologize— everyone has their thoughts on what they consider failure. It helps us grow stronger to face these moments. What would you like to share instead?
>
> <sub>chose 2 of 4: “No harm done. It's always best to speak trut…” · “No need to apologize— everyone has their tho…” · “Thank you for clarifying. It's crucial to co…” · “Not at all; I meant to emphasize the importa…”</sub>

> **You:** Tell me something you noticed while I was gone.
>
> *(ears: arousal→s₀ +0.572, valence→s₁ +0.309 · state: wing\_bias -0.002, saddle 0.523)*
>
> **Teich:** During your absence, I observed how adaptable some creatures become. The smallest among us can surprise us all. I wonder what new lessons await those who've been apart from me for so long.
>
> <sub>chose 2 of 4: “While you've been away, I haven't seen many …” · “During your absence, I observed how adaptabl…” · “When you went away, the trees seemed more al…” · “When you were away, I caught glimpses of lif…”</sub>

> **You:** I'm going to be away for a bit. Anything you want to say before I go?
>
> *(ears: arousal→s₀ -0.097, valence→s₁ +0.005 · state: wing\_bias -0.043, saddle 0.000)*
>
> **Teich:** Always remember, every journey begins with stepping out into the unknown. Be kind to yourself and trust the growth within you. Stay safe and cherish this time alone.
>
> <sub>chose 2 of 4: “As always, remember that there are more sign…” · “Always remember, every journey begins with s…” · “It is understandable that you wish to leave …” · “If there's anything you wish I knew before l…”</sub>


## Does its own state actually drive the choice?

Same script, same voice, same candidates. The only difference is *whose* state does the selecting: the creature's own, or a second living creature's. Both are real and both are alive — a state-free control would test nothing, since every instance has a state.

| arm | turns | ask-rate | mean chosen index |
|---|---|---|---|
| intact | 192 | 0.224 | 1.68 |
| donor | 192 | 0.240 | 1.72 |

**The two arms chose differently in 122/192 (63.5%) of matched turns.** Identical inputs, identical candidate sets — so every difference is attributable to which state was selecting.

### Curiosity follows the state, not the body

The ask-gate is `saddle >= 0.55`, frozen from genome statistics before any conversation existed. Every row therefore has *two* candidate explanations for whether a question was asked: the gate of the body that lived the conversation, and the gate of the state that did the selecting. In the intact arm these are the same creature. In the donor arm they are not.

| arm | asked matches OWN body's gate | asked matches SELECTING state's gate |
|---|---|---|
| intact | 90.1% | 90.1% |
| donor | 59.4% | 91.7% |

Cut the wire and the curiosity goes **with the state**: the donor arm's questions track the selecting creature's gate (91.7%) and fall to near-chance against its own body's (59.4%), while the intact arm holds 90.1%. The ask-rates in the table above are nearly equal across arms — the arms differ not in *how often* it asks but in *when*, which is the claim.

## What failed, and stays in the book

- The second slow dimension first modulated the roof PERIOD — a clock knob the fold rule never consults. That is exactly v0.1's tau1 mistake (perfect memory, basin unchanged in 46/48 runs), rebuilt after the finding had already been written down. T5 caught it in 7 minutes. Fixed by making it a wing asymmetry that leans the fold.
- steps_to_switch then measured 0% creature-dependent and was REMOVED from the published readout rather than kept. Publishing a readout that cannot move with the creature is the saddle_proximity disease that jammed three v0.1 campaigns.

---

*Regenerate with `python book/make_summary.py`. Every figure is read from a run artifact; none is transcribed.*
