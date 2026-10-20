"""Generate the S1b judge kernel (Mistral-Small-24B 4-bit, Kaggle 2xT4): smoke 4 sentences, then all 200. Progress streams."""
import base64, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
files = {"build/s1b_label_kaggle.py": base64.b64encode((ROOT / "build/s1b_label_kaggle.py").read_bytes()).decode(),
         "s1_sentences.jsonl": base64.b64encode((ROOT / "data_heldout/dialog/s1_sentences.jsonl").read_bytes()).decode()}
src = f'''# Teich v0.4 gate S1b judge kernel (Amendment 1, broad reading) — independent mirror labels (streams progress)
import base64, json, os, subprocess, sys
FILES = json.loads({json.dumps(json.dumps(files))})
for p, b in FILES.items():
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True); open(p, "wb").write(base64.b64decode(b))
def run(c):
    print("$", c, flush=True); return subprocess.run(c, shell=True).returncode
run("pip install -q 'bitsandbytes>=0.45' 'accelerate>=1.0'")
run("nvidia-smi --query-gpu=name,memory.total --format=csv")
if run("python3 build/s1b_label_kaggle.py s1_sentences.jsonl smoke --limit 4"):
    json.dump({{"stopped": "smoke crashed"}}, open("STATUS.json", "w")); sys.exit(0)
v = [json.loads(l) for l in open("smoke/s1b_votes.jsonl")]
print("SMOKE parsed", sum(x["ok"] for x in v), "/", len(v), [x["answer"] for x in v], flush=True)
if sum(x["ok"] for x in v) < 10:
    json.dump({{"stopped": "smoke: answers do not parse"}}, open("STATUS.json", "w")); sys.exit(0)
rc = run("python3 build/s1b_label_kaggle.py s1_sentences.jsonl judge")
json.dump({{"ok": rc == 0}}, open("STATUS.json", "w"))
'''
out = ROOT / "kaggle_s1b_judge"; out.mkdir(exist_ok=True); (out / "judge.py").write_text(src)
json.dump({"id": "mhmdrzaqjvnd/teich-v04-s1b-judge", "title": "teich-v04-s1b-judge", "code_file": "judge.py",
           "language": "python", "kernel_type": "script", "is_private": True, "enable_gpu": True, "enable_tpu": False,
           "enable_internet": True, "machine_shape": "NvidiaTeslaT4", "dataset_sources": [], "competition_sources": [],
           "kernel_sources": [], "model_sources": []}, open(out / "kernel-metadata.json", "w"), indent=1)
print(out, len(src), "bytes")
