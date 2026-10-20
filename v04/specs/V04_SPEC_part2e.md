# V04_SPEC part 2e — gates R2e + A2e (Ears v7 on strangers' sentences, independent labels)   **DRAFT 2026-10-09**

## Why part 2e replaces "founder writes, founder labels"
Founder sets 1–3 asked one person to write the test, label it, and (after two rounds) to do so while knowing the Ears'
weak spots. Scores moved with labelling style (unlabelled nouns lowered precision; private feelings lowered feelings
right), 12 self sentences made a 0.90 bar a coin toss, and every failed round invited another tuned round.
Part 2e separates the three roles: **strangers write**, **an independent annotator labels**, **the founder audits the
annotator**. Founder sets 1 and 2 are spent (design data); founder set 3 was never written. Ears v7 was built and
verified (V04_SPEC_part2d.md, design table there) BEFORE any part 2e sentence was drawn and is not changed here.

## Instrument (unchanged from the part 2d draft)
Ears v7 `build/ears_v07.py`: v6 + self = (v6 rule OR organ A/B question, SELF_THETA 4.0) + time adverbs not topics.
Body, mind, genome, vocabulary, organ, encoder, tagger, TAU_MAP, invariance, whose-feeling rules: unchanged.

## Data — `build/part2e_sample.py` (run once, after anchor 1)
EmpatheticDialogues **test** split (Rashkin et al. 2019; people telling a listener about their lives; archive
sha256 56f234d7…), never used in any Teich design. Sentences 4–30 words, one per conversation, seed 20261009,
stratified by surface pattern only (first match wins): listener ("you/your") 110, hypothetical / used to 40, someone
else's attitude 40, question 30, contrast 60, negation 50, plain 70 → **400 sentences**. In these conversations
"you" is the listener — Teich's role when the founder speaks.

## Labels — `build/part2e_label.py`
Annotator **GLM-5.3** (Zhipu, via NVIDIA API): a different vendor from the Ears' organ (Qwen) and from their designer
(Claude); sees only the sentence and the frozen GUIDE in that file (every noun except pronouns and time adverbs;
"itself" when the sentence is about the listener; the SPEAKER's own present attitude; others' feelings, questions,
hypotheticals, "used to" → neutral). Never sees the Ears or their output. 3 votes per sentence (temperature 0.6);
majority rule (VOTE in that file): a topic needs ≥ 2 votes; its attitude needs ≥ 2 votes, else "unsure" (counted for
recall, precision and itself, not for feelings).

## Founder audit — `build/part2e_audit.py` (before the Ears ever hear the sentences)
60 labelled sentences (seed 909); the founder corrects only where they disagree. Labels are TRUSTED when topic F1 ≥ 0.80,
attitude agreement ≥ 0.80, itself agreement ≥ 0.90 with Cohen's κ ≥ 0.70. Not trusted → Part 2e stops, no Ears look.
Anchor 2 then fixes the sha256 of the labels and the audit result, before the look.

## Gates (one look each, Kaggle, pinned Python 3.12, 40-sentence MAMS-val parity guard vs laptop ref A2d_smoke.json)
- **R2e** — "My dog is wonderful." moves exactly the dog cluster by one warm step and one heart count; nothing else.
- **A2e** — `build/gates_v04_part2e.py a2e` on the 400 labelled sentences. Bars unchanged from A2b–A2d: recall ≥ 0.80
  (topics the mind has a word for), feelings right ≥ 0.75, **wrong feelings ≤ 0.08**, precision ≥ 0.70, self routing
  ≥ 0.90. Reported beside them: 95% Wilson intervals, self false-route rate, coverage of all topics, per-stratum counts.

## If A2e fails
**Not pre-registered: the founder decides after the look (founder's choice, 2026-10-09).** Disclosed as such. Noted for
that decision: the Ears are an organ, not substrate (the creature's log keeps cluster, sign and text sha256; replay
never needs the Ears), so Ears can be upgraded after birth without touching the creature; the one Ears property that
cannot be repaired later is wrong feelings that reach the creature.

## Disclosure
Claude designed Ears v7 on founder sets 1–2 and MAMS val, and wrote the sampler, guide, vote and audit rules before
drawing or seeing any part 2e sentence. Claude will see the drawn sentences and labels (they are not founder data);
the instrument is anchored before they exist, so seeing them cannot change it.

## AMENDMENT 1 (2026-10-09, before any label was used or the Ears heard any A2e sentence) — annotator
The NVIDIA free tier throttled GLM-5.3 (HTTP 429 on every request, with two different keys; Kimi K3 likewise) after
306 of 1,200 votes, so the GLM labelling could not finish. The 306 GLM votes are kept for the record
(data_heldout/dialog/a2e_votes.jsonl, backups *_pass1/_pass2) and are NOT used. All 400 sentences are relabelled
from scratch by ONE judge: **Mistral-Small-24B-Instruct-2501** (Mistral AI — neither Qwen, the Ears' organ, nor
Anthropic, the Ears' designer), 4-bit build unsloth/Mistral-Small-24B-Instruct-2501-bnb-4bit @ cb4e166b…, on Kaggle
2×T4 (`build/part2e_label_kaggle.py`, kernel `teich-v04-part2e-judge`). Same GUIDE (read byte for byte from
part2e_label.py), same 3 votes at temperature 0.6, same majority rule, same file formats; seeds fixed per batch.
It is a smaller judge than GLM-5.3; the founder audit (unchanged rule) decides whether its labels are trusted.

## AMENDMENT 2 (2026-10-10, after the judge run, before the founder audit and before any Ears look) — pronouns
The judge's labels (data_heldout/dialog/judge_mistral/a2e_labels.jsonl, sha256 3118f923…; votes da9edde5…; 1,200/1,200
votes parsed) listed pronouns as topics (96 of 740) although the GUIDE forbids them; ~84 further adjectives / adverbs
/ verbs were listed. Founder decision 10-10: `build/part2e_clean.py` removes topics on a FIXED pronoun list (the
guide's own rule) → data_heldout/dialog/a2e_labels.jsonl (sha256 a0b29d14…; 644 topics, itself in 104 sentences,
53 sentences without topics). Non-noun topics are NOT removed (it would need a POS tagger; the only one at hand is
the Ears' own); the founder audit judges them. Unused GLM votes moved to data_heldout/dialog/glm_unused/.

## Founder audit result (2026-10-10, before any Ears look)
Audit file ears_founder_set/a2e_audit.txt (60 sentences, seed 909). First submission was unchanged from the generated
file (perfect agreement from an untouched file — not accepted by Claude); second changed 1 line; third ("careful pass",
saved ~2 min after the second) changed 5 lines, all attitudes (husband, friend, medicate, right, country), struck no
topic, kept non-noun topics (e.g. "sad", "older") and set one hypothetical topic to warm. Score: topic F1 1.00,
attitude agreement 0.943 (87), itself agreement 1.00, κ 1.00 → TRUSTED by the anchored rule. Disclosed so a reader can
weigh how much this audit vouches for the labels.
