"""Generate the gate S1b Kaggle kernel (Ears v9). Pinned env + parity guard on 40 MAMS val sentences vs the laptop's v9
reference (out_smoke/S1b_smoke.json), then R-v9 and S1b (the one scored look) only if parity holds. Run after the judge."""
import base64
import json
import sys
from pathlib import Path

MODE = "s1b"
ROOT = Path(__file__).resolve().parents[1]; B = ROOT / "build"
names = ["ears_v04.py", "ears_v05.py", "ears_v06.py", "ears_v07.py", "ears_v09.py", "generic_you.py", "s1b_trust.py",
         "gates_v04_s1b.py", "ref/A2e_v7_detail.json", "out_smoke/A2d_smoke.json", "genome_v04.py", "creature_v04.py", "seat_v04.py",
         "vocab_v04.json", "geometry_v04.json", "geometry_v04.bin", "talk_v04.py"]
files = {f"build/{n}": base64.b64encode((B / n).read_bytes()).decode() for n in names}
files["data_heldout/mams/val.xml"] = base64.b64encode((ROOT / "data_heldout/mams/val.xml").read_bytes()).decode()
files["ears_founder_set/s1_audit.txt"] = base64.b64encode((ROOT / "ears_founder_set/s1_audit.txt").read_bytes()).decode()
for n in ("a2e_labels.jsonl", "s1_sentences.jsonl", "s1b_labels.jsonl", "s1b_trust.json"):
    files[f"data_heldout/dialog/{n}"] = base64.b64encode((ROOT / "data_heldout/dialog" / n).read_bytes()).decode()
manifest = {}
for l in open(ROOT / "specs/MANIFEST_S1b.sha256"):
    h, p = l.split(); p = p.replace("../", "")
    manifest[p if p.startswith(("specs/", "ears_founder_set/", "kaggle", "data_heldout/")) else f"build/{p}"] = h
ref = json.load(open(ROOT / "build/out_smoke/S1b_smoke.json"))["detail"]

src = f'''# Teich v0.4 Ears — {MODE.upper()} kernel (spec anchored teich-03, ref v04-spec-S1b).
import base64, hashlib, json, os, subprocess, sys
MODE = "{MODE}"
FILES = json.loads({json.dumps(json.dumps(files))})
MANIFEST = {json.dumps(manifest)}
REF = json.loads({json.dumps(json.dumps(ref))})
PINS = {{"torch": "2.3.1", "numpy": "1.26.4", "transformers": "4.44.2", "tokenizers": "0.19.1",
         "sentence_transformers": "3.0.1", "huggingface_hub": "0.24.7", "spacy": "3.8.16"}}
def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"$ {{cmd[:120]}}\\n  exit {{r.returncode}}\\n" + (r.stdout[-800:] + r.stderr[-1500:] if r.returncode else ""), flush=True)
    return r.returncode
def stop(msg):
    print("STOP:", msg, flush=True); json.dump({{"stopped": msg}}, open("STATUS.json", "w")); sys.exit(0)

for p, b in FILES.items():
    os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "wb").write(base64.b64decode(b))
bad = [p for p, h in MANIFEST.items() if p in FILES and hashlib.sha256(open(p, "rb").read()).hexdigest() != h]
if bad: stop(f"manifest mismatch {{bad}}")
print("manifest check: OK", flush=True)

# ---- pinned Python 3.12 environment (Kaggle's own Python is 3.13; the pins have no 3.13 builds)
PY = "/tmp/venv/bin/python"; UV = f"{{sys.executable}} -m uv"
for c in ("pip install -q uv", f"{{UV}} python install 3.12", f"{{UV}} venv -p 3.12 /tmp/venv",
          f"{{UV}} pip install --python {{PY}} --index-url https://download.pytorch.org/whl/cpu torch==2.3.1",
          f"{{UV}} pip install --python {{PY}} numpy==1.26.4 transformers==4.44.2 tokenizers==0.19.1 "
          f"sentence-transformers==3.0.1 huggingface_hub==0.24.7 spacy==3.8.16 "
          f"https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl"):
    if sh(c): stop(f"setup failed: {{c[:80]}}")
ver = subprocess.run([PY, "-c", "import json,sys,torch,numpy,transformers,tokenizers,sentence_transformers,huggingface_hub,spacy;"
                      "print(json.dumps({{m: sys.modules[m].__version__ for m in ['torch','numpy','transformers','tokenizers',"
                      "'sentence_transformers','huggingface_hub','spacy']}}))"], capture_output=True, text=True)
got = json.loads(ver.stdout.strip().splitlines()[-1]) if ver.returncode == 0 else {{}}
print("versions:", got, flush=True)
wrong = {{k: got.get(k) for k, v in PINS.items() if not str(got.get(k, "")).startswith(v)}}
if wrong: stop(f"pinned versions not met: {{wrong}}")
dl = (
    "import os\\nfrom huggingface_hub import snapshot_download\\n"
    "hub=os.path.expanduser('~/.cache/huggingface/hub')\\n"
    "for repo, rev in (('Qwen/Qwen2.5-1.5B-Instruct','989aa7980e4cf806f80c7fef2b1adb7bc71aa306'),"
    "('sentence-transformers/all-MiniLM-L6-v2','1110a243fdf4706b3f48f1d95db1a4f5529b4d41')):\\n"
    "    snapshot_download(repo, revision=rev)\\n"
    "    d=os.path.join(hub,'models--'+repo.replace('/','--'),'refs'); os.makedirs(d, exist_ok=True)\\n"
    "    open(os.path.join(d,'main'),'w').write(rev)\\n")
if subprocess.run([PY, "-c", dl]).returncode: stop("model download failed")
print("models pinned", flush=True)
cpu = next((l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")), "?")

# ---- parity: hear the 40 MAMS val sentences exactly as the laptop did
r = subprocess.run([PY, "gates_v04_s1b.py", "smoke"], cwd="build", capture_output=True, text=True)
if r.returncode: stop("smoke run failed: " + r.stderr[-1500:])
mine = json.load(open("build/out_smoke/S1b_smoke.json"))
diff = [i for i, (a, b) in enumerate(zip(mine["detail"], REF)) if a != b]
parity = {{"cpu": cpu, "sentences": len(REF), "mentions": sum(len(x["heard"]) for x in REF),
           "sentences_differing": len(diff), "differing_idx": diff}}
json.dump(parity, open("PARITY.json", "w"), indent=1); print("PARITY:", json.dumps(parity), flush=True)
if diff: stop(f"Kaggle hears differently from the laptop on {{len(diff)}} of {{len(REF)}} sentences")

# ---- the one scored look
for g in ("rv9", "s1b"):
    r = subprocess.run([PY, "gates_v04_s1b.py", g], cwd="build", capture_output=True, text=True)
    print(g, "exit", r.returncode, r.stdout[-2500:], r.stderr[-1500:] if r.returncode else "", flush=True)
json.dump({{"ok": "scored run finished", "cpu": cpu}}, open("STATUS.json", "w"))
'''
out = ROOT / "kaggle_s1b"; out.mkdir(exist_ok=True)
(out / "s1b.py").write_text(src)
json.dump({"id": "mhmdrzaqjvnd/teich-v04-s1b", "title": "teich-v04-s1b", "code_file": "s1b.py",
           "language": "python", "kernel_type": "script", "is_private": True, "enable_gpu": False, "enable_tpu": False,
           "enable_internet": True, "dataset_sources": [], "competition_sources": [], "kernel_sources": []},
          open(out / "kernel-metadata.json", "w"), indent=1)
print(out, len(src), "bytes")
