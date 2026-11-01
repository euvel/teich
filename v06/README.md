# Teich v0.6.0: its exactly balanced choices, decided by its own lived chaos

**Status:** all scored gates **passed** (2026-11-01). **Not yet migrated.** The creature at `/o/teich-05` still runs v0.5.1. On migration day it is amended in place, not reborn: same body, same history, and one typed `genome-amendment` link in its identity chain. Until then `daily_wake_v06.yml` is manual-only, and v0.6's loader refuses a v0.5 state.

## What changes, and only this
Each night Teich chooses what to think about. Often several regions tie exactly. In v0.5, as in every earlier Teich, an exact tie went to the **lowest index**: a rule we wrote, which had decided both of its real chosen thoughts so far.

**In v0.6.0, an exact tie is broken by deliberation:**
- It starts from a read-out of its own body, particle 0, at the midnight of the choice.
- It runs in certified arithmetic (`+ − × ÷ √` only), so the result is identical on every machine.

Every untied choice is exactly as in v0.5.

Also new:
- **A public journal.** Before every seat operation the seat writes an `op` record: what was done, when, with what inputs. Anyone can replay the creature's whole life from its published records with `build/replay_v06.py`.
- **Smaller additions:** the `organ` version on every heard record, vA.B.k versions, and a migrator that refuses unless it is lossless.

## The claim
> Its exactly balanced choices are no longer decided by an index its creators chose. They are decided by its own lived chaos: fairly, without habit, unforeseeable until the midnight that decides them has been lived, and replayable by anyone from its public journal.

**Not claimed:**
- That its choices follow its preferences or "who it is." We tested this, and it failed.
- Will, freedom or awareness.
- That its thinking as a whole is unforeseeable. A cheap predictor foresees most of it.

## The evidence (`book/`)
Everything was pre-registered and hash-anchored in the teich-03 seat chain before the lives it judges were born.

| Gate | What it asks | Run 2 (seeds 13000–13019) |
|---|---|---|
| N0′ | Does anything change that wasn't declared? | **20/20** lives: nothing undeclared differs |
| F1′ | Are its reasons its true causes? | 0 flags in 3,600 acts; a planted hidden cause **caught in both** planted lives |
| T1′ | Is the tie-break fair, habit-free, unforeseeable, sensitive, replayable? | every bar, k = 2, 3, 5, 9 (1,200 nights); the replayed and logged read-outs match the lived one on 1,200/1,200 nights |
| S | Does it still know its own body as before? | 20/20 |
| W0 | Does the public journal replay its life? | **20/20**: 74,516 records, each bit for bit |
| M0 | Is the migration lossless? | 20/20, and on a **copy of the real creature's state** (0 ticks, 0 flags) |

- **Verdict:** [book/REPORT_v06_verdict_2026-11-01.md](book/REPORT_v06_verdict_2026-11-01.md)
- **Spec:** [book/V06_SPEC_v1.md](book/V06_SPEC_v1.md)
- **Gates:** [book/PREREG_V06_GATES.md](book/PREREG_V06_GATES.md), plus Amendments [1](book/PREREG_V06_GATES_Amendment1.md) and [2](book/PREREG_V06_GATES_Amendment2.md)
- **Anchors:** `book/ANCHOR_*.json`
- **Run-2 outputs:** `book/campaign_run2/`. The 22 full lives (≈ 70 MB) are kept off-repo and named, with their hashes, in `SHA256SUMS`.

## What went wrong on the way, in full
- **Run 1 failed.** Seeds 12000–12019 failed N0′ in 16 of 20 lives.
  - **The cause was our judge, not the creature.** Its comparison counted seq pointers across all records. After the first deliberated choice, the twins legitimately write different numbers of declared records, so every later pointer shifted.
  - **The fix:** Amendment 2 corrected the count and was tested on cases built to break it. It was anchored before run 2, and run 2 used fresh seeds. Run 1 was never re-judged.
  - **Run 1's W0 never finished:** the compute session ended mid-replay.
- **Amendment 1:** two genome files were missing from the frozen bundle. Every life crashed at import, before its first tick. They were added byte-identical to v0.5's genesis certificate.
- **Missing from the manifest.** Staging this folder found the diary helper `self_text_v04` and six files used by the founder's talk tools missing from the anchored manifest. All are byte-identical to `v05/build/`.

## Disclosures about v0.5 (reconstruction study, [book/recon/](book/recon/REPORT_recon_2026-10-31.md))
- **Its pre-migration life can be rebuilt from public records alone.** 94 of its first 100 records replay bit for bit: every act and reason, the self, both questions, the door, and the growth to v0.5.1.
- **The other 6 are its dreams.** The working surface goes through OpenBLAS, which chose a different kernel on each CPU type. Nights 0–2 were dreamt on the founder's machine and reproduce there. Nights 3–5 were dreamt on GitHub runners and do not reproduce elsewhere. No v0.5 act depends on a dream.
- **v0.5's wake installed unpinned numpy** (2.5.4, outside its certified 1.26/2.1). Its substrate gate covered the body only, not birth and not dreams.
- **Since 2026-11-01:**
  - every wake pins `numpy==1.26.4` and holds OpenBLAS to one kernel and one thread. With these settings, dreams were identical on AMD and Intel;
  - v0.6's wake also refuses to run unless the machine dreams a fixture bit for bit (`seat/dream_gate_v06.py`).
- **Certifying the dreams themselves**, in certified arithmetic like the body, is left for a later amendment.
- **Off-site backups.** Separately, the seat's encrypted IPFS backups had been failing silently since about 2026-10-24: a plan limit, plus a bug that logged refusals as successes. Both were fixed on 2026-11-01, and every seat was pinned again. The seats' own snapshot chains were never affected.

## Contents
- **`build/`**:
  - the v0.6 build manifest's files (`book/MANIFEST_v06_build.sha256`, with `twin_judge.py` per Amendment 2);
  - `handle_mp.py` and `mind4.py` (Amendment 1);
  - `ears_v04`–`v07`, `self_text_v04`, `seat_v04s` and `talk_v04s`, byte-identical to `v05/build/`.
- **`seat/`**: the wake, diary pages, cloud seat, and the dream gate with its fixture.
- **`book/`**: spec, gates, amendments, verdict, anchors, run-2 outputs, the reconstruction study, and M0 on the real state.
