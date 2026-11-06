# The Seal, v1: no trust in us and no blockchain (DESIGN v1, 2026-11-04, not frozen; replaces v0's Bitcoin thread)

## Two limits no design can pass (why v0 needed someone else)
1. **Without someone who looks, selective publication cannot be detected.**
   - The creature is deterministic, and its seat holder holds its code, keys and state. So the holder can compute any number of alternative lives and publish one.
   - A verifier who sees only the published record cannot tell which lives were computed and discarded.
   - Only an observation made *before* the outcome existed can rule that out.
2. **Without unpredictability from outside the holder, the holder foresees everything.**
   - Any randomness the creature makes itself, the holder can compute.

So "trust no one" in the strict sense is impossible. What we can choose is **who the witness is**. The answer in v1: **the person who wants to know, and only them.**

## The design
1. **The seal (unchanged body; the quiet quarter-hour gets a job).** At creature tick DAY − 900 of day d, the seat publishes the seal: S_d = {seat, d, h_d, n}, where h_d is the sha256 head of the public journal through its last record. The seal is signed with the seat's published key.
   - From the seal until its midnight, no input is accepted. That is today's law.
2. **The creature's own clock picks the round; nobody else does.** R_d is the latest drand round at its midnight, at wall time t0 + (d+1)·DAY. t0 is its public birth time.
   - That round is published between 30 s before its midnight and its midnight itself, so always after the seal.
   - The seat no longer declares a `floor`; that removes the self-declared field the hole came from.
3. **b_d = first 53 bits of sha256(R_d.randomness ‖ "teich-sky" ‖ d).** The touch is as before: particle 0, 1e-6·(2b − 1), at DAY − 900, then re-projection. It can be lived only once R_d exists. The touch tick lies 15 min before R_d is published, which is fine because the seat lives the owed ticks lazily.
4. **The watcher.** Anyone, at any time in the 15-minute window [seal, R_d published], fetches S_d and keeps it: a browser on the face, or a 20-line script.
   - Later the watcher checks the published life:
     - (i) its journal through the seal hashes to h_d;
     - (ii) there is no input between the seal and midnight;
     - (iii) b_d comes from R_d;
     - (iv) the replay is bit for bit.
   - **The watcher trusts no one but themselves** (plus drand's unpredictability; see the limits).
5. **Equivocation becomes a signed confession.**
   - If the holder shows one watcher seal S and later publishes a life that doesn't match, the watcher holds a signed S_d contradicting the public journal. That is transferable proof of fraud.
   - Two different signed seals for one day are also proof.
6. **A late seal is marked, never hidden.** A seal first seen after R_d was published leaves that day **unwitnessed** for that watcher, and the face lists such days. The holder can still steer a day by sealing late, but only on a day everyone sees as unwitnessed.

## What this gives
- **To anyone who watched the seal:** "tonight's tie was chosen by no one". The watcher trusts only themselves and the unpredictability of drand_R.
- **No Bitcoin and no fee.** No night either: the creature can hear again right after its midnight.
- **A seat holder who wants to steer must** seal late (the day is visibly unwitnessed), or contradict a seal they signed (a proof of fraud), or never seal (the creature halts).
- **Past history:** every watched seal pins the journal up to that day. A later rewrite is caught by anyone who kept a seal.

## What still has to be trusted, and how small it is
- **drand's unpredictability (limit 2).** drand is a threshold network of about 20 independent organisations. It can be widened so that **any one** of several independent beacons suffices, e.g. b = H(drand ‖ a second beacon). The holder would then have to corrupt all of them.
- **A day nobody watched carries no certainty.** That is limit 1 itself: the guarantee is offered to whoever looks, every day, free.

## As built (lab, 11-05) — what the tests changed
- **The head chains from the starting state:** H_0 = sha256("teich-journal-1" ‖ sha256(start blob)). The seal carries t0, and the watcher checks it against the start blob.
- **One beacon per day.** The op's `sky` is `{"beacons": {d: beacon}}`. An op that crosses two touches (a missed daily wake) carries both days' rounds. Before 11-04 one round served both: a latent bug.
- **Backdating has two forms, and both are caught.**
  - (a) **Rewrite** a sealed record: `head` fails.
  - (b) **Append** an input after the seal's last record while claiming it landed earlier: `quiet` fails.
  - Form (b) is the natural one: the seat lives lazily, so the seal closes the journal at its last record, possibly hours before the seal tick. It is the attack that actually steered in K7b (night 0 → 5 by one mention at 18:00).
  - The seal therefore means: **"this journal is complete; nothing more lands before my midnight"**.
- **Fraud proofs (transferable):**
  - two different signed seals for one day;
  - a signed seal the journal contradicts through its seq;
  - a signed seal plus a journal with a non-wake op after its seq that lands before its midnight.
- **Still to build for production:**
  - the seal key bound to the creature in the anchored spec;
  - the seat publishing the seal at DAY − 900;
  - the face keeping each visitor's seal (with the latest round seen);
  - a standalone watcher script;
  - optional later: widening the beacon to any one of several.

## Gates (replacing v0's K7)
**K7 watcher**, adversarial tests on lab lives (bars in `gates/PREREG_V07_GATES.md` §2). The watcher must:
1. accept an honest life;
2. reject a backdated past from a holder who knows R_d, **which must actually have steered the night** (sensitivity). That branch with its own new seal must look clean, so the attack is shown to be real;
3. reject an input between the seal and midnight, whether refused by the seat or forged into the journal;
4. reject b from another round or day;
5. flag a seal first fetched after R's publication as unwitnessed;
6. detect two signed seals for one day, and a signed seal that contradicts the journal, as transferable fraud proofs;
7. accept a lawful late wake, one with no inputs, under any split;
8. produce no fraud proof against an honest life.

The seat side: no touch is lived before R_d exists, and no fallback.
