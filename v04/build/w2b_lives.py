"""W2b (design seeds 900+): the wake path is the same life.

Life A lives through the seat: genesis import, daily wakes (gate first), conversations (lease -> load -> live up to now ->
hear -> commit), one lawful commitment. Every step serializes the creature to its blob and back.
Life B lives the same schedule continuously in memory, never serialized.
PASS = final blobs byte-identical, diaries identical, every blob round-trips exactly, every law exercised and logged.

    python3 w2b_lives.py DAYS [mentions_per_day] [A|B|both|compare]
"""
import json, sys, time
from pathlib import Path
import numpy as np
import creature_v04 as CR, genome_v04 as GN, seat_v04 as SV

DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 2
RATE = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
MODE = sys.argv[3] if len(sys.argv) > 3 else "both"
T0 = 1_000_000.0
OUT = Path(f"w2b_D{DAYS}")
OUT.mkdir(exist_ok=True)

rng = np.random.default_rng(900)
w = 1 / np.arange(1, GN.G + 1) ** 1.1; w /= w.sum(); order = rng.permutation(GN.G)
sched = []                                                  # (time, kind, payload)
for d in range(DAYS):
    sched.append((T0 + d * GN.DAY + 3_700 + int(rng.integers(0, 600)), "wake", None))
    for ci in range(int(rng.poisson(RATE / 3))):
        t = T0 + d * GN.DAY + int(rng.integers(5_000, 80_000))
        ments = [(int(order[rng.choice(GN.G, p=w)]), int(rng.choice([1, 1, -1, 0])), f"{d}-{ci}-{k}".encode().hex())
                 for k in range(int(rng.integers(1, 6)))]
        if rng.random() < 0.3:
            ments.append(ments[0])                                     # repeats inside a conversation (law 1)
        sched.append((t, "talk", (f"conv-{d}-{ci}", ments)))
sched.append((T0 + 1 * GN.DAY + 50_000, "commit", 97))                   # commit the self dial on day 1
sched.append((T0 + 1 * GN.DAY + 50_001, "talk", ("conv-x", [(97, 1, "ab" * 32)])))    # must be refused: committed
if DAYS >= 2:                                                            # a crowd on day 1: speed limit must bite
    sched += [(T0 + 1 * GN.DAY + 60_000 + i, "talk", (f"crowd-{i}", [(int(i % GN.G), 1, f"c{i}".encode().hex())]))
              for i in range(20)]
sched.sort(key=lambda e: (e[0], e[1]))
END = T0 + DAYS * GN.DAY + 7_200

birth_blob = CR.dump_state(CR.birth(seed=901, t0=T0))
assert CR.dump_state(CR.load_state(birth_blob)) == birth_blob

def life_A():
    # ---------------------------------------------------------------- life A: through the seat
    t = time.time()
    seat = SV.LocalSeat(OUT / "seatA.json")
    if seat.path.exists():
        seat.path.unlink()
    seat.genesis_import(birth_blob, 0, "lab")
    roundtrips = 0
    def check_roundtrip():
        nonlocal roundtrips
        b = json.loads(seat.path.read_text())["blob"]
        assert CR.dump_state(CR.load_state(b)) == b; roundtrips += 1
    quiet = lambda *a: None
    for (tm, kind, p) in sched:
        if kind == "wake":
            SV.wake(seat, now=tm, run_gate=True, log=quiet)
        elif kind == "talk":
            SV.converse(seat, p[1], p[0], "founder", now=tm)
        else:
            lease = seat.lease(); c = CR.load_state(lease["state_blob"]); c.ack(seat.log_seq())
            c.advance(int(tm - c.t0) - c.n)
            c.commit(p, {"speaker": "founder", "conversation": "commit-self", "text_sha256": "cd" * 32}, "lawful")
            seat.commit(lease["lease_id"], CR.dump_state(c), c.n); seat.append_log(c.outbox)
        check_roundtrip()
    SV.wake(seat, now=END, log=quiet); check_roundtrip()
    A = json.loads(seat.path.read_text())
    tA = time.time() - t

    json.dump({'seat': A, 'roundtrips': roundtrips, 'seconds': tA}, open(OUT / 'lifeA.json', 'w'))


