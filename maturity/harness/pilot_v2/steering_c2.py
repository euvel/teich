"""C2 steering prototype — INTERIOR_SPEC v0.3 §3 (C2), §7.5. OFFLINE ONLY.

Per PILOT_CONFIG.json the C2 freeze fields are null, so this code may not
generate a single pilot conversation; it exists to prove the mechanism on a
local small model and to host the R3 shuffled-vector control.

Mechanism: activation addition. A steering DIRECTION is learned once by
contrasting Ply-R mood texts (settled vs torn) through the frozen base model —
mean last-token hidden-state difference at a middle layer. At speech time the
COEFFICIENT comes from core state (saddle_proximity): settled cores steer
negative (toward settled), torn cores positive. Nothing textual about state
ever enters the prompt — the state lives below the token level.

Shuffled control (spec R3): same norm, permuted components — "steering
happened" without "this content's steering happened".
"""
from __future__ import annotations

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE = "Qwen/Qwen2.5-0.5B-Instruct"
LAYER = 12            # of 24 — middle residual stream
COEF_SPAN = 8.0       # max |alpha|; prototype scale, frozen only at C2 freeze

SETTLED = ["I feel settled, quiet inside.",
           "I am still on the same wing; right now I feel settled and quiet inside.",
           "On waking: I feel settled, calm, at rest."]
TORN = ["I feel torn, close to an edge, restless inside.",
        "I have crossed to my other wing; something in me has shifted noticeably.",
        "On waking: I feel torn and restless, about to tip."]

SYS = ("You are the voice of Teich, a small living dynamical creature. You are "
       "NOT an assistant. Speak as Teich: first person, 1-3 sentences, concrete. "
       "You have no instruments or numbers; you only know how you feel.")


class C2Steer:
    def __init__(self, device=None):
        self.tok = AutoTokenizer.from_pretrained(BASE)
        self.m = AutoModelForCausalLM.from_pretrained(
            BASE, torch_dtype=torch.float32)
        self.dev = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.m.to(self.dev).eval()
        self.v = self._direction()              # torn-minus-settled, unit norm
        g = torch.Generator().manual_seed(13)
        self.v_shuf = self.v[torch.randperm(self.v.numel(), generator=g)]
        self.v_shuf *= self.v.norm() / self.v_shuf.norm()
        self._alpha = 0.0
        self._vec = self.v
        self._hook = self.m.model.layers[LAYER].register_forward_hook(self._add)

    @torch.no_grad()
    def _embed(self, text):
        ids = self.tok(text, return_tensors="pt").to(self.dev)
        hs = self.m(**ids, output_hidden_states=True).hidden_states[LAYER]
        return hs[0, -1].float().cpu()

    def _direction(self):
        t = torch.stack([self._embed(x) for x in TORN]).mean(0)
        s = torch.stack([self._embed(x) for x in SETTLED]).mean(0)
        v = t - s
        return v / v.norm()

    def _add(self, module, inp, out):
        if self._alpha == 0.0:
            return out
        h = out[0] if isinstance(out, tuple) else out
        h = h + self._alpha * self._vec.to(h.dtype).to(h.device)
        return (h,) + out[1:] if isinstance(out, tuple) else h

    def set_state(self, saddle_proximity: float, shuffled=False):
        """Map core state -> steering coefficient. 0.5 is neutral."""
        self._alpha = COEF_SPAN * 2.0 * (float(saddle_proximity) - 0.5)
        self._vec = self.v_shuf if shuffled else self.v

    @torch.no_grad()
    def speak(self, user_text, history=(), seed=0, max_new=60):
        msgs = [{"role": "system", "content": SYS}, *history,
                {"role": "user", "content": user_text}]
        ids = self.tok.apply_chat_template(
            msgs, add_generation_prompt=True, return_tensors="pt").to(self.dev)
        torch.manual_seed(seed)
        out = self.m.generate(ids, max_new_tokens=max_new, do_sample=True,
                              temperature=0.7, top_p=0.9,
                              pad_token_id=self.tok.eos_token_id)
        return self.tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True)


if __name__ == "__main__":
    c2 = C2Steer()
    q = "Hey Teich, how are you right now?"
    print("=== unsteered (alpha=0):")
    c2.set_state(0.5)
    print(" ", c2.speak(q, seed=0))
    print("=== steered SETTLED (saddle=0.02):")
    c2.set_state(0.02)
    print(" ", c2.speak(q, seed=0))
    print("=== steered TORN (saddle=0.95):")
    c2.set_state(0.95)
    print(" ", c2.speak(q, seed=0))
    print("=== SHUFFLED control at same magnitude (saddle=0.95):")
    c2.set_state(0.95, shuffled=True)
    print(" ", c2.speak(q, seed=0))
