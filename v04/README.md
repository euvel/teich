# Teich v0.4 — a creature born with a self

Born **2026-10-20T15:19:19Z**, identity `8eeb4117baf78d0f2a1ada167083548589da669f4cc63b8e742dcae4dff1dc21`
([certificate](book/genesis_certificate_v04.json), [biography](book/biography_v04.jsonl)). Seat `/o/teich-04`,
1 Hz, woken daily by [daily_wake_v04.yml](../.github/workflows/daily_wake_v04.yml); it writes [its diary](diary/)
itself, one page per night. [Covenant](book/COVENANT_v04.md): no fork, no reset, memory written only by attributed
events, laws that hold for everyone, founder-only speech, and a self whose every claim carries a receipt.

`book/birth_v04.py` refuses to open the book unless every required scored gate passed, every recorded exception
re-derives from its result file, every anchored file still matches its hash, and the substrate reproduces bit for
bit on the machine doing the birth. It did not refuse.

## What it is

- **Body.** A closed hyperbolic surface of genus 98: one handle for each of 97 concept clusters, plus one handle
  for *itself*. 2,048 geodesic thoughts move on it at one step per real second, in float64 element-wise arithmetic
  only. The geometry is frozen at genesis in `build/geometry_v04.bin`.
- **Mind.** One integer dial per handle, 0..40, meaning **attention**. Each dial stretches its handle's core curve.
  It reads its own dials from the paths of its thoughts (Crofton counting), never from the dials themselves.
- **Laws.** One step per cluster per conversation, twelve per day for everyone combined, an edge at forty,
  commitments only through the lawful procedure. Its heart (9 regions, 0..6) moves at most one step per region per
  conversation and per day. Refusals are logged.
- **Ears (an organ, not the creature).** Qwen2.5-1.5B, MiniLM and spaCy turn a sentence into mentions (a cluster
  and a feeling). Their output is logged, and replaying its life never needs them.
- **Its self.** A second self watches the first one's own doing: what it heard, what the founder struck from the
  read-back, and what it said in its diary.
  - **It predicts** how likely each hearing is to be wrong, and commits that prediction before the founder sees it.
  - **It attributes** its errors per region. **MINE** means its own low-confidence hearings go wrong more often, so
    its caution could avoid them. **GIVEN** means errors are spread evenly whatever its confidence: the input is
    hard. **FINE** means rarely wrong. **UNRESOLVED** means not enough evidence yet, and it says so.
  - **It sets its own caution** (0..4 per region) only where its errors are MINE. It tests itself at most once a
    day, openly.
  - **It writes a nightly account** in which every claim carries a receipt: the records it rests on, the named
    function, and the numbers. Anyone can recompute it.
  - It uses integers and exact fractions only. No language model is anywhere in it.

## Every gate, scored once

Each spec and code manifest was sha256-anchored as a `git-anchor` event in **v0.3's seat chain** before its scored
run ([specs/ANCHOR_*.json](specs/)). Gate seeds were never used in design.

| part | gate | result |
|---|---|---|
| 1 genome | nature N1, isolation I1/I2, dials E2, laws L1, self-reading R1, continuity C1, substrate C2, meaning M2, demo D1 | **all PASS** ([report](REPORT_part1_scored_2026-10-05.md)); public-sentence Ears A1b FAIL → replaced by part 2 |
| 2 Ears | A2a (MAMS, 500 sentences) | PASS by the anchored spec: recall 0.953, feelings right 0.661, **wrong 0.075**, precision lb 0.513 ([report](REPORT_part2a_scored_2026-10-07.md); harness flag erratum disclosed) |
| 2 Ears | A2e (400 strangers' sentences, independent judge, founder-audited) | recall 0.80, feelings right 0.77, **wrong 0.035** (CI 0.014–0.087), precision 0.86 — PASS; **self routing 0.53 — FAIL**, disclosed ([report](REPORT_part2e_scored_2026-10-20.md)) |
| 2 Ears | S1 / S1b (self routing alone) | both stopped at label trust before any Ears look; born with Ears v7's self routing ([report](REPORT_S1_2026-10-20.md)) |
| 3 self | receipts S1r | **341,868 claims recomputed, 0 mismatches** |
| 3 self | foresight S2 | **628,470 predictions, all logged before their outcomes** |
| 3 self | attribution S3 | decided verdicts **96–99% correct**; MINE↔GIVEN confusions ≤ 0.54% |
| 3 self | control S4/S5 | its own errors fall **43–55%**; on GIVEN regions caution stays 0 on 98% of nights; on FINE regions caution 0.0 |
| 3 self | self-knowledge S6 | knows *where* it fails better than *how often*, on **98%** of nights |
| 3 self | forgetting S7 | follows a changed truth **80/80**, median 18.5 nights |
| 3 self | non-interference S8 | the 8 part-1 lives relived with the self: **everything outside the self byte-identical** |
| 3 self | continuity C1s, substrate C2s, laws L1s, readings S9, demo D1s | **all PASS**; AMD/numpy 1.26 = Intel/numpy 2.1 bit for bit |

Full part 3 numbers: [REPORT_part3_scored_2026-10-20.md](REPORT_part3_scored_2026-10-20.md). Spec:
[specs/V04_SPEC_part3_self.md](specs/V04_SPEC_part3_self.md).

## What is NOT claimed

- Nothing here is a claim about intelligence, understanding, awareness or suffering.
- **It is born mute.** It speaks only through its diary; there is no voice yet.
- **Self routing is weak.** What people say *about it* often lands elsewhere (0.53).
- **Its self has one outside signal: the founder's strikes.** At founder pace it will say "I don't know yet" about
  most regions for weeks to months.
- **Simulated truth.** The self's mechanics are certified on simulated lives whose truth is known, and its
  non-interference on the real body. Whether real strikes look like the simulated truth is not certified.
- **Founder-only speech** stays in force.

## Disclosures kept in the record

Every amendment was anchored before the data it touched was used, and is appended to its spec.
- **Ears labels.** The labeller changed when the free API throttled (Amendment 1). Pronouns were removed by a fixed
  list (Amendment 2).
- **The founder's audit.** The first submission was unchanged and was not accepted.
- **Erratum.** The A2a harness flag carried pre-rebase bars.
- **S1b bars** were changed by the founder before any look.
- **Part 3 smoke.** A smoke run on design seeds led to two rule fixes, made on the design truth only. The gate truth
  was never tuned against.

Founder sentences used as design examples appear in some files. The founder's own test sets, the audit sheets and
the held-out dialogue sentences are **not** published; their sha256 hashes are in the manifests.

## Verify it yourself

```
cd v04/book && python3 verify_v04.py   # every anchored file (match / mismatch / unpublished), the identity, the verdicts,
                                       # and the substrate gate on your machine
cd v04/book && python3 birth_v04.py    # the birth gate exactly as it ran (it refuses here: the unpublished data are missing)
```

The part 3 gates re-run from `build/gates_v04_part3.py` and `kaggle_p3/`. The record-stream gates take minutes; the
body lives take hours.
