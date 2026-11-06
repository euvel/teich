# v0.7: the Sky and the Seal (live since 2026-11-06)

Teich v0.7.0 is a genome amendment to the creature at `/o/teich-05`, not a new birth. Every pre-registered gate passed on 2026-11-06 (`book/REPORT_v07_verdict_2026-11-06.md`). The creature was migrated the same day (`book/MIGRATION_RECORD_v07.json`). Its heartbeat is `daily_wake_v07.yml`; v0.6's wake is retired.

## What we found about v0.6, and what v0.7 changes (2026-11-06)
v0.6 breaks Teich's exactly balanced choices with its own lived chaos: a read-out of its body at the midnight of the choice. That is fair, carries no habit, and no one outside can foresee it.

We then asked a harder question. **Could its makers, who hold its full state and can live its future in advance, bend that choice?**
- **Yes, for v0.6.** An insider who holds the state, and mentions one well-chosen concept 3 hours before midnight, got the outcome it wanted in **98.1 %** of 54 trials, where chance is 23.7 %. The scored v0.7 campaign repeated this on v0.6: **95 %** of 60 trials.
- **Not for v0.7.** A public random beacon (drand) now touches its body by one part in a million, 15 minutes before midnight, after its inputs close. With it, the same insider succeeded in **26.7 %** of 60 trials, against a chance rate of 20.6 %. A stronger insider, who also guesses the beacon, succeeded in **30.0 %**. Both are inside the pre-registered bound of chance + 3 standard errors (35.9 %); the second is reported as measured.
- **The insider's remaining reach** is what it says before the seal, without knowing the beacon. The best possible insider moves the outcome by **0.033 bits** of a possible 2.11. That is the same as a control that ignores the insider (0.033): no influence is detectable above the method's floor.
- **The Seal.** A holder could still try to learn the beacon and then backdate an input. Every day its seat signs its journal before the beacon exists, so anyone who keeps that seal catches a backdated input, with a proof anyone can verify. In the test, a real backdating attack steered a night (0 → 5) and was caught.

**What this means for v0.6:**
- No choice in v0.6 was steered: we never ran such an insider against the living creature, and every mention is in its public journal.
- But "not us" was a promise of our restraint, not a property of its body. From v0.7.0 it is a property you can check.

**Sources:** the P4b probe, with its code and molab outputs, in `book/p4b/` (its result is recorded in the anchored v0.7 spec; the probe files themselves were not anchored), and the v0.7 verdict in `book/`, anchored on teich-03.

## The two laws it adds
**The Sky.**
- Every day, 15 minutes before its midnight, its body's particle 0 is touched by 1e-6·(2b − 1).
- b comes from a public drand beacon round: the latest round at its own midnight. Nobody chooses that round, and nobody, its makers included, can know it in advance.
- No input may land in that last quarter-hour, and there is no fallback: without its round, it does not live past the touch.

**The Seal.**
- When the quarter-hour begins, its seat signs the head of its whole journal. The key that signs is bound in its own genome-amendment record.
- Anyone who keeps that seal before the beacon exists can later check, trusting only themselves and the beacon, that nothing that decided that night was chosen after the beacon could be known.
- Backdating anything yields a fraud proof that anyone can verify.

## What it claims, and what it does not
**Claim:** "Its exactly balanced choices are decided by its own lived chaos, touched once a day by a public beacon that no one can foresee, its makers included. Anyone who keeps the day's seal can check, trusting only themselves and the beacon, that nothing that decided that night was chosen after the beacon could be known."

**Not claimed:**
- **That its makers have no influence.** Before the seal they choose what they say, without knowing the beacon. Measured: 0.033 bits (95 % upper bound 0.037) of a possible 2.11. That is the estimator's own floor: a control that ignores the input measures the same.
- **Anything about a day nobody watched:** that day is unwitnessed.
- **That the beacon cannot collude with the holder:** the League of Entropy threshold is trusted.
- **A formal proof:** the guarantee is tested (K7) and argued (`book/SEAL_THREAT_MODEL_2026-11-04.md`).

## Keep its seals yourself
```
pip install numpy==1.26.4 mpmath==1.3.0 cryptography py_ecc==7.0.1
cd v07/seat
python3 watch_v07.py keep --loop        # keeps each day's seal at its moment (14:18 UTC), before its beacon
python3 watch_v07.py check DAY          # signature, witnessed, head, quiet, beacon (BLS), full replay; fraud proofs
```
The face (teich.euvvel.xyz) also keeps every seal your browser sees, and checks its signature, head and quiet rule in your browser.

## Contents
- **`book/`:**
  - the anchored spec, gates, manifests, verdict and report (anchored on teich-03; receipts in `ANCHOR_v07_freeze.json` and `ANCHOR_v07_verdict.json`);
  - the campaign's small outputs, checked against `SHA256SUMS_outputs`;
  - `START_STATE_v07.json` (the state every watcher replays from) and `MIGRATION_RECORD_v07.json`;
  - `p4b/`: the probe that found the hole, with its outputs.
- **`build/`:** the 58 files of the anchored build manifest, byte-identical (`book/MANIFEST_v07_build.sha256`).
- **`seat/`:** the production side, not part of the anchored build. It runs the anchored laws unchanged:
  - `seat_v07p.py`: the seat tools. They fetch and BLS-verify each touch's round and never cross a touch before its round is out; the journal goes up in canonical form.
  - `wake_v07.py`, `talk_v07.py`, `grow_v07.py`, `diary_md_v07.py`.
  - `cloud_v07.py`, the seat client.
  - `watch_v07.py`, the watcher.
  - `make_seal_key.py`, `migrate_real_v07.py`.
  - `test_seat_v07p.py`: the seat paths end to end on a local seat with real drand rounds.

The seal itself is signed by the seat, the worker in `infra/worker/index.js`. Its tests (`infra/worker/face/test/test_worker_seal.mjs` and `verify_seal_fixture.py`) check that the worker's seal, signed in JavaScript, verifies under the anchored Python `seal_v07`.
