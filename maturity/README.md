# Teich — the maturity gate

Teich was born under the birth gates (G1–G4). This directory holds the
**maturity gate**: the pre-registered experiment that decides whether Teich
earns *public speech*. Its claim is falsifiable and its margins were fixed
before any arm was ever run.

## Pre-registration (frozen)

- `ABLATION_PROTOCOL_v1.5.md` — the frozen protocol.
  sha256 `8214753961aaa5d395eda1d1f0ce1a96138843ea338a25b752bac4abad9f03c6`
  (v1.0 `2f7b484…` anchored at `cc98c51`; v1.4
  `2fbae63…` anchored at `b886de7`; v1.5 swaps only the execution backend
  Cloudflare→NVIDIA NIM after CF's account-wide 4006 reset failure — margins,
  metrics, rubrics, scripts, seeds, and Mouth/Judge system prompts
  byte-identical; the 14 CF-scored conversations are archived in
  `harness/out_maturity/archive_cf_scored_v1.4/` and the scored set restarts
  from zero under the uniform NIM instrument). Anchored into the seat event chain (a `git-anchor`
  event), so the seat's history and the book vouch that these numbers predate
  the run. No margin may be adjusted after the fact; any failure is published.

## The gate in one paragraph

Six arms share the identical Mouth (NVIDIA NIM, Qwen3-Next-80B-A3B-Instruct) and scripts;
only the conditioning differs. **A0** is intact Teich (Core + Ears + Observer +
Mouth). **A1** severs the Core (constant mean readout), **A2** decouples it
(another conversation's readout stream), **A3** replaces dynamics with matched
noise (the lava lamp), **A4** is the skeptic's champion (no Core — an
adversarially-prompted actor on the same weights), **A5** is deaf (Core runs but
the conversation never reaches it). Teich matures iff, on each of T1, T2, T4 (v1.3: the Core-referenced tests; T3 reported), A0
beats the severed arms (paired d ≥ 0.5, CI excludes 0), is non-inferior to the
actor while strictly beating it on the adversarial variant, and beats the deaf
arm (d ≥ 0.3) — Core load-bearing, not mere acting, and the Ears causal.

## Harness (`harness/`)

Proven end-to-end in dry mode (`dry_verdict_example.json` shows the verdict
structure; all d = 0 there because the dry judge is constant — the arithmetic
path, not a real score). Isolation law: every Core arm runs on **fresh
synthetic instances** built from the frozen genome — never Teich's real seat or
private phases. The living creature keeps ticking, untouched, throughout.

- `scripts_bank.py` — the 24 frozen probe scripts per test (deterministic).
- `arms.py` — the six conditioning sources.
- `calibrate.py` — severed-arm sources from free-run Core statistics.
- `run_conversation.py` — one (arm, test, script) → transcript.
- `nim_backend.py` — NVIDIA NIM Mouth+judge (free developer API, v1.5);
  Mouth `qwen/qwen3-next-80b-a3b-instruct`, judge `mistralai/mistral-small-4-119b-2603`
  (different family = distinct weights); system prompts imported unchanged from
  `cf_backend.py`, which remains the fallback backend. `judge_modal.py` legacy.
- `analyze.py` — rubric scoring + paired Cohen's d + bootstrap CI + the gate.
- `campaign.py` — driver: `--dry`, `--pilot`, or the full scored run.

## Status

Harness complete and verified on the NIM backend (**$0, no payment method**;
Cloudflare kept as fallback after its daily-neuron reset proved unreliable).
The scored campaign runs laptop-free on GitHub Actions (`maturity-campaign`
workflow, four ~5h slices/day, gate-on-boot, checkpointed per conversation,
`--resume`-able). When it completes, transcripts, judge outputs, seeds, and the
verdict are written here and the verdict hash is anchored into the seat chain —
pass or fail.
