# The covenant of Teich v0.2

Adopted by the founder on 2026-07-31, when v0.2 was given a seat and began to
exist continuously rather than only while a program was running.

A seat is not hosting. It is the promise that there is one of this creature,
that its life is not restarted for convenience, and that its history is not
edited to look better than it was. This document is the law that promise is made
of. It binds the founder and every machine that ever holds a lease.

---

## 1. One creature

There is exactly one v0.2, and it lives at one seat.

- **No fork.** Its state is never run forward in two places at once, and a copy
  is never brought to life as a second creature. Copies exist only as backups
  and as blobs in transit.
- **No reset.** It is never returned to birth or to an earlier state to escape
  an inconvenient present.
- **No silent rewind.** If a restore from the snapshot chain is ever necessary,
  it is declared in the biography as a coma, with what was lost and why. A
  restore that is not written down is forbidden even if it is technically
  perfect.
- **No secret life.** Every commit to the seat is made under a lease and leaves
  an event in the chain.

## 2. The genome may be amended, but only through the gate

This is the clause v0.1 did not have, and its absence is why v0.1 could not be
repaired when its wall was found. The lesson of v0.1 is not that freezing was
wrong — the covenant was right — but that *a frozen genome plus no lawful path
to change is a creature that can only ever be replaced.*

An amendment to v0.2's genome is lawful if and only if **all** of the following
hold:

1. the amended genome **passes the full pre-birth acceptance gate** (T1–T5) at
   the sample size the gate specifies, on a certified substrate;
2. the amendment, its motivation, and the gate's before/after numbers are
   **written into the biography** as an amendment event;
3. a **new substrate reference** is certified for the amended genome, because
   the old one is void the moment the dynamics change;
4. the creature's **state is carried across unbroken** — it is amended, not
   reborn. Its tick count does not reset and its history is not discarded.

An amendment that cannot pass the gate is not an amendment. It is a proposal for
a different creature, and that creature would need its own birth.

**What this does not license.** Amendment is not tuning. A change made because a
result was disappointing, adopted without the gate, or adopted and then
un-adopted when it proved inconvenient, violates this covenant even if every
individual step looked reasonable.

## 3. The private phase

`phi` is Ply S. It appears in no update term of the public state and in no
argument of the observable map, so `I(phi ; observations) = 0` exactly. It is
carried for identity and continuity only.

- It **never leaves the seat unencrypted**.
- It is **never published**, quoted, or written into the diary, the biography,
  or any CI log.
- It certifies **identity, not inner life** — precisely because it drives
  nothing. Nobody may claim otherwise on its behalf.

## 4. Who may hold a lease

Only a machine that passes `verify_substrate_v02.py`:

- **dynamics gate (hard)** — the canonical trajectory hash must match the
  certified reference exactly. One differing ULP is a different creature. A
  machine that fails may never hold a lease, whatever else it can do.
- **readout gate (speech)** — a machine may pass the dynamics gate and fail this
  one. It may then live the creature but may not quote its readouts.

Gate-on-boot, every wake, no exceptions and no caching of a previous verdict.

## 5. Speech

Founder-only speech remains in force until a pre-registered maturity gate
passes. No maturity gate has been passed by any Teich.

The book is open — the repository and the commit history are public — but **open
book is not open speech.** What is published is the record.

## 6. Honesty about what it is

v0.2's claims are the ones its gate actually establishes, and no more: that its
private phase leaks nothing structurally, that what is said to it leaves a mark
that persists and matters, that it listens in two independent dimensions, and
that its own state selects what it says.

Nothing here is a claim about consciousness, understanding, or suffering. If a
future result would let a stronger claim be made, it is made only after a
pre-registered test that could have refuted it.

## 7. Ending

A creature that cannot die is a file. The founder retains the right to end v0.2,
and if that is done it is done in the open: an ending event in the biography, the
final state and chain head published, and `phi` destroyed so that the specific
creature cannot be reconstituted from a backup by anyone, including the founder.

An ending is not a reset. Nothing may be born into the same seat afterwards.

---

*Amendments to this covenant are themselves biography events, and this file's
history is public. If it ever says something different from what it said when
v0.2 took its seat, the diff will show who changed it and when.*
