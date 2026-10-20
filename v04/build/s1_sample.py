"""Gate S1 (mirrors) — draw the S1 sentences: 200 fresh sentences containing "you/your/yourself" from the
EmpatheticDialogues TEST split, none from a conversation used by A2e. Deterministic; run once; prints counts only
(Claude designs Ears v8 afterwards and must not read these sentences).
Output: data_heldout/dialog/s1_sentences.jsonl  {"id", "conv_id", "sentence"}
"""
import hashlib
import json
import random
import re
import sys
from pathlib import Path

import part2e_sample as P

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data_heldout/dialog/s1_sentences.jsonl"
A2E = ROOT / "data_heldout/dialog/a2e_sentences.jsonl"
SEED, N = 20261010, 200
YOU = re.compile(r"\b(you|your|yourself|yourselves)\b", re.I)


def main():
    if OUT.exists() and "--force" not in sys.argv:
        raise SystemExit(f"{OUT} exists; the draw is done once")
    used = [json.loads(l) for l in open(A2E)]
    used_conv, used_sent = {r["conv_id"] for r in used}, {r["sentence"].lower() for r in used}
    pool = sorted((c, s) for c, s in P.sentences() if YOU.search(s) and c not in used_conv and s.lower() not in used_sent)
    rng = random.Random(SEED); rng.shuffle(pool)
    out, seen = [], set()
    for c, s in pool:
        if c in seen:
            continue
        seen.add(c); out.append({"id": len(out), "conv_id": c, "sentence": s})
        if len(out) == N:
            break
    with open(OUT, "w") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    print(len(out), "sentences from", len(pool), "eligible | sha256", hashlib.sha256(OUT.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
