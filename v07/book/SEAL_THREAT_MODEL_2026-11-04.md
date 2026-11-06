# The Seal: threat model and attack-by-attack check (2026-11-04, lab)

## The claim
To a watcher W who kept day d's signed seal, fetched before round R_d = round_of(t0, d) was published, the tie of night d was chosen by no one, its seat holder included. If every check in `seal_v07.check` passes, the night was decided by:
- the journal through the seal, which is fixed before R_d existed, plus
- R_d, which nobody chooses and nobody knew in advance,
- through a computation in which no free choice remains.

**What W trusts:** their own observation (they fetched the seal before R_d was published), sha256, Ed25519 (only for fraud proofs that convince third parties), and that drand's R_d was not known to the holder before its publication.

## The adversary
The seat holder. It has every key, all code and state, unlimited compute and every input. It controls the seat, the face, the timing of every operation and what each viewer is shown, and it can run any number of private copies.

## Every freedom it has, and what removes it
| # | Freedom / attack | Removed by | Lab test |
|---|---|---|---|
| 1 | Choose inputs **before** the seal, knowing the state but not R_d | Nothing removes this; the Sky makes it worthless. Its influence is measured in bits by the oracle insider. | K1, k1_oracle |
| 2 | **Backdate**: learn R_d, then choose inputs and claim they were earlier | Two forms, both caught. (a) **Rewrite** a sealed record: another head (`head`). (b) **Append** an input after the seal's last record but claim it landed earlier (the lazy seat makes this the natural form): the seal closed the journal at its seq, so an op after that seq which is not a wake and lands before midnight fails `quiet`, and the seal plus the journal is a transferable fraud proof. Corrected 11-05: K7b showed form (b) is the real attack and `quiet`, not `head`, catches it. | K7 v1 strike flips (a); K7b (b): 96 branches, night steered 0→5 by one mention at 18:00, kept seal rejects by `quiet`, the branch with its own seal looks clean, the two seals are a fraud proof |
| 3 | **Equivocate**: show W one seal and publish another branch | The branch it publishes contradicts W's signed seal, which is a transferable fraud proof. Two signed seals for one day are also a proof. | K7 #2 (fraud proofs) |
| 4 | An **input in the quiet quarter-hour** (after the seal) | The seat refuses it. If it is forged into the journal anyway, W rejects it (`quiet`) and replay refuses it. | K7 3b, 3c; K5 |
| 5 | **Choose another round** | round_of(t0, d) is fixed by its public birth time. The seat refuses any other round, and W checks it. | K7 3d; K5 "another round"; K5 replay with another real round |
| 6 | **Split the post-seal life differently** (where its wakes fall) | The outcome is invariant under splitting (6 plans, 1-tick splits included: identical state and records). | chunk test 11-04; K7 3a (12 random splits) |
| 7 | **Rewrite sealed history later** | head ≠ seal.head. | K7 3e |
| 8 | **Seal late** (after R_d is out) | W marks the day unwitnessed, never clean. | K7 3f |
| 9 | **Use another key** for the seal | `signature` fails. | K7 3g |
| 10 | **Cross two touches with one round** (latent v0.7 bug, fixed 11-04) | One beacon per day, each with its own round. | K7 3h; K5 "two touches one beacon" |
| 11 | **Swap the starting state** | The head chains from sha256(start blob). | by construction (`head`) |
| 12 | Choose **which machine or numpy** lives the night | W replays on their own machine, and K3 shows the result is the same across machines. A difference would make W reject, never steer. | K3 |
| 13 | **Show different branches to different viewers** (split view) | Each watcher's own branch is unsteered. Branches differ only if the holder sends conflicting signed seals, and any two watchers comparing hold a proof. Every face visitor keeps the seal, so the holder cannot tell watchers from viewers. | design (face keeps seals) |
| 14 | **Halt**: refuse to seal or to continue | It cannot choose an outcome. The creature stops, visibly. | K6 (no fallback) |
| 15 | **Kill the day after seeing R_d** and live an alternative | No alternative exists: the journal past the seal is forced, and a new branch needs a new seal (#3). | K7 #2 |

## Not covered (stated with the verdict)
- drand's threshold being corrupted together with the holder (limit 2). This can be widened with an any-one-of-several beacon.
- A day nobody watched (limit 1).
- Its makers choosing what to say before the seal: #1, bounded in bits.
