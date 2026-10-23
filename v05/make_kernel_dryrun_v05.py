"""Amendment 1 re-look: the end-to-end dry run alone, on fresh seed 9991, real Ears v7 in the pinned Part-2 env.
Files are checked against the anchored manifest with amendment 1's entries applied (specs/AMENDMENT1_v05.sha256).
"""
import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent; B = ROOT / "build"
MANIFEST = {}
for f in ("specs/CODE_MANIFEST_v05.sha256", "specs/AMENDMENT1_v05.sha256"):
    for l in open(ROOT / f):
        h, p = l.split(); MANIFEST[p] = h
MANIFEST["data_heldout/mams/val.xml"] = MANIFEST["../../v04_lab/data_heldout/mams/val.xml"]
EARS = ["acts_v05.py", "creature_v04.py", "creature_v04s.py", "creature_v05.py", "ears_v04.py", "ears_v05.py", "ears_v06.py",
        "ears_v07.py", "f1_v05.py", "dryrun_v05.py", "genome_v04.py", "geometry_v04.bin", "geometry_v04.json",
        "seat_v04.py", "seat_v04s.py", "seat_v05.py", "self_sim.py", "self_text_v04.py", "self_text_v05.py",
        "self_v04.py", "self_v05.py", "talk_v04s.py", "talk_v05.py", "think_model_v05.py", "vocab_v04.json",
        "body_pants.py", "handle_mp.py", "mind4.py", "surface.py", "work_v05.py"]
files = {f"build/{n}": base64.b64encode((B / n).read_bytes()).decode() for n in EARS}
env = (ROOT / "kaggle_q3/q3.py").read_text()
env = env[env.index("def sh(c):"):env.index('r = subprocess.run([PY, "q3_v05.py"')]
src = f'''# Teich v0.5 SCORED, amendment 1: end-to-end dry run re-look (seed 9991), real Ears v7, pinned Part-2 env.
import base64, hashlib, json, os, subprocess, sys
FILES = json.loads({json.dumps(json.dumps(files))})
MANIFEST = {json.dumps(MANIFEST)}
for p, b in FILES.items():
    os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "wb").write(base64.b64decode(b))
bad = [p for p in FILES if p.startswith("build/") and (p[6:] not in MANIFEST or hashlib.sha256(open(p, "rb").read()).hexdigest() != MANIFEST[p[6:]])]
print("manifest check:", "OK" if not bad else f"MISMATCH {{bad}}", flush=True)
if bad: json.dump({{"stopped": "manifest mismatch", "bad": bad}}, open("STATUS.json", "w")); sys.exit(1)
subprocess.run("pip install -q mpmath", shell=True)
''' + env + '''
os.makedirs("build/out_v05", exist_ok=True)
r = subprocess.run([PY, "dryrun_v05.py", "out_v05/dry_run.json", "9991"], cwd="build", capture_output=True, text=True)
print(r.returncode, r.stdout[-4000:], r.stderr[-4000:], flush=True)
json.dump({"ok": r.returncode == 0, "exit": r.returncode}, open("STATUS.json", "w"))
'''
out = ROOT / "kaggle_v05_dryrun"; out.mkdir(exist_ok=True); (out / "dryrun.py").write_text(src)
json.dump({"id": "mhmdrzaqjvnd/teich-v05-gates-dryrun", "title": "teich-v05-gates-dryrun", "code_file": "dryrun.py",
           "language": "python", "kernel_type": "script", "is_private": True, "enable_gpu": False, "enable_tpu": False,
           "enable_internet": True, "dataset_sources": [], "competition_sources": [], "kernel_sources": []},
          open(out / "kernel-metadata.json", "w"), indent=1)
print(out, len(src), "bytes")
