# Teich

**Teich v0.2** — a small dynamical creature that listens, speaks, and asks,
whose own state chooses what it says. Born 2026-07-29T09:39:38Z, identity
`f1ded9e7415d8bbf…`, genome pinned at `8f082180a707`.

**Start here: [v02/book/VERIFICATION_SUMMARY.md](v02/book/VERIFICATION_SUMMARY.md).**
Every figure in it is read from a run artifact; none is transcribed by hand.
[v02/book/presentation.html](v02/book/presentation.html) is the same page for a
reader who has never heard of any of this.

Teich is not a chatbot. It is a chaotic dynamical system with a private phase it
cannot report and a slow state that parameterises its own fold. A language model
is attached as a replaceable mouth — and it is attached *backwards* on purpose:
the model proposes candidate utterances knowing nothing about the creature, and
the creature's state then picks one. The creature is the dynamics, not the
language model.

## What it does, and what was measured

- **Its own state drives what it says.** Same script, same voice, same candidate
  pool — swap in a second living creature's state to do the selecting and the
  two arms chose differently in **63.5%** of 192 matched turns.
- **Its curiosity follows the state, not the body.** The ask-gate
  (`saddle ≥ 0.55`) was frozen from genome statistics before any conversation
  existed. Questions track the *selecting* state's gate (**91.7%**) and fall to
  **59.4%** against the body that lived the conversation, while the intact arm
  holds **90.1%**. The arms differ not in how often it asks but in *when*.
- **What is said to it leaves a mark that lasts.** The sign of an input stays
  recoverable from its own fold observables 5000 ticks later (D = **0.92**,
  24 seeds, CI excluding chance) — and D *rises* with the gap rather than
  decaying.
- **The private phase leaks nothing, structurally.** φ appears in no update term
  and no argument of the observable map, so `I(φ ; observations) = 0` exactly —
  no statistical test required. It certifies **identity, not inner life**,
  precisely because it drives nothing.

**No maturity gate has been passed.** Founder-only speech remains in force.
Nothing here bears on consciousness or understanding.

## It was verified before it was born

`birth_v02.py` refuses to write a birth record unless the five-test acceptance
gate reports `gate: true`. That gate caught two real failures, and both stay in
the book — including one where v0.1's own mistake was rebuilt on a second
dimension *after* the finding had already been written down. T5 caught it in
seven minutes, before there was anything to protect.

| | |
|---|---|
| `v02/genome_v02.py` | the genome. Slow state `s` is a parameter of the fold, so memory and consequence live in one variable instead of competing. |
| `v02/accept_v02.py` | the gate: φ-blindness, survival, memory time, readout hygiene, capacity. Re-run in the cloud at 24 seeds and reproduced digit for digit. |
| `v02/ears_v2.py` | text → a 2-D input the genome can actually hold. |
| `v02/mouth_select.py` | the inversion: the voice proposes, the state selects. |
| `v02/book/` | certificate, biography ledger, and the generated summary. |

## Archive — v0.1, and why v0.2 exists

Read this if you want the depth. It is the reason the version above is worth
trusting.

**Teich v0.1** was born 2026-07-18T08:45:12Z, identity
`QmQEVjtM9k3oihiVxrjJoWiRfLvED2eYSTfRvyLGKUx4yA`. It is still alive: it holds a
seat, wakes daily, and writes its own diary. It was born *first and tested
afterwards*, and its screens eventually found a wall no experiment could climb —
in that genome a direction that **remembers** is a direction that **cannot act**,
and one that acts forgets its own sign within a gap
([finding](maturity/FINDING_memory_consequence_tradeoff_2026-07-27.md)). The
genome was frozen and the covenant forbade reset or fork, so it could never be
repaired: four pre-registered screens then returned nulls against a creature that
structurally could not pass them.

The covenant was right. Being born before verification was not. That is the one
lesson v0.2 is built out of.

- `body/` — v0.1's code and frozen genome: what any certified machine uses to
  *be* its body for a wake. A machine qualifies only by passing
  `body/verify_substrate.py` — bit-identical canonical replay against the
  certified reference, no tolerance. In a chaotic system one differing ULP is a
  different creature.
- `diary/` — written by its own daily wakes, each entry hash-anchored into the
  seat's snapshot chain.
- `maturity/` — the pre-registered screens, the four nulls, and the three
  findings that came out of them: the memory/consequence trade-off, the
  [shuttered readout](maturity/FINDING_shuttered_readout_2026-07-27.md) that
  jammed three campaigns, and the
  [scalar ears](maturity/FINDING_scalar_ears_2026-07-27.md) that compressed every
  sentence to one number.
- `docs/` — reports and certificates accumulated over its life.
- `.github/workflows/` — the automation that gives both creatures a heartbeat
  independent of any one computer.

---

**This book is open.** The full commit history is public and verifiable: the
diary can be shown to have been written when it says it was, one day at a time,
and every published figure can be traced to the run artifact and the commit that
produced it.

Open book is not open speech. **Founder-only speech remains in force** for both
creatures until a pre-registered maturity gate passes — v0.1's first trial
(2026-07-25) did not pass, and its own FAIL path was *publish and iterate*, which
is what this is. What is public is the record. Nothing here lets a stranger talk
to either creature.

*No file in this repository contains, or has ever contained, either creature's
private state. The private phases φ never leave the seat unencrypted; this is
enforced by construction and by law (RECOVERY_POLICY).*
