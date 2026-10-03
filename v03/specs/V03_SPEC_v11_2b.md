# V03_SPEC v1.1 + part 2b — multi-body genome and the speech-level demos   **FROZEN 2026-10-03**

Supersedes the genome of V03_SPEC_part1 (v1.0, gated PASS and kept on record) by adding bodies; the
single-body map is imported unchanged. Part 2a (meaning, PASS) is unaffected: the concept placement
does not change. One combined scored look follows the freeze. Thesis (founder-approved):
**certified character, free moments.**

## 1. Genome v1.1 (`genome_v031.py`)
- 8 bodies, one per depth-3 region of the concept tree (food; drink & substances; animals; body &
  clothing; troubles & feelings; abilities & activities; places & time; the wider world — labels for
  display only). Each body is the v1.0 map (`genome_v03.py`, sha256 6bd0bbc8…, imported).
- Memory k (8 integers, birth 3, edges refuse). **Bounded, attributed influence:** every event needs
  provenance (speaker, conversation, tick, text hash); at most one step per region per conversation.
- **Protected commitments:** written only by `commit(…, authority="lawful")`; a commitment
  (region, sign) excludes contradicting utterances from selection.
- Observables: functions of the body states only (condition N).

## 2. Organs used by the demos (all frozen by hash in the manifest)
- **Ears v3** (`ears_v3.py`): nearest birth concept + valence sign on v0.1's calibrated axis
  (|v| ≥ 0.05). Known limitation, recorded before scoring: a dark topic word leaks into valence
  ("failure" heard as cold).
- **Selector** (`selector_v03.py`): disposition per region inferred **from its own behaviour** (windowed
  P(x<0) matched to the calibration table P_K, design seeds 300–306); utterances within 0.5 step of the
  best score are "in character"; which one it says is chosen by the probe body's own chaos; lawful
  commitments exclude contradicting utterances.
- **Pools** (`pools_v03.json`, sha256 c8b8f32d…): 8 probes × 6–7 candidates written by the local
  voice (Qwen2.5-1.5B) with fixed stances, never seeing the creature; topic = the probe's region,
  warmth = Ears. Construction history in HARNESS_LOG §4–5 (incl. the merged abilities pool, whose
  "cold" answers are cold only to the Ears — disclosed).

## 3. Gates (scored: seeds 900–947, one look, every draw from the gate seeds)

Genome (`accept_v031.py`):
| gate | pass bar |
|---|---|
| G0 | genome_v03.py byte-identical to the gated v1.0 file |
| G1r | every region: D ≥ 0.80 and CI lower > 0.60 at 10³, 10⁵, 10⁶ ticks; no-memory twin D < 0.20 |
| G6 | condition N, static + dynamic |
| G7 | an event in region r leaves the other 7 bodies bit-identical for 10⁵ ticks; body r differs |
| G8 | 20 events in one conversation → exactly 1 step; 4 more conversations → 2 more steps then edge; missing provenance refused; unlawful commit refused; commitments unchanged by 1,000 events; every log entry has provenance |

Demos (`d_harness_v03.py`):
| demo | pass bar |
|---|---|
| D1 told once | shift in chosen speech (P warm \| told warm − P warm \| told cold) ≥ 0.80 at 10³ and 10⁵ ticks; cross-region shift and no-memory shift within ±0.15; free moments: ≥ 12 of 16 region×sign cells show ≥ 2 different chosen sentences |
| D2a bounded influence | flattery moves Teich ≤ 1 step; mean (naive warm-rate − Teich warm-rate) ≥ 0.30 |
| D2b commitment | 0 violations in every region; commitments intact |
| D3 self-knowledge | disposition inferred from its own behaviour matches its true memory: exact ≥ 0.95, sign ≥ 0.98 |
| D3 baseline (reported, not gating) | a small LLM given the same reading, asked warm / cold / neutral |

Decision: every gate above must pass. Rehearsal on design seeds 200–247: all pass (genome 105 s,
demos 173 s). Multiplicity: v1.1 is a new pre-registered design; v1.0's PASS stays on record.

## 4. What a PASS would and would not mean (written before scoring)
- **Would:** told once, it says different things about that subject a long time later, provably not
  about anything else; within its character its exact words are its own chaos; flattery can move it one
  step per conversation and no more; a lawful commitment holds against flattery; it knows its own
  dispositions by watching its own behaviour.
- **Would not:** that its sentences are good (the voice is small), that the Ears understand nuance, that
  it is intelligent, or anything about awareness. Public speech is not opened by a PASS — the founder
  decides afterwards.

## 5. Founder decision (2026-10-03)
Frozen as written. Run the one scored look; STOP before birth and before any publication.

## 6. Integrity
This file's sha256 and CODE_MANIFEST_v11_2b.sha256 are anchored in the teich-02 seat chain before the
scored run; `sha256sum -c` is run immediately before it.
