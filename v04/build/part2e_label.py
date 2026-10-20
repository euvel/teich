"""Part 2e — independent labels for the A2e sentences by GLM-5.3 (Zhipu; via NVIDIA API), blind to the Ears.

The annotator is a different vendor from the Ears' organ (Qwen) and from the Ears' designer (Claude), sees only the
sentence and the GUIDE below (frozen in the part 2e anchor), never the Ears or their output. Three independent votes
per sentence (temperature 0.6); majority rules (VOTE below). Raw responses kept in a2e_votes.jsonl (resumable).
Rate: <= 36 requests/minute (API limit 40). Key: ~/.nvidia_api_key (never in code or repo).
    python3 part2e_label.py            -> data_heldout/dialog/a2e_votes.jsonl, a2e_labels.jsonl
"""
import collections
import hashlib
import json
import re
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data_heldout/dialog"
SENT, VOTES, LABELS = D / "a2e_sentences.jsonl", D / "a2e_votes.jsonl", D / "a2e_labels.jsonl"
URL, MODEL = "https://integrate.api.nvidia.com/v1/chat/completions", "z-ai/glm-5.3"
N_VOTES, TEMP, RPM, WORKERS = 3, 0.6, 36, 6

GUIDE = """You label one sentence that a speaker says to a listener in a conversation. Follow these rules exactly.

TOPICS
- List EVERY thing the sentence names with a noun: people (sister, boss, friend), things (car, coffee, table), places
  (park, office), activities and events named by nouns (job, party, exam, trip), animals, ideas (life, money).
  Include small ones too ("the cup on the TABLE" -> cup and table).
- Write each as it appears in the sentence, singular, lowercase ("dogs" -> dog). A name made of several words for
  one thing is written whole ("ice cream", "phone call", "high school").
- NOT topics: pronouns (I, you, he, it, they, this, that, something...), time expressions used as adverbs (today,
  yesterday, this week, one day, these days, last night, 10 minutes), and feelings carried only by a verb or adjective
  ("I was happy" has no topic "happiness").
- ITSELF: add the topic "itself" when the sentence is about the LISTENER ("you"): what the listener is, does, can do,
  feels, or is like, or how the speaker sees or treats the listener ("you are so kind", "I am glad I can talk to you",
  "you must be proud"). Do NOT add it when "you" only asks about or points at something else ("have you seen the
  movie?" -> movie only; "you should try the soup" -> soup only) or when "you" means people in general ("you have to
  wait an hour there").

ATTITUDE (for every topic): the SPEAKER's OWN attitude toward it, right now, as the sentence SAYS it.
- warm = the speaker likes, praises, loves, is glad about, is grateful for it.
- cold = the speaker dislikes, criticises, fears, is upset or sad about it.
- neutral = no attitude of the speaker's is said about it (just mentioned, a fact, in passing).
- Someone else's feeling is not the speaker's: "my sister loves jazz" -> sister: neutral, jazz: neutral.
- A question, a hypothetical (if / unless / whether ...), or an old feeling ("I used to love it") -> neutral.
- Negation counts: "not bad" -> warm; "I never liked it" -> cold.

Answer with JSON only, no other text:
{"topics": [{"noun": "...", "attitude": "warm|cold|neutral"}, ...]}"""

VOTE = """Majority of 3 votes: a topic is kept when >= 2 votes list it; its attitude is the attitude given by >= 2 of the
votes that list it, else it is kept as a topic with attitude "unsure" (counted for recall / precision / itself, not
for feelings). A vote whose answer cannot be parsed is retried (up to 4 times), then counted as an empty vote."""


class Limiter:
    def __init__(self, rpm):
        self.gap, self.t, self.lock = 60.0 / rpm, 0.0, threading.Lock()

    def wait(self):
        with self.lock:
            now = time.time(); t = max(now, self.t + self.gap); self.t = t
        time.sleep(max(0.0, t - time.time()))


LIM, KEY = Limiter(RPM), (Path.home() / ".nvidia_api_key").read_text().strip()


def ask(sentence):
    body = {"model": MODEL, "temperature": TEMP, "top_p": 1, "max_tokens": 8000, "stream": False,
            "messages": [{"role": "system", "content": GUIDE}, {"role": "user", "content": f'Sentence: "{sentence}"'}]}
    for attempt in range(6):
        LIM.wait()
        try:
            req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json",
                                                                          "Authorization": f"Bearer {KEY}"})
            d = json.load(urllib.request.urlopen(req, timeout=300))
            txt = d["choices"][0]["message"].get("content") or ""
            m = re.search(r"\{.*\}", txt, re.S)
            topics = json.loads(m.group(0))["topics"]
            out = []
            for t in topics:
                n, a = str(t["noun"]).strip().lower(), str(t["attitude"]).strip().lower()
                if n and a in ("warm", "cold", "neutral"):
                    out.append([n, a])
            return {"ok": True, "topics": out, "raw": txt[-2000:]}
        except Exception as e:                                    # retry: network, rate limit, unparsable answer
            err = repr(e)[:300]; time.sleep(5 * (attempt + 1))
    return {"ok": False, "topics": [], "raw": err}


def main():
    sents = [json.loads(l) for l in open(SENT)]
    done = {(v["id"], v["vote"]) for v in map(json.loads, open(VOTES))} if VOTES.exists() else set()
    jobs = [(s, k) for s in sents for k in range(N_VOTES) if (s["id"], k) not in done]
    print(len(sents), "sentences;", len(jobs), "votes to get", flush=True)
    wlock = threading.Lock()

    def work(job):
        s, k = job; r = ask(s["sentence"])
        with wlock, open(VOTES, "a") as f:
            f.write(json.dumps({"id": s["id"], "vote": k, **r}) + "\n")
        return r["ok"]
    with ThreadPoolExecutor(WORKERS) as ex:
        for i, ok in enumerate(ex.map(work, jobs), 1):
            if i % 60 == 0 or not ok:
                print(f"{i}/{len(jobs)} {'ok' if ok else 'FAILED vote'}", flush=True)
    votes = collections.defaultdict(dict)
    for v in map(json.loads, open(VOTES)):
        votes[v["id"]][v["vote"]] = v
    with open(LABELS, "w") as f:
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
    print("labels sha256", hashlib.sha256(LABELS.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
