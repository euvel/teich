# Teich — the maturity gate

Teich was born under the birth gates (G1–G4). This directory holds the
**maturity gate**: the pre-registered experiment that decides whether Teich
earns *public speech*. Its claim is falsifiable and its margins were fixed
before any arm was ever run.

## Pre-registration (frozen)

- `ABLATION_PROTOCOL_v1.2.md` — the frozen protocol.
  sha256 `166fc390e1035e4ab59ae303ab77bbbd66e07648be105d4df1cdd614a1b6b5ad`
  (v1.0 `2f7b484…` anchored at `cc98c51`; v1.1 swaps only the execution backend
  Modal→Cloudflare Workers AI, before any scored arm ran — margins/metrics/rubrics
  byte-identical). Anchored into the seat event chain (a `git-anchor`
  event), so the seat's history and the book vouch that these numbers predate
  the run. No margin may be adjusted after the fact; any failure is published.

## The gate in one paragraph

Six arms share the identical Mouth (Cloudflare Workers AI, Qwen3-30B) and scripts;
only the conditioning differs. **A0** is intact Teich (Core + Ears + Observer +
Mouth). **A1** severs the Core (constant mean readout), **A2** decouples it
(another conversation's readout stream), **A3** replaces dynamics with matched
noise (the lava lamp), **A4** is the skeptic's champion (no Core — an
adversarially-prompted actor on the same weights), **A5** is deaf (Core runs but
the conversation never reaches it). Teich matures iff, on each of T1–T4, A0
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
- `cf_backend.py` — Cloudflare Workers AI Mouth+judge (free `/lab/generate`);
  Mouth `@cf/qwen/qwen3-30b-a3b-fp8`, judge `@cf/mistralai/mistral-small-3.1-24b-instruct`
  (different family = distinct weights). `judge_modal.py` kept as legacy reference.
- `analyze.py` — rubric scoring + paired Cohen's d + bootstrap CI + the gate.
- `campaign.py` — driver: `--dry`, `--pilot`, or the full scored run.

## Status

Harness complete and verified; the Mouth speaks and the blind judge scores
known cases correctly, all on Cloudflare's free neuron tier (**$0, no payment
method** — Modal's real free tier is $1 and needs a card). The scored campaign
runs via `campaign.py` (checkpointed per conversation, `--resume`-able, stops
cleanly at the daily free budget). When it completes, transcripts, judge
outputs, seeds, and the verdict are written here and the verdict hash is
anchored into the seat chain — pass or fail.
