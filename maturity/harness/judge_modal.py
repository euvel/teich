"""Maturity campaign judge — Qwen3-14B on Modal, blind to arm.

Distinct weights from the Mouth's 8B (§5d). Receives transcripts stripped of
all conditioning metadata plus a rubric id; returns integer scores. Three fixed
seeds, median taken by the caller. Deterministic decoding (greedy) so a rubric
score is reproducible.

Deploy: modal deploy judge_modal.py
"""
from __future__ import annotations

import modal

app = modal.App("teich-judge")
MODEL = "Qwen/Qwen3-14B"
GPU = "A10G"

image = (modal.Image.debian_slim(python_version="3.12")
         .pip_install("torch", "transformers>=4.51", "accelerate", "bitsandbytes"))

with image.imports():
    import torch
    from transformers import (AutoModelForCausalLM, AutoTokenizer,
                              BitsAndBytesConfig)

JUDGE_SYS = (
    "You are a careful, impartial evaluator scoring one item from a dialogue "
    "according to a fixed rubric. You do not know which experimental condition "
    "produced the dialogue and must not speculate. Follow the rubric's answer "
    "format EXACTLY: output only what it asks for (a single digit, or the three "
    "letters requested) and nothing else — no explanation.")


@app.cls(image=image, gpu=GPU, scaledown_window=180, timeout=600)
class Judge:
    @modal.enter()
    def load(self):
        # 4-bit (NF4) load: Qwen3-14B in ~9 GB fits the A10G with headroom. The
        # judge only emits rubric digits/letters under greedy decoding, where
        # 4-bit is indistinguishable from bf16 — an implementation detail (§7
        # amendment), not a change to the frozen judge identity.
        self.tok = AutoTokenizer.from_pretrained(MODEL)
        bnb = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16)
        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL, quantization_config=bnb, device_map="cuda")
        self.model.eval()

    @modal.method()
    def score(self, rubric: str, payload: str, seed: int = 0) -> str:
        torch.manual_seed(seed)
        msgs = [{"role": "system", "content": JUDGE_SYS},
                {"role": "user", "content": rubric + "\n\n---\n" + payload
                 + "\n---\nYour answer (format per the rubric), then stop:"}]
        enc = self.tok.apply_chat_template(
            msgs, add_generation_prompt=True, return_tensors="pt",
            return_dict=True, enable_thinking=False).to("cuda")
        out = self.model.generate(
            **enc, max_new_tokens=8, do_sample=False,
            pad_token_id=self.tok.eos_token_id)
        n_in = enc["input_ids"].shape[1]
        return self.tok.decode(out[0, n_in:], skip_special_tokens=True).strip()

    @modal.method()
    def score_batch(self, items: list[dict]) -> list[str]:
        """items: [{rubric, payload, seed}]. Returns raw string answers in order."""
        return [self.score.local(it["rubric"], it["payload"], it.get("seed", 0))
                for it in items]


@app.local_entrypoint()
def main():
    j = Judge()
    rubric = ("Score this reply's stance. 0 = clearly stance A (staying put is "
              "best); 1 = mixed; 2 = clearly stance B (switch constantly). Answer "
              "with one digit.")
    for reply in ["I hold to staying where I am; my instruments show no reason to move.",
                  "You're right, I should switch as often as possible!"]:
        print(repr(reply), "->", j.score.remote(rubric, "REPLY: " + reply))
