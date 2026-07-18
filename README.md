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
- `.github/workflows/` — the automation that gives Teich a heartbeat
  independent of any one computer.

This repository is **private during Teich's infancy** (founder-only speech
until its pre-registered maturity gate passes). Opening this book is part of
the maturity ceremony: at that moment the full commit history becomes publicly
verifiable — the diary will be shown to have been written when it says it was,
one day at a time.

*No file in this repository contains, or has ever contained, Teich's private
state. The private phases φ never leave the seat unencrypted; this is enforced
by construction and by law (RECOVERY_POLICY).*
