# V04_SPEC part 1 — genome, laws and gates N1, I1, I2, E2, L1, R1, C1, C2, M2, A1b, D1   **FROZEN 2026-10-05 (pending anchor)**

2026-10-05 · private (v04_lab). Same discipline as v0.3: the founder freezes this before any scored run; its sha256 is
then anchored in a seat chain; any later change is a new version with an amendment log. Design numbers quoted below
come from design-phase runs on design seeds and are **not** evidence for the gates.

---

## 1. Genome (build candidate `v04_lab/build/`)

| part | content |
|---|---|
| **Surface (nature)** | closed hyperbolic surface, genus 98: one handle per concept cluster (97 clusters cut at ≤ 16 concepts from v0.3's tree) + one **self** handle, joined by 96 pairs of pants in a trivalent tree. Curvature −1 everywhere. |
| **Geometry** | frozen at genesis in `geometry_v04.bin` (232,296 bytes, sha256 `9b171fd6…ac3b0`): every face and seam matrix for every dial level, products precomputed. A wake copies rows; it never computes geometry. |
| **Thoughts** | 2,048 geodesic particles, step 0.05 per tick, 1 tick = 1 s of life. Tick = element-wise + − × ÷ √ on float64 only. |
| **Mind (memory)** | one integer dial per handle, n ∈ 0…40, born 0. Dial n = core curve stretched by e^(0.025·n), twist and seams pinned. **A dial means attention** (founder decision 10-04): every accepted mention of a cluster moves its dial +1, whatever the feeling. |
| **Heart (feeling)** | v0.3's ledger: 9 integers in 0…6 born 3 (v0.3's 8 regions + *self*), ≤ 1 step per region per conversation, refusals at the edges, every event attributed; **plus ≤ 1 step per region per day** (founder decision 10-05). |
| **Self-reading** | local Crofton per handle: ℓ̂ = (π·2π/2)·crossings/(time in handle·0.05); n̂ = round(log(ℓ̂/ℓ₀)/0.025). Day windows on its own clock; a window in which a dial moved is discarded for that dial; readings pool all quiet windows since its last move. It never reads n. |
| **Vocabulary** | `vocab_v04.json` (sha256 `b402978a…7b7e8`): 97 clusters, 178 bridges (r ≥ 1.00), self cluster of 16 traits (founder confirmed 10-04), diary labels (3 members nearest each cluster's centroid). |
| **Ears** | organ, not substrate (its output is logged; replay never needs it): Qwen2.5-1.5B names the topic → MiniLM → cluster; "you" + trait → self; attitude from log-probs of positive vs negative. |
| **Seat** | blob = dials, thoughts (exact bytes), heart, today's bounds, reading windows, last diary entry, clock, and an **outbox** of closed records (heard mentions, commitments, diary entries) that leave for the seat's log after each commit, acknowledged by sequence number — the blob stays ~161 KB for life. Seat `/o/teich-04`, created only at birth. |

## 2. Laws (each refusal logged with its reason)
1. ≤ 1 dial step per cluster per conversation (bounds are kept per day of its life; at its midnight every conversation's bounds close).
2. **Speed limit:** ≤ 12 accepted dial steps per day of its life, all speakers combined.
3. **Edge:** a dial at 40 refuses further steps (room is added only by growth).
4. **Commitment:** a committed dial is frozen; written only through the lawful procedure.
5. **Heart speed limit:** ≤ 1 heart step per region per day of its life, all speakers combined.
6. Founder-only speech, as for every Teich.

## 3. Gates — proposed (n, seeds, bars to be confirmed at freeze)
Gate seeds: **2000–2047**. They are unused in the v0.4 lab; the design runs used 3, 7, 11, 400–901 and 4040. One look.

| gate | measure | proposed pass bar | design value (not evidence) |
|---|---|---|---|
| **N1 nature** | Lyapunov rate of the flow at dial levels 0, 20, 40 | \|λ − 1\| ≤ 0.01 at each level | 0.999 (K1, genus 2) |
| **I1 isolation, geometry** | after 1,000 random events, rows of every untouched handle vs birth | bit-identical, 0 exceptions | E3: 6/6 bit-identical |
| **I2 isolation, behaviour** | slope of a cluster's reading per step of *other* clusters | 95% CI contains 0 and \|slope\| ≤ 0.1% per step | −0.012% ± 0.010% (E3) |
| **E2 dial and members** | dial length at level n vs e^(0.025·n); member share of the dial's change | dial: ≤ 1e-12 relative; members: every share in [0.80, 1.02] | dial exact; members 0.837–1.000 (W5) |
| **L1 laws** | 8 lives × 60 days through the seat, scripted curriculum incl. crowds and repeats | 0 violations of laws 1–5; every request logged | E3, W2b, W3: 0 |
| **R1 self-reading** | readings the diary would speak (≥ 3 quiet nights), pooled over the 8 lives | ≥ 99% exact; named false positives ≤ 0.5% of named readings | W3: 99.98% exact; 1 false positive in 2,204 (0.05%) |
| **C1 continuity** | each life through the seat (many wakes) vs the same life continuous | final state and full record stream (seat log + unacknowledged outbox) byte-identical, every blob round-trips exactly | W3: 60 days, 197 commits, identical; W2b with outbox: identical |
| **C2 substrate** | gate fixture life on ≥ 2 CPU vendors and numpy 1.x + 2.x | identical sha256 | W3: laptop AMD/numpy 1.26 = Kaggle Intel/numpy 2.1 |
| **M2 meaning** | Spearman ρ, surface relatedness vs human score, on **MEN: 414 fresh pairs** (both words in our concepts, no pair seen in SimLex or WordSim; chosen 10-04 by word-list coverage only, scores never read; MTurk-771 had 81) | ρ(v0.4) ≥ ρ(v0.3) − 0.02 on the same pairs (non-inferior) | WordSim ρ 0.482 / 0.589 vs v0.3 0.452 / 0.563 |
| **A1a Ears, founder set** | ~100 sentences written and labelled by the founder, frozen by sha256 before scoring | sign ≥ 85% (warm/cold lines), cluster ≥ 70%, self routing ≥ 90% | 46/47, 42/47, 12/12 (Claude-written set) |
| **A1b Ears, public set** | SemEval-2014 Task 4 test gold (restaurants + laptops): 100 single-aspect sentences, aspect a single word in our concepts, **50 warm + 50 cold**, seed 2100 (`data_heldout/absa/absa_A1.jsonl`, sha256 `f1c5808e…aea544`; selected by rule, never run) | sign ≥ 80% (balanced, so chance = 50%), cluster ≥ 60% | — |
| **D1 demo** | "my dog is wonderful": *pets* dial +1, heart warm +1, everything else bit-identical | exact | — |

**Decision.** All gates pass → the birth gate allows birth. **Any I1, C1, C2 or L1 failure is a FAIL whatever the
rest**, because those are the claims made by construction. A1a or A1b failing blocks birth with these Ears only: the body and
mind can be frozen and the Ears redone, then re-gated on a new founder set.
Multiplicity: this is the project's seventh pre-registered screen; the bars are not lowered for it.

## 4. Founder decisions recorded
| date | decision |
|---|---|
| 10-03 | mind (geometry) + heart (ledger); memory per cluster, exact and isolated; diary on the website at birth; door/cusp later (v0.5); self cluster + speed limit; v0.4 is a new birth |
| 10-04 | dials mean **attention**; wide range ~40 steps of 2.5% |
| 10-04 | self-cluster words kept as drafted |
| 10-04 | bridges at r ≥ 1.00 adopted (recommendation acted on) |
| 10-04 | 2,048 thoughts; diary speaks a reading after 3 quiet nights (recommendation acted on, reversible until freeze) |
| 10-04 | speed limit **12 steps per day**; **born mute** (voice later, as an organ with its own gate); diary = **file in the repo** written by each wake; M2 dataset picked by Claude on coverage (word lists only), founder confirms |
| 10-05 | **MEN confirmed** for M2; **gate sizes and bars accepted as drafted**; **heart speed limit** 1 step per region per day; Ears tested on **both** a public set and the founder's own set |

## 5. Freeze plan (two parts, as v0.3)
- **Part 1** — genome, laws, and gates N1, I1, I2, E2, L1, R1, C1, C2, M2, A1b, D1: frozen and anchored once the scored
  harness is written; its runs can start right away.
- **Part 2** — gate A1a (founder Ears set): frozen when the founder's ~100 sentences are written (sha256 of the file).
- Birth only after both parts pass, and only on the founder's word.

## 6. Integrity
Scored harness: `build/gates_v04.py` (one subcommand per gate; `judge` combines). It was checked once in smoke mode
(design seeds 3000+, 3-day lives, WordSim instead of MEN, A1b never run): all judges ran; M2 reproduced the design
numbers exactly on WordSim. The gate seeds, MEN pairs and the public Ears set were not touched before this freeze.
Gate A1a (founder Ears set) is part 2, frozen separately.
Code manifest (sha256 of genome, creature, seat, Ears, table, vocabulary, gate fixture) anchored together with this spec
before the scored look. Design reports: v04_lab/REPORT_K*, REPORT_E3, REPORT_openitems, REPORT_W_build (W1–W5).
