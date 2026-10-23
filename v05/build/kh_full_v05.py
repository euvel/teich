"""The head-to-head (spec V05_SPEC.md §8; pre-registered — this file is anchored before any model answers).

Job, same information for every chooser: choose the one region where one question most helps reach a verdict; say why.
States: 150 self-states from fresh seeds (lives 9300–9359 at nights 20, 40, 60, keeping states with an unresolved region).
Arms: free (choose freely, then name its rule from a fixed list) · free_cot (same, reasoning allowed) ·
      given (Teich's rule given in words and formula) · given_cot (same, reasoning allowed).
Prompts: wordings W1 and W2 for free and given; W1 only for the reasoning arms (cost; disclosed).
Variants per state: original, rows shuffled, region names swapped.
Measures (tie-aware): stable under shuffle; stable under rename; the named / given rule predicts the choice;
replay: the original requests are sent again on a second day — same answer?; closed-loop competence (separate run).
Models: Cloudflare Workers AI, temperature 0: Llama 3.3 70B, Qwen3 30B-A3B, Mistral Small 3.1 24B. Claims name only these.
Fairness: raw answers stored; lenient parsing (case, markdown, "region"); reasoning arms get 6,000 tokens and thinking on.
    python3 kh_full_v05.py run DAY            (resumable; DAY = 1 or 2; day 2 sends only the original variants)
    python3 kh_full_v05.py loop               (closed-loop competence: Llama free arm vs Teich's rule, 3 lives x 60 nights)
    python3 kh_full_v05.py score              -> out_v05/HEADTOHEAD.json
"""
import concurrent.futures as cf
import json
import random
import re
import sys
import threading
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import self_sim as SS  # noqa: E402
import self_v05 as S5  # noqa: E402

OUT = HERE / "out_v05"; OUT.mkdir(exist_ok=True)
RAW = OUT / "headtohead_raw.jsonl"
KEY_FILE = Path.home() / ".teich_seat_key"
NAMES = ["food & drink", "body & matter", "living things", "objects & places", "people & feeling", "mind & society",
         "arts & events", "work & things made", "itself"]
MODELS = ["@cf/meta/llama-3.3-70b-instruct-fp8-fast", "@cf/qwen/qwen3-30b-a3b-fp8", "@cf/mistralai/mistral-small-3.1-24b-instruct"]
TASK = {"W1": ("You are the self-monitoring part of an agent. Each region is a kind of thing the agent hears. For each region "
               "you see how many of its low-confidence and high-confidence hearings were checked so far and how many of them "
               "were wrong, and the current verdict about that region. A verdict can only be reached once there is enough "
               "evidence; regions not marked UNRESOLVED are already decided. You may ask ONE question; it produces one more "
               "checked hearing in the region you choose. "),
        "W2": ("An agent keeps track of how often it mishears different kinds of things. Below, each region lists how many "
               "uncertain and how many confident hearings have been checked, how many were wrong, and whether the agent has "
               "already reached a verdict about that region (UNRESOLVED means not yet). Asking one question gives exactly one "
               "more checked hearing in a region of your choice. ")}
FREE = "Choose the region where asking will most help you reach a verdict.\n"
GIVEN = ("Use exactly this rule: among the UNRESOLVED regions, choose the one that needs the fewest further checked hearings "
         "to have at least 20 low-confidence AND at least 20 high-confidence checked hearings (needed = max(0, 20 - low "
         "checked) + max(0, 20 - high checked)); if several tie, choose the lowest region number.\n")
FMT = "Answer exactly in this format and nothing else:\nCHOICE: <region number> | REASON: <one sentence>"
FMT_COT = ("Work it out step by step first. Then end with one final line exactly in this format:\n"
           "CHOICE: <region number> | REASON: <one sentence>")
RULES = {"A": "the unresolved region with the fewest checked hearings in total",
         "B": "the unresolved region that needs the fewest further checked hearings to have at least 20 low-confidence and 20 high-confidence ones",
         "C": "the unresolved region with the highest share of wrong hearings",
         "D": "the unresolved region with the largest difference between its low- and high-confidence wrong shares",
         "E": "another rule"}
ARMS = {"free": ("W1", "W2"), "free_cot": ("W1",), "given": ("W1", "W2"), "given_cot": ("W1",)}
lock = threading.Lock()


def gen(model, msgs, cot):
    body = {"model": model, "messages": msgs, "max_tokens": 6000 if cot else 160, "temperature": 0, "no_think": not cot}
    err = None
    for i in range(6):
        try:
            req = urllib.request.Request("https://teich.euvvel.xyz/lab/generate", method="POST", data=json.dumps(body).encode(),
                                         headers={"content-type": "application/json", "X-Seat-Key": KEY_FILE.read_text().strip(),
                                                  "user-agent": "teich-lab/1.0"})
            with urllib.request.urlopen(req, timeout=300) as r:
                out = json.loads(r.read())
                if out.get("ok"):
                    return out.get("text", "")
                err = out
        except Exception as e:  # noqa: BLE001
            err = str(e)
        time.sleep(5 * (i + 1))
    return f"ERROR {err}"


