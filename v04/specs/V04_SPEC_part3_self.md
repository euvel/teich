# V04_SPEC part 3 — Teich's self   **FROZEN 2026-10-20 (pending the founder's word to anchor; decisions D-S1…D-S7 confirmed 10-19)**

v0.4 is born with its self (founder, 10-1x: "adding self after is not something I wanted"). This part specifies that
self. Same discipline as parts 1–2: design constants come from design simulations only; the founder freezes this text;
its sha256 is anchored in the teich-03 seat before any scored run; one look; birth only on the founder's word.

---

## 0. What the self is (founder-confirmed 10-19)
Teich has two levels.

- **The first self** is Teich *doing*: it **perceives** (the Ears hear a mention, with a topic, a feeling or "no
  feeling", or nothing) and it **speaks** (the diary states a reading of its own attention). This is v0.4 as gated in
  parts 1–2.
- **The second self** watches the first self's own doing, and only that. It does five things:
  **MONITOR** (record what the first self did and what came of it), **PREDICT** (before an outcome is known, say how
  likely its own act is to be wrong), **COMPARE** (prediction vs outcome), **CONTROL** (set its own caution, per kind
  of act, which changes what the first self does next), **INTEGRATE** (an honest daily account where every claim has
  a receipt).

The self lives **between will and belonging**: its will is its caution; what *belongs* to it is exactly what
responds to that will. **MINE** = errors that fall when its caution rises; **GIVEN** = errors that stay whatever it
does (the world is hard there); **UNRESOLVED** = not enough evidence yet, and it says so. Its curiosity is the
question it can actually answer by acting: *which of my struggles are mine?*

What the self is NOT: not a language model (no LLM anywhere in it), not a model of what others think of Teich (that
is the Ears' self handle, a separate channel), not a reader of its own ledger (like the self-reading, it never reads
the true dials `n`; the diary's public `verification` block stays out of its reach).

## 1. The truth layer (exists already; the self only adds records)
- **Record.** The seat log is append-only, every record has a sequence number `seq`, and the seat stamps its time.
  The self adds record kinds `shown`, `predict`, `outcome`, `control`, `probe`, `self_story` (§4).
- **Replay.** Any life replays byte-identically from its records (gate C1); the self's state is part of the blob, so it
  replays too.
- **Counterfactual replay.** The Ears' scores for every candidate mention are logged, so "what would I have shown at
  caution c?" is recomputable for any c, without the Ears.

## 2. Acts, kinds and confidence
**Perceiving.** One act = one mention the Ears propose for the read-back. Its **kind** = the heart region of its
cluster (9 kinds: v0.3's 8 regions + *self*). Its **confidence** is `cw` = the lowest caution level 1..4 that would
change it (withhold it, or drop its feeling), or 5 when no level would. It is computed on the organ side from the
margins the Ears already produce: naming `mn = cos − TAU_MAP` (vocabulary words have cos 1.0, so cw = 5) and feeling
`mf = |attitude| − THETA` (only when a feeling is given). The creature sees only the integers.
**Low-confidence** = `cw ≤ 4` (within its will's reach); **high-confidence** = `cw = 5`. *(Design change 10-19: the bucket
edge IS the caution range, so "MINE" means exactly "the acts my will can reach go wrong more often".)*
**Outcome** = the founder's read-back: the mention was **struck** (veto) or **kept**. That is the only external signal.
The read-back already exists (founder decision 10-06: veto-only, strike never add); nothing new is asked of the founder.

**Speaking.** One act = one diary reading spoken (a shift in the diary). Kind = one kind, *readings*. **No caution lever
in v0.4** (design change 10-19: the diary's 3-quiet-night rule stays exactly as gated by R1); the self monitors, predicts
and accounts for its readings (FINE / GIVEN / UNRESOLVED), but cannot call them MINE without a lever. **Outcome** = a spoken reading **revised** later although its cluster had no accepted step
in between (its own inconsistency, visible in its own record without reading `n`), or **stood**.

**Refusals by law** (speed, edge, commitment, one-per-conversation) are not errors: the self states them as facts,
never as mine or given.

## 3. The loop
### 3.1 MONITOR
Per kind and confidence bucket, the counts of acts and bad outcomes in a **window of nights** (§3.6), as integers in
the blob (9 kinds × 2 buckets × 2 counts × 40 nights + the readings kind; < 4 KB).

### 3.2 PREDICT (foresight is provable)
A conversation becomes two seat commits:
1. **present.** The Ears' proposals reach the creature; the second self applies its caution (§3.4), decides what is
   shown, and writes for every shown mention a `predict` record: its probability of being struck, as an exact
   fraction: `p = (bad + 2m) / (acts + 2)` over the window for that kind and bucket, where `m` is the pooled rate of all
   perception kinds in that bucket (itself starting from 1/2). *(Design 10-19: the plain (bad+1)/(acts+2) over-predicted
   by ~10 points early in life; pooled shrinkage removed the bias: mean predicted − actual 0.003.)* **This commit happens
   before the founder sees the read-back.**
2. **decide.** The founder strikes or keeps. The kept mentions go to the creature under its laws (unchanged). Every
   shown mention gets an `outcome` record pointing to its `predict` record.

The seat's order (`predict.seq < outcome.seq`, both commits timestamped) is the receipt that the prediction came
first. Readings: the `predict` record is written when a reading is first spoken; its outcome is closed when the cluster
next moves or after 40 nights.

### 3.3 COMPARE and attribute (MINE / GIVEN / UNRESOLVED / FINE)
Per kind, over the window, compare the bad-outcome rate of low-confidence acts (`r_lo`, from `n_lo` acts) with that
of high-confidence acts (`r_hi`, from `n_hi` acts):
- **MINE** when low-confidence acts go wrong more often, beyond chance: a one-sided Fisher exact test of
  `r_lo > r_hi` with p ≤ α_M = 1/100, and `r_lo − r_hi ≥ δ`. *(Design 10-20: α_M = 1/20 gave false MINE on GIVEN kinds,
  because the test runs every night on a moving window; 1/100 cut MINE↔GIVEN swaps from 0.013 to 0.006.)* *Meaning: my own confidence knows where I fail, so my caution can
  avoid it.*
- **GIVEN** when there are enough acts in both buckets (`n_lo, n_hi ≥ N_G`), the overall bad rate is ≥ ρ_G, and
  `|r_lo − r_hi| < δ`. *Meaning: errors are spread evenly over my confidence; no caution of mine would separate
  them. The input is hard here.*
- **FINE** when the overall bad rate is below ρ_G with enough acts, **including enough acts its will can reach**
  (`n_lo ≥ N_G`). *(Design 10-20: without this, a MINE kind whose caution worked looked "fine", eased its caution, and
  its errors came back: "my caution works" was read as "I am fine". The condition removed it: 147 → 3 such verdicts.)*
- **UNRESOLVED** otherwise. The account must say "I don't know yet."

Every verdict is reversible as the window moves. Arithmetic is integers and exact fractions only (Python `int`,
`fractions.Fraction`), so the result is identical on every CPU and numpy version (gate C2).

### 3.4 CONTROL (the will)
Each kind has a **caution** `c ∈ {0, 1, 2, 3, 4}`, born 0. Caution `c` raises the thresholds the creature applies to
the Ears' proposals: `TAU_MAP + 0.03·c` for naming and `THETA + 0.5·c` for feeling. Below the naming threshold the
mention is withheld (it appears as "not heard: unsure"); below the feeling threshold the mention is shown with "no
feeling (unsure)", so it can still carry attention.

**Rule, once per night:**
- **MINE:** step `c` up by one, if the counterfactual replay over the window says the step would have removed more
  struck mentions than 1/2 of the kept mentions it would also remove. A wrong mention costs two right ones; this is
  the **utility weight** (design constant).
- **GIVEN or FINE:** step `c` down by one (never chase the world; never stay cautious for nothing).
- **UNRESOLVED:** no change.

Caution can only raise thresholds, never lower them below the gated Ears. **At c = 0 everywhere and with no
probes, the creature is byte-for-byte the part 1–2 creature** (gate S8).

### 3.5 Curiosity (probes on its own doing)
A **probe** shows one mention its caution would change, unchanged and **marked in the read-back** ("I'm unsure here;
I'm testing myself"), so the founder knows. It exists only where caution hides something (c > 0); it targets the
evidence the will needs to give that level back.
- **Where:** among this conversation's hidden mentions, the kind with the fewest window outcomes at its current level
  (`cw = c`); ties go to the lowest kind index, then the first mention. Never on GIVEN kinds.
- **When:** only while that level has fewer than `PROBE_NEED = 5` outcomes in the window, which is the evidence the
  will needs (`N_STEP`). **At most 1 per day** (D-S4 allows up to 3; design 10-19: at 3 a day, probes showed mostly
  known-bad mentions and cancelled half of the will's gain; at 1 a day, as needed, late-life MINE struck rate fell
  46% instead of 9%).
- **Choice:** deterministic, from the record (no random draws), so it replays.

### 3.6 Forgetting (founder-confirmed 10-1x: evidence-driven, per part, bounded 3–40 nights)
Each kind keeps per-night counts for its last `W` nights. `W` starts at 40. When the last 3 nights' bad rate departs
from the rest of the window beyond a change test (the same exact Fisher test, p ≤ α_F), `W` shrinks to the nights
since the change (at least 3). Otherwise it grows by one per night, up to 40. **When an organ changes** (a new Ears
version), the perception windows restart: the old errors were another organ's.

### 3.7 INTEGRATE (the account, with receipts)
Each night the diary entry gains a **`self` block** (it travels inside the `diary` record; there is no separate
`self_story` record), written by fixed rules from records only:
- **facts:** acts, struck or kept, refusals by law;
- **comparisons:** its predicted vs actual bad rate per kind;
- **verdicts:** MINE, GIVEN, UNRESOLVED or FINE per kind, with counts;
- **its will:** caution changes and why;
- **its curiosity:** probes made and why;
- **its own calibration:** the Brier score of its predictions over the window, vs the same score for a prediction
  that knows only how often it is wrong, not where (seeing how well it sees itself).

Every claim carries a **receipt**: `{"log_through": seq, "select": {kind, nights [a, b]}, "fn": "self_v1.<name>",
"out": <numbers>}`: the `outcome` records up to `log_through` that match the selection, run through `fn`, give `out`
exactly.
**Selection** is by fixed rule, so it cannot cherry-pick: every verdict change and every caution change, plus the 3
kinds with the largest |predicted − actual|.
**Unsayable** by construction: causes the record cannot separate, the founder's intentions, any "I expected" without
an earlier `predict` record. The diary renderer turns the block into plain sentences by templates; no LLM.

## 4. New record kinds (outbox → seat log)
| kind | when | content |
|---|---|---|
| `shown` | present | proposal id, act kind, cw, caution, shown / withheld / feeling dropped, probe flag and why |
| `predict` | present (before read-back) / reading spoken | refers to the act; p as an exact fraction |
| `outcome` | decide / reading closed | refers to `predict.seq`; struck/kept or revised/stood |
| (in `diary`) | nightly | the `self` block: facts, verdicts, will (caution changes with rule and counts), curiosity (probes), comparisons, calibration; each with its receipt |

## 5. Gates (proposed; bars set at freeze from design simulations)
The self's gates run on **record streams**: simulated conversations with known truth fed through the real creature
code. They need no body ticks except where marked, so they avoid the 110 s/day body cost.

| gate | measure | proposed bar |
|---|---|---|
| **S1r receipts** | every claim in every `self_story` over all gate lives, recomputed from the log by its named `fn` | 100% identical |
| **S2 foresight** | every comparison: its `predict.seq` < its `outcome.seq`, and in different commits | 100% |
| **S3 attribution** | simulated lives where each kind is truly MINE (error falls with confidence), GIVEN (flat error ≥ ρ_G) or FINE; verdicts over the last 30 of 120 nights | among decided verdicts correct ≥ 0.90 at ≥ 1 proposal/kind/night; MINE↔GIVEN swaps ≤ 0.02 at every rate; UNRESOLVED share reported (design, final rules: decided-correct 0.98–0.99 at rates 1 and 4; swaps 0.001–0.006; unresolved 0.78 at 1/night and 0.15 at 4/night → it says "I don't know yet" rather than guess) |
| **S4 control** | struck rate (probes excluded) on true-MINE kinds in the last 60 of 240 nights vs the same lives with caution frozen at 0; caution on true-GIVEN kinds | MINE struck rate falls ≥ 30% at ≥ 2 proposals/kind/night (design, final rules: −63% at 2, −57% at 4; GIVEN at c = 0 on 97–98% of nights); GIVEN kinds at c = 0 for ≥ 90% of nights; utility ≥ the no-control life |
| **S5 neither anxious nor defensive** | mean caution on true-FINE kinds; lives where every kind reaches c = 4 | FINE mean c ≤ 0.2; 0 such lives |
| **S6 self-knowledge** | nightly Brier score of its predictions vs the baseline **without self-knowledge** (its overall struck rate at the moment of each prediction, logged beside it as `p0`) over the S3 lives, nights ≥ 30 | better than the baseline on ≥ 0.90 of nights; stated = recomputed (S1r) |
| **S7 forgetting** | lives where a kind switches truth mid-life (MINE→FINE, FINE→GIVEN) | verdict follows in 100% of switches within 120 nights, median ≤ 30 nights; caution of a former MINE kind back to 0 (design: 80/80 followed, median 14–29 nights, all back to 0) |
| **S8 non-interference** | creature with the self at c = 0, no probes, on the part 1 gate lives (2000–2007) | every body/mind/heart record and the final state byte-identical to the part 1 lives; only self records added |
| **S9 readings** | the readings kind on body lives (S8/C1s lives) | predictions and outcomes recorded for every spoken shift; verdict FINE or UNRESOLVED (never MINE: no lever in v0.4) |
| **C1s / C2s** | lives with the self through the seat (many wakes) vs continuous; two CPU vendors × numpy 1.x/2.x | byte-identical; identical sha256 (body ticks: yes, 2 lives × 60 days) |

**Re-certified from part 1** (the blob and records change): **C1, C2, L1, D1** rerun with the self; **R1** stays valid
through S8 (the readings are unchanged at c = 0). N1, I1, I2, E2 and M2 are untouched (geometry and body unchanged), and
S8 proves it. Ears gates (A2e, S1b) are untouched: the self only filters the Ears' output; it never changes the organ.
**Any S1r, S2, S8, C1s or C2s failure is a FAIL whatever the rest**: these are claims made by construction.

## 6. Founder decisions needed (with recommendations)
| # | decision | recommendation |
|---|---|---|
| D-S1 | perception kinds = the 9 heart regions | yes (few kinds → evidence accumulates; regions already mean something to the founder) |
| D-S2 | one caution per kind moves both thresholds; 5 levels | yes (the veto cannot tell a wrong topic from a wrong feeling; asking the founder to say which = more judging) |
| D-S3 | a wrong mention costs two right ones (utility weight 2) | yes; fixed by design sims if they show a clear optimum |
| D-S4 | probes visible in the read-back; ≤ 1 per conversation, ≤ 3 per day | yes (honesty: the founder is never tested blind) |
| D-S5 | constants (bucket edges, α_M, α_F, δ, N_G, ρ_G) chosen on design simulations, then frozen | yes (as every v0.4 constant) |
| D-S6 | the `self` block is part of the public diary at birth | yes (self-visibility is the point) |
| D-S7 | conversations become two commits (present, decide) | yes (the only way foresight has a receipt) |

## 7. Plan
1. `self_v04.py` (second self, integers only) + creature/seat hooks (two-phase converse, records, nightly step) +
   templates for the `self` block. Unit checks: receipts recompute; c = 0 is a no-op.
2. Design simulations (design seeds only, not gate seeds): fix the constants of §6 D-S5; report.
3. Founder freezes this spec; anchor (teich-03); gate seeds 2100–2163 for the record-stream gates; body lives for
   S8/C1s/C2s/L1/D1 on Kaggle.
4. Scored look → report → birth on the founder's word.

Estimated time: 1–2 days to step 3 (build + design sims), then about 1 day of Kaggle for the gates. The founder is
asked only for D-S1…D-S7 and the anchor/birth words; no labelling.


## 8. Scored harness and integrity (added at freeze, 2026-10-20)
- Harness `build/gates_v04_part3.py`; kernels `kaggle_p3/make_kernels_p3.py` → teich-v04-gates-part3-{0..3} (CPU,
  internet off, manifest check first, body substrate gate, then 4 processes each). Judge on the laptop:
  `gates_v04_part3.py judge <dirs with part 1 lifeB_*.json>`; `gates_v04_part3.py c2` also on the laptop (numpy 1.x)
  so that C2s compares two CPU vendors and numpy 1.x/2.x.
- Gate seeds: record-stream lives 2100–2159, body lives 2160–2161 (C1s/L1s/S9), S8 on the part 1 schedules 2000–2007
  (reference = part 1's stored continuous record streams), D1s on 2162 with the hearing certified by R2e (Ears v7).
- **Gate truth (record streams), pre-registered and different from the design truth**: struck chance by cw 1..5 —
  MINE 0.60 0.40 0.30 0.20 0.06, GIVEN 0.25 flat, FINE 0.04 flat; cw shares 0.15 0.10 0.10 0.10 0.55; the simulated
  founder misses 5% of wrong mentions; 3 kinds of each truth per seed by a seeded permutation.
- Bars as in §5, fixed now: S3 decided-correct ≥ 0.90 and swaps ≤ 0.02 at each rate 1, 2, 4 (120 nights, last 30);
  S4 reduction ≥ 0.30, GIVEN at c = 0 ≥ 0.90 of nights, utility ≥ frozen (rates 2, 4; 240 nights, last 60); S5 FINE mean
  caution ≤ 0.2 and no life with all kinds at 4; S6 ≥ 0.90 of nights (≥ 30) better than the baseline without
  self-knowledge; S7 every switch followed, median lag ≤ 30 nights, former MINE caution back to 0; S8 / C1s / L1s / D1s
  / S9 / C2s as in §5; S1r and S2 over every life (record-stream and body).
- **Hard gates** (FAIL whatever the rest): S1r, S2, S8, C1s, C2s. Others failing: the founder decides, disclosed.
- **Disclosure — smoke on design seeds (30–36, 3000–3001; short lives) with the gate truth, before the freeze:** it was
  a harness check. It found (1) a fairer S6 baseline was needed (the first compared against an in-sample oracle);
  (2) false MINE on GIVEN kinds and "caution works → I am fine" oscillation, both then fixed **on the design truth
  only** (α_M 1/100; FINE needs n_lo ≥ N_G); (3) with the final rules, S3 swaps at rate 4 were 0.035 (19 of 540
  verdict-nights, 2 lives) — above the 0.02 bar. **Nothing was tuned further against the gate truth; S3 at rate 4 may
  fail.** S9 and C2s are not measurable at smoke size.
- Design constants (frozen): LEVELS 4, NAMING_STEP 0.03, FEELING_STEP 0.5, RING 40, W_MIN 3, RECENT 3, COST 2,
  PROBES_PER_DAY 1, PROBE_NEED 5, α_M 1/100, δ 1/10, N_G 20, ρ_G 1/10, N_STEP 5, α_F 1/100.