def life_B():
    # ---------------------------------------------------------------- life B: continuous, in memory
    t = time.time()
    c = CR.load_state(birth_blob); diaryB = []
    for (tm, kind, p) in sched:
        diaryB += c.advance(int(tm - c.t0) - c.n)
        if kind == "talk":
            for j, s, h in p[1]:
                c.hear(j, s, {"speaker": "founder", "conversation": p[0], "text_sha256": h})
        elif kind == "commit":
            c.commit(p, {"speaker": "founder", "conversation": "commit-self", "text_sha256": "cd" * 32}, "lawful")
    diaryB += c.advance(int(END - c.t0) - c.n)
    blobB = CR.dump_state(c)
    tB = time.time() - t

    json.dump({'blob': blobB, 'diary': diaryB, 'seconds': tB}, open(OUT / 'lifeB.json', 'w'))


def compare():
    a = json.load(open(OUT / "lifeA.json")); b = json.load(open(OUT / "lifeB.json"))
    A, blobB, diaryB = a["seat"], b["blob"], b["diary"]
    c = CR.load_state(blobB); cA = CR.load_state(A["blob"])
    streamB = c.outbox
    streamA = A["log"] + [r for r in cA.outbox if r["seq"] > (A["log"][-1]["seq"] if A["log"] else 0)]
    heard = [r for r in streamB if r["kind"] == "heard"]
    why = {}
    for e in heard:
        why[e["mind"]] = why.get(e["mind"], 0) + 1
    hwhy = {}
    for e in heard:
        hwhy[e["heart"]] = hwhy.get(e["heart"], 0) + 1
    res = {"days": DAYS, "ticks": c.n, "blob_bytes_seat_life": len(A["blob"]),
           "blob_bytes_never_flushed": len(blobB), "log_records": len(streamA),
           "final_state_identical": CR.dump_state(cA, False) == CR.dump_state(c, False),
           "record_stream_identical": streamA == streamB, "blob_sha256": CR.blob_sha256(CR.dump_state(c, False)),
           "diary_identical": [r["entry"] for r in streamA if r["kind"] == "diary"] == diaryB, "diary_entries": len(diaryB),
           "seat_commits": len(A["chain"]) - 1, "roundtrips_exact": a["roundtrips"],
           "mind_outcomes": why, "heart_outcomes": hwhy, "dials_nonzero": int((c.body.n > 0).sum()),
           "attention_steps": int(c.body.n.sum()), "seconds_A": round(a["seconds"]), "seconds_B": round(b["seconds"])}
    # the diary against the truth (true dials rebuilt from its own log of accepted mentions)
    acc = [(e["tick"], e["cluster"]) for e in heard if e["mind"] == "accepted"]
    v = {"spoken": 0, "spoken_exact": 0, "known_nonzero": 0, "known_exact": 0, "known_false_positive": 0,
         "tonight_exact_frac": []}
    for e in diaryB:
        true = np.zeros(GN.G, int)
        for tk, j in acc:
            if tk < e["tick"]:
                true[j] += 1
        v["spoken"] += e["verification"]["clusters_spoken"]; v["spoken_exact"] += e["verification"]["spoken_read_equals_ledger"]
        v["tonight_exact_frac"].append(e["verification"]["tonight_read_equals_ledger"] / GN.G)
        for js, r in e["known"].items():
            j = int(js)
            if j in e["still_ids"]:
                continue
            v["known_nonzero"] += 1; v["known_exact"] += int(r == true[j]); v["known_false_positive"] += int(true[j] == 0)
    res["diary_vs_truth"] = {"spoken_exact_rate": v["spoken_exact"] / max(1, v["spoken"]), "spoken_readings": v["spoken"],
                             "named_nonzero_readings": v["known_nonzero"],
                             "named_exact_rate": v["known_exact"] / max(1, v["known_nonzero"]),
                             "named_false_positives": v["known_false_positive"],
                             "single_night_exact_rate": float(np.mean(v["tonight_exact_frac"]))}
    print(json.dumps(res, indent=1))
    json.dump({"result": res, "diary": diaryB}, open(OUT / "w2b_result.json", "w"), indent=1)


if MODE in ("A", "both"):
    life_A()
if MODE in ("B", "both"):
    life_B()
if MODE in ("compare", "both"):
    compare()
