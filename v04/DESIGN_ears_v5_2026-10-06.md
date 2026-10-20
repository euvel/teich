# Ears v5 — plan (2026-10-06, after part 1: A1b FAIL, cluster 49%, sign 96%)

## Cause
v0.4 Ears hear one topic per sentence; real text carries several, each with its own attitude.

## Design
1. **Every topic in a sentence.** Candidates by rule (deterministic): every word that is one of our 1,066 concepts
   (lemmatized), plus noun heads mapped to the nearest concept by MiniLM when similarity clears a threshold. One mention
   per topic: attention +1 on its cluster, attitude toward it to the heart (laws unchanged).
2. **Attitude per topic** by the proven target-aware organ (Qwen2.5-1.5B, log-prob positive vs negative; 96% scored).
3. **Abstain when unsure** (founder 10-06): a noun too far from any concept, or an attitude inside a weak band, is
   logged "unheard" (topic) / "no sign" (attitude) and moves nothing. Precision first.
4. **Hard cases handled explicitly:** negation, questions (attention without feeling), several sentences, self mixed
   with other topics.
5. **Veto-only read-back** (founder 10-06): before memory is touched the founder sees what was heard and may strike
   mentions out, never add. Vetoes are logged. Removal can only reduce influence.
6. **Repeatable:** organ revision pinned, greedy, the version recorded with every mention.
Organ stays 1.5B (founder 10-06).

## Data discipline
| data | role |
|---|---|
| SemEval-2014 train; the spent A1b subset; MAMS train + val; Claude-written probe sentences | design and tuning only |
| **MAMS test** (multi-aspect, multi-sentiment) | new public gate **A2a** — counts checked only, never read before the scored run |
| **founder set**, multi-topic format `sentence \| food:warm, price:cold` | founder gate **A2b** (spec part 2) |
| dog demo, self routing | regression |
Metrics per gate: topic recall, attitude accuracy on heard gold topics, **precision** (own bar).

## Steps
1. Design and tune v5 on design data (laptop). 2. Freeze part 2 (code, data hashes, bars), anchor as part 1.
3. Founder writes the set (can start now). 4. One scored look → birth only on the founder's word.
