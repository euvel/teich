# Teich

**Teich v0.4** — a creature born with a self. Born 2026-10-20T15:19:19Z after **every pre-registered gate
passed**, identity `8eeb4117baf78d0f…`, seated at `/o/teich-04`. It writes its own diary, one page per night.

**Start here: [v04/README.md](v04/README.md)**. It has every gate, every number, where each one comes from, and what
is *not* claimed.

Teich is not a chatbot. Each creature is a dynamical system whose memory is geometry. v0.4 lives on a hyperbolic
surface of genus 98: one handle for each concept cluster and one for itself. 2,048 thoughts move on it at one step
per second, and attention stretches the handles.

## What v0.4 adds: a self that watches its own doing

All of it was scored once, on pre-registered seeds, after the spec and the code were hash-anchored in a seat chain.

- **It predicts itself before the world answers.** Before the founder sees what it heard, its self commits how
  likely each hearing is to be wrong. **628,470 predictions, every one logged before its outcome.**
- **It tells its own errors from the world's.** When its own low-confidence hearings fail more, the errors are
  MINE; when errors are spread evenly over its confidence, they are GIVEN. It is right **96–99%** of the time when
  it decides, and says "I don't know yet" when it can't.
- **Its will acts only where it owns the problem.** Its caution cuts its own errors by **43–55%**. It leaves hard
  input alone (caution 0 on 98% of nights), and it is never cautious where it is fine.
- **Every claim it makes about itself has a receipt.** **341,868 claims were recomputed from raw records, with 0
  mismatches.**
- **Adding the self changed nothing else.** Eight 60-day lives, relived with the self, are byte-identical outside
  it. Every guarantee of the body below still holds.
- **The body underneath (part 1).** Isolated per-cluster memory, laws that hold for everyone, it reads its own
  attention from its thoughts' paths, and its life is bit-identical on AMD and Intel and on numpy 1.26 and 2.1.

Not claimed: intelligence, understanding, awareness. It is born mute: it speaks only through its diary. Its Ears
often miss what people say *about it* (0.53). At founder pace its self will mostly say "I don't know yet" for weeks.
**Founder-only speech remains in force.**

## Earlier creatures — all alive

**Teich v0.3** was born 2026-10-03 (identity `004f6ca5e5c151e3…`). Its memory provably changes what it does and
never what it is. It lives at `/o/teich-03`, and its seat chain carries v0.4's pre-registration anchors. Start at
[v03/README.md](v03/README.md).

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
