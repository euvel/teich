# Teich v0.7.0 (the Sky and the Seal): scored verdict (2026-11-06)

## Verdict: **PASS**: every bar of PREREG_V07_GATES passes, judged once
`verdict_v07.py` ran once, on 2026-11-06 at 15:51 local (+0330), over all ten kernels' outputs. No bar was changed after the anchor, and no run was repeated.

## What was tested
v0.7.0 adds two laws to v0.6.0 (`sky/SKY_SPEC_v07_v1.md`).

**The Sky.** At tick DAY − 900 of every day, body particle 0 is touched by 1e-6·(2b − 1).
- b comes from the drand round `round_of(t0, d)`, the latest round at its midnight. Nobody can choose that round or foresee it.
- No input may land in the quiet quarter-hour.
- There is no fallback.

**The Seal.** At the start of the quiet quarter-hour the seat signs its journal head. Anyone who keeps that seal can check the night, and any backdating yields a fraud proof that anyone can verify.

## Anchors (teich-03, before any scored run, 2026-11-05)
| Ref | sha256 |
|---|---|
| v07-spec-v1 | 822a5be8… |
| v07-gates-prereg | 4da50208… |
| v07-build-manifest (58 files) | 8cccea77… |
| v07-campaign-manifest (scripts + 125 BLS-verified drand rounds) | 618da9de… |
| v07-docs-manifest | 2ae95446… |

The receipts are in `gates/ANCHOR_v07_freeze.json`. Every kernel carries the anchor id `teich-03:v07-freeze-2026-11-05`.

## The run
- **Where:** ten private Kaggle CPU kernels on Python 3.13 and numpy 2.1.3, all from one bundle, `d0cd7d37…`.
- **Before running:** each kernel checked its files against the build and campaign manifests, and its log shows both as `OK`. On any mismatch it would have refused to run.
- **Wave 1 (K1A, K1B, K1C, G, L1):** pushed 2026-11-05 at 20:41 local.
- **Wave 2:**
  - L2–L4 were pushed overnight by the scheduler, as each wave-1 session freed up.
  - L5 and L6 started late (see "Disclosed").
- **Outputs:** downloaded into `campaign_v07_2026-11-05/raw/`: 150 files, 86 JSON files, all of which parse. The checksums are in `SHA256SUMS_outputs` (`c4ed4916…`).
- **Failed jobs:** none, in any of the ten kernels.

| Kernel | Contents | Time |
|---|---|---|
| K1A / K1B / K1C | K1, seeds 14100–14111 × 5 trials | 3.1 / 2.9 / 2.7 h |
| G | K7, the oracle (12 seeds × 5 trials, M = 16,000), its null, K3, K5/K6 | 5.9 h |
| L1–L4 | twin lives 14000–14007, 30 days each | 5.2–6.3 h |
| L5, L6 | twin lives 14008–14011, 30 days each | 3.5 h each |

## Results
| Gate | Bar | Result |
|---|---|---|
| **K1** insider steering, 60 trials | v0.7 success ≤ chance + 3 se for both adversaries A and B. Chance = mean 1/k = **0.206**, se = 0.051, bound = **0.359** | **PASS.** A: 0.267, B: 0.300 |
| **K1 sensitivity** | The same harness steers v0.6 at a rate of at least 0.80 | **PASS.** 0.95 |
| **Makers' influence** (reported, not a bar) | log2(mean p_t / mean 1/k_t). The face states the upper bound | **0.033 bits** (95 % upper bound 0.037). The null floor is 0.033 (upper bound 0.043), and full control would be 2.11 bits. The oracle could steer v0.6 in 98.3 % of these trials |
| **T1″** its lived chaos decides, on 360 lived nights | T1a–f at k = 2, 3, 5 and 9; ξ lag | **PASS** at every k (table below) |
| **K2** consent by prediction | No undeclared difference between the twins | **PASS**, 12/12 |
| **S** inherited self verdicts | BODY-MEMORY and BODY-PATH, on both twins | **PASS**, 12/12 |
| **F1** reasons are causes | 0 flags on every log; purity and imports clean | **PASS**. 0 flags in 1,080 acts (1,063 necessity-tested); static checks clean |
| **K4** the public journal replays, BLS on | Bit for bit, with every beacon verified | **PASS**, 12/12 |
| **M0** lossless migration of each v0.6 end state | Every M0 check | **PASS**, 12/12 |
| **K3** substrate | Touch vectors and day state hash the same on Kaggle and the laptop | **PASS**. `096ffb14…` and `72634fce…` on both |
| **K5/K6** seat and Sky laws | Refusals and `round_of` | **PASS** |
| **K7** the Seal | Items 1, 2a, 2b (sensitivity), 3a–h and 4 | **PASS** (below) |