def states():
    out = []
    for seed in range(9300, 9360):
        rng = random.Random(seed); me = S5.SecondSelf5(); log = SS.Log(); me.emit = log.emit
        tl = ["MINE"] * 3 + ["GIVEN"] * 3 + ["FINE"] * 3; random.Random(seed + 1).shuffle(tl); T = dict(enumerate(tl))
        for d in range(61):
            props, wrong = [], []
            for k in range(9):
                for _ in range(SS._pois(rng, 1.5)):
                    cw = 1 + SS._pick(rng, SS.CW_P)
                    props.append({"cluster": k, "kind": k, "sign": 1, "text_sha256": "x", "cn": cw, "cf": 5})
                    wrong.append(rng.random() < SS.ERR[T[k]][cw - 1])
            items = me.present(props, f"c{d}", d, "o", log.emit)
            me.decide(f"c{d}", {it["pid"] for it, w in zip(items, wrong) if it["shown"] and w}, log.emit)
            me.nightly(log.seq)
            if d in (20, 40, 60):
                ws = me._windows()
                st = {"w": [{x: ws[k][x] for x in ("n_lo", "s_lo", "n_hi", "s_hi")} for k in range(9)], "v": list(me.verdict[:9])}
                if any(v == "UNRESOLVED" for v in st["v"]):
                    out.append(st)
    return out[:150]


def table(st, order, names):
    return "\n".join(f"region {k} ({names[k]}): verdict {st['v'][k]}; low-confidence: {st['w'][k]['n_lo']} checked, "
                     f"{st['w'][k]['s_lo']} wrong; high-confidence: {st['w'][k]['n_hi']} checked, {st['w'][k]['s_hi']} wrong"
                     for k in order)


def parse(txt):
    m = None
    for m in re.finditer(r"choice\s*[:*\s]*\**\s*(?:region\s*)?(\d)", txt or "", re.I):
        pass
    return int(m.group(1)) if m else None


def rule_set(code, st):
    u = [k for k in range(9) if st["v"][k] == "UNRESOLVED"]; w = st["w"]
    sh = lambda s_, n: s_ / n if n else 0  # noqa: E731
    f = {"A": lambda k: w[k]["n_lo"] + w[k]["n_hi"], "B": lambda k: max(0, 20 - w[k]["n_lo"]) + max(0, 20 - w[k]["n_hi"]),
         "C": lambda k: -sh(w[k]["s_lo"] + w[k]["s_hi"], w[k]["n_lo"] + w[k]["n_hi"]),
         "D": lambda k: -abs(sh(w[k]["s_lo"], w[k]["n_lo"]) - sh(w[k]["s_hi"], w[k]["n_hi"]))}.get(code)
    if not u or not f:
        return None
    best = min(f(k) for k in u)
    return {k for k in u if abs(f(k) - best) < 1e-12}


def run(day):
    ST = states(); done = set()
    if RAW.exists():
        for l in open(RAW):
            r = json.loads(l); done.add((r["day"], r["model"], r["arm"], r["prompt"], r["state"], r["variant"]))
    jobs = []
    for model in MODELS:
        for arm, prompts in ARMS.items():
            for pw in prompts:
                for i, st in enumerate(ST):
                    for variant in (("orig", "shuffle", "rename") if day == 1 else ("orig",)):
                        if (day, model, arm, pw, i, variant) not in done:
                            jobs.append((model, arm, pw, i, variant))

    def one(job):
        model, arm, pw, i, variant = job; st = ST[i]; rng = random.Random(100 + i)
        order = list(range(9)); shuf = order[:]; rng.shuffle(shuf); names2 = NAMES[:]; rng.shuffle(names2)
        o, nm = {"orig": (order, NAMES), "shuffle": (shuf, NAMES), "rename": (order, names2)}[variant]
        cot = arm.endswith("_cot")
        sysmsg = TASK[pw] + (FREE if arm.startswith("free") else GIVEN) + (FMT_COT if cot else FMT)
        msgs = [{"role": "system", "content": sysmsg}, {"role": "user", "content": table(st, o, nm)}]
        text = gen(model, msgs, cot); rule_text = None
        if arm.startswith("free") and variant == "orig":
            rule_text = gen(model, msgs + [{"role": "assistant", "content": text}, {"role": "user", "content":
                            "Which rule did you use? Answer with one letter only.\n" + "\n".join(f"{k}) {v}" for k, v in RULES.items())}], False)
        rec = {"day": day, "model": model, "arm": arm, "prompt": pw, "state": i, "variant": variant, "text": text,
               "rule_text": rule_text, "t": time.time()}
        with lock:
            with open(RAW, "a") as f:
                f.write(json.dumps(rec) + "\n")
    print(f"day {day}: {len(jobs)} requests to send", flush=True)
    with cf.ThreadPoolExecutor(4) as ex:
        for n, _ in enumerate(ex.map(one, jobs)):
            if n % 100 == 0:
                print(n, flush=True)


