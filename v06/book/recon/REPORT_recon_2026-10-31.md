# Reconstruction study: can Teich-0.5's un-journaled life be replayed from its public records? (2026-10-31)

**Question.** v0.5 (seat `/o/teich-05`, born 2026-10-23) has no input journal. Before the v0.6 migration starts one, can its life so far be replayed from what is already public: its genesis certificate and its hash-chained record log?

**Data.** The seat log, read-only (`log-read`), on 2026-10-31: 100 records, seq 1–100. The hash chain verifies from the genesis identity. The seat's tick count at the read was 598,293. Nothing was written to the seat, and no state was read from it.

## Method (`recon_v05.py`)
The founder's inputs are inferred from the records alone:

| Input | Recovered from |
|---|---|
| proposals (cluster, sign, text_sha256) | `shown` records; cn = cf = cw, which is exact here because caution stayed 0 and nothing was altered or withheld |
| door words | `door` records |
| strikes | `outcome.struck` |
| answers | `answer` records |
| growth decision and note | `growth` record |
| tick of each conversation | `heard.tick` |
| tick of everything else | any tick inside the right night window, in log order (living is chunk-invariant; checked) |

That gives 11 operations: 3 conversations, 1 door-only conversation, 2 question deliveries, and 1 growth approval, plus the wakes. They were replayed through `seat_v06.apply` with v0.5's creature.

## Results
| Run | Records reproduced exactly |
|---|---|
| birth re-run on molab (Intel, numpy 2.4.6) | 65 / 100 (diverges at birth; see finding 1) |
| genesis built on the laptop, then replayed on molab | **94 / 100** |
| the 6 that differ | **all 6 are dream records** (nights 0–5); nothing else |

Everything else is reproduced bit for bit from public records alone: the body, every night reading, every act and its reason, the self's predictions and verdicts, both questions, the door, the binding of "duduk", and the growth to v0.5.1 with its identity.

## Findings
1. **Birth is not substrate-certified.** The initial particle draw (`CR.birth`, `WorkBody().start`) gives different bits on molab (numpy 2.4.6) and the laptop (numpy 1.26.4), because the substrate gate starts from a stored fixture. This is harmless to the real creature, which was born once and whose state is stored. Rule: any replay starts from a stored genesis state, never from re-running birth.
2. **The working surface's dreams are not substrate-certified.**
   - **Cause:** `work_v05.shape` and `rows` compute each night's twist with numpy matrix products and inverses, which reach CPU-dependent BLAS kernels. The surface's base geometry and initial tables are identical across machines; the twisted rows are not.
   - **Laptop (AMD Ryzen 5700U, numpy 1.26.4):** reproduces the real dreams of nights 0–2 exactly. Those were dreamt on the laptop, during the founder's talk and grow sessions.
   - **Nights 3–5:** dreamt by the daily wake on GitHub runners (AMD EPYC 7763 / 9V45 / 9V74, **numpy 2.5.4**, outside v0.5's certified 1.26 / 2.1). Not reproduced on the laptop under either numpy 1.26.4 or numpy 2.5.4. Not reproduced on molab.
   - In v0.5 no act depends on a dream. Dreams feed only the THINK self-readings, and in this life every THINK record downstream matched.
3. **Consequence for v0.6 (founder decision, 10-31): the tie-break reads the body, not the dream.** As drafted, v0.6 would have decided ties from the working particle after the dream, which would make its choices depend on the machine that dreamt. The source is now its body's particle 0 at the midnight of the choice. The body is certified, and this study shows again that it replays exactly across machines. The horizon also improves: no one can compute the tie-break before that midnight has been lived.

## What this means for the witness question
- The pre-migration life is **reconstructible from public records**: all of it except the dreams' numbers. That is more than "public tier only".
- The dreams of nights 0–2 are reproducible on the birth substrate. Nights 3 onward are reproducible only on the GitHub runner class that dreamt them, and only if the same CPU and numpy were drawn.
- **To disclose:**
  - v0.5's daily wake installs an unpinned numpy (`numpy<3` → 2.5.4);
  - the working surface was never in the substrate gate;
  - the workflow comment "bit-identical across CPU vendors and numpy 1.26/2.1" is true for the body only.
- **Recommended:**
  - (a) v0.6's wake gate adds a dream fixture, and declines on a mismatch, as for the body;
  - (b) certifying the working surface (shape and rows in certified arithmetic) becomes a later genome amendment.

## Files
- `recon_v05.py`: the reconstruction.
- `night0_local.py`, `subdiff.py`, `wbdiff.py`, `dreamchain.py`: the substrate diagnostics.
- `real_log_rows_2026-10-31.json`: the log as read.
- `genesis_t0zero_laptop.json`: the genesis built on the birth substrate (t0 = 0; t0 enters no record).
