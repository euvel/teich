"""W4: the build Ears reproduce the design scores of ears_v4c on its 47 design sentences (same set; not independent)."""
import json, sys, time, contextlib, io
sys.path.insert(0, "/home/euvel/pjs/teichai/v04_lab"); sys.path.insert(0, "/home/euvel/pjs/teichai/v04_lab/build")
with contextlib.redirect_stdout(io.StringIO()):
    import ears_v4_design as V4                     # only for the design set D
import ears_v04 as E, genome_v04 as GN
cl = {w: c["j"] for c in GN.VOCAB["clusters"][:GN.SELF] for w in c["members"]}
ears = E.EarsV4(); t = time.time(); s_ok = c_ok = self_ok = n_self = 0; miss = []
for text, gt, gs in V4.D:
    h = ears.hear_sentence(text)
    gold = GN.SELF if gt == "SELF" else cl[ears.concept_of(gt, gt)]
    s_ok += h["sign"] == gs; c_ok += h["cluster"] == gold
    if gt == "SELF": n_self += 1; self_ok += h["cluster"] == GN.SELF
    if h["cluster"] != gold or h["sign"] != gs: miss.append((text, h["topic_word"], h["concept"], h["sign"], gs))
design = json.load(open("ears_v4c_design.json"))["rows"]
res = {"sign": f"{s_ok}/{len(V4.D)}", "cluster": f"{c_ok}/{len(V4.D)}", "self": f"{self_ok}/{n_self}",
       "design_v4c": {"sign": sum(r["sign_ok"] for r in design), "cluster": sum(r["gold_cluster"] == r["got_cluster"] for r in design)},
       "seconds": round(time.time() - t)}
print(json.dumps(res, indent=1)); [print("  miss:", m) for m in miss]
json.dump({"result": res, "misses": miss}, open("build/w4_ears_repro.json", "w"), indent=1)
