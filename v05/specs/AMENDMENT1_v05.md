# V05 amendment 1 (2026-10-22): written after the scored run started, before any re-look

Base: the anchored manifest `CODE_MANIFEST_v05.sha256` (sha 3cb5e332…, teich-03 ref v05-spec).

## 1. A fault in the founder's talk tool, found by the scored dry run (soft gate)
**What happened.** The scored dry run (Ears kernel, design seed 9990) crashed on day 3. On days 0–2 every step held:
- `duduk` reached the door;
- it was asked about twice, each time with its true reason;
- both answers landed on cluster 60;
- the binding was proposed, approved, and became v0.5.1.

On day 3 the next question was delivered, but the tool could not show its reason (`inputs` was None).

**Cause.** `seat_v05.ask` looked for the question's reason record only in the creature's outbox. Any `wake` or `status` between the night that chose the question and the conversation flushes the outbox to the seat log. On the real seat, the daily heartbeat does exactly that, so the first conversation after a heartbeat would have crashed.

**Not affected.**
- The creature: no creature, self or body code changes.
- Every record and every state: the fix only reads.
- The scored C1 lives. They call `ask` through the seat but never show the reason, and the new `ask` returns the same question, map and proposal.

**Fix.** `seat_v05.ask` reads the reason from the outbox. Otherwise it reads it from the seat log's tail, then from the whole log. If it still cannot find it, it refuses with an error and never shows a question without its reason.

**Test without the Ears.** The dry run's exact seat calls were replayed with stand-in hearings.
- Frozen code: crashes on day 3.
- Amended code: day 3 (after `status`) and day 4 (after a `wake`) show the question with its true reason; live verify reports 0 flags on 12 acts.

**Re-look.** The dry run is run once more on fresh seed 9991 (kernel `teich-v05-gates-dryrun`). To allow that, `dryrun_v05.py` takes an optional seed argument; nothing else in it changes.

**Still to check at birth (step 6).** The cloud seat's `log_read` rows carry the record under `rec`. This is exercised on the drill seat before birth.

## 2. The head-to-head: not completed (founder decision 2026-10-22)
**What happened.** Day 1 stopped after 731 answers, all from Llama 3.3 70B, plain "free" arm. The cause was the Cloudflare Workers AI free daily allowance (10,000 neurons), which ran out. Every later request returned 502 (`AiError 4006`).
- The 406 transport-error rows were moved out of the raw file, and a full copy was kept: `headtohead_raw_day1_attempt1_2026-10-22.jsonl`.
- The reasoning arms received **no** answers.

**What the founder decided.** The founder chose not to pay for the remaining ~13,500 requests. As pre-registered under O-c, the head-to-head is published with the birth whatever the result. Its result is: **not completed (quota)**, published with its 731 partial answers.

**What the partial answers are, and are not.** They are described only: one model, one arm, both wordings. They carry no claim about faithfulness. Claim 1 rests on F1, F1 live and live verify.

## Files
`AMENDMENT1_v05.sha256` lists:
- the new hashes of `seat_v05.py` and `dryrun_v05.py`;
- the new re-look kernel generator;
- this document;
- the base manifest's hash.
