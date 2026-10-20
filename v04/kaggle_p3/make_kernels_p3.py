"""Generate the 4 part 3 SCORED kernels (spec part 3, anchored teich-03 ref v04-spec-part3). CPU, internet off.
Each kernel: manifest check, body substrate gate, then 4 processes in parallel:
  k0: s8 2000, s8 2001, c1 2160 A, c1 2160 B        k1: s8 2002, s8 2003, c1 2161 A, c1 2161 B
  k2: s8 2004, s8 2005, streams, then c2 + demo     k3: s8 2006, s8 2007, c2
"""
import base64, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; B = ROOT / "build"
names = ["genome_v04.py", "creature_v04.py", "creature_v04s.py", "self_v04.py", "self_sim.py", "seat_v04.py", "seat_v04s.py",
         "gates_v04.py", "gates_v04_part3.py", "vocab_v04.json", "geometry_v04.json", "geometry_v04.bin",
         "gate_fixture_v04.json", "gate_v04.json", "ref/R2e_v7.json"]
files = {n: base64.b64encode((B / n).read_bytes()).decode() for n in names}
manifest = {}
for l in open(ROOT / "specs/CODE_MANIFEST_part3.sha256"):
    h, p = l.split()
    manifest[p] = h
JOBS = {0: [["s8", "2000"], ["s8", "2001"], ["c1", "2160", "A"], ["c1", "2160", "B"]],
        1: [["s8", "2002"], ["s8", "2003"], ["c1", "2161", "A"], ["c1", "2161", "B"]],
        2: [["s8", "2004"], ["s8", "2005"], ["streams"]],
        3: [["s8", "2006"], ["s8", "2007"], ["c2"]]}
for k, jobs in JOBS.items():
    src = f'''# Teich v0.4 SCORED gate run, spec part 3 (the self), anchored teich-03 ref v04-spec-part3. Kernel {k}.
import base64, hashlib, json, os, subprocess, sys
FILES = json.loads({json.dumps(json.dumps(files))})
MANIFEST = {json.dumps(manifest)}
for p, b in FILES.items():
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True); open(p, "wb").write(base64.b64decode(b))
bad = [p for p in FILES if p not in MANIFEST or hashlib.sha256(open(p, "rb").read()).hexdigest() != MANIFEST[p]]
print("manifest check:", "OK" if not bad else f"MISMATCH {{bad}}", flush=True)
if bad: sys.exit(1)
subprocess.run([sys.executable, "gates_v04.py", "substrate"])
JOBS = {json.dumps(jobs)}
procs = [subprocess.Popen([sys.executable, "gates_v04_part3.py"] + j, stdout=open("job_" + "_".join(j) + ".log", "w"),
                          stderr=subprocess.STDOUT) for j in JOBS]
rc = [p.wait() for p in procs]
if {k} == 2:
    rc.append(subprocess.run([sys.executable, "gates_v04_part3.py", "c2"]).returncode)
    rc.append(subprocess.run([sys.executable, "gates_v04_part3.py", "demo"]).returncode)
print("exit codes", rc, "| out_part3:", sorted(os.listdir("out_part3")), flush=True)
json.dump({{"ok": all(r == 0 for r in rc), "exit": rc}}, open("STATUS.json", "w"))
'''
    out = ROOT / f"kaggle_p3_{k}"; out.mkdir(exist_ok=True); (out / f"p3_{k}.py").write_text(src)
    json.dump({"id": f"mhmdrzaqjvnd/teich-v04-gates-part3-{k}", "title": f"teich-v04-gates-part3-{k}", "code_file": f"p3_{k}.py",
               "language": "python", "kernel_type": "script", "is_private": True, "enable_gpu": False, "enable_tpu": False,
               "enable_internet": False, "dataset_sources": [], "competition_sources": [], "kernel_sources": []},
              open(out / "kernel-metadata.json", "w"), indent=1)
    print(out, len(src), "bytes")
