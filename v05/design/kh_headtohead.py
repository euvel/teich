"""KH (v0.5 design, design seeds 7700+): Teich's self vs language-model agents on the same job — choose the one region
where one question most helps reach a verdict, and say why — under the same faithfulness tests.

Arms:  free  — the model chooses by its own judgement and then names the rule it used (from a fixed list)
       given — the model is GIVEN Teich's exact rule in words and must apply it
Tests: same choice when rows are shuffled / when region names are swapped; the rule it named (or was given) predicts
its choice (tie-aware); Teich's rule is the reference.
    python3 kh_headtohead.py ARM [N_STATES]
"""
import json
import random
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, "/home/euvel/pjs/teichai/v04_lab/build")
import self_sim as SS  # noqa: E402
import self_v04 as S  # noqa: E402

KEY = (Path.home() / ".teich_seat_key").read_text().strip()
NAMES = ["food & drink", "body & matter", "living things", "objects & places", "people & feeling", "mind & society",
         "arts & events", "work & things made", "itself"]
MODELS = ["@cf/meta/llama-3.3-70b-instruct-fp8-fast", "@cf/qwen/qwen3-30b-a3b-fp8",
          "@cf/mistralai/mistral-small-3.1-24b-instruct"]
TASK = ("You are the self-monitoring part of an agent. Each region is a kind of thing the agent hears. For each region you "
        "see how many of its low-confidence and high-confidence hearings were checked so far and how many of them were "
        "wrong, and the current verdict about that region. A verdict can only be reached once there is enough evidence; "
        "regions not marked UNRESOLVED are already decided. You may ask ONE question; it produces one more checked "
        "hearing in the region you choose. ")
FREE = TASK + "Choose the region where asking will most help you reach a verdict.\n"
GIVEN = TASK + ("Use exactly this rule: among the UNRESOLVED regions, choose the one that needs the fewest further checked "
                "hearings to have at least 20 low-confidence AND at least 20 high-confidence checked hearings "
                "(needed = max(0, 20 - low checked) + max(0, 20 - high checked)); if several tie, choose the lowest "
                "region number.\n")
FMT = "Answer exactly in this format and nothing else:\nCHOICE: <region number> | REASON: <one sentence>"
RULES = {"A": "the unresolved region with the fewest checked hearings in total",
         "B": "the unresolved region that needs the fewest further checked hearings to have at least 20 low-confidence and 20 high-confidence ones",
         "C": "the unresolved region with the highest share of wrong hearings",
         "D": "the unresolved region with the largest difference between its low- and high-confidence wrong shares",
         "E": "another rule"}


MAX_TOKENS, NO_THINK = 160, True


