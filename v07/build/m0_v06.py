"""Gate M0 (spec V06 §5): is the migration lossless? On a COPY of a v0.5 state blob (never the seat itself):
  1. migrate() refuses a pending growth proposal and a non-v0.5 creature (checked on doctored copies)
  2. the v0.6 blob round-trips exactly (dump(load(b)) == b)
  3. every state field is carried unchanged, except: species, blob version, growth.version/base/identity/amendments
  4. the identity chain recomputes: new = sha256(previous + sha256(amendment doc)), the doc names the before-state sha
  5. exactly one record is added, the typed "genome-amendment" link, and F1's log checks still find 0 flags
  6. 0 ticks lived: n, t0 and the body unchanged
    python3 m0_v06.py BLOB_V05.json SPEC_SHA ANCHOR VERDICT_SHA [OUT.json]
"""
from __future__ import annotations

import hashlib
import json
import sys

import creature_v05 as C5
import creature_v06 as C6
import f1_v06 as F

CARRIED_EXCEPT = {"v", "species", "growth"}


def m0(blob5: str, change: dict, log_records=()):
    r = {}
    d5 = json.loads(blob5)
    # 1. refusals
    pend = json.loads(blob5); pend["growth"]["proposal"] = {"act_id": -1, "bindings": [["zz", 0]], "prediction": {}}
    try:
        C6.migrate(json.dumps(pend, sort_keys=True), change); r["refuses_pending"] = False
    except ValueError:
        r["refuses_pending"] = True
    if d5["growth"]["proposal"] is not None:
        r["real_has_pending_proposal"] = True
        return {**r, "passed": False, "why": "the real state has a pending growth proposal: no amendment now (§3.5)"}
    blob6 = C6.migrate(blob5, change)
    try:
        C6.migrate(blob6, change); r["refuses_v06"] = False
    except ValueError:
        r["refuses_v06"] = True
    # 2. round trip
    r["roundtrip_exact"] = C6.dump_state(C6.load_state(blob6)) == blob6
    d6 = json.loads(blob6)
    # 3. carried fields
    r["changed_fields"] = sorted(k for k in set(d5) | set(d6) if k not in CARRIED_EXCEPT and k != "outbox"
                                 and d5.get(k) != d6.get(k))
    g5, g6 = d5["growth"], d6["growth"]
    r["growth_changed"] = sorted(k for k in set(g5) | set(g6) if g5.get(k) != g6.get(k))
    # 4. identity chain
    rec = [x for x in d6["outbox"] if x["kind"] == "genome-amendment"]
    doc = rec[0]["amendment"] if rec else {}
    a_sha = hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()
    r["identity_ok"] = bool(rec) and (
        doc.get("state_before_sha256") == hashlib.sha256(blob5.encode()).hexdigest()
        and rec[0]["prev_identity"] == g5["identity"] and rec[0]["amendment_sha"] == a_sha
        and g6["identity"] == hashlib.sha256((g5["identity"] + a_sha).encode()).hexdigest() == rec[0]["identity"]
        and g6["version"] == "0.6.0" and doc.get("from_version") == g5["version"])
    # 5. one record added, F1 over the whole known log
    r["records_added"] = [x["kind"] for x in d6["outbox"] if x["seq"] > d5["seq"]]
    allrecs = list(log_records) + [x for x in d6["outbox"] if x["seq"] > max((y["seq"] for y in log_records), default=0)]
    r["f1"] = F.check_log(allrecs)
    # 6. no life lived
    r["ticks_lived"] = d6["n"] - d5["n"] if "n" in d5 else None
    r["passed"] = (r["refuses_pending"] and r["refuses_v06"] and r["roundtrip_exact"]
                   and set(r["changed_fields"]) <= {"seq"} and set(r["growth_changed"]) <= {"version", "base", "identity", "amendments"}
                   and r["identity_ok"] and r["records_added"] == ["genome-amendment"] and r["ticks_lived"] in (0, None)
                   and all(v == 0 for k, v in r["f1"].items() if k not in ("acts", "necessity_tested")))
    return r, blob6


if __name__ == "__main__":
    blob = open(sys.argv[1]).read()
    d = json.loads(blob)
    blob = next((d[k] for k in ("state_blob", "blob") if k in d), blob)      # a seat state or a lab life file
    res, _ = m0(blob, {"spec_sha256": sys.argv[2], "anchor": sys.argv[3], "verdict_sha256": sys.argv[4]})
    print(json.dumps(res, indent=1))
    if len(sys.argv) > 5:
        json.dump(res, open(sys.argv[5], "w"), indent=1)
