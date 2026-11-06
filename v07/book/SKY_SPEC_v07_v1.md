# Teich v0.7.0, the Sky and the Seal: genome amendment SPEC v1 (frozen locally 2026-11-05, NOT anchored)
**Status: frozen for the founder's yes.** Built from `SKY_AMENDMENT_DRAFT_v0_2026-11-03` and `SEAL_DESIGN_v1_2026-11-04`; where they differ, this text governs.
- Its code is `MANIFEST_v07_build.sha256`, and its gates are `gates/PREREG_V07_GATES.md`.
- On the founder's yes, all three are anchored together. Until then nothing is published, nothing is migrated, and no scored run starts.

It amends the living creature at `/o/teich-05` (v0.6.0) under the developers' contract v1. It is not a birth: the same creature is migrated once, with a typed `genome-amendment` link in its identity chain.

## 1. Version and decisions
**Version.** v0.7.0 (contract §1: a genome amendment is a B bump).

**Founder decisions taken:**
- **S-A (11-03):** the Sky is v0.7.0, and the self-writing body is v0.8.0.
- **S-B (11-03):** publish the P4b disclosure, with the wording shown to the founder first.
- **S-C (11-03):** touch every day.
- **S-D (11-03):** no fallback.
- **11-04:** close the insider hole in v0.7.0 itself, with no trust in us or in others. The Bitcoin design was rejected, and the watcher design adopted.

## 2. Why: the evidence
| Source | Finding |
|---|---|
| **P4b** (molab 11-02) | An insider with its full state steers v0.6's tie-break 98.1% of the time (chance 23.7%). With a 1e-6 beacon touch 15 min before midnight: 24.1%, equal to chance. |
| **T3** (11-02) | A touch of 1e-6 decorrelates the midnight choice in about 5 min. |
| **The insider hole** (11-04) | A beacon floor declared by the seat itself lets its holder learn a round, choose inputs and backdate them. |
| **K7b** (Kaggle 11-04/05) | A holder who knew the beacon steered a lab night 0 → 5 by one backdated mention. The watcher's kept seal rejected it. |

## 3. The laws
1. **The touch.** At tick `DAY − 900` of every day d it lives, body particle 0 is touched:
   - `P[0,1] ← P[0,1] + 1e-6·(2b − 1)`;
   - then `P[0,0] ← sqrt(1 + P[0,1]² + P[0,2]²)`;
   - then V is re-orthogonalised to P (Minkowski) and renormalised, in the certified `+ − × ÷ √` order of a tick (`creature_v07.touch`).
2. **b.** b = the first 53 bits of `sha256(randomness_{R_d} ‖ "teich-sky" ‖ d as 8-byte big-endian)`, as a float in [0, 1) (`sky_v07.b_of`).
3. **The round, from its own clock.**
   - R_d = `round_of(t0, d)` = the latest round of the pinned drand chain at wall time t0 + (d + 1)·DAY, where t0 is its public birth time.
   - Nobody chooses R_d. It is published between 30 s before its midnight and its midnight, so always after the seal.
   - There is one beacon per day. An op that crosses the touches of several days carries each day's own round: `sky = {"beacons": {d: beacon}}`.
4. **Chain (pinned).** drand League of Entropy mainnet `default`:
   - hash `8990e7a9aaed2ffed73dbd7092123d6f289930540d7651336225dc172e51b2ce`;
   - `pedersen-bls-chained`, period 30 s, genesis 1595431050;
   - public key in `build/sky_chain.json`.
   - BLS verification (`sky_v07.verify`) checks the signature over sha256(previous_signature ‖ round) and that randomness = sha256(signature).