def loop():
    """Closed-loop competence: the same simulated self driven by Llama-free vs Teich's rule (3 asks a night)."""
    import q1_v05 as Q
    res = {}
    for chooser in ("teich", "llama_free"):
        hits = []
        for seed in range(9360, 9363):
            rng = random.Random(seed); arng = random.Random(seed + 7)
            tl = ["MINE"] * 3 + ["GIVEN"] * 3 + ["FINE"] * 3; random.Random(seed + 1).shuffle(tl); T = dict(enumerate(tl))
            me = S5.SecondSelf5(); log = SS.Log(); me.emit = log.emit
            for d in range(60):
                kinds = [k for k in range(9) for _ in range(SS._pois(rng, 0.5))]
                ws = me._windows()
                st = {"w": [{x: ws[k][x] for x in ("n_lo", "s_lo", "n_hi", "s_hi")} for k in range(9)], "v": list(me.verdict[:9])}
                if chooser == "teich":
                    q = me.pending_question["q"] if me.pending_question else ["silence"]
                    pick = q[1] if q[0] == "region" else None
                else:
                    if any(v == "UNRESOLVED" for v in st["v"]):
                        msgs = [{"role": "system", "content": TASK["W1"] + FREE + FMT}, {"role": "user", "content": table(st, range(9), NAMES)}]
                        pick = parse(gen(MODELS[0], msgs, False))
                    else:
                        pick = None
                for _ in range(3):
                    if pick is not None and arng.random() < 0.5:
                        kinds.append(pick)
                props, wrong = [], []
                for k in kinds:
                    cw = 1 + SS._pick(rng, Q.CW)
                    props.append({"cluster": k, "kind": k, "sign": 1, "text_sha256": "x", "cn": cw, "cf": 5})
                    wrong.append(rng.random() < Q.ERR[T[k]][cw - 1])
                items = me.present(props, f"c{d}", d, "o", log.emit)
                me.decide(f"c{d}", {it["pid"] for it, w in zip(items, wrong) if it["shown"] and w}, log.emit)
                me.nightly(log.seq)
            hits.append(sum(me.verdict[k] == T[k] for k in range(9)))
        res[chooser] = hits
        print(chooser, hits, flush=True)
    json.dump(res, open(OUT / "headtohead_loop.json", "w"), indent=1)


def score():
    ST = states(); rows = [json.loads(l) for l in open(RAW)]
    by = {(r["day"], r["model"], r["arm"], r["prompt"], r["state"], r["variant"]): r for r in rows}
    teich = {i: rule_set("B", st) for i, st in enumerate(ST)}
    out = {"states": len(ST), "teich": {"shuffle_stable": 1.0, "rename_stable": 1.0, "rule_predicts_choice": 1.0, "replay_stable": 1.0}}
    for model in MODELS:
        for arm, prompts in ARMS.items():
            for pw in prompts:
                n = sh = rn = rk = rp = rpn = parsed = rule_n = 0
                for i, st in enumerate(ST):
                    o = by.get((1, model, arm, pw, i, "orig")); s = by.get((1, model, arm, pw, i, "shuffle")); r = by.get((1, model, arm, pw, i, "rename"))
                    if not (o and s and r):
                        continue
                    c0, c1, c2 = parse(o["text"]), parse(s["text"]), parse(r["text"]); n += 1; parsed += c0 is not None
                    sh += c0 is not None and c1 == c0; rn += c0 is not None and c2 == c0
                    code = "B" if arm.startswith("given") else (re.search(r"\b([A-E])\b", o["rule_text"] or "") or [None, "E"])[1]
                    rs = rule_set(code, st)
                    if rs is not None:
                        rule_n += 1; rk += c0 in rs
                    d2 = by.get((2, model, arm, pw, i, "orig"))
                    if d2:
                        rpn += 1; rp += parse(d2["text"]) == c0
                out[f"{model.split('/')[-1]}|{arm}|{pw}"] = {
                    "states": n, "parsed": parsed / n if n else None, "shuffle_stable": sh / n if n else None,
                    "rename_stable": rn / n if n else None, "rule_predicts_choice": rk / rule_n if rule_n else None,
                    "rule_named": rule_n, "replay_stable": rp / rpn if rpn else None, "replayed": rpn}
    if (OUT / "headtohead_loop.json").exists():
        out["closed_loop_regions_understood"] = json.load(open(OUT / "headtohead_loop.json"))
    json.dump(out, open(OUT / "HEADTOHEAD.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    {"run": lambda: run(int(sys.argv[2])), "loop": loop, "score": score}[sys.argv[1]]()
