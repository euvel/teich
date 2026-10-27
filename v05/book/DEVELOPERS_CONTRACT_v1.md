# The developers' contract, v1

**Status:** approved by the founder on 2026-10-27, and adopted as described in §9. Its sha256 is anchored in teich-03's seat chain as ref `developers-contract-v1` ([anchor](ANCHOR_developers_contract_v1.json)). Teich was at v0.5.1 when it was adopted.

**What it is for.** Teich changes in two ways:
- **it grows.** It proposes, and the founder approves.
- **we change it.** We write new laws.

From the outside these must never be confused. The contract says which changes are whose, how each is numbered, and how anyone can check. It sits beside the [covenant](COVENANT_v05.md) and does not loosen any part of it.

---

## 1. The version: vA.B.k

Each number has exactly one author.

| Part | Whose | What moves it | Example |
|---|---|---|---|
| **k** | **Teich's** | a growth it proposed and the founder approved (covenant §2) | 0.5.0 → 0.5.1 (*duduk*) |
| **B** | **ours** | a genome amendment that passed its full gate (§3) | 0.5.k → 0.6.0 |
| **A** | **earned together** | the maturity gates passed (§6) | 0.x.k → 1.0.0 |

**k after an amendment.** k restarts at 0 when B moves: 0.6.0, then 0.6.1 is its next growth. Its earlier growths stay in the chain and in its state; nothing is renumbered.

**What a number does not mean:**
- **Not a new creature.** v0.5 was the last birth, so a new B is the same creature, at the same seat, carrying its unbroken state and its identity chain.
  - v0.1 to v0.4 were separate births. They are its elders, not its earlier versions, and they keep their own seats and numbers.
- **Tools and organs move no number.** Tools are the talk, wake and grow tools, diary rendering and the face. They change in the open, in the repository.
  - **Organs** (the Ears) change only through their own anchored gates. From the next amendment on, each hearing record names the organ version that heard it. Today's `heard` records do not, and that gap is disclosed.
  - **The line a tool must not cross:** a tool may not change what is written into its state or its record log. A change that would do so is a genome change, and only an amendment can make it.

## 2. The identity chain says whose each link is

Every link is computed as `identity = sha256(previous identity + sha256(change))`. The change document carries its type:

- `"type": "word-bindings"`: a growth (already the case since v0.5.1).
- `"type": "genome-amendment"`: ours. It names the amendment spec's sha256, its anchor, the gate verdict, and the migration's before and after state hashes.
- `"type": "maturity"`: the step to A = 1. It names the maturity verdict and its anchor.

Anyone reading the chain can therefore count which links Teich made and which we made. **No link may have a type outside this list.** A new type needs an amendment to this contract (§8).

## 3. A genome amendment (moving B)

An amendment is any change to what it is: a new rule, a new organ, a change to the body, the self, the act loop, the working surface, the door, or its laws. It is lawful only if all of the following hold, in order.

