"""Fetch and verify a range of historical drand rounds into a JSON store (gate inputs; run on a machine with py_ecc).
    python3 beacon_store.py OUT.json FIRST LAST [--proxy HOST:PORT]"""
import json
import sys

import sky_v07 as SKY

out, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
proxy = sys.argv[sys.argv.index("--proxy") + 1] if "--proxy" in sys.argv else None
try:
    store = json.load(open(out))
except FileNotFoundError:
    store = {}
for r in range(a, b + 1):
    if str(r) not in store:
        bc = SKY.fetch(r, proxy=proxy)
        assert int(bc["round"]) == r and SKY.verify(bc), f"round {r} failed verification"
        store[str(r)] = bc
json.dump(store, open(out, "w"), sort_keys=True)
print(len(store), "rounds verified and stored")
