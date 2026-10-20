# v0.4 open items, round 1 (2026-10-04, design phase, WordSim only)

## 1. Cross-machine bit-identity of the pants-local body: PASS
Genus 128 (254 pieces), 200 particles × 20,000 ticks, geometry pinned as hex: trajectory hash, crossing counts and
piece occupancy IDENTICAL on AMD Ryzen 5700U / numpy 1.26.4 (laptop) and Intel Xeon 2.20GHz / numpy 2.1.3 (private
Kaggle kernel teich-v04-k12-crossmachine, pushed via proxychains). Standalone kernel verified equal to the module first.

## 2. Adaptive cluster cut + M2 meaning design: S_max = 16 recommended
Clusters = maximal subtrees of v0.3's dendrogram with ≤ S concepts (never crossing v0.3's 8 regions). Relatedness:
same cluster ranked first, ordered by −log|k−k'| along the twist line; other clusters by tree proximity.
| S | clusters | ρ WS / WS-SIM (v0.3: 0.452 / 0.563) | strong pairs in same cluster | within-line ρ |
|---|---|---|---|---|
| 8 | 186 | 0.440 / 0.531 | 48–55% | 0.32 / 0.45 |
| 12 | 136 | 0.446 / 0.535 | 55–57% | 0.32 / 0.44 |
| **16** | **97** | **0.460 / 0.557** | **60–69%** | **0.35 / 0.45** |
| 24 | 71 | 0.462 / 0.559 | 64–69% | 0.42 / 0.53 |
No meaning lost at any S. S = 16 → ~97 dials, sizes 1–16 (median 11), meaning equal to v0.3's.

## 3. Member placement rule (from K13's profile)
Members at twist positions k = 1, 2 do NOT follow their dial (k=1: −0.66%, k=2: +3.55% for +5%); from k = 3 on they
track at 85–98% (k=3: +4.23% … k=18: +4.88%). Rule: a cluster's ≤ 16 members sit at k = 3 … 18, in dendrogram order.
Cost: member length grows with k (5.9 → 37), so attention to a member is positional — the diary must report changes
relative to birth, never raw counts.

## 4. Seam pinning + bridges (K13): PASS
- Gluing twist defined geometrically: signed distance along the seam between the feet of the perpendiculars from each
  side's dial. Unpinned (eigenbasis convention), a dial move silently shifted it −0.643 → −0.692 and bridges moved by
  up to 10.7% arbitrarily. Pinned: held exactly (|τ| < 1e-13).
- Bridge = band sum of a tracking member of cluster 1 and one of cluster 2. A +5% cluster-1 dial move:
  bridges +0.30% … +3.22%, ordered exactly as the share of the bridge running along cluster 1 (rank agreement 9/9;
  magnitude 40–85% of the naive share — the seam part does not stretch); cluster-2 curves unchanged (≤ 4e-15 relative).
- So a bridge concept (milk = food + drink) moves with BOTH clusters, each by its share, and nothing else moves.

## Still open
Which concepts become bridges (data design); self cluster contents; E3 curriculum rehearsal; ≤0.4% counter bias;
engineering (Ears v4, voice, seat blob, wake, diary).