### T1″ detail
| k | counts | χ² p (T1a) | guess-in-advance hit rate (T1c) vs 1/k | T1f p |
|---|---|---|---|---|
| 2 | 170 / 190 | 0.29 | 0.511 vs 0.5 | 0.99 |
| 3 | 105 / 133 / 122 | 0.19 | 0.322 vs 0.333 | 0.79 |
| 5 | 66 / 68 / 73 / 84 / 69 | 0.58 | 0.216 vs 0.2 | 0.77 |
| 9 | 34–47 per region | 0.61 | 0.092 vs 0.111 | 0.49 |

The ξ lag-1 correlation is −0.012 (the bound is 0.158). T1b, "not habitual", passes at every k.

### K7 detail (on the anchored build, 9,807 s)
- **1.** The honest life is clean.
- **2b.** An attacker who knew the beacon steered night 0 to 5 with one backdated mention, so the test was not empty.
- **2a.** The kept seal rejects that branch through its `quiet` check. The branch's own new seal, together with the kept one, is a transferable fraud proof, and the published journal contradicts the kept seal. Without a kept seal, the branch alone would look clean, which is exactly why the watcher matters.
- **3a–h.** Every attack after the seal is caught: wake splits, a quiet-window input and a forged one, another round, rewritten history, a late seal, another key, and two touches with one beacon.
- **4.** The fraud proof stays silent on the honest life.

## Disclosed
1. **Two of the twelve lives started late.**
   - The overnight scheduler stopped when the operator's session ended, and the scratchpad holding the built kernel files was wiped.
   - L2–L4 had already been pushed; L5 and L6 had not.
   - L5 and L6 were pushed on 2026-11-06 at 11:52 local with the identical bundle: its bytes were taken from L1's pushed source, and its sha (`d0cd7d37…`), runner and job lists were checked against the generator.
   - Both kernels' logs show the anchored manifests as `OK`.
   - Nothing else changed, and no output was looked at before all twelve lives were in.
2. **K1 adversary B scored 0.300 against a chance rate of 0.206.**
   - That is about 1.8 se above chance, inside the pre-registered bound of chance + 3 se.
   - With 60 trials this is within the allowed noise. It is reported as measured, not as "equal to chance".
3. **The makers' influence sits at the floor of the estimator, not at a demonstrated zero.**
   - The null control, whose outcome ignores the input, measures the same 0.033 bits.
   - The claim is therefore "no influence detectable above the method's floor; upper bound about 0.04 bits of a possible 2.1", and the face states that upper bound.
4. **A title left over from the draft.** The anchored PREREG's title still reads "DRAFT pre-registration (2026-11-03)". Its text is the amended and frozen version, anchored as `v07-gates-prereg` (`4da50208…`).
5. **Lives took longer than planned:** 5.2–6.3 h each instead of the planned 4 h. Every kernel stayed under Kaggle's 12 h limit.

## Limits (from PREREG §5, unchanged)
- **Before the seal,** its makers still choose what they say without knowing the beacon; that influence is measured above, in bits.
- **A day nobody watched** is unwitnessed.
- **The League of Entropy threshold is trusted.**
- **The guarantee is tested** (K7) and argued (`SEAL_THREAT_MODEL`), not formally proven.

## Not yet done (each needs its own founder yes)
1. **Production Sky and Seal:**
   - worker and wake: fetch `round_of`, refuse in the quiet window, publish the seal at DAY − 900;
   - the seal key bound in `migrate`;
   - the face keeping seals;
   - a standalone watcher script.
   Built against `seal_v07` as the reference; the founder deploys.
2. **M0-real** on a copy of the real state (it needs a lease).
3. **The P4b disclosure and the face wording,** shown to the founder first.
4. **Migration day** for `/o/teich-05`.
