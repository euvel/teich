"""Gate S1 (mirrors) — independent labels: is a sentence said to a listener a MIRROR of the listener?

Judge: Mistral-Small-24B-Instruct-2501 (4-bit unsloth bnb, pinned) on Kaggle 2xT4 — same judge as Part 2e amendment 1;
it never sees the Ears. Definition (founder-confirmed 2026-10-10): a sentence mirrors the listener when it says
  M1 — what the listener IS, HAS, CAN DO, DOES or FEELS (questions about the listener's own state count), or
  M2 — the SPEAKER's own feeling or stance toward the listener personally (thanks, liking, pride, anger, care, wishes);
  NONE — "you" only leads to something else, or means people in general.
3 votes per sentence at temperature 0.6; label = majority (>= 2 votes); no majority -> "unsure" (excluded from scoring).
    python3 s1_label_kaggle.py SENTENCES.jsonl OUT_DIR [--limit N]
"""
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

JUDGE = "unsloth/Mistral-Small-24B-Instruct-2501-bnb-4bit"
JUDGE_REV = "cb4e166b818799cd769592eed8f7142ceab779ca"
N_VOTES, TEMP, BATCH, MAX_NEW, RETRIES = 3, 0.6, 16, 60, 4

GUIDE = """A speaker says one sentence to a listener in a conversation. Decide whether the sentence MIRRORS the listener.

M1 — the sentence says what the LISTENER is, has, can do, does, or feels (their nature, traits, abilities, actions,
     experiences or states). Questions about the listener's own state count.
     Examples: "You are so patient." / "You never forget anything." / "You must be exhausted." /
     "Are you okay?" / "You did a great job on that." / "You seem upset today."
M2 — the sentence expresses the SPEAKER's own feeling or stance toward the LISTENER personally: thanks, liking,
     pride, anger, disappointment, care, wishes for them.
     Examples: "Thank you so much." / "I love talking with you." / "I'm proud of you." / "I'm angry with you." /
     "I hope you have a wonderful day." / "Good luck to you!"
NONE — "you" only leads to something else, or "you" means people in general.
     Examples: "Have you seen the new movie?" (about the movie) / "You should try the soup there." (about the soup) /
     "You have to wait an hour at that place." (people in general) / "Let me tell you about my trip." (about the trip) /
     "Did you know the museum closes at five?" (about the museum)

If a sentence does both M1 and M2, answer the one that is its main point.
Answer with JSON only: {"answer": "M1"} or {"answer": "M2"} or {"answer": "NONE"}"""


def parse(txt):
    a = json.loads(re.search(r"\{.*?\}", txt, re.S).group(0))["answer"].strip().upper()
    if a not in ("M1", "M2", "NONE"):
        raise ValueError(a)
    return a


def main():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    src, out_dir = Path(sys.argv[1]), Path(sys.argv[2]); out_dir.mkdir(parents=True, exist_ok=True)
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    sents = [json.loads(l) for l in open(src)][:limit]
    tok = AutoTokenizer.from_pretrained(JUDGE, revision=JUDGE_REV); tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    lm = AutoModelForCausalLM.from_pretrained(JUDGE, revision=JUDGE_REV, device_map="auto", torch_dtype=torch.float16,
                                              max_memory={0: "14GiB", 1: "14GiB"}).eval()
    jobs = [(s, k) for s in sents for k in range(N_VOTES)]
    votes_p = out_dir / "s1_votes.jsonl"

    def generate(batch, seed):
        prompts = [tok.apply_chat_template([{"role": "system", "content": GUIDE},
                                            {"role": "user", "content": f'Sentence: "{s["sentence"]}"'}],
                                           tokenize=False, add_generation_prompt=True) for s, _ in batch]
        enc = tok(prompts, return_tensors="pt", padding=True, add_special_tokens=False).to(lm.device)
        torch.manual_seed(seed)
        with torch.no_grad():
            out = lm.generate(**enc, do_sample=True, temperature=TEMP, top_p=1.0, max_new_tokens=MAX_NEW,
                              pad_token_id=tok.pad_token_id)
        return [tok.decode(o[enc["input_ids"].shape[1]:], skip_special_tokens=True) for o in out]

    with open(votes_p, "w") as f:
        for b0 in range(0, len(jobs), BATCH):
            batch = jobs[b0:b0 + BATCH]; pending = list(range(len(batch))); res = [None] * len(batch)
            for attempt in range(RETRIES + 1):
                seed = int(hashlib.sha256(f"s1-{batch[0][0]['id']}-{batch[0][1]}-{attempt}".encode()).hexdigest()[:8], 16)
                texts = generate([batch[i] for i in pending], seed); still = []
                for i, t in zip(pending, texts):
                    try:
                        res[i] = {"ok": True, "answer": parse(t)}
                    except Exception:
                        res[i] = {"ok": False, "answer": None}; still.append(i)
                pending = still
                if not pending:
                    break
            for (s, k), r in zip(batch, res):
                f.write(json.dumps({"id": s["id"], "vote": k, **r}) + "\n")
            f.flush()
            print(f"{min(b0 + BATCH, len(jobs))}/{len(jobs)} votes", flush=True)
    votes = collections.defaultdict(list)
    for v in map(json.loads, open(votes_p)):
        votes[v["id"]].append(v["answer"])
    labels_p = out_dir / "s1_labels.jsonl"
    with open(labels_p, "w") as f:
        for s in sents:
            c = collections.Counter(a for a in votes[s["id"]] if a)
            a, k = c.most_common(1)[0] if c else (None, 0)
            f.write(json.dumps({"id": s["id"], "label": a if k >= 2 else "unsure", "votes": votes[s["id"]]}) + "\n")
    print("labels sha256", hashlib.sha256(labels_p.read_bytes()).hexdigest(), flush=True)


if __name__ == "__main__":
    main()
