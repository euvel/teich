"""PREREG_V07 §4: the K2 judge on must-pass / must-fail mutations of a FULL-LENGTH twin pair (not scored).
    python3 test_judges_v07.py TWIN.json [OUT.json]
"""
from __future__ import annotations

import base64
import copy
import json
import sys

import numpy as np

import judge_v07 as J

t0 = json.load(open(sys.argv[1]))
first_night = J.k2(t0)["first_divergent_night"]


def blob_edit(t, key, fn):
    s = json.loads(t[key]); fn(s); t[key] = json.dumps(s, sort_keys=True)


def particle(s, i, field):
    a = np.frombuffer(base64.b64decode(s[field]), "<f8").reshape(-1, 3).copy()
    a.view(np.uint64)[i, 1] ^= np.uint64(1)                       # one bit
    s[field] = base64.b64encode(a.tobytes()).decode()


def first(recs, pred):
    return next(r for r in recs if pred(r))


def diary7(t):
    return [r for r in t["records7"] if r["kind"] == "diary" and r["entry"].get("self")]


def m_extra_sky(t):
    t["records7"].append({"seq": 10 ** 9, "kind": "sky", "day": 999, "round": 1, "b": "0x0p+0", "tick": 0})


def m_p0(t):
    blob_edit(t, "blob7", lambda s: particle(s, 0, "P"))


def m_diary_reading(t):
    e = diary7(t)[-1]["entry"]; e["known"] = {"0": 99}; e["attending_most"] = []


def m_p1(t):
    blob_edit(t, "blob7", lambda s: particle(s, 1, "P"))


def m_dial(t):
    blob_edit(t, "blob7", lambda s: s["dials"].__setitem__(3, s["dials"][3] + 1))


def m_heart(t):
    blob_edit(t, "blob7", lambda s: s["heart"]["k"].__setitem__(0, s["heart"]["k"][0] + 1))


def m_door(t):
    blob_edit(t, "blob7", lambda s: s.__setitem__("door", {**s["door"], "zzz": {"bound": None, "answers": []}}))


def m_nonthink_act(t):
    r = first(t["records7"], lambda r: r["kind"] == "act" and r.get("act_type") not in ("think",))
    r["act"] = ["mutated"]


def m_nonthink_reason_removed(t):
    r = first(t["records7"], lambda r: r["kind"] == "reason" and r.get("act_type") not in ("think",))
    t["records7"].remove(r)


def m_verdict(t):
    d = diary7(t)[len(diary7(t)) // 2]["entry"]["self"]["self5"]["kinds"]["BODY-MEMORY"]
    d["verdict"] = "UNRESOLVED" if d.get("verdict") != "UNRESOLVED" else "FINE"


def m_declared_before_divergence(t):
    r = first(t["records7"], lambda r: r["kind"] == "dream" and (first_night is None or r["night"] < first_night))
    r["ticks"] = r["ticks"] + 1


def m_undeclared_removed(t):
    t["records7"].remove(first(t["records7"], lambda r: r["kind"] == "heard"))


def m_night_moved(t):
    r = first(t["records7"], lambda r: r["kind"] == "night-reading")
    r["moved"] = [1 - int(bool(x)) for x in r["moved"]] if isinstance(r["moved"], list) else (not r["moved"])


def m_bp_path(t):
    r = first(t["records7"], lambda r: r["kind"] == "body-predict" and r["path"])
    h = next(iter(r["path"])); r["path"][h][1] = -r["path"][h][1]


def m_bp_memory(t):
    r = first(t["records7"], lambda r: r["kind"] == "body-predict" and r["memory"])
    h = next(iter(r["memory"])); r["memory"][h] += 1


CASES = [("body-predict path guess flipped (declared)", m_bp_path, True),
         ("body-predict memory prediction changed", m_bp_memory, False),
("unchanged", None, True), ("extra sky record", m_extra_sky, True), ("particle 0 changed", m_p0, True),
         ("diary self-reading changed", m_diary_reading, True),
         ("particle 1 one bit", m_p1, False), ("a dial", m_dial, False), ("the heart", m_heart, False),
         ("a door entry", m_door, False), ("a non-think act changed", m_nonthink_act, False),
         ("a non-think reason removed", m_nonthink_reason_removed, False),
         ("a BODY-MEMORY verdict flipped", m_verdict, False),
         ("a declared kind before the first divergent choice", m_declared_before_divergence, False),
         ("an undeclared record removed", m_undeclared_removed, False),
         ("night-reading 'moved' changed", m_night_moved, False)]
out = {"twin": sys.argv[1], "first_divergent_night": first_night, "cases": {}}
for name, fn, must in CASES:
    t = copy.deepcopy(t0)
    try:
        if fn:
            fn(t)
        got = J.k2(t)["passed"]
    except StopIteration:
        got = None                                                # the mutation target does not exist in this life
    ok = "n/a" if got is None else got == must
    out["cases"][name] = {"must_pass": must, "judge_passed": got, "ok": ok}
    print(f"{name:52s} must {'pass' if must else 'fail'}: {'n/a (no target in this life)' if ok == 'n/a' else 'ok' if ok else 'WRONG'}"
          f" ({got})", flush=True)
out["not_applicable"] = [n for n, c in out["cases"].items() if c["ok"] == "n/a"]
out["all_ok"] = all(c["ok"] is True for n, c in out["cases"].items() if n not in out["not_applicable"]) and \
    len(out["not_applicable"]) <= 1
print("ALL OK" if out["all_ok"] else "JUDGE TEST FAILED")
if len(sys.argv) > 2:
    json.dump(out, open(sys.argv[2], "w"), indent=1)
