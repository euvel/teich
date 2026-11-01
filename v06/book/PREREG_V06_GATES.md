# Teich v0.6.0: the scored gates (pre-registered 2026-10-31, before any scored run)
**Status:** FROZEN CANDIDATE, for the founder's yes. On that yes it is anchored, together with the spec (`V06_SPEC_v1.md`) and the code manifest (`MANIFEST_v06_build.sha256`). Only then does the scored campaign run. One look per gate. Every failure is named. No rescue.

## What is being tested
v0.6.0 = v0.5 plus one law: **exact ties in its chosen thought are broken by its deliberation**, which starts from the read-out u of **its body's particle 0 at the midnight of the choice**, instead of by the lowest index. Its body is substrate-certified. Also: an `organ` field on `heard` records, vA.B.k versioning, the migrator, and the public journal (an `op` record before every seat operation).

**Why the body and not the dream (founder decision 10-31, recon study):** the working surface's dreams are not substrate-certified, so a tie-break read from a dream would depend on the CPU that dreamt it.

## Lives
| | Seeds (never used before) | Length | What |
|---|---|---|---|
| **Twin lives** | 12000–12019 (20) | 60 days | gates_v04's lab schedule. v0.5 and v0.6 twins from one birth, under one founder policy (`twin_v06.life`): questions answered 70%, its region questions tagged `asked`, strikes 12%, door words on days < 20, every growth proposal approved. Policy randomness is seeded by (seed, event), so twins never desynchronise |
| **Planted lives** | 12100, 12101 | 20 days | v0.6 with a hidden cause: the tie-break secretly reads body particle 1 while its reason logs particle 0's u |

- **Compute:** molab CPU (Intel, numpy 2.4.6). The build there must match this manifest, checked by sha256 before the run.
- **Births are lab births on molab.** Birth is not substrate-certified, and the twins are compared only with each other on the same machine.

## Gates and bars
| Gate | Hard | Bar (all 20 twin lives unless stated) |
|---|---|---|
| **N0′** nothing undeclared changes | yes | After canonicalisation (journal `op` records removed, seq pointers renumbered, the declared format changes undone: think@2→think@1 without u, `deliberation` dropped, `organ` dropped, v0.6 versions/identities masked):<br>(a) every record is identical up to the first night where v0.6 chose differently from the index;<br>(b) after it, every record kind outside the declared set {`thought`, `think-predict`, `dream`, `thought-refused`} has an identical stream;<br>(c) think reasons and acts match one to one (act_id, rule);<br>(d) in diaries and state, only keys named `THINK` (and list items of kind THINK) may differ;<br>(e) the final state is identical outside `work`, `growth`, `self.THINK`, `v`, `species`, `seq`, with body, dials, heart, door, Ears map and every non-THINK self field bit-identical;<br>(f) growth bindings and refusals are identical |
| **F1′** reasons are causes | yes | (a) `check_log` on every v0.6 twin: completeness = receipt = consequence = necessity = 0;<br>(b) the planted hidden cause is flagged (receipt + consequence > 0) in **both** planted lives;<br>(c) rule purity and L-CL imports are clean |
| **T1′** T1 inside the real code | yes | On the lived u of all v0.6 twin nights (N ≈ 1,200), for virtual k = 2, 3, 5, 9 with the certified deliberation:<br>**T1a** fair: χ² uniformity p > 0.01, every share within 1/k ± 4·SE;<br>**T1b** not habitual: lag-1 contingency p > 0.01 (k = 3, 5), and \|lag-1 circular correlation of 2πu\| < 3/√N;<br>**T1c** the read-out one midnight earlier predicts at most 1/k + 3·SE;<br>**T1d** a 1e-12 change to particle 0's P[0,1] one day earlier changes the choice at a rate ≥ (1 − 1/k) − 3·SE;<br>**T1e** the exact shadow equals the lived particle's u bit for bit on every night, and so does each night's logged u;<br>**T1f** step bins {0, 1, 2, 3, ≥ 4} match 2·10⁵ uniform u (χ² p > 0.01).<br>Also reported, not barred: the real ties per k (positions; χ² where expected counts ≥ 5); the undecided count |
| **S** inherited self verdicts | yes | in both twins of every life, the last diary's BODY-MEMORY = FINE and BODY-PATH = GIVEN |
| **W0** the public journal replays | yes | `replay_v06(start, records)` on every v0.6 twin: `ok`, every record bit for bit, no unpublished tail |
| **M0** lossless migration | yes | `m0_v06` on the 20 v0.5 twins' end states: `passed` (refusals, exact round trip, only seq changed, growth only version/base/identity/amendments, identity recomputes, exactly one `genome-amendment` record, 0 ticks, F1 0 flags).<br>**M0-real:** the same on a copy of the real seat's state. It needs a lease, so it is asked of the founder separately and is run before migration day |

**Already passed (not re-run):** C0, the certified deliberation (REPORT_C0_2026-10-31; its hash is identical on AMD, Intel Kaggle and Intel molab).

## Verdict
- **PASS:** every hard bar above passes.
- **FAIL:** anything else. Every failing bar is named; the creature is not migrated; v0.6 goes back to design.

## Disclosed with the verdict, whatever it is
- **Reconstruction study (`recon/REPORT_recon_2026-10-31.md`):** the real v0.5 life replays from public records except the 6 dream records, which are substrate-bound.
- **v0.5's daily wake** has run on unpinned numpy 2.5.4 (outside its certified set). Its gate never covered birth or the working surface's dreams.
- **Laws we chose, which name no outcome:** the read-out map and the coverage ρ = 0.6.
