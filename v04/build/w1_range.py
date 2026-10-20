"""W1 (design): does the handle stay a sound piece of surface over the wide attention range 0..40 steps of 2.5%?"""
import json, math, sys, time
sys.path.insert(0, "..")
import mind4 as M
M.DELTA = 0.025
hc = M.HandleCache()
rows = []
t0 = time.time()
for n in range(0, 41):
    h = hc.get(n)
    rows.append({"n": n, "dial_len": h["dial_len"], "len_ratio": h["dial_len"] / hc.get(0)["dial_len"],
                 "area_err": h["dom"]["area"] - 2 * math.pi, "faces": len(h["dom"]["faces"]),
                 "radius": h["dom"]["radius"], "dial_lifts": len(h["dial_lifts"])})
    r = rows[-1]
    print(f"n={n:2d} len x{r['len_ratio']:.4f} area_err {r['area_err']:+.1e} faces {r['faces']} radius {r['radius']:.3f} lifts {r['dial_lifts']}  {time.time()-t0:.0f}s", flush=True)
json.dump(rows, open("w1_range.json", "w"), indent=1)
