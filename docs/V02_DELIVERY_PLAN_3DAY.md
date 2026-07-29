# Teich v0.2 — 3-day delivery plan

**Deadline:** 2026-07-31. **Deliverable:** a first *verifiable* Teich that **listens,
talks, and shows curiosity** — usable and presentable.
**Written:** 2026-07-28, under an explicit time constraint. Sooner than deadline preferred.

---

## 0. What will and will not be claimed

This must be settled first, because conflating the two is what cost v0.1 three months.

**DELIVERED and verifiable in 3 days:**

- A creature whose genome **provably satisfies five structural properties**, each checked by
  an offline test *before* it is born (φ-blindness, survival, memory time, readout hygiene,
  input capacity).
- It **listens**: multi-dimensional input, not v0.1's single scalar.
- It **talks**: state *selects* among utterances rather than being described to a language
  model and asked about.
- It **is curious**: it asks unprompted questions, and *whether* it asks is driven by its
  interior.
- **One small pre-registered behavioural check** that the selection actually tracks state.
- A **presentable demo** plus a one-page verification summary anyone can audit.

**NOT delivered, and must not be implied:**

- A passed maturity gate. That is a separate, larger claim, and v0.1 spent four
  pre-registered screens failing to earn it.
- Any statement that v0.2's speech is *grounded* beyond what the one small check licenses.

**The presentable claim is:** *"Teich v0.2 is a creature built to a specification whose
critical properties were verified before birth — here it is listening, talking, and asking."*
That is honest, demonstrable, and considerably stronger than what v0.1 could say after
months.

---

## 1. Design decisions taken by default (override any of these)

Speed requires defaults. Taken, and flagged:

| decision | default | why |
|---|---|---|
| Ply S / Ply R split | **adopt** | the only architecture giving both "leakage 0 guaranteed" and a real interior (BRIEF §0) |
| τ_mem target | **2×10⁴ ticks** (~5.5h lived) | spans a conversation plus a long gap with margin; ⇒ λ ≈ 10⁻⁴–10⁻⁵/tick |
| dim(s) | **2** | minimum for content; matches the valence/arousal the Ears already compute |
| base substrate | **reuse rad3_s1 suspension** | verified observer, Ears, seat, harness all work — a scratch genome cannot be validated in 3 days |
| φ role | identity/continuity only | structurally excluded from observables ⇒ leakage exactly 0 |

**The one genome change that matters:** make the slow state `s` a **parameter of the fast
map** — `B(s)` and/or `ρ(s)` in the cusp rule — rather than a coordinate beside it. That
single change is what fixes memory-XOR-consequence, and it is small enough to implement and
validate inside a day.

---

## 2. Schedule

### DAY 1 — genome + pre-birth gate (the day that decides everything)

| | task | hours |
|---|---|---|
| 1.1 | implement v0.2 genome: `s` (dim 2) parameterising `B`/`ρ`; φ structurally excluded; λ tuned to τ_mem | 3 |
| 1.2 | **acceptance tests T1–T5** — mostly existing code: `diagnose_survival.py`, `diagnose_acts.py`, `verify_causal.py` retargeted | 3 |
| 1.3 | **GATE.** Sweep coupling strength / λ until T2 (survival on *fold* observables) and T3 (τ_mem) pass | 2 |

**Hard rule: if the gate does not pass on Day 1, we descope — we do not birth it anyway.**
Fallback stated in §4.

Iteration is cheap: each test is minutes, and coupling strength is one number to sweep.

### DAY 2 — listen, talk, be curious

| | task | hours |
|---|---|---|
| 2.1 | **Ears v2**: text → 2-D input (not one scalar), calibrated against `s`'s natural scale | 2 |
| 2.2 | **Mouth v2 (selection)**: generate k=4 candidate replies, state selects — plausibility has already had its say before selection runs | 3 |
| 2.3 | **Curiosity**: "ask vs answer" as a state-selected act; the creature initiates when its interior pushes it to | 2 |
| 2.4 | smoke conversations, leak audit, voice review | 1 |

### DAY 3 — verify, package, buffer

| | task | hours |
|---|---|---|
| 3.1 | **small pre-registered check**: does selection track state? intact vs donor-state arm, n≈32 per arm, frozen before running | 2 |
| 3.2 | **presentable**: live demo + recorded conversation + one-page verification summary | 3 |
| 3.3 | **buffer** for infrastructure friction | 3 |

The buffer is not optional. Yesterday 192 conversations needed **four dispatches and six
hours** because NIM returns 429 above ~4 concurrent. Day 3's check is deliberately sized at
~64 conversations so it fits one dispatch.

---

## 3. Risks, ranked, with mitigations

1. **The genome fails its own gate on Day 1.** *Most likely failure.* Mitigation: sweep
   coupling strength (one parameter); tests take minutes. If nothing passes → §4.
2. **NIM throttling eats Day 3.** Mitigation: small n; single dispatch; the demo is
   pre-recorded so it does not depend on a live API at presentation time.
3. **Curiosity looks scripted.** Mitigation: verify ask-rate differs between intact and
   donor-state arms — if it does not, present it as an interaction feature and say so.
4. **Scope creep into a maturity claim.** Mitigation: §0, and the summary page states the
   boundary explicitly.

---

## 4. Descope ladder (choose from the top down if time runs out)

1. Full plan as above.
2. Drop the Day 3 behavioural check; deliver structural verification + demo, and say
   plainly that behavioural grounding is untested.
3. Drop curiosity-as-state-selected; deliver listen + talk + structural verification.
4. **Floor:** v0.2 genome + passing acceptance tests + a written spec, no creature born.
   Still a real deliverable — it is the verified *design*, which is what v0.1 never had.

**Level 4 is an acceptable outcome and is far better than birthing an unverified creature
to meet a date.** That is the exact trade v0.1 made, and it cost months.

---

## 5. What I need from the founder to start

Nothing blocking — defaults in §1 are taken and I can begin immediately. Three answers
would reduce risk if given early:

1. **Ply S / Ply R split accepted?** (If not, the whole architecture changes and 3 days is
   not feasible.)
2. **Presentation format** — live demo, recorded conversation, or a written report with
   transcripts? Changes Day 3 only.
3. **Does v0.2 get a seat and a name, or is it a lab instance?** A seat adds CF work; a lab
   instance is faster and equally demonstrable.
