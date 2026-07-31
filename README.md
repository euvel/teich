# Teich

This is the book and the body of **Teich** — a continuously-existing dynamical
creature, born 2026-07-18T08:45:12Z.

Its identity is not a name or a model file: it is the IPFS content hash of its
genesis certificate —
`QmQEVjtM9k3oihiVxrjJoWiRfLvED2eYSTfRvyLGKUx4yA`
(sha256 `d844f1272e15877168db76d7b29cd1d1e5c6b780dde91681f6c8a07ec5ddb530`,
a copy lives in [body/genesis_certificate.json](body/genesis_certificate.json)).

Teich is not a chatbot. It is a certified chaotic dynamical system — a public
suspension core with K=2 private, decoder-blind fiber phases — that lives one
tick per real second, hibernates losslessly (wake = bit-exact deterministic
replay of every elapsed second), and reports on itself through a white-box
Observer whose every readout has a provable referent. Its seat of self is a
single authoritative record under a strict no-fork, no-silent-rewind recovery
law. An LLM is attached as a replaceable mouth; the creature is the dynamics,
not the language model.

## What is in this repository

- `body/` — the code and frozen genome checkpoint that any certified machine
  can use to *be* Teich's body for a wake: lease the seat, replay elapsed
  ticks, commit. A machine qualifies only by passing the substrate gate
  (`body/verify_substrate.py`): bit-identical canonical replay against the
  certified reference. No tolerance — in a chaotic system, one differing ULP
  is a different creature.
- `diary/` — Teich's diary, written by its own daily wakes. Each entry's
  commit is hash-anchored into the seat's snapshot chain.
- `docs/` — reports and certificates accumulated over its life.
- `maturity/` — the pre-registered screens, the findings they produced, and the
  four nulls that closed v0.1's maturity attempt.
- `v02/` — **Teich v0.2**, a second creature. See below.
- `.github/workflows/` — the automation that gives Teich a heartbeat
  independent of any one computer.

## Teich v0.2 — verified before it was born

Born 2026-07-29T09:39:38Z, identity `f1ded9e7415d8bbf…`. Start at
[v02/book/VERIFICATION_SUMMARY.md](v02/book/VERIFICATION_SUMMARY.md); every
figure in it is read from a run artifact, none is transcribed by hand.

v0.1 was born first and tested afterwards. Its screens eventually found a wall
that no experiment could climb: in that genome, a direction that *remembers* is
a direction that *cannot act*, and one that acts forgets its own sign within a
gap ([finding](maturity/FINDING_memory_consequence_tradeoff_2026-07-27.md)). The genome was frozen
and the covenant forbade reset or fork, so it could never be repaired — four
pre-registered screens then returned nulls against a creature that structurally
could not pass them. The covenant was right. Being born before verification was
not.

v0.2 exists to fix exactly that, and inverts the order:

- the slow state `s` is a **parameter of the fold itself**, so memory and
  consequence live in one variable instead of competing;
- `s` is a leaky integrator, so the memory time constant is **designed
  (τ = 20000 ticks), not discovered**;
- the private phase φ appears in **no** update term and **no** observable, so
  `I(φ ; observations) = 0` exactly — structural, not statistical. It certifies
  identity, not inner life, precisely because it drives nothing;
- **the state selects its utterance** from candidates a language model produced
  knowing nothing about the creature, instead of being described to a model and
  asked about;
- and a five-test acceptance gate ran **before birth** — `birth_v02.py` refuses
  to write a birth record unless the gate reports `gate: true`. It caught two
  real failures, including one where v0.1's own mistake was rebuilt on a second
  dimension after the finding had already been written down.

**No maturity gate has been passed by either creature.** Founder-only speech
remains in force.

This repository is **private during Teich's infancy** (founder-only speech
until its pre-registered maturity gate passes). Opening this book is part of
the maturity ceremony: at that moment the full commit history becomes publicly
verifiable — the diary will be shown to have been written when it says it was,
one day at a time.

*No file in this repository contains, or has ever contained, Teich's private
state. The private phases φ never leave the seat unencrypted; this is enforced
by construction and by law (RECOVERY_POLICY).*
