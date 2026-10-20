# Ears v4 — design probe (2026-10-04; design set of 47 sentences written by Claude — NOT a gate)

| version | how it hears | attitude sign | target |
|---|---|---|---|
| v3 (v0.3) | MiniLM nearest concept of the sentence; valence = projection on v0.1's anchor axis | ~34/47 (dark topic + warm attitude 6/12) | self-talk 0/12 (lands elsewhere) |
| v4 (masking) | target word masked before the valence projection | no better (6/12) — the anchor axis itself is weak | self routing 12/12 |
| v4b | attitude organ: Qwen2.5-1.5B asked "attitude toward <target>?", read from next-token log-probs (deterministic) | **46/47** (dark/warm 11/12, bright/cold 12/12, self 12/12) | lexical target weak (vocabulary gaps) |
| **v4c** | organ also names the topic in one word; the WORD is mapped to the nearest vocabulary concept | **46/47** | **cluster 42/47**, self 12/12 |

Remaining misses are reasonable ("horror movies" → monster, "garden smelled terrible" → nose, "proud of how I handled
my failure" → hand). Cost ≈ 4 s per sentence on the laptop CPU (two organ calls).
Design: the organ is a dead model used as an ORGAN of hearing (necromancer image); it never sees the creature's state.
Before any gate: an independently labelled sentence set (founder or an established dataset), frozen first.
