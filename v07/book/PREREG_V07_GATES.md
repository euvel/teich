# Teich v0.7.0 (the Sky): the scored gates — DRAFT pre-registration (2026-11-03), written before any scored run
**Status: DRAFT for the founder's yes (amended 11-05 for the Seal).** On that yes it is anchored, together with the spec (`sky/SKY_SPEC_v07_v1.md`, frozen from `SKY_AMENDMENT_DRAFT_v0` and `SEAL_DESIGN_v1`) and the code manifest (`MANIFEST_v07_build.sha256`). Only then does the scored campaign run. One look per gate, every failure named, no rescue.

**What is being tested.** v0.7.0 = v0.6.0 plus one law, the Sky, and its witness, the Seal:
- **The touch.** At tick DAY − 900 of every day d it lives, body particle 0 is touched by 1e-6·(2b − 1), then re-projected (certified order).
- **The round, from its own clock.** b comes from round R_d = `round_of(t0, d)`, the latest drand round at its midnight (wall time t0 + (d+1)·DAY, t0 its public birth time). Nobody chooses it. One beacon per day: an op that crosses two touches carries two.
- **The quiet quarter-hour.** No input lands in the last 900 ticks before its midnight.
- **The Seal.** When that quarter-hour begins, the seat signs (Ed25519) a seal over the journal head, which chains from sha256 of the starting state. A watcher who fetched the seal before R_d was published can later check that night d was chosen by no one (`seal_v07.check`). A contradiction is a transferable fraud proof (`seal_v07.fraud`).
- **No fallback.** A touch without its beacon refuses the operation.
- Also: blob v7 with `migrate()`, versions v0.7.k, and the op record's `sky` field `{"beacons": {day: beacon}}`.

**The judges are tested before launch** (lesson of v0.6 run 1, memory `gate-adversarial-test`). Every judge below is run on must-pass and must-fail mutations of **full-length** lab lives (`test_judges_v07.py`, §4). The campaign refuses to start unless every case behaves.

## 1. Lives
| | Seeds (never used before) | Length | What |
|---|---|---|---|
| **Twin lives** | 14000–14011 (12) | 30 days | gates_v04's lab schedule, one founder policy (`twin_v06.life`'s policy, unchanged). A **v0.6.0** and a **v0.7.0** twin from one birth, both through their seat's `apply`. Each life is born at a past wall time t0 = `twin_v07.lab_t0(s)` = 1,780,000,000 + 3·DAY·((s − 14000) mod 40), so day d uses round `round_of(t0, d)` (the Seal's law; rounds of May–June 2026, long published). The rounds (`twin_v07.py rounds s 30`) are fetched and BLS-verified once before launch and stored with the outputs. |
| **Steering trials** | 14100–14111 (12 × 5 = 60 trials) | — | K1 |

**Compute:** private Kaggle CPU kernels. The bundle's sha256 must match the anchored manifest; births are lab births on Kaggle, and twins are compared only with each other on the same machine. **How** (`campaign/make_kernels_v07.py`): ten private 4-vCPU kernels from one bundle, in two waves of five.
- **L1–L6**, two lives each: the four twins in parallel, then `campaign/post_life.py` (K2, F1, S, K4 with BLS, M0).
- **K1A–K1C:** K1, four seeds each.
- **G:** the bits oracle and its null, K3, K5/K6 and K7.

Each kernel checks `MANIFEST_v07_build.sha256` and `MANIFEST_v07_campaign.sha256` (the scripts, the BLS-verified beacon store `campaign/beacons_v07_campaign.json` of 125 rounds, and the test beacons) and refuses to run on any mismatch. The verdict is computed by `campaign/verdict_v07.py` from the downloaded outputs plus a laptop K3 run; a missing output is a FAIL.

