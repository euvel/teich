"""A local voice — candidate utterances with no API at all.

Why this exists. The v0.2 demo needs SIX generations. NIM has taken two hours
and not delivered them, and the founder's IP is geo-blocked from it besides, so
every attempt costs a cloud round-trip and an unpredictable wait. Meanwhile the
thing being demonstrated is the SELECTION, not the eloquence of the candidates:
the architecture's whole claim is that the voice produces options knowing
nothing about the creature, and the creature's own state then chooses.

A small local model satisfies that requirement exactly as well as a large remote
one, and buys three things that matter more than prose quality here:

  * it runs on the founder's laptop, so the deadline stops depending on someone
    else's rate limiter;
  * the demo becomes self-contained — nothing to fail live in front of an
    audience;
  * the whole pipeline becomes reproducible offline by anyone auditing the book.

Qwen2.5-1.5B-Instruct is already the model the v0.1 C2 steering work used, so
the weights are known-good in this environment. CPU is pinned as law: ROCm
`generate()` hangs on this machine, verified during that work.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

BASE = "Qwen/Qwen2.5-1.5B-Instruct"


class LocalVoice:
    """Same contract as the NIM path: messages in, one completion string out."""

    def __init__(self, model_id: str = BASE, device: str = "cpu"):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id, torch_dtype=torch.float32, attn_implementation="eager")
        self.model.to(device).eval()      # CPU: ROCm generate() hangs here
        self.device = device
        self.model_id = model_id

    def complete(self, msgs, max_tokens: int = 320, temperature: float = 0.95,
                 seed: int = 0) -> str:
        torch = self.torch
        torch.manual_seed(seed)
        text = self.tok.apply_chat_template(msgs, tokenize=False,
                                            add_generation_prompt=True)
        enc = self.tok(text, return_tensors="pt").to(self.device)
        with torch.no_grad():
            out = self.model.generate(
                **enc, max_new_tokens=max_tokens, do_sample=True,
                temperature=temperature, top_p=0.95,
                pad_token_id=self.tok.eos_token_id)
        return self.tok.decode(out[0][enc["input_ids"].shape[1]:],
                               skip_special_tokens=True)


class NIMVoice:
    """The remote path, kept behind the same interface."""

    def complete(self, msgs, max_tokens: int = 320, temperature: float = 0.95,
                 seed: int = 0) -> str:
        sys.path.insert(0, str(HERE.parent / "maturity" / "harness"))
        from nim_backend import MOUTH_MODEL, _call
        return _call(MOUTH_MODEL, msgs, max_tokens=max_tokens,
                     temperature=temperature, seed=seed)


def get_voice(kind: str = "local"):
    return LocalVoice() if kind == "local" else NIMVoice()