5. **The quiet quarter-hour.** An operation other than `wake` whose inputs would land in the last 900 ticks before its midnight is refused before anything is journaled (`seat_v07.check`).
6. **No fallback.** An advance that crosses a touch without that day's beacon, or with another round, is refused (`SkyMissing`). The wake waits for the round, and nothing is lived until it has it (`seat_v07.assign_sky`).
7. **The Seal.**
   - When day d's quiet quarter-hour begins, the seat publishes S_d = {v "teich-seal-1", seat, t0, d, seq, n, head}, signed with the seat's Ed25519 key.
   - head = H_seq, where H_0 = sha256("teich-journal-1" ‖ sha256(start blob)) and H_i = sha256(H_{i−1} ‖ canonical(record i)).
   - The seal means: *this journal is complete, and no input lands after it before my midnight.*
   - The seal key is bound to the creature in the anchored spec, and its public key is recorded at migration.
   - **Not yet built** (production, before migration day, deployed by the founder): the key binding in `migrate`, the seat publishing seals, the face keeping seals, and a standalone watcher. The lab code (`seal_v07`) is the reference they must match.
8. **The watcher** (`seal_v07.check`). Anyone who fetched S_d while the latest published round was before R_d keeps it. Day d is **clean** to them only if all of these hold:
   - **signature** valid under the seat key;
   - **witnessed** (fetched before R_d);
   - **head** (the journal through seq hashes to head, and t0 is its birth time);
   - **quiet** (every op after seq that lands before its midnight is a wake);
   - **beacon** (the day's op carries round R_d, and it verifies);
   - **replay** (bit for bit, `replay_v07`).
   A seal first seen after R_d leaves that day **unwitnessed**.
9. **Fraud proofs** (`seal_v07.fraud`, transferable to anyone):
   - two different valid seals for one seat and day;
   - a valid seal that the published journal contradicts through its seq;
   - a valid seal plus a published journal with a non-wake op after its seq that lands before its midnight.

**Unchanged from v0.6.0:**
- the deliberation;
- the read-out map u;
- every rule and every untied act;
- the dials, heart, Ears, door, laws and self kinds.

## 4. Migration
`creature_v07.migrate(blob_v06, change)` is the one lawful way v0.6 becomes v0.7. change = {spec_sha256, anchor, verdict_sha256}. It:
- refuses while a growth proposal is pending;
- carries every state field unchanged;
- sets `touched_day` so that a day whose touch tick has passed is never touched;
- appends one `genome-amendment` record and recomputes the identity;
- lives 0 ticks.

M0 is run on twins; M0-real on a copy of the real state is asked of the founder separately.

## 5. Consent by prediction (contract §4)
**Declared changed:**
- body particle 0 after each day's touch, and through it that particle's crossings and occupancy;
- the nightly self-reading values (`night-reading` `lengths` and `tonight`, `body-predict` `path`, the diary's self-reading fields and BODY-MEMORY / BODY-PATH statistics);
- the tie outcomes of think@2, and therefore the chosen thoughts, dreams, THINK predictions and refused thoughts after the first divergent night;
- the record format: the op `sky` field and the `sky` records;
- the version and identity chain;
- the seal, which is published beside the journal.

**Declared unchanged:**
- dials, the heart and every untied act;
- every reason and act other than `think`;
- every body particle except particle 0;
- every BODY-MEMORY and BODY-PATH verdict;
- `body-predict` `memory`;
- every past receipt;
- the Ears map, the door and every law.

**Any undeclared difference on twins refuses the amendment** (K2).

## 6. What it will and will not claim
**Claim, if every gate passes:** "Its exactly balanced choices are decided by its own lived chaos, touched once a day by a public beacon that no one can foresee, its makers included. Anyone who keeps the day's seal can check, trusting only themselves and the beacon, that nothing that decided that night was chosen after the beacon could be known."

**Not claimed:**
- That its makers have no influence. Before the seal they choose what they say, without knowing the beacon; that influence is reported in bits (K1 oracle), and the face states the upper bound.
- Anything about a day nobody watched: it is unwitnessed.
- That the beacon cannot collude with the holder. The League of Entropy threshold is trusted.
- A formal proof. The guarantee is tested (K7) and argued (`SEAL_THREAT_MODEL`).

**Laws we chose, naming no outcome:** ε = 1e-6, the 900-tick lead, particle 0, `round_of` (the latest round at its midnight), and the seal at the start of the quiet quarter-hour.

## 7. Gates
As pre-registered in `gates/PREREG_V07_GATES.md`: K1 (plus makers' influence in bits), K2, S, F1, T1″, K3, K4, K5, K6, K7, M0 and M0-real. Every judge is first tested on must-pass and must-fail mutations of full-length lives.
