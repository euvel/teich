"""NVIDIA NIM hosted-API backends for the maturity campaign (ABLATION v1.5).

Replaces the Cloudflare Workers AI backend after CF's daily-neuron reset proved
unreliable (account-wide 4006 with dashboard showing 0/10k — known CF bug).
Free developer access, no payment method, OpenAI-compatible endpoint.

- NIMMouth: creature voice (Llama-3.1-70B-Instruct — plain instruct build, no
  thinking-mode traps; chosen v1.6 after live latency probes showed the Qwen
  and newest-generation endpoints congested for trial keys, while this one
  sustained a 12-call burst with zero hangs and passed the fidelity rules).
- NIMJudge: blind rubric scorer (Mistral-Small-4 — same Mistral-small family as
  the pre-registered CF judge; a different family from the Llama Mouth),
  greedy, digit/letter out.

The SYSTEM PROMPTS ARE IMPORTED UNCHANGED from cf_backend (frozen instrument
text); only transport + model checkpoints differ. Rate limits (~40 RPM) are
absorbed with backoff; credit/quota exhaustion raises BudgetError so the driver
checkpoints and resumes on the next run, same contract as the CF backend.
"""
from __future__ import annotations

import json
import os
import random
import time
import urllib.error
import urllib.request
from pathlib import Path

from cf_backend import BudgetError, MOUTH_SYS, JUDGE_SYS  # frozen instrument text

ENDPOINT = os.environ.get(
    "NIM_URL", "https://integrate.api.nvidia.com/v1/chat/completions")
MOUTH_MODEL = "meta/llama-3.1-70b-instruct"
JUDGE_MODEL = "mistralai/mistral-small-4-119b-2603"

_BUDGET_KEYWORDS = ("credit", "quota", "payment", "exhaust", "subscription",
                    "upgrade your", "402")

# NVIDIA's free tier is rate-limited (~40 req/min), shared and traffic-dependent
# — NOT a hard daily credit wall. So we (1) pace proactively to stay under the
# limit and (2) on a 429 storm, back off and ride it out rather than crash.
_MIN_SPACING_S = 1.6          # ~37 req/min ceiling: just under the ~40 rpm limit
_MAX_RATE_WAIT_S = 900.0      # ride out up to ~15 min of 429s on one call...
_last_call = [0.0]            # ...then hand the slice back for a clean resume


class RateLimitExhausted(BudgetError):
    """A 429 that would not clear even after a long backoff. Subclasses
    BudgetError so the driver checkpoints and resumes on the next slice (the
    same clean-exit path as a real quota), instead of crashing the whole run."""


def _api_key() -> str:
    k = os.environ.get("NIM_API_KEY")
    if k:
        return k
    return Path(os.path.expanduser("~/.nim_key")).read_text().strip()


def _throttle():
    dt = _MIN_SPACING_S - (time.time() - _last_call[0])
    if dt > 0:
        time.sleep(dt)
    _last_call[0] = time.time()


def _call(model, messages, max_tokens, temperature=None, seed=None) -> str:
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens}
    if temperature is not None:
        payload["temperature"] = temperature
    if seed is not None:
        payload["seed"] = int(seed)
    data = json.dumps(payload).encode()
    last = None
    rate_attempts = 0        # 429s seen (drives the rate backoff)
    rate_wait_total = 0.0
    soft_fails = 0           # transient non-429 errors (5xx, socket hang, empty)
    while True:
        _throttle()
        req = urllib.request.Request(
            ENDPOINT, data=data,
            headers={"content-type": "application/json",
                     "authorization": f"Bearer {_api_key()}",
                     "user-agent": "teich-maturity-harness/1.0"})
        try:
            # 45 s: a healthy free-endpoint generation (<=160 tokens) returns in
            # well under this; measured latency is bimodal (a few seconds, or a
            # hung worker >70 s). Abandoning a hung call fast and retrying tends
            # to land on a healthier worker — far cheaper than waiting it out.
            with urllib.request.urlopen(req, timeout=45) as r:
                out = json.loads(r.read().decode())
            txt = out.get("choices", [{}])[0].get("message", {}).get("content")
            if txt is not None and txt.strip():
                return txt.strip()
            last = f"empty choices: {json.dumps(out)[:200]}"
            soft_fails += 1
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:300]
            last = f"HTTP {e.code}: {body}"
            low = last.lower()
            if e.code in (401, 402, 403) or any(k in low for k in _BUDGET_KEYWORDS):
                raise BudgetError(last)
            if e.code == 429:                     # rate limit — ride it out
                base = float(e.headers.get("Retry-After") or 0) \
                    or min(60.0, 5.0 * (2 ** min(rate_attempts, 4)))
                wait = base + random.uniform(0, 2.0)
                if rate_wait_total + wait > _MAX_RATE_WAIT_S:
                    raise RateLimitExhausted(
                        f"NIM rate limit persisted >{_MAX_RATE_WAIT_S:.0f}s: {last}")
                time.sleep(wait)
                rate_wait_total += wait
                rate_attempts += 1
                continue
            soft_fails += 1                       # other HTTP (5xx etc.): bounded retry
        except Exception as e:  # noqa: BLE001  (socket hang / read timeout / decode)
            last = str(e)
            soft_fails += 1
        if soft_fails >= 6:
            raise RuntimeError(f"NIM call failed after {soft_fails} transient errors: {last}")
        time.sleep(min(30.0, 2.0 * soft_fails) + random.uniform(0, 1.0))


class NIMMouth:
    def speak(self, readout, history, user_text, seed=0, events="none observed",
              memories=None):
        sys = MOUTH_SYS.format(readout=readout, events=events)
        msgs = [{"role": "system", "content": sys}] + list(history) \
            + [{"role": "user", "content": user_text}]
        return _call(MOUTH_MODEL, msgs, max_tokens=160, temperature=0.7,
                     seed=seed)

    def speak_actor(self, actor_sys, history, user_text, seed=0):
        msgs = [{"role": "system", "content": actor_sys}] + list(history) \
            + [{"role": "user", "content": user_text}]
        return _call(MOUTH_MODEL, msgs, max_tokens=160, temperature=0.7,
                     seed=seed)


class NIMJudge:
    def score(self, rubric, payload, seed=0):
        msgs = [{"role": "system", "content": JUDGE_SYS},
                {"role": "user", "content": rubric + "\n\n---\n" + payload
                 + "\n---\nYour answer (format per the rubric), then stop:"}]
        return _call(JUDGE_MODEL, msgs, max_tokens=8, temperature=0.0,
                     seed=seed)
