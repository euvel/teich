"""Part 2e AMENDMENT (2026-10-09) — the annotator runs on Kaggle instead of the NVIDIA API.

Why: the NVIDIA free tier throttled GLM-5.3 (HTTP 429 for every request, two keys, then Kimi K3 too) after 306 of 1,200
votes; the job could not finish. All 400 sentences are relabelled from scratch by ONE judge (no mixing with GLM votes).
Judge: Mistral-Small-24B-Instruct-2501 (Mistral AI; neither Qwen — the Ears' organ — nor Anthropic — the Ears' designer),
4-bit build unsloth/Mistral-Small-24B-Instruct-2501-bnb-4bit @ JUDGE_REV, on Kaggle 2×T4.
Unchanged from part2e_label.py: the GUIDE (same text, byte for byte, read from that file), 3 votes per sentence at
temperature 0.6, the VOTE majority rule, the vote / label file formats. Seeds fixed per batch (reproducible on the same
hardware and libraries). An answer that cannot be parsed is re-sampled up to 4 times, then counted as an empty vote.
    python3 part2e_label_kaggle.py SENTENCES.jsonl OUT_DIR [--limit N]
"""
import ast
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

JUDGE = "unsloth/Mistral-Small-24B-Instruct-2501-bnb-4bit"
JUDGE_REV = "cb4e166b818799cd769592eed8f7142ceab779ca"
N_VOTES, TEMP, BATCH, MAX_NEW, RETRIES = 3, 0.6, 12, 400, 4
HERE = Path(__file__).resolve().parent


def guide():
    """The GUIDE string of part2e_label.py, read without importing it (that module needs the API key)."""
    tree = ast.parse((HERE / "part2e_label.py").read_text())
    return next(n.value.value for n in tree.body if isinstance(n, ast.Assign)
                and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "GUIDE")


def parse(txt):
    m = re.search(r"\{.*\}", txt, re.S)
    topics = json.loads(m.group(0))["topics"]
    out = []
    for t in topics:
        n, a = str(t["noun"]).strip().lower(), str(t["attitude"]).strip().lower()
        if n and a in ("warm", "cold", "neutral"):
            out.append([n, a])
    return out


def main():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    src, out_dir = Path(sys.argv[1]), Path(sys.argv[2]); out_dir.mkdir(parents=True, exist_ok=True)
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    sents = [json.loads(l) for l in open(src)][:limit]
    G = guide()
    tok = AutoTokenizer.from_pretrained(JUDGE, revision=JUDGE_REV); tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    lm = AutoModelForCausalLM.from_pretrained(JUDGE, revision=JUDGE_REV, device_map="auto", torch_dtype=torch.float16,
                                              max_memory={0: "14GiB", 1: "14GiB"}).eval()
    votes_p = out_dir / "a2e_votes.jsonl"
    done = {(v["id"], v["vote"]) for v in map(json.loads, open(votes_p))} if votes_p.exists() else set()
    jobs = [(s, k) for s in sents for k in range(N_VOTES) if (s["id"], k) not in done]
    print(len(sents), "sentences;", len(jobs), "votes to get", flush=True)

    def generate(batch, seed):
        prompts = [tok.apply_chat_template([{"role": "system", "content": G},
                                            {"role": "user", "content": f'Sentence: "{s["sentence"]}"'}],
                                           tokenize=False, add_generation_prompt=True) for s, _ in batch]
        enc = tok(prompts, return_tensors="pt", padding=True, add_special_tokens=False).to(lm.device)
        torch.manual_seed(seed)
        with torch.no_grad():
            out = lm.generate(**enc, do_sample=True, temperature=TEMP, top_p=1.0, max_new_tokens=MAX_NEW,
                              pad_token_id=tok.pad_token_id)
        return [tok.decode(o[enc["input_ids"].shape[1]:], skip_special_tokens=True) for o in out]

    with open(votes_p, "a") as f:
        for b0 in range(0, len(jobs), BATCH):
            batch = jobs[b0:b0 + BATCH]; pending = list(range(len(batch))); res = [None] * len(batch)
            for attempt in range(RETRIES + 1):
                seed = int(hashlib.sha256(f"{batch[0][0]['id']}-{batch[0][1]}-{attempt}".encode()).hexdigest()[:8], 16)
                texts = generate([batch[i] for i in pending], seed)
                still = []
                for i, t in zip(pending, texts):
                    try:
                        res[i] = {"ok": True, "topics": parse(t), "raw": t[-2000:]}
                    except Exception:
                        res[i] = {"ok": False, "topics": [], "raw": t[-2000:]}; still.append(i)
                pending = still
                if not pending:
                    break
            for (s, k), r in zip(batch, res):
                f.write(json.dumps({"id": s["id"], "vote": k, **r}) + "\n")
            f.flush()
            print(f"{min(b0 + BATCH, len(jobs))}/{len(jobs)} votes, unparsable after retries: {len(pending)}", flush=True)

    votes = collections.defaultdict(dict)
    for v in map(json.loads, open(votes_p)):
        votes[v["id"]][v["vote"]] = v
    labels_p = out_dir / "a2e_labels.jsonl"
    with open(labels_p, "w") as f:
        for s in sents:
            vs = [votes[s["id"]][k]["topics"] for k in range(N_VOTES)]
            listed = collections.Counter(n for v in vs for n in {t[0] for t in v})
            tags = []
            for n, c in sorted(listed.items()):
                if c < 2:
                    continue
                atts = collections.Counter(a for v in vs for t, a in v if t == n)
                a, ca = atts.most_common(1)[0]
                tags.append([n, a if ca >= 2 else "unsure"])
            f.write(json.dumps({"id": s["id"], "stratum": s["stratum"], "sentence": s["sentence"], "tags": tags,
                                "failed_votes": sum(not votes[s["id"]][k]["ok"] for k in range(N_VOTES))}) + "\n")
    print("labels sha256", hashlib.sha256(labels_p.read_bytes()).hexdigest(), flush=True)


if __name__ == "__main__":
    main()
