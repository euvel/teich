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


def _api_key() -> str:
    k = os.environ.get("NIM_API_KEY")
    if k:
        return k
    return Path(os.path.expanduser("~/.nim_key")).read_text().strip()


def _call(model, messages, max_tokens, temperature=None, seed=None,
          retries=6) -> str:
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens}
    if temperature is not None:
        payload["temperature"] = temperature
    if seed is not None:
        payload["seed"] = int(seed)
    data = json.dumps(payload).encode()
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(
            ENDPOINT, data=data,
            headers={"content-type": "application/json",
                     "authorization": f"Bearer {_api_key()}",
                     "user-agent": "teich-maturity-harness/1.0"})
        try:
            # 90 s: congested NIM endpoints hang the socket rather than 429 —
            # fail fast and let the retry loop re-enter the queue.
            with urllib.request.urlopen(req, timeout=90) as r:
                out = json.loads(r.read().decode())
            txt = out.get("choices", [{}])[0].get("message", {}).get("content")
            if txt is not None:
                return txt.strip()
            last = f"empty choices: {json.dumps(out)[:200]}"
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:300]
            last = f"HTTP {e.code}: {body}"
            low = last.lower()
            if e.code in (402, 403) or any(k in low for k in _BUDGET_KEYWORDS):
                raise BudgetError(last)
            if e.code == 429:                     # rate limit — honor and retry
                wait = float(e.headers.get("Retry-After") or 0) or 5.0 * (attempt + 1)
                time.sleep(min(wait, 90.0))
                continue
        except Exception as e:  # noqa: BLE001
            last = str(e)
        time.sleep(2.0 * (attempt + 1))
    raise RuntimeError(f"NIM call failed after {retries}: {last}")


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
