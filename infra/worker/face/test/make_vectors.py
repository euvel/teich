"""Reference vectors for delib.js: Python's delib_cert / think_2 on (1) every v0.6 lab night's u at every k = 2..9,
(2) every logged think@2 choice, (3) 25,000 random u per k.   python3 make_vectors.py BUILD_DIR LIVES_DIR OUT.json"""
import glob, json, random, sys
sys.path.insert(0, sys.argv[1])
import delib_cert as DC, acts_v06 as A
us, choices = [], []
for f in sorted(glob.glob(sys.argv[2] + "/twin_*.json")):
    for r in json.load(open(f))["records6"]:
        if r["kind"] == "reason" and r.get("rule") == "think@2":
            us.append(r["inputs"]["u"]); choices.append({"lc": r["inputs"]["life_counts"], "u": r["inputs"]["u"],
                                                         "act": A.think_2(r["inputs"])})
rng = random.Random(20261101)
rand = [rng.random().hex() for _ in range(25000)]
vec = []
for u in us + rand:
    for k in range(2, 10):
        c, steps, rr, (x, y), und = DC.deliberate(k, float.fromhex(u))
        vec.append([k, u, c, steps, rr, x.hex(), y.hex(), und])
json.dump({"lab_nights": len(us), "vectors": vec, "choices": choices}, open(sys.argv[3], "w"))
print(len(us), "lab nights,", len(vec), "vectors,", len(choices), "logged choices")
