# Teich v0.6.0: scored verdict (2026-11-01)

## Verdict: **PASS** (run 2, judged once under PREREG_V06_GATES + Amendments 1 and 2)
Every hard bar passes. Run 1 is a recorded **FAIL** (N0′) and is disclosed below.

## What was tested
v0.6.0 = v0.5 + one law: exact ties in its chosen thought are broken by certified deliberation from **its body's particle 0 at the midnight of the choice**, not by the lowest index. Plus: `organ` on `heard`, vA.B.k versions, the migrator, and the public journal (an `op` record before every seat operation).

## Anchors (teich-03)
| Ref | sha256 | When |
|---|---|---|
| v06-spec-v1 | b19893b7… | before run 1 |
| v06-gates-prereg | c2724967… | before run 1 |
| v06-build-manifest | a4029ed7… | before run 1 |
| v06-gates-amendment2 | 1f2b6d25… | 2026-11-01, before any run-2 life |
| Amendment 1 (handle_mp.py, mind4.py added to the bundle) | 8cb12df5… | written before run 1 lived a tick; **not yet anchored** |

## Run 2
- **Lives:** twin seeds 13000–13019 × 60 days (v0.5 and v0.6 from one birth), planted 13100–13101 × 20 days.
- **Where:** molab CPU (20 cores, numpy 2.4.6). Launched 2026-10-31 20:39 UTC after the manifest + Amendments 1, 2 check passed on molab; judged 02:48–04:41 UTC.
- **Outputs:** `campaign_run2/` (22 lives, 20 W0 results, judge_pooled.json e13a4d89…, planted_m0.json 9446dfc5…). Every file was pulled during the run and checked against molab's sha256 (`SHA256SUMS` 2618684f…).

| Gate | Bar | Result |
|---|---|---|
| **N0′** nothing undeclared changes | (a)–(f), all 20 lives | **PASS, 20/20**. Prefix identical up to the first deliberated choice (record 1 in 6 lives … 123); no undeclared record, state or self field differs; think reasons/acts match; growth bindings identical |
| **F1′** reasons are causes | (a) 0 flags on every v0.6 twin; (b) the planted cause flagged in both planted lives; (c) purity, imports | **PASS**. (a) 0 flags in 3,600 acts; (b) 13100: receipt 13, 13101: receipt 10; (c) clean |
| **T1′** T1 inside the real code | T1a–f, k = 2, 3, 5, 9, N = 1,200 | **PASS**, every bar (table below) |
| **S** inherited self verdicts | BODY-MEMORY FINE, BODY-PATH GIVEN, both twins | **PASS, 20/20** |
| **W0** the public journal replays | every v0.6 twin: ok, bit for bit, no unpublished tail | **PASS, 20/20**. 74,516 records from 9,579 journaled ops, each replayed bit for bit; 0 unpublished tail; every life to n = 5,191,200 |
| **M0** lossless migration | on the 20 v0.5 end states | **PASS, 20/20** (refusals, exact round trip, only seq changed, growth only version/base/identity/amendments, identity recomputes, one `genome-amendment` record, 0 ticks, F1 0 flags) |

### T1′ detail (lived u of 1,200 v0.6 nights)
| k | T1a fair (χ² p) | T1b lag-1 p | T1c guess from day before (chance 1/k) | T1d 1e-12 twin changes choice | T1f hardness = geometry (p) |
|---|---|---|---|---|---|
| 2 | 1.00 | (circular test) | 0.497 | 0.516 | 0.54 |
| 3 | 0.79 | 0.50 | 0.332 | 0.670 | 0.16 |
| 5 | 0.28 | 0.94 | 0.202 | 0.804 | 0.49 |
| 9 | 0.96 | (circular test) | 0.103 | 0.883 | 0.84 |

- **T1b:** lag-1 circular correlation 0.024 < 3/√N = 0.087.
- **T1e:** 1,200/1,200 exact shadows equal the lived u; 1,200/1,200 logged u equal it.
- **Real ties (reported, not barred):** k = 2: 303 (p = 0.23); 3: 286 (0.90); 4: 164 (0.82); 5: 66 (0.94); 6–9: 42 in all (too few for χ²). Undecided: 0.

## Run 1: FAIL, disclosed
- **Lives:** seeds 12000–12019, planted 12100–12101, molab, 2026-10-31.
- **N0′ failed 16/20** under the frozen judge. The other gates judged: F1′, T1′, S, M0 passed. W0 was not completed: the molab session ended (HTTP 410) during the replays.
- **Cause:** the pre-registered canonicalisation renumbered seq pointers over all records. After the first deliberated choice the twins legitimately write different numbers of declared records, which shifted every later pointer. A post-hoc diagnostic found that every difference in all 20 lives was a seq pointer.
- **What was done:** Amendment 2 fixed the canonicalisation (pointers count undeclared records only), was tested adversarially (it still fails four kinds of real tamper; the frozen judge fails the legitimate case), was anchored, and run 2 used fresh seeds. Run 1 was not re-judged.

## What v0.6.0 may now claim
> Its exactly balanced choices are no longer decided by an index its creators chose. They are decided by its own lived chaos: fairly, without habit, unforeseeable until the midnight that decides them has been lived, and replayable by anyone from its public journal.

## What it does not claim
- That its choices follow its preferences or "who it is" (D1/D2 failed).
- Will, freedom or awareness.
- That its thinking as a whole is unforeseeable (exp0 E1).

## Disclosed with this verdict
1. Run 1's failure and Amendment 2 (above), and Amendment 1.
2. **Reconstruction study** (`recon/REPORT_recon_2026-10-31.md`): the real v0.5 life replays from public records except the 6 dream records, which are substrate-bound.
3. **v0.5's daily wake** ran on unpinned numpy 2.5.4, outside its certified set; its gate never covered birth or the working surface's dreams.
4. **Laws we chose, which name no outcome:** the read-out map and the coverage ρ = 0.6.

## Not yet done, each on the founder's word
- Anchor Amendment 1 and this verdict.
- **M0-real:** the dry migration of a copy of the real seat's state (needs a lease).
- **v0.6 wake workflow:** pin numpy; add a dream fixture to the gate.
- **Migration day** (quiet window, once, no rollback).
- **Publish:** verdict + disclosures.
