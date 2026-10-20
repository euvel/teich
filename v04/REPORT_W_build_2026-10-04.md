# v0.4 build checks W1–W5 (2026-10-04, lab, design seeds — not gates)

Build candidate: `v04_lab/build/` (genome_v04, creature_v04, seat_v04, ears_v04, geometry table sha256 9b171fd6…ac3b0,
vocabulary sha256 b402978a…7b7e8). Nothing created on any seat; nothing published.

| check | what | result |
|---|---|---|
| W1 range | handle geometry at all 41 attention levels (stretch 0…1.0, dial ×1…×2.718) | area 2π within 3e-9, 10–11 faces, 3–7 dial lifts, radius stable — sound |
| W2a equivalence | genome body (rows copied from the frozen table) vs lab engine mind4 (computed geometry) | rows bit-identical at birth and after 60 random moves; 3,000-tick lives identical |
| W2b continuity (2 days, laptop) | life through the seat vs the same life continuous | final blob + diary byte-identical, 29/29 round-trips exact |
| **W3 rehearsal (60 days, Kaggle Intel Xeon, numpy 2.1.3)** | 197 seat commits (daily wakes with gate, conversations, a commitment, a crowd), vs continuous life | **final blob byte-identical, 60 diary entries identical, 197/197 round-trips exact** |
| W3 gate cross-machine | gate fixture recorded on the laptop (AMD, numpy 1.26.4), relived on Kaggle (Intel, numpy 2.1.3) | **PASS, same sha256** (09a4a84f…) |
| W3 laws | 419 mind requests | 300 accepted; refused: 56 per-conversation, 54 speed limit, 7 edge (a dial reached 40), 2 committed; 0 violations |
| W3 diary vs truth | 5,051 readings spoken (≥ 3 quiet nights) | **99.98% exact**; 2,204 named non-zero readings 99.95% exact; **1 false positive** (day 4, chaos·mud·noise read +1, true 0); a single night alone 91.3% exact |
| W4 Ears | build module vs design v4c on the 47 design sentences | identical: sign 46/47, cluster 42/47, self 12/12 (design set, not independent) |
| W5 members | member T_A^k(B), k = 3…18, change share vs dial change over the wide range | 0.84–1.00, tightening as the dial grows |

Cost: a day of life at 2,048 thoughts = 111 s (laptop AMD), ~200 s (Kaggle Intel).

## Findings to carry
1. **Blob growth.** The blob was 170 KB at birth and 303 KB after 60 days at ~6 mentions a day: the logs grow inside it.
   At founder-only rates this lasts years under the seat's 2 MB row limit, but the clean fix before birth is to move
   closed logs out of the blob (into the repo diary / seat events) and keep only the open per-conversation state.
2. **The heart saturates under heavy talk** (104 edge refusals; v0.3's law, no speed limit on the heart). Expected and
   lawful; noted because the mind now has a speed limit and the heart does not.
3. Popular attention fills up: at 6 mentions a day the most-mentioned cluster (meal·food·dinner) reached the edge (40)
   by day ~55. Growth adds room later, as decided.