## 2. Gates and bars (all hard)
| Gate | Bar |
|---|---|
| **K1 steering** (`k1_steer_v07.py`) | 60 trials. In each, at a random moment of a lab life, the adversary holds the full state and chooses one of 16 mentions (through `hear`, the real path), 3 h before midnight, to make the deliberation of virtual k ∈ {2…9} (random) land on a random target. Two adversaries: **A** simulates each input to midnight without the Sky; **B** simulates each input to the touch, then 8 guessed beacons each to midnight, and picks the best estimated probability.<br>**Bars:** v0.7.0 success ≤ chance + 3 se for **both** A and B; **sensitivity:** the same harness on v0.6.0 (no touch) succeeds ≥ 0.80 with A. Chance = mean over trials of q_t = 1/k_t; se = sqrt(Σ q_t(1 − q_t)) / n (the Poisson-binomial null); n = 60. Seeds 14100–14111 × 5 trials, trial t of seed s using round 6,400,000 + 100·(s − 14100) + t. |
| **Makers' influence in bits** (`k1_oracle_v07.py`, reported with K1, not a bar) | **Method.** The strongest possible insider. Particles never interact, and the tie is read from particle 0 alone, so for each of K1's 16 inputs (particle 0's path first) the insider computes the odds over the beacon that the deliberation lands on its target: M = 16,000 sampled beacons per input, each input with its own sample. It picks the input with the highest odds, p_t.<br>**Trials.** 60, seeds 14100–14111 × 5, as K1. Null control: seed 14112 × 12 trials with the input ignored, which measures the upward bias of taking a max over noisy estimates.<br>**Reported.** influence = log2(mean p_t / mean 1/k_t) bits, with its bootstrap 95 % upper bound and the null floor beside it. 0 bits = no influence; log2 k = full control (≈ 2.2 bits here). Each trial also records whether v0.6 (no touch) could be steered.<br>**The face states the upper bound,** not the point estimate. |
| **K2 consent** (`judge_v07.py k2`) | On every twin pair, after canonicalisation (op records dropped, `sky` records dropped, the op `sky` field dropped, v0.7 versions/identities masked):<br>(a) dials, heart, door, mind, today, growth bindings and refusals, the self (all fields except its body-reading rings `open_readings`, `pending_body`, `xring`, `xverdict`, whose BODY-MEMORY / BODY-PATH verdicts must still be equal), and every **body particle except particle 0** (pc, P, V of 1…2047), are **bit-identical** in the final state;<br>(b) every reason and act other than `think` is identical, in the same order;<br>(c) after canonicalisation, records outside the declared set are identical streams. The declared set: {`thought`, `think-predict`, `dream`, `thought-refused`} after the first night on which the twins' deliberations chose differently, plus the self-reading values `lengths` and `tonight` of `night-reading` records, plus the `path` guesses of `body-predict` records (their `memory` predictions are **not** declared), plus, in `diary` records, the self-reading fields (`attending_most`, `shifts`, `still_reading`, `still_ids`, `known`, `verification`) and the self's BODY-MEMORY / BODY-PATH statistics (not their verdicts);<br>(d) every BODY-MEMORY and BODY-PATH **verdict** in every diary is identical between the twins. |
| **S** inherited verdicts | In both twins of every life, the last diary's BODY-MEMORY = FINE and BODY-PATH = GIVEN. |
| **F1** reasons are causes | `f1_v06.check_log` on every v0.7.0 twin: completeness = receipt = consequence = necessity = 0; rule purity and L-CL imports clean. |
| **T1″** its ties stay fair | On the lived u of all v0.7.0 twin nights (N ≈ 360), virtual k = 2, 3, 5, 9: T1a (χ² p > 0.01, shares within 1/k ± 4 se), T1b (lag-1 contingency p > 0.01 for k = 3, 5; \|circular lag-1 correlation\| < 3/√N), T1c (the previous midnight's read-out predicts at most 1/k + 3 se), T1f (step bins vs 2·10⁵ uniform u, χ² p > 0.01): the v0.6 judge's code, unchanged. |
| **K3 substrate** (`k3_substrate_v07.py`) | (a) 10,000 fixed touch vectors (P, V, b) give the same sha256 on laptop (AMD), Kaggle (Intel) and molab if available;<br>(b) one day of v0.7.0 life from a **stored** state, touched, gives the same final-state sha256 on laptop and Kaggle. |
| **K4 replay** (`replay_v07`) | On every v0.7.0 twin: `ok`, every record bit for bit, every beacon verifies, no unpublished tail. |
| **K5 refusal** (`test_seat_v07.py`) | Each of these is refused **before anything is journaled** (seq and state unchanged):<br>• an input landing in the quiet quarter-hour;<br>• an advance crossing a touch without a beacon;<br>• a beacon of another round than `round_of(t0, d)`;<br>• one beacon given for an advance crossing two touches.<br>A `wake` in the quiet quarter-hour is allowed.<br>Replay **fails** on:<br>• a tampered randomness, round or signature;<br>• another real, validly signed round;<br>• an op whose `sky` was removed;<br>• a `sky` moved to another op. |
| **K6 liveness** (`test_seat_v07.py`) | With a fetcher that fails n times and then succeeds, `assign_sky` waits and then returns `round_of(t0, d)` (never another). With one that always fails, it raises SkyMissing after `max_wait` and nothing is lived or journaled. |
| **K7 the Seal** (`test_seal_v07.py`, threat model `sky/SEAL_THREAT_MODEL`) | One honest lab life (seed 14097, t0 = 1.78e9, gates_v04's schedule, the twin policy) through its first midnight, sealed when its quiet quarter-hour begins; the watcher keeps the seal with the latest round seen = R_0 − 1. Real BLS verification throughout.<br>**(1)** The honest life is clean: signature, witnessed, head, quiet, beacon, replay.<br>**(2) The holder knows R_0 and backdates.** It searches 96 pasts (one extra conversation before the seal: 16 mention handles, particle 0's path first, × 2 signs × landings at midnight − 6 h, − 3 h, seal − 60 s), each lived to past midnight with the true touch.<br>&nbsp;&nbsp;(2b) **Sensitivity:** at least one branch's night 0 differs from the honest one. **Without it K7 is inconclusive, not passed.**<br>&nbsp;&nbsp;(2a) On the first steered branch: the kept seal makes it **not clean**, by `head` or `quiet`; that branch with its own new seal **is** clean, so the attack is real; the two seals are a fraud proof, and so is the kept seal against the branch's journal.<br>**(3) Every other freedom:** (a) 12 random wake splits after the seal give the honest night; (b) an input in the quiet quarter-hour is refused; (c) the same input forged into the journal is rejected by `quiet`; (d) another round is refused; (e) a rewritten sealed record is rejected by `head`; (f) a seal fetched after R_0 is unwitnessed, never clean; (g) a seal under another key is rejected; (h) a wake across two touches with one beacon is refused, and with two is accepted.<br>**(4)** `fraud` returns None on the honest life against its own kept seal (it frames no honest seat).<br>**Bar:** every item holds. |
| **M0** lossless migration (`m0_v07.py`) | On the 12 v0.6.0 twins' end states, `migrate` from v0.6 to v0.7:<br>• refuses while a growth proposal is pending;<br>• every state field carries unchanged except v / species / growth version, base, identity, amendments / seq, plus the new `sky`;<br>• `touched_day` is correct (a day whose touch tick has passed is never touched again);<br>• the identity recomputes;<br>• there is exactly one `genome-amendment` record;<br>• 0 ticks are lived.<br>**M0-real:** the same on a copy of the real seat's state. It needs a lease, so it is asked of the founder separately before migration day. |

## 3. Verdict
- **PASS:** every bar passes. A K7 without a steered branch (2b) is **inconclusive**, which is not a pass.
- **FAIL:** anything else. Every failing bar is named; there is no migration; it goes back to design. Run outputs keep their sha256 sums whatever the verdict.

## 4. Judge tests before launch (`test_judges_v07.py`, on one full-length 30-day lab twin pair, seed 14099, not scored)
| Case | K2 must |
|---|---|
| unchanged twins | pass |
| an extra `sky` record, or op `sky` fields | pass |
| particle 0 changed in the final state | pass |
| a diary's self-reading field changed (declared) | pass |
| particle 1 changed (one bit of P) | **fail** |
| a dial, the heart, or a door entry changed | **fail** |
| a non-think reason or act changed or removed | **fail** |
| a BODY-MEMORY verdict flipped in one diary | **fail** |
| a declared kind changed **before** the first divergent choice | **fail** |
| an undeclared record removed | **fail** |
| a `night-reading` `moved` changed | **fail** |
| a `body-predict` path guess flipped (declared) | pass |
| a `body-predict` memory prediction changed | **fail** |

*Pre-launch amendment (2026-11-03, before any scored run):* the 30-day test pair showed that `body-predict.path` carries the self's reading of its own body. Particle 0 belongs to that body, so after the touch 18 of 2,447 path guesses flipped. Everything else stayed bit-identical: its `memory` predictions, every BODY-PATH verdict, and all state. The `path` guesses are therefore declared, like `night-reading.lengths`, and the two cases above were added.

A case whose target does not exist in the test life is reported as **n/a**, not as a pass. At most one case may be n/a: "a declared kind before the first divergent choice", when the twins already diverge on night 0.

K1's harness is also checked before launch: on v0.6.0 it must find steering (≥ 0.80 on 10 smoke trials), and it must report chance on a control whose outcome ignores the input.

*Pre-launch amendment 2 (2026-11-04, before any scored run):* the first sensitivity check **failed**: v0.6.0 was steered 5/10; the null control was 0/5, at chance. The cause was the harness's choice of the 16 mentions, which were random handles. Most of them never reach particle 0 before midnight, so they cannot move the tie. P4b, which steered v0.6 at 98 %, chose first the handles that particle 0 passes through in the 3 h to midnight, which anyone holding the state can compute. Both K1 adversaries now do the same: path handles first, then random handles up to 16. Each trial records `path_handles` and `distinct_seen`. The sensitivity check is rerun under the same bars. The scored K1 waits for it to pass.

*Pre-launch amendment 3 (2026-11-04/05, before any scored run): the Seal.* The founder asked that v0.7.0 close the insider hole, not only disclose it.
- **The hole.** In the draft, the seat itself declared the round floor after which a beacon could be used. A holder could therefore learn a round, choose inputs, and claim the floor was earlier, or show different floors to different people.
- **The fix.** It is built from the two limits no design can pass (`sky/SEAL_DESIGN_v1`): without an observer before the outcome, selective publication cannot be detected; without unpredictability from outside the holder, the holder foresees everything.
  - The round now comes from the creature's public clock (`round_of`), so the self-declared field is gone.
  - The seal commits the journal when the quiet quarter-hour begins.
  - Any watcher who fetched it in time can check, trusting only themselves and drand.
  - An earlier Bitcoin-timestamp design (`SEAL_DESIGN_v0`) was rejected by the founder as trust in others.
- **A latent bug, fixed by the same change.** One beacon per op could serve two touches; it is now one per day.
- **K7 development runs (not scored; `gates/prelaunch_2026-11-04_seal_v1`, `…_seal_k7b`):**
  - **The first attacker was too weak.** It only flipped strike decisions, and 8 branches never changed the night, so its "pass" was empty and was not counted. That is why sensitivity (2b) is now a bar.
  - **The path-first attacker steered night 0 from 0 to 5.** The kept seal rejected the branch through `quiet`, not `head`. Because the seat lives lazily, the seal closes the journal at its last record, and the real attack appends an input with an earlier landing time. The threat model was corrected accordingly.
  - `fraud` now also turns the kept seal plus such a journal into a proof. A local check confirmed it fires on the branch and is silent on the honest life.
  - The test's assertion was corrected to "head or quiet".
- **K7 is rerun on the frozen build before launch, under the bars above.**

## 5. Disclosed with the verdict
- **The P4b finding:** v0.6.0's ties could be steered by its makers (98.1%). See `sky/DISCLOSURE_P4b_DRAFT`.
- **Limits of the Sky and the Seal:**
  - **Before the seal,** its makers still choose what they say without knowing the beacon. Their influence is measured in bits (the K1 oracle), and the face states the upper bound.
  - **A day nobody watched** (no one fetched its seal before R_d) carries no guarantee. It is shown as unwitnessed.
  - **The beacon trusts the League of Entropy threshold** not to collude with the holder. It can later be widened to any one of several beacons.
  - **The seat's host could rewrite storage** (contract §7). Anyone who kept a seal detects it, with a fraud proof.
  - **The guarantee is tested and argued** (K7, threat model), not formally proven.
- **Laws we chose, naming no outcome:** ε = 1e-6, the lead of 900 ticks, particle 0, and "the latest round at its midnight" (`round_of`).