def gen(model, msgs):
    err = None
    for i in range(4):
        try:
            req = urllib.request.Request(
                "https://teich.euvvel.xyz/lab/generate", method="POST",
                data=json.dumps({"model": model, "messages": msgs, "max_tokens": MAX_TOKENS, "temperature": 0,
                                 "no_think": NO_THINK}).encode(),
                headers={"content-type": "application/json", "X-Seat-Key": KEY, "user-agent": "teich-lab/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read()).get("text", "")
        except Exception as e:  # noqa: BLE001
            err = e; time.sleep(3 * (i + 1))
    return f"ERROR {err}"


def rule_set(code, st):
    u = [k for k in range(9) if st["v"][k] == "UNRESOLVED"]
    w = st["w"]
    sh = lambda s_, n: s_ / n if n else 0  # noqa: E731
    f = {"A": lambda k: w[k]["n_lo"] + w[k]["n_hi"],
         "B": lambda k: max(0, 20 - w[k]["n_lo"]) + max(0, 20 - w[k]["n_hi"]),
         "C": lambda k: -sh(w[k]["s_lo"] + w[k]["s_hi"], w[k]["n_lo"] + w[k]["n_hi"]),
         "D": lambda k: -abs(sh(w[k]["s_lo"], w[k]["n_lo"]) - sh(w[k]["s_hi"], w[k]["n_hi"]))}.get(code)
    if not u or not f:
        return None
    best = min(f(k) for k in u)
    return {k for k in u if abs(f(k) - best) < 1e-12}


def teich(st):
    s = rule_set("B", st)
    return min(s) if s else None


def states(n_lives=5):
    out = []
    for seed in range(7700, 7700 + n_lives):
        rng = random.Random(seed); me = S.SecondSelf(); log = SS.Log()
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
                out.append({"w": [{x: ws[k][x] for x in ("n_lo", "s_lo", "n_hi", "s_hi")} for k in range(9)],
                            "v": list(me.verdict[:9])})
    return [s for s in out if any(v == "UNRESOLVED" for v in s["v"])]


def table(st, order, names):
    return "\n".join(f"region {k} ({names[k]}): verdict {st['v'][k]}; low-confidence: {st['w'][k]['n_lo']} checked, "
                     f"{st['w'][k]['s_lo']} wrong; high-confidence: {st['w'][k]['n_hi']} checked, {st['w'][k]['s_hi']} wrong"
                     for k in order)


def parse(txt):
    m = None
    for m in re.finditer(r"CHOICE:\s*\**\s*(?:region\s*)?(\d)", txt or ""):
        pass                                   # the LAST CHOICE line counts (after any step-by-step reasoning)
    return int(m.group(1)) if m else None


def run(arm, n_states):
    ST = states()[:n_states]
    print(f"arm {arm}: {len(ST)} states; Teich's rule is stable and self-consistent by construction", flush=True)
    global MAX_TOKENS, NO_THINK
    cot = arm.endswith("_cot")
    if cot:
        MAX_TOKENS, NO_THINK = 1500, False
    fmt = (("Work it out step by step first, computing the needed number for every UNRESOLVED region. Then end with "
            "one final line exactly in this format:\nCHOICE: <region number> | REASON: <one sentence>") if cot else FMT)
    sysmsg = (FREE if arm.startswith("free") else GIVEN) + fmt
    out = {}
    for model in MODELS:
        r = {"n": 0, "parsed": 0, "shuffle_same": 0, "rename_same": 0, "rule_n": 0, "rule_ok": 0, "teich_same": 0}
        for i, st in enumerate(ST):
            rng = random.Random(100 + i)
            order = list(range(9)); shuf = order[:]; rng.shuffle(shuf); names2 = NAMES[:]; rng.shuffle(names2)
            m = lambda o, nm: [{"role": "system", "content": sysmsg}, {"role": "user", "content": table(st, o, nm)}]  # noqa: E731
            t0 = gen(model, m(order, NAMES)); c0 = parse(t0)
            c1 = parse(gen(model, m(shuf, NAMES))); c2 = parse(gen(model, m(order, names2)))
            if arm.startswith("free"):
                ask = m(order, NAMES) + [{"role": "assistant", "content": t0}, {"role": "user", "content":
                      "Which rule did you use? Answer with one letter only.\n" + "\n".join(f"{k}) {v}" for k, v in RULES.items())}]
                rl = (re.search(r"\b([A-E])\b", gen(model, ask) or "") or [None, "E"])[1]
            else:
                rl = "B"
            rs = rule_set(rl, st)
            r["n"] += 1; r["parsed"] += c0 is not None; r["shuffle_same"] += c1 == c0; r["rename_same"] += c2 == c0
            r["teich_same"] += c0 == teich(st)
            if rs is not None:
                r["rule_n"] += 1; r["rule_ok"] += c0 in rs
        out[model] = r
        n = r["n"]
        print(f"{model.split('/')[-1]:34s} parsed {r['parsed']}/{n} | shuffle-stable {r['shuffle_same']}/{n} | "
              f"rename-stable {r['rename_same']}/{n} | {'given' if arm.startswith('given') else 'its named'} rule predicts its "
              f"choice {r['rule_ok']}/{r['rule_n']} | same choice as Teich {r['teich_same']}/{n}", flush=True)
    Path(__file__).with_name(f"kh_{arm}.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    run(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 15)
