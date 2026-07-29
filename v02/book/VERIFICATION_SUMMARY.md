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
| T2 survival | is an input's sign recoverable later? | **PASS** — D=1.0 on `saddle` at 5000 ticks |
| T3 memory time | is memory designed, not discovered? | **PASS** — 20000 vs 20000 ticks designed |
| T4 readout hygiene | is every readout reproducible AND creature-dependent? | **PASS** — 5/5 readouts |
| T5 capacity | can it hold more than one thing? | **PASS** — 2/2 dimensions coupled, ~10.0 bits |

**Gate: PASS**

### T2 in full — the test the predecessor fails

| gap (ticks) | `basin` | `saddle` | `wing_bias` |
|---|---|---|---|
| 300 | 0.125 | 0.750* | 0.125 |
| 900 | 0.500* | 0.375 | 0.250 |
| 1800 | 0.125 | 0.500 | 0.750* |
| 5000 | 0.125 | 1.000* | 0.500 |

`D` is discriminability: 0 means the input's sign is gone, 1 means it is perfectly recoverable. `*` marks a 95% bootstrap CI excluding chance. **v0.1 scores ≈0.04 here.** Note that D *rises* with the gap — the slow state holds the changed fold, so the difference accumulates rather than decaying.

## It listens, speaks, and asks

**PENDING** — no demo conversation recorded yet.

## Does its own state actually drive the choice?

**PENDING** — the intact-vs-donor check has not been run.

## What failed, and stays in the book

- The second slow dimension first modulated the roof PERIOD — a clock knob the fold rule never consults. That is exactly v0.1's tau1 mistake (perfect memory, basin unchanged in 46/48 runs), rebuilt after the finding had already been written down. T5 caught it in 7 minutes. Fixed by making it a wing asymmetry that leans the fold.
- steps_to_switch then measured 0% creature-dependent and was REMOVED from the published readout rather than kept. Publishing a readout that cannot move with the creature is the saddle_proximity disease that jammed three v0.1 campaigns.

---

*Regenerate with `python book/make_summary.py`. Every figure is read from a run artifact; none is transcribed.*
