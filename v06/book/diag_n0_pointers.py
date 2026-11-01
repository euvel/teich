"""POST-HOC DIAGNOSTIC, not a gate (written 2026-10-31 after the scored N0' failed; the verdict stands as judged).
Question: are the N0' differences only seq pointers shifted by the declared records (thought, think-predict, dream,
thought-refused), whose number legitimately differs between twins after the first deliberated choice?
Test: renumber every seq pointer to the count of UNDECLARED records up to it (instead of all records), then rerun
N0' (b) and (e). Also report, for every differing leaf under the pre-registered canon, whether it is a pointer.
    python3 diag_n0_pointers.py OUT.json twin_*.json
"""
import bisect
import json
import sys

import twin_judge as J


def canon_undeclared(recs, also=None):
    kept = sorted((r for r in recs if r["kind"] != "op"), key=lambda r: r["seq"])
    useqs = [r["seq"] for r in kept if r["kind"] not in J.DECLARED_KINDS]

    def fix(x):
        if isinstance(x, dict):
            return {k: (bisect.bisect_right(useqs, v) if k in J.POINTERS and isinstance(v, int) else fix(v))
                    for k, v in x.items() if k != "seq"}
        if isinstance(x, list):
            return [fix(v) for v in x]
        return x
    if also is not None:
        return [fix(r) for r in kept], fix(also)
    return [fix(r) for r in kept]


def leaves(a, b, p=""):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in set(a) | set(b):
            yield from leaves(a.get(k), b.get(k), f"{p}.{k}")
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            yield from leaves(x, y, f"{p}[]")
    elif a != b:
        yield p


def diag(t):
    out = {}
    # 1. under the pre-registered canon: which leaves differ, in undeclared kinds?
    a = [J.as_v05(r) for r in J.canon(t["records5"])]
    b = [J.as_v05(r) for r in J.canon(t["records6"])]
    paths, nonptr = set(), set()
    for k in sorted({r["kind"] for r in a} | {r["kind"] for r in b}):
        if k in J.DECLARED_KINDS:
            continue
        sa = [r for r in a if r["kind"] == k and not J.is_think(r)]
        sb = [r for r in b if r["kind"] == k and not J.is_think(r)]
        if len(sa) != len(sb):
            nonptr.add(f"{k}: count {len(sa)} vs {len(sb)}")
            continue
        for x, y in zip(sa, sb):
            for p in leaves(x, y, k):
                paths.add(p)
                if p.rsplit(".", 1)[-1] not in J.POINTERS:
                    nonptr.add(p)
    out["differing_leaves"] = sorted(paths)
    out["non_pointer_leaves"] = sorted(nonptr)
    # 2. under undeclared-only pointer numbering: are undeclared streams and the state identical?
    a = [J.as_v05(r) for r in canon_undeclared(t["records5"])]
    b = [J.as_v05(r) for r in canon_undeclared(t["records6"])]
    bad = []
    for k in sorted({r["kind"] for r in a} | {r["kind"] for r in b}):
        if k in J.DECLARED_KINDS:
            continue
        if [r for r in a if r["kind"] == k and not J.is_think(r)] != [r for r in b if r["kind"] == k and not J.is_think(r)]:
            bad.append(k)
    out["undeclared_kinds_differ_after"] = bad
    s5, s6 = json.loads(t["blob5"]), json.loads(t["blob6"])
    for s, recs in ((s5, t["records5"]), (s6, t["records6"])):
        _, (le, me) = canon_undeclared(recs, also=[s.get("last_entry"), s["self"]])
        s["last_entry"] = J.drop_think(le); s["self"] = J.drop_think(me)
    out["state_diff_after"] = sorted(k for k in set(s5) | set(s6)
                                     if k not in ("v", "species", "seq", "work", "growth", "self") and s5.get(k) != s6.get(k))
    out["self_diff_after"] = sorted(k for k in set(s5["self"]) | set(s6["self"]) if s5["self"].get(k) != s6["self"].get(k))
    out["declared_count_5_6"] = [sum(r["kind"] in J.DECLARED_KINDS for r in t["records5"]),
                                 sum(r["kind"] in J.DECLARED_KINDS for r in t["records6"])]
    out["only_pointers"] = not out["non_pointer_leaves"] and not bad and not out["state_diff_after"] and not out["self_diff_after"]
    return out


if __name__ == "__main__":
    res = {}
    for p in sys.argv[2:]:
        t = json.load(open(p))
        res[t["seed"]] = diag(t)
        print(t["seed"], res[t["seed"]]["only_pointers"], res[t["seed"]]["declared_count_5_6"],
              res[t["seed"]]["non_pointer_leaves"][:5], flush=True)
    json.dump(res, open(sys.argv[1], "w"), indent=1)
