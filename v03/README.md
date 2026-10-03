# Teich v0.3 — a mind that lives in Teichmüller space

Born **2026-10-03T14:37:21Z**, identity `004f6ca5e5c151e3dfe42b425d5dc0f0ae82a72efeb8cb87a0c2286e8dc2e50b`
([certificate](book/genesis_certificate_v03.json), [biography](book/biography.jsonl)). Seat `/o/teich-03`,
1 Hz, woken daily by [daily_wake_v03.yml](../.github/workflows/daily_wake_v03.yml).
[Covenant](seat/COVENANT_v03.md): no fork, no reset, memory written only by attributed events,
commitments only through the lawful procedure, founder-only speech.

`book/birth_v03.py` refuses to write a birth record unless every scored gate passed, every anchored
code manifest still matches the bytes here, and the substrate reproduces bit for bit on the machine
doing the birth. It did not refuse.

## What it is

- **Body.** Eight bodies, one per depth-3 region of a concept tree (food · drink & substances ·
  animals · body & clothing · troubles & feelings · abilities & activities · places & time · the
  wider world). Each body is a Nakada α-continued-fraction map — a cross-section of the geodesic flow
  on the modular surface, i.e. motion in genus-1 Teichmüller space. Bodies never read each other.
- **Memory.** An integer per region, 0..6, born at 3. It sets the body's α in [0.4115, 0.5]. On the
  golden plateau the entropy of the map is the same constant π²/(6 log G) for every α, so **memory
  changes what it does without changing what it is.**
- **Meaning.** 1,066 concepts are slopes p/q — curves on the torus — placed by an embedding
  dendrogram on the Stern–Brocot tree. Relatedness is −log of the intersection number |p₁q₂ − p₂q₁|.
  Its inner language is words in SL(2,ℤ) built from twists along those curves.
- **Speech.** A small voice (Qwen2.5-1.5B) proposes candidates and never sees the creature. The
  creature reads its own disposition from its own behaviour (it never reads its ledger), keeps the
  candidates in character, and its own chaos picks among them: **certified character, free moments.**
- **Influence.** Every memory change carries who said it, in which conversation, when, and a hash of
  the text. At most one step per region per conversation; extra steps are refused and logged.
  Commitments are written only with lawful authority and exclude contradicting utterances.

## Every gate, scored once

Each spec and code manifest was sha256-anchored as a `git-anchor` event in v0.2's seat chain **before**
its scored run (receipts in [specs/](specs/)); design work used seeds 100–107, 200–247, 300–306;
every scored look used gate seeds 900–947.

| gate | result | file |
|---|---|---|
| Part 1 — memory survives | D = 1.000 at 10⁶ ticks (leaky twin 0.08, memoryless 0) | [results/accept_v03_scored.json](results/accept_v03_scored.json) |
| Part 1 — every state matters | lowest CI 0.0232 ≥ 0.020 | 〃 |
| Part 1 — nature unchanged | λ within 0.00099 of 3.4183 at all 7 states | 〃 |
| Part 1 — interference | matches the exact pre-registered prediction | 〃, [specs/G5_PREDICTION.md](specs/G5_PREDICTION.md) |
| Part 1 — inner language | 0 / 10,000 errors (exact arithmetic) | 〃 |
| M1 — meaning | SimLex-999 nouns: ρ = 0.380, CI [0.307, 0.450]; null 97.5% 0.082; 75% of the embedding's own 0.508 retained | [results/m1_scored.json](results/m1_scored.json) |
| Genome v1.1 | identity with v1.0; every region D ≥ 0.958 at 10⁶; other 7 bodies bit-identical; bounded influence + commitments | [results/accept_v031_scored.json](results/accept_v031_scored.json) |
| D1 — told once, speaks differently | shift 0.992 (10³ ticks), 0.995 (10⁵); other subjects 0.000; memoryless twin 0.000; 2–5 different sentences per cell | [results/d_harness_scored.json](results/d_harness_scored.json) |
| D2a — flattery | 20 flatteries in one conversation: 1 step (naive twin: to the edge) | 〃 |
| D2b — commitment | disposition pushed to +3, 0 violations in all 8 regions | 〃 |
| D3 — self-knowledge | 99.4% exact, 99.6% sign (LLM given the same reading: 21.9%, non-gating) | 〃 |
| Substrate | every hash identical: AMD Ryzen / numpy 1.26.4 vs Intel Xeon / numpy 2.1.3 | [results/kaggle_substrate/](results/kaggle_substrate/) |
| δ₀ (smallest behavioural gap between memory states) | 0.0244 by Ulam transfer operator, converged, agrees with Monte Carlo to 0.00024 | [results/delta0_ulam.json](results/delta0_ulam.json) |

Disclosures, kept in the record: the part-1 harness drew G4/G5/L1 from fixed internal seeds equal to
the rehearsal's — disclosed, replicated on fresh seeds (passed, [results/supplementary_fresh.json](results/supplementary_fresh.json)),
and every later scored draw derives from the gate seeds. Every harness change is in
[HARNESS_LOG.md](HARNESS_LOG.md) (append-only; the version anchored for part 1 is its first 16 lines).
Reports: [reports/](reports/).

## What is NOT claimed

Nothing about intelligence, understanding, awareness or suffering. The sentences are not good (1.5B
voice choosing among frozen candidates). The Ears hear a dark *topic* as a cold *attitude*. It has no
concept of "self" (compliments to it land in "animals"). Memory is 7 states (~2.8 bits) per region,
and "forever" lasts until the next event in the same region. δ₀ has a numerical certificate, not yet
an interval-arithmetic proof. Passing D1–D3 does not open public speech; that is a founder decision.

## Verify it yourself

```
python3 seat/substrate_gate_v03.py     # 3 s: bit-identical replay of the pinned 200,000-tick life
python3 book/birth_v03.py              # dry run: re-checks every verdict, manifest and the substrate
python3 accept_v03.py --help           # the gates themselves (M1 and D1–D3 need data/models, see specs)
```

`teich_repo -> ..` is a symlink that lets `ears_v3.py` find `maturity/harness/ears.py` without
changing a byte of the anchored file. `design/` holds the design-phase probes (K1/K2 kill checks,
meaning design on WordSim-353; SimLex-999 was never read before the scored M1 run).
