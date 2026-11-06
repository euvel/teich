"""Gate M0 (PREREG_V07 §2): is the v0.6 -> v0.7 migration lossless? On a COPY of a v0.6 state blob (never the seat itself):
  1. migrate() refuses a pending growth proposal and a non-v0.5 creature (checked on doctored copies)
  2. the v0.6 blob round-trips exactly (dump(load(b)) == b)
  3. every state field is carried unchanged, except: species, blob version, growth.version/base/identity/amendments;
     the new field sky = {touched_day}: the current day if its touch tick has passed, else the day before
  4. the identity chain recomputes: new = sha256(previous + sha256(amendment doc)), the doc names the before-state sha
  5. exactly one record is added, the typed "genome-amendment" link, and F1's log checks still find 0 flags
  6. 0 ticks lived: n, t0 and the body unchanged
    python3 m0_v07.py BLOB_V06.json SPEC_SHA ANCHOR VERDICT_SHA [OUT.json]
"""
from __future__ import annotations

import hashlib
import json
import sys

import creature_v06 as C6
import creature_v07 as C7
import genome_v04 as GN
import f1_v06 as F

CARRIED_EXCEPT = {"v", "species", "growth", "sky"}


def m0(BIN: str, change: dict, log_records=()):
    r = {}
    DIN = json.loads(BIN)
    # 1. refusals
    pend = json.loads(BIN); pend["growth"]["proposal"] = {"act_id": -1, "bindings": [["zz", 0]], "prediction": {}}
    try:
        C7.migrate(json.dumps(pend, sort_keys=True), change); r["refuses_pending"] = False
    except ValueError:
        r["refuses_pending"] = True
    if DIN["growth"]["proposal"] is not None:
        r["real_has_pending_proposal"] = True
        return {**r, "passed": False, "why": "the real state has a pending growth proposal: no amendment now (§3.5)"}
    BOUT = C7.migrate(BIN, change)
    try:
        C7.migrate(BOUT, change); r["refuses_v07"] = False
    except ValueError:
        r["refuses_v07"] = True
    # 2. round trip
    r["roundtrip_exact"] = C7.dump_state(C7.load_state(BOUT)) == BOUT
    DOUT = json.loads(BOUT)
    # 3. carried fields
    r["changed_fields"] = sorted(k for k in set(DIN) | set(DOUT) if k not in CARRIED_EXCEPT and k != "outbox"
                                 and DIN.get(k) != DOUT.get(k))
    GIN, GOUT = DIN["growth"], DOUT["growth"]
    r["growth_changed"] = sorted(k for k in set(GIN) | set(GOUT) if GIN.get(k) != GOUT.get(k))
    # 4. identity chain
    rec = [x for x in DOUT["outbox"] if x["kind"] == "genome-amendment"]
    doc = rec[0]["amendment"] if rec else {}
    a_sha = hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()
    r["identity_ok"] = bool(rec) and (
        doc.get("state_before_sha256") == hashlib.sha256(BIN.encode()).hexdigest()
        and rec[0]["prev_identity"] == GIN["identity"] and rec[0]["amendment_sha"] == a_sha
        and GOUT["identity"] == hashlib.sha256((GIN["identity"] + a_sha).encode()).hexdigest() == rec[0]["identity"]
        and GOUT["version"] == "0.7.0" and doc.get("from_version") == GIN["version"])
    # 5. one record added, F1 over the whole known log
    r["records_added"] = [x["kind"] for x in DOUT["outbox"] if x["seq"] > DIN["seq"]]
    allrecs = list(log_records) + [x for x in DOUT["outbox"] if x["seq"] > max((y["seq"] for y in log_records), default=0)]
    r["f1"] = F.check_log(allrecs)
    # 6. no life lived
    r["ticks_lived"] = DOUT["n"] - DIN["n"] if "n" in DIN else None
    day = DIN["n"] // GN.DAY
    r["touched_day_ok"] = DOUT.get("sky") == {"touched_day": day if DIN["n"] % GN.DAY > GN.DAY - C7.SKY_LEAD else day - 1}
    r["passed"] = (r["refuses_pending"] and r["refuses_v07"] and r["roundtrip_exact"]
                   and set(r["changed_fields"]) <= {"seq"} and set(r["growth_changed"]) <= {"version", "base", "identity", "amendments"}
                   and r["identity_ok"] and r["touched_day_ok"] and r["records_added"] == ["genome-amendment"] and r["ticks_lived"] in (0, None)
                   and all(v == 0 for k, v in r["f1"].items() if k not in ("acts", "necessity_tested")))
    return r, BOUT


if __name__ == "__main__":
    blob = open(sys.argv[1]).read()
    d = json.loads(blob)
    blob = next((d[k] for k in ("state_blob", "blob") if k in d), blob)      # a seat state or a lab life file
    res, _ = m0(blob, {"spec_sha256": sys.argv[2], "anchor": sys.argv[3], "verdict_sha256": sys.argv[4]})
    print(json.dumps(res, indent=1))
    if len(sys.argv) > 5:
        json.dump(res, open(sys.argv[5], "w"), indent=1)
