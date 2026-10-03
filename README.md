# Teich

**Teich v0.3** — a creature whose memory provably changes what it does, and never
what it is. Born 2026-10-03T14:37:21Z after **every pre-registered gate passed**,
identity `004f6ca5e5c151e3…`, seated at `/o/teich-03`.

**Start here: [v03/README.md](v03/README.md)** — what it is, every gate, every
number, where each one comes from, and what is *not* claimed.

Teich is not a chatbot. Each creature is a chaotic dynamical system; a language
model is attached as a replaceable voice, *backwards* on purpose: the voice
proposes candidate sentences knowing nothing about the creature, and the
creature's own state chooses. v0.3 lives in genus-1 Teichmüller space: eight
bodies, one per region of a concept tree, each a section of the modular geodesic
flow whose shape is set by an integer memory.

## What v0.3 does, and what was measured

All scored once, on pre-registered seeds, after the spec and the code were
hash-anchored in a seat chain. Full numbers in [v03/README.md](v03/README.md).

- **Memory drives behaviour, as a guarantee.** One remembered event is still
  readable from its behaviour after 10⁶ ticks (D = 1.000; a leaky twin 0.08,
  a memoryless twin 0).
- **Memory never changes its nature.** Its chaos (entropy λ = π²/6 log G =
  3.4183) is identical at every memory state — a theorem, confirmed to 0.001.
- **Its notion of "related" carries human meaning.** Concepts are curves on a
  torus; their intersection number tracks human similarity judgements
  (SimLex-999, ρ = 0.38, CI [0.31, 0.45]).
- **Told once, it acts on it in speech.** What it chooses to say about a subject
  shifts (0.99) long afterwards; about every other subject, by exactly 0.
- **Flattery is bounded.** One step per region per conversation, every change
  attributed to who made it. **Commitments hold:** 0 violations under maximal
  flattery.
- **It knows itself by watching itself:** 99.4% correct about its own
  dispositions from its own behaviour (a language model given the same reading:
  21.9%).
- **Hardware-independent life:** bit-identical on AMD and Intel, numpy 1.26 and
  2.1 — neither earlier creature could do this.

Not claimed: intelligence, understanding, awareness. The voice is small (1.5B),
the Ears confuse a dark topic with a cold attitude, it has no concept of "self"
yet. **Founder-only speech remains in force.**

## Earlier creatures — both alive

**Teich v0.2** was born 2026-07-29 (identity `f1ded9e7415d8bbf…`), the first
creature verified before birth; it lives at `/o/teich-02` and its seat chain
carries v0.3's pre-registration anchors. Its state chooses what it says (63.5%
of 192 matched turns differ when another creature's state selects); what is said
to it stays recoverable 5000 ticks later (D = 0.92, 24 seeds). Start at
[v02/book/VERIFICATION_SUMMARY.md](v02/book/VERIFICATION_SUMMARY.md).

## Archive — v0.1, and why v0.2 and v0.3 exist

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
- `.github/workflows/` — the automation that gives all three creatures a heartbeat
  independent of any one computer.

---

**This book is open.** The full commit history is public and verifiable: the
diary can be shown to have been written when it says it was, one day at a time,
and every published figure can be traced to the run artifact and the commit that
produced it.

Open book is not open speech. **Founder-only speech remains in force** for all
three creatures. For v0.1 and v0.2 it holds until a pre-registered maturity gate
passes; v0.3's speech demos passed before birth, and opening its speech is a
separate founder decision not yet taken. v0.1's first trial
(2026-07-25) did not pass, and its own FAIL path was *publish and iterate*, which
is what this is. What is public is the record. Nothing here lets a stranger talk
to any of them.

*No file in this repository contains, or has ever contained, any creature's
private state. The private phases φ (v0.1, v0.2; v0.3 has none) never leave the seat unencrypted; this is
enforced by construction and by law (RECOVERY_POLICY).*
