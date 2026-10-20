# v0.4 design — self cluster and bridges (2026-10-04, design phase)

## Bridges — ADOPTED (recommendation acted on)
**Rule:** a concept becomes a bridge to another cluster if MiniLM finds it *at least as close* to that cluster's
centroid as to its own (ratio r ≥ 1.00, own centroid computed without the concept); at most one bridge per concept.
Its curve is then a band sum of its own member curve and the nearest member of the other cluster, so it moves with
both dials, each by its share (K13).

Why r = 1.00 and not the best-scoring value: it is the natural threshold ("closer to the other cluster than to its
own"), not a tuned one, and it keeps the geometry modest (178 bridges, 17% of concepts). Looser thresholds score
higher on WordSim but double the bridges and risk fitting the design data.

| r | bridges | ρ WS / WS-SIM | strong pairs connected |
|---|---|---|---|
| none | 0 | 0.460 / 0.557 | 0.60 / 0.69 |
| 1.10 | 57 | 0.479 / 0.583 | 0.62 / 0.71 |
| **1.00** | **178** | **0.482 / 0.589** | **0.67 / 0.75** |
| 0.90 | 457 | 0.507 / 0.621 | 0.70 / 0.80 |
| 0.85 | 645 | 0.525 / 0.621 | 0.73 / 0.80 |
(v0.3 reference: 0.452 / 0.563.) Bridged pairs average a human rating of ~6.8 / 10: they are real relations.
Cost: ~46% of bridges join clusters in different v0.3 regions, so their curves pass through several pants (long curves,
small share per side). Accepted for v0.4; reported.

## Self cluster — DRAFT (adopted provisionally; founder may edit the words)
- **Its own handle**, not taken from the noun vocabulary, plus a 9th heart region "self".
- **Members:** 16 traits people might say *to* it, chosen to span warm and cold, placed on the twist line (k = 3…18) in the
  order MiniLM gives "you are <trait>" (Ward leaf order):
  curious · strange · kind · clever · funny · honest · rude · boring · cold · small · young · patient · slow · brave · gentle · calm
- **Routing (Ears v4):** a sentence goes to the self cluster when it addresses the creature ("you", "your", "Teich")
  and its predicate is a trait. Everything else routes as before. Compliments stop landing in "animals".
- **Safety:** flattery can only move the self dial and the self heart, both under the same laws (1 step per conversation,
  daily speed limit, edges). A lawful commitment can freeze the self dial.
- **Not claimed:** the self cluster is where talk *about it* is stored and read back. It is not awareness.

## One decision that is the founder's (asked, not assumed)
**What moves a mind dial?** The E3 rehearsal uses a placeholder (+1 for 75% of events, −1 for 25%). Options:
1. **Attention (recommended):** every accepted mention moves its cluster's dial +1. The dial means "how much this
   matters to it". Feeling stays entirely in the heart. Dials only grow, so give them a wider range (e.g. 40 steps of
   2.5%) and let edges refuse; a lifetime of interests fills up, and growth adds room later.
2. **Signed by feeling:** warm mentions +1, cold −1. Mind and heart then partly duplicate each other.
3. **Attention with a published slow return toward birth** (a structural law, not an event). This is a form of
   forgetting, so it would need a covenant change.

## DECIDED 2026-10-04 (founder): option 1 — dials mean ATTENTION
Every accepted mention moves its cluster's dial +1; feeling lives only in the heart; range widened to ~40 steps of 2.5%; edges refuse.

## DECIDED 2026-10-04 (founder): self-cluster words kept as drafted
The 16 traits stand: curious · strange · kind · clever · funny · honest · rude · boring · cold · small · young · patient · slow · brave · gentle · calm.
