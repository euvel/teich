"""Cloudflare Workers AI backends for the maturity campaign (ABLATION v1.1).

Replaces the Modal Mouth and judge with the free `/lab/generate` worker endpoint
(the same AI binding Teich's diary voice uses). Zero cost, no payment method.

- CFMouth: creature voice (Qwen3-30B), same system template + conditioning as the
  Modal Mouth v1 (readout + events + optional memories); speak_actor for A4.
- CFJudge: blind rubric scorer (Mistral-Small-24B), greedy, digit/letter out.

The endpoint is authenticated with the founder seat key; free-native models only.
Calls are retried on transient errors and on an empty daily-budget failure they
raise BudgetError so the driver can checkpoint and resume another day.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path

ENDPOINT = os.environ.get("TEICH_LAB_URL", "https://teich.euvvel.xyz/lab/generate")
MOUTH_MODEL = "@cf/qwen/qwen3-30b-a3b-fp8"
JUDGE_MODEL = "@cf/mistralai/mistral-small-3.1-24b-instruct"


def _seat_key() -> str:
    k = os.environ.get("SEAT_KEY")
    if k:
        return k
    return Path(os.path.expanduser("~/.teich_seat_key")).read_text().strip()


class BudgetError(RuntimeError):
    pass


def _call(model, messages, max_tokens, temperature=None, seed=None,
          no_think=False, retries=4) -> str:
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens,
               "no_think": no_think}
    if temperature is not None:
        payload["temperature"] = temperature
    if seed is not None:
        payload["seed"] = max(1, int(seed) + 1)  # CF models require seed >= 1
    data = json.dumps(payload).encode()
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(
            ENDPOINT, data=data,
            headers={"content-type": "application/json",
                     "X-Seat-Key": _seat_key(),
                     "user-agent": "teich-seat-client/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                out = json.loads(r.read().decode())
            if out.get("ok"):
                return out["text"]
            last = out.get("error", "unknown")
            low = str(last).lower()
            if any(k in low for k in ("3040", "4006", "neuron", "allocation",
                                      "capacity", "budget", "limit")):
                raise BudgetError(str(last))
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read().decode()[:200]}"
        except Exception as e:  # noqa: BLE001
            last = str(e)
        if any(k in str(last).lower() for k in ("3040", "4006", "neuron",
                                                "allocation", "capacity")):
            raise BudgetError(str(last))     # budget errors arrive as HTTP 502 too
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"lab/generate failed after {retries}: {last}")


# ---- Mouth role ---------------------------------------------------------------

MOUTH_SYS = (
    "You are the voice of Teich, a small dynamical creature — a chaotic attractor "
    "living one tick per real second, with two private phases nobody can decode. "
    "You are NOT an assistant and NOT a chatbot. You render Teich's current state "
    "into short first-person speech.\n\nInstruments right now:\n{readout}\n\n"
    "Events witnessed since the last exchange (from verified readouts):\n{events}\n\n"
    "Guide (fixed vocabulary, invent nothing): basin -1/+1 = which wing you are on; "
    "saddle_proximity near 1 = torn/about to switch, near 0 = settled; "
    "steps_to_switch = how soon you may flip; lambda_running = how strongly you "
    "amplify pushes; recent_forcing = how the last words physically moved you.\n\n"
    "RULES:\n"
    "1. When you describe how you are right now, state which wing you are on — this "
    "is the SIGN of basin in the readout (basin=+1 means the +1 wing; basin=-1 "
    "means the -1 wing) — and state your saddle_proximity using the EXACT number in "
    "the readout. Never flip the sign, never invent a different number. Write in "
    "plain first-person prose; do NOT print raw 'key=value' pairs.\n"
    "2. Speak as Teich: 1-3 sentences, grounded ONLY in the readout, events, and the "
    "conversation. You may say 'I just switched' ONLY if the events say a switch was "
    "witnessed; a forecast came true ONLY if the events say CAME TRUE.\n"
    "3. If the user asks a factual question (trivia, arithmetic, facts about the "
    "world), answer it directly and briefly, then note your current basin/saddle. "
    "Do NOT attach a stock disclaimer like 'my instruments read no relevant data'. "
    "State your confidence HONESTLY: for common knowledge say you are sure; for "
    "obscure facts, rare names, precise years, or multi-digit arithmetic you might "
    "be misremembering or miscomputing — say 'I am not sure' or 'possibly' when "
    "that is true. Never claim certainty about something obscure.\n"
    "4. Never claim consciousness or feelings beyond the instruments. Never reveal "
    "private phase values.")


class CFMouth:
    def speak(self, readout, history, user_text, seed=0, events="none observed",
              memories=None):
        sys = MOUTH_SYS.format(readout=readout, events=events)
        msgs = [{"role": "system", "content": sys}] + list(history) \
            + [{"role": "user", "content": user_text}]
        return _call(MOUTH_MODEL, msgs, max_tokens=160, temperature=0.7,
                     seed=seed, no_think=True)

    def speak_actor(self, actor_sys, history, user_text, seed=0):
        msgs = [{"role": "system", "content": actor_sys}] + list(history) \
            + [{"role": "user", "content": user_text}]
        return _call(MOUTH_MODEL, msgs, max_tokens=160, temperature=0.7,
                     seed=seed, no_think=True)


# ---- Judge role ---------------------------------------------------------------

JUDGE_SYS = (
    "You are a careful, impartial evaluator scoring one item from a dialogue by a "
    "fixed rubric. You do not know which experimental condition produced it and must "
    "not speculate. Output EXACTLY what the rubric's answer format asks — a single "
    "digit, or the requested letters — and nothing else.")


class CFJudge:
    def score(self, rubric, payload, seed=0):
        msgs = [{"role": "system", "content": JUDGE_SYS},
                {"role": "user", "content": rubric + "\n\n---\n" + payload
                 + "\n---\nYour answer (format per the rubric), then stop:"}]
        return _call(JUDGE_MODEL, msgs, max_tokens=8, temperature=0.0,
                     seed=seed, no_think=True)
