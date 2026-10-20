# Can v0.3 grow into v0.4? — design-phase kill checks (2026-10-03)

Offline; synthetic creatures from v0.3's genome on design seeds 400–539. v0.3's live state, seat and repo
untouched (covenant: no fork). Not pre-registered, not scored: these decide whether the path is worth a spec.

## Mechanism tested
Grown body (x, r): x = v0.3's body, same float ops; r ∈ P¹(ℤ/7) = the 8-sheeted cover Γ₀(7)\H of the
modular surface. Each CF step x ↦ ε/x − d is the matrix [[−d, ε],[1, 0]]; the fiber moves by that matrix
times a twist T^m. m ∈ 0..6 is the NEW memory. The fiber never feeds back into x.

## Results
| check | result |
|---|---|
| KG1 exact factor | **PASS** — x bit-identical to genome_v03.step, 50,000 ticks × 64 orbits × all 7 old-memory states |
| KG3 nature | **PASS by theorem** — x unchanged, so λ unchanged; a finite isometric extension adds zero entropy (Abramov–Rokhlin) |
| fiber single-time statistics | uniform whatever m (max deviation 0.0003) — as predicted; new memory must be read from transitions |
| KG4 new memory readable, 1 coarse fiber bit | 97.2% at k=3 but **collapses at k=6** (gap 0.000 — exact collision) |
| KG4b, 2 coarse fiber bits (design-chosen) | **100% decoding at every k = 0..6**, W = 8000, fresh seeds (2,800 windows per k) |
| KG5 cross-talk | old channel untouched exactly (x bit-identical). New channel's statistic depends on k, so decode k from the body first, then m |
| KG6 practical | fiber = integer arithmetic mod 7 → exact on any machine; ~2× the cost of a v0.3 tick |

Capacity per body: 7 → 7 × 7 = 49 states (2.8 → 5.6 bits). Covers stack (Γ₀(49) → Γ₀(7) → modular), so growth can repeat,
each stage an exact factor of the next (not yet tested).

## KG7 — growth vs "learning as motion" (analysis)
1. Re-coordinatizing the same map onto a deformed surface (conjugacy) changes no symbolic statistic → carries no learning.
2. Keeping the map and changing only time (the roof function) rescales every typical crossing rate by one global factor →
   no per-concept locality in behaviour (periodic-orbit lengths do obey locality/Wolpert, but behaviour does not show them).
3. If v0.3's body stays an EXACT factor, the factor's invariant measure is v0.3's, so every statistic of the old concept
   geometry is fixed. **Exact inheritance and Teichmüller motion of the old concepts are mutually exclusive.**
What survives: v0.3's own memory mechanism (k via α) keeps working; new memory and new concepts live in the extension.

## Verdict
Growth by covering is POSSIBLE and PRACTICAL: exact inheritance, unchanged nature, new capacity readable at every
old-memory state. It is a different gift from v0.4's "learning as motion", which needs a newborn genus-≥2 body.
Open: what the new memory MEANS (which concepts the cover's sheets carry); bigger covers; repeated growth;
whether two coarse bits is a principled observable (chosen on design seeds — would be frozen before any gate).