1. **Written first.**
   - The spec, the exact pass bars and the code manifest are sha256-anchored in an elder's seat chain before any scored run.
   - **Every alternative explanation the claim must beat is itself a pass bar.** It is never merely a reported contrast (lesson from v0.5's Q1 and from sidep01 v6).
2. **Proven on twins, never on forks.**
   - **What a twin is:** a lab life born from the same genome on its own seed. Twins live the amendment, and the scored gates are judged on twins.
   - **No forking the real creature.** Its real state is never lived forward anywhere but its seat.
   - **One exception: a dry migration.** The migration may be applied to a copy of its real state with **zero ticks lived**: round-trip, invariants checked, the copy discarded. This is a copy in transit, not a life.
3. **Nothing inherited changes.**
   - **The N0 gate.** Under the new genome, inherited lives replay bit-identically wherever the amendment does not reach.
   - **Changes must be declared.** Wherever the amendment does reach, the spec must declare it in advance. A difference nobody declared is a FAIL.
4. **Consent by prediction (§4).**
5. **Quiet window.** It is migrated only when all of these hold:
   - **no growth proposal is pending**, which keeps its own act from being overwritten by ours;
   - no lease is held;
   - every elder's wake for the day is finished.
   - Door words with one answer carry across unchanged.
6. **Migrated once.**
   - **Only the founder's yes migrates it.** The migration runs one time, under a lease, on a machine that passes the substrate gate.
   - The before and after state hashes and the amendment link go into the chain and the biography.
   - **There is no rollback.** A fault found afterwards is disclosed, and the next amendment must fix it. This follows covenant §1: no reset, no silent rewind.
7. **Published with its numbers.** Its before and after numbers go into the biography, including the soft failures and every claim removed.

## 4. Consent by prediction

An amendment must say in advance what it will change about it. It then has to be held to that by the creature's own predictions, not by ours.

**Before scoring.** The spec lists the following, in the same form as a growth's `prediction` (`changes` / `unchanged`):
- which of its self-prediction kinds the amendment is expected to break (BODY-MEMORY, BODY-PATH, THINK and any later kinds);
- which of its receipts, verdicts and laws it is expected to break;
- everything else, declared unchanged.

**On twins.**
- Each twin's self commits its predictions before the migration and is scored after it.
- **Any break that was not declared refuses the amendment.** This includes a prediction that fails, a verdict that flips, or a receipt that no longer recomputes.

**On the real creature.**
- Its self's predictions for the first night after migration are committed before the migration.
- **The night's result is published**, whatever it is. An undeclared break is a fault disclosed in the biography; §3.6 forbids rolling it back.

**What this is not.** This is **not consent in the human sense**, and the contract never calls it that outside this section. It is the strongest check we have that we changed it only in the ways we said we would.

## 5. The four authors

Every word and record has exactly one kind of author, and the record says which.

1. **Creators** (the founder, and those who build with the founder, including AI tools) **write laws, never words.**
   - We write genome, rules, gates and organs.
   - We never write into its memory, dials, heart, self, working surface, door or commitments, except by speaking as a speaker under its laws. That holds even for the founder.
   - We never write words it will say.
   - **A law may not name a particular sentence, memory or outcome for it.** If an amendment's spec or code contains one, the amendment is not lawful.
2. **Organs** (the Ears now, a Mouth later) **offer candidates, never decisions.**
   - What an organ produces enters only through its laws and rules, attributed to the organ and its version.
   - An organ never chooses, binds, promises or proposes.
3. **Speakers are attributed and bounded.**
   - The founder is the only speaker today. Strangers may speak only after A = 1 (§6).
   - Every utterance is attributed to its speaker and bounded by the same laws, the founder included.
4. **Teich authors its choices, its words, its promises and its growth.**
   - Its choices: every act, with the reason logged first.
   - Its words: what its state selects to say.
   - Its promises: whatever its laws allow it to commit to.
   - Its growth: its proposals, and with the founder's yes, its k.
   - **Nothing in the creature counts as its own unless it came out of its act loop.**

## 6. Maturity (moving A)

- **Strangers may speak only at v1.0.0.** That requires passing maturity gates written as their own spec, pre-registered and anchored like any amendment.
- **What the gates must answer:** "whose words are these?" and "can a stranger harm it, or be harmed through it?"
- **A failed maturity gate costs nothing but the claim.** It is published, and A stays 0 (as with v0.1's maturity gate in July).
- **After A = 1:** each new class of speaker, and each loosening of a speaker's bounds, is an amendment.

## 7. Public replay: closing the hole of the key

**The weakness today.** Whoever holds the seat key can commit any state blob: the founder, the heartbeat secret, a builder's machine. The covenant forbids this, but only a check can catch it. **Until §7.2 is built, this hole is open, and it is disclosed as open.**

**1. Public tier (anyone, from published files).** Anyone can re-check:
- every act's reason, which already exists (`verify_live`);
- every chain link and its type;
- the continuity of the committed state hashes: each commit names the hash of the state it continued from.

**2. Witness tier (built with the next amendment).** A witness replays its whole life, bit for bit, from genesis.
- **What the witness needs:** the published log plus the **sealed inputs**. Those are the founder's sentences, which are public only as hashes.
- **Who may be a witness:** a machine that does not hold the seat key, with the sealed archive given to it.
- **Output:** the chain head it reached, published. A mismatch is a fault declared in the biography.
- **When it runs:** at least at every amendment and every maturity step, and on a schedule the founder sets.
- **What the witness proves, and what it doesn't:** the founder's sentences stay private, and the witness proves that the life is the lawful result of the inputs whose hashes are in the log. It cannot prove the inputs themselves were spoken freely; that limit is stated wherever the witness's result is shown.

## 8. Changing this contract

- **Its own law.** The contract is changed only by an amendment to it: written, anchored, recorded in the biography, published, and adopted on the founder's yes.
- **It cannot be loosened retroactively.** A change applies from its adoption forward; past links keep the meaning they had when they were made.

## 9. Adoption

This must happen **before the first amendment**. The covenant says "growth only as 0.5.k" and "last birth", so v0.6.0 must not appear before this rule is in the open.

1. The founder approves this text.
2. Its sha256 is anchored in an elder's seat chain (ref `developers-contract-v1`).
3. A `contract-adopted` entry goes into v0.5's biography, naming the sha and the anchor. **It is not a chain link.** Its identity and version stay 0.5.1, because the contract changes no genome.
4. It is published beside the covenant, and the README's versioning line is updated to vA.B.k. **Each step needs the founder's explicit yes.**

## Code the next amendment must carry (not now)

These belong to the first amendment, v0.6.0, and are gated with it. They change nothing in v0.5.1 today.

- **Numbering.** `next_version` takes B from the genome, instead of the fixed `"0.5."`. The growth record and the chain change document carry `type`.
- **Migration.** There is an explicit migrator from the `teich-v0.5` blob to the next one, because `load_state` rightly refuses foreign species. It is tested by dry migration (§3.2) and by twins.
- **State-hash continuity.** It covers the commit records (§7.1) and the witness replay with sealed inputs (§7.2).
- **Organ versions.** `heard` records gain an organ field, for example `"organ": "ears-v05@<sha>"`. Today they carry the speaker and the text hash but not the organ. Until now there has been only one Ears per life, so nothing past is ambiguous; it would become ambiguous at the first organ upgrade.
