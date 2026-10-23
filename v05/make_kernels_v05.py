"""Generate the v0.5 SCORED kernels (after freeze + anchor). Every kernel checks its files against the anchored
manifest (specs/CODE_MANIFEST_v05.sha256) before running anything.
  b0: n0 2000, n0 2001, c1 9800 A, c1 9800 B        b1: n0 2002, n0 2003, c1 9801 A, c1 9801 B
  b2: n0 2004, n0 2005, g1 9900, oracle 9910 x6      b3: n0 2006, n0 2007, streams, c2
  o1: o1_v05 9950 x4 twins x 40,000 ticks          ears: q3, g1-ears, dry run (pinned Part-2 env, real Ears v7)
"""
import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent; B = ROOT / "build"
MANIFEST = {}
for l in open(ROOT / "specs/CODE_MANIFEST_v05.sha256"):
    h, p = l.split(); MANIFEST[p] = h
MANIFEST["data_heldout/mams/val.xml"] = MANIFEST["../../v04_lab/data_heldout/mams/val.xml"]   # where the Ears kernel unpacks it
BODY = ["acts_v05.py", "body_pants.py", "creature_v04.py", "creature_v04s.py", "creature_v05.py", "f1_v05.py",
        "g1_v05.py", "gate_fixture_v04.json", "gates_v04.py", "gates_v04_part3.py", "gates_v05.py", "gate_v04.json",
        "genome_v04.py", "geometry_v04.bin", "geometry_v04.json", "handle_mp.py", "mind4.py", "o1_v05.py", "oracle_v05.py",
        "q1_v05.py", "seat_v04.py", "seat_v04s.py", "seat_v05.py", "self_sim.py", "self_text_v04.py", "self_text_v05.py",
        "self_v04.py", "self_v05.py", "surface.py", "think_model_v05.py", "vocab_v04.json", "work_v05.py"]
EARS = ["acts_v05.py", "creature_v04.py", "creature_v04s.py", "creature_v05.py", "ears_v04.py", "ears_v05.py", "ears_v06.py",
        "ears_v07.py", "f1_v05.py", "g1_ears_v05.py", "dryrun_v05.py", "genome_v04.py", "geometry_v04.bin", "geometry_v04.json",
        "q3_v05.py", "seat_v04.py", "seat_v04s.py", "seat_v05.py", "self_sim.py", "self_text_v04.py", "self_text_v05.py",
        "self_v04.py", "self_v05.py", "talk_v04s.py", "talk_v05.py", "think_model_v05.py", "vocab_v04.json",
        "body_pants.py", "handle_mp.py", "mind4.py", "surface.py", "work_v05.py"]
EARS_ENV = (Path(ROOT / "kaggle_q3/q3.py").read_text())


def pack(names, extra=None):
    files = {f"build/{n}": base64.b64encode((B / n).read_bytes()).decode() for n in names}
    for k, v in (extra or {}).items():
        files[k] = base64.b64encode(Path(v).read_bytes()).decode()
    return files


def header(files):
    return f'''import base64, hashlib, json, os, subprocess, sys
FILES = json.loads({json.dumps(json.dumps(files))})
MANIFEST = {json.dumps(MANIFEST)}
for p, b in FILES.items():
    os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "wb").write(base64.b64decode(b))
bad = [p for p in FILES if p.startswith("build/") and (p[6:] not in MANIFEST or hashlib.sha256(open(p, "rb").read()).hexdigest() != MANIFEST[p[6:]])]
print("manifest check:", "OK" if not bad else f"MISMATCH {{bad}}", flush=True)
if bad: json.dump({{"stopped": "manifest mismatch", "bad": bad}}, open("STATUS.json", "w")); sys.exit(1)
subprocess.run("pip install -q mpmath", shell=True)
'''


def body_kernel(k, jobs):
    files = pack(BODY)
    src = f"# Teich v0.5 SCORED body kernel {k} (spec V05_SPEC.md, anchored).\n" + header(files) + f'''
JOBS = {json.dumps(jobs)}
procs = [subprocess.Popen([sys.executable, "gates_v05.py"] + j, cwd="build", stdout=open("job_" + "_".join(j) + ".log", "w"),
                          stderr=subprocess.STDOUT) for j in JOBS]
rc = [p.wait() for p in procs]
print("exit codes", rc, sorted(os.listdir("build/out_v05")), flush=True)
json.dump({{"ok": all(r == 0 for r in rc), "exit": rc}}, open("STATUS.json", "w"))
'''
    return src


def write(name, src, gpu=False, internet=True):
    out = ROOT / f"kaggle_v05_{name}"; out.mkdir(exist_ok=True); (out / f"{name}.py").write_text(src)
    json.dump({"id": f"mhmdrzaqjvnd/teich-v05-gates-{name}", "title": f"teich-v05-gates-{name}", "code_file": f"{name}.py",
               "language": "python", "kernel_type": "script", "is_private": True, "enable_gpu": gpu, "enable_tpu": False,
               "enable_internet": internet, "dataset_sources": [], "competition_sources": [], "kernel_sources": []},
              open(out / "kernel-metadata.json", "w"), indent=1)
    print(out, len(src), "bytes")


write("b0", body_kernel("b0", [["n0", "2000"], ["n0", "2001"], ["c1", "9800", "A"], ["c1", "9800", "B"]]))
write("b1", body_kernel("b1", [["n0", "2002"], ["n0", "2003"], ["c1", "9801", "A"], ["c1", "9801", "B"]]))
write("b2", body_kernel("b2", [["n0", "2004"], ["n0", "2005"], ["g1", "9900"], ["oracle", "9910", "6"]]))
write("b3", body_kernel("b3", [["n0", "2006"], ["n0", "2007"], ["streams"], ["c2"]]))
files = pack(BODY)
write("o1", "# Teich v0.5 SCORED: gate O1 (twin dreams), gate seeds 9950+.\n" + header(files) + '''
os.makedirs("build/out_v05", exist_ok=True)
rc = subprocess.run([sys.executable, "o1_v05.py", "9950", "4", "40000", "out_v05/O1.json"], cwd="build").returncode
json.dump({"ok": rc == 0}, open("STATUS.json", "w"))
''')
ears_files = pack(EARS, {"build/data_heldout/mams/val.xml": str(ROOT.parent / "v04_lab/data_heldout/mams/val.xml")})
env = EARS_ENV[EARS_ENV.index("def sh(c):"):EARS_ENV.index('r = subprocess.run([PY, "q3_v05.py"')]
write("ears", "# Teich v0.5 SCORED: Q3, G1 Ears half, end-to-end dry run — real Ears v7, pinned Part-2 env.\n" + header(ears_files) + env + '''
os.makedirs("build/out_v05", exist_ok=True)
rc = []
for script, out in (("q3_v05.py", "out_v05/Q3.json"), ("g1_ears_v05.py", "out_v05/G1_ears.json"), ("dryrun_v05.py", "out_v05/dry_run.json")):
    r = subprocess.run([PY, script, out], cwd="build", capture_output=True, text=True)
    print(script, r.returncode, r.stdout[-2000:], r.stderr[-2000:], flush=True); rc.append(r.returncode)
json.dump({"ok": all(x == 0 for x in rc), "exit": rc}, open("STATUS.json", "w"))
''')
