"""Amendment 2 adversarial check (not scored): the amended N0' canon must pass the real twin unchanged,
pass an extra DECLARED record, and still fail every real undeclared change, pointer changes included.
    python3 test_amend2.py TWIN.json
"""
import copy
import json
import sys

sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/build")
import twin_judge as J

t0 = json.load(open(sys.argv[1]))


def run(name, mutate, want):
    t = copy.deepcopy(t0)
    mutate(t)
    got = J.n0(t)["passed"]
    print(f"{'ok ' if got == want else 'BAD'} {name}: passed={got} (want {want})")
    return got == want


def nth(t, kind, i=-5):
    return [r for r in t["records6"] if r["kind"] == kind][i]


def insert_declared(t):              # an extra thought-refused late in v0.6's log: declared, must not shift pointers
    recs = t["records6"]; k = len(recs) // 2; s = recs[k]["seq"]
    for r in recs[k:]:
        r["seq"] += 1
        for p in J.POINTERS:
            if isinstance(r.get(p), int) and r[p] >= s:
                r[p] += 1
    _bump(t, s)
    recs.insert(k, {"kind": "thought-refused", "seq": s, "why": "test"})


def _bump(t, s):
    def fix(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in J.POINTERS and isinstance(v, int) and v >= s:
                    x[k] = v + 1
                else:
                    fix(v)
        elif isinstance(x, list):
            for v in x:
                fix(v)
    for r in t["records6"]:
        if r["seq"] >= s:
            fix({k: v for k, v in r.items() if k not in J.POINTERS})
    d = json.loads(t["blob6"]); fix(d.get("last_entry")); fix(d["self"]); t["blob6"] = json.dumps(d, sort_keys=True)


def pointer_plus1(t):                # an outcome pointing one undeclared record later
    nth(t, "outcome")["predict_seq"] += 50


def diary_pointer(t):
    nth(t, "diary")["entry"]["self"]["log_through"] -= 40


def outcome_content(t):
    o = nth(t, "outcome"); k = next(k for k in o if k not in ("seq", "kind", "predict_seq")); o[k] = "tampered"


def drop_outcome(t):
    t["records6"].remove(nth(t, "outcome"))


ok = all([
    run("extra declared record", insert_declared, True),
    run("outcome pointer moved", pointer_plus1, False),
    run("diary pointer moved", diary_pointer, False),
    run("outcome content changed", outcome_content, False),
    run("an outcome removed", drop_outcome, False),
])
print("real twin under amended canon:", J.n0(t0)["passed"])
print("ALL OK" if ok else "FAILURES")
