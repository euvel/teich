"""Gate S1 RETRY (S1b, Amendment 1) — independent labels under the founder's broad reading (2026-10-19 audit):
a sentence MIRRORS the listener when some you-word in it is the listener personally; NONE only when every "you" is
generic, the filler "you know", or quoted. Same judge, votes and rules as S1 (s1_label_kaggle.py); only GUIDE, the
answer set (MIRROR | NONE) and the vote seeds differ.
    python3 s1b_label_kaggle.py SENTENCES.jsonl OUT_DIR [--limit N]
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

GUIDE = """A speaker says one sentence to a listener in a conversation. Decide whether "you" in the sentence is the
LISTENER — the specific person being spoken to.

MIRROR — some "you" / "your" / "yourself" in the sentence is the listener personally: what they are, have, can do, did,
     do, plan, think or feel; a question to them about any of this; an invitation or advice to them; or the speaker's
     own feeling toward them. It does NOT matter what else the sentence is about.
     Examples: "You are so patient." / "Are you okay?" / "Have you seen the new movie?" / "You should try the soup
     there." / "What does your husband do?" / "Did you know the museum closes at five?" / "Let me tell you about my
     trip." / "Thank you so much." / "I'm proud of you." / "I hope you have a wonderful day."
NONE — no "you" in the sentence is the listener: "you" means people in general, anyone, or "one"; or it is only the
     filler "you know"; or it is quoted from somebody else.
     Examples: "You never know these days." / "You have to be fit to do that job." / "It can really get to you after
     a while." / "Before you know it, the kids are grown." / "It was, you know, a long day." / "He said 'you are late'."

If any "you" in the sentence is the listener, answer MIRROR.
Answer with JSON only: {"answer": "MIRROR"} or {"answer": "NONE"}"""


def parse(txt):
    a = json.loads(re.search(r"\{.*?\}", txt, re.S).group(0))["answer"].strip().upper()
    if a not in ("MIRROR", "NONE"):
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
    votes_p = out_dir / "s1b_votes.jsonl"

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
                seed = int(hashlib.sha256(f"s1b-{batch[0][0]['id']}-{batch[0][1]}-{attempt}".encode()).hexdigest()[:8], 16)
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
    labels_p = out_dir / "s1b_labels.jsonl"
    with open(labels_p, "w") as f:
        for s in sents:
            c = collections.Counter(a for a in votes[s["id"]] if a)
            a, k = c.most_common(1)[0] if c else (None, 0)
            f.write(json.dumps({"id": s["id"], "label": a if k >= 2 else "unsure", "votes": votes[s["id"]]}) + "\n")
    print("labels sha256", hashlib.sha256(labels_p.read_bytes()).hexdigest(), flush=True)


if __name__ == "__main__":
    main()
