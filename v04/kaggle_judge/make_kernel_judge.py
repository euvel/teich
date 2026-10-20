"""Generate the Part 2e judge kernel (Mistral-Small-24B 4-bit on Kaggle 2xT4): smoke 4 sentences, then all 400."""
import base64, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
files = {f"build/{n}": base64.b64encode((ROOT / "build" / n).read_bytes()).decode() for n in ("part2e_label.py", "part2e_label_kaggle.py")}
files["a2e_sentences.jsonl"] = base64.b64encode((ROOT / "data_heldout/dialog/a2e_sentences.jsonl").read_bytes()).decode()
src = f'''# Teich v0.4 Part 2e judge kernel — independent labels for the A2e sentences (amendment 2026-10-09)
import base64, json, os, subprocess, sys
FILES = json.loads({json.dumps(json.dumps(files))})
for p, b in FILES.items():
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True); open(p, "wb").write(base64.b64decode(b))
def sh(c):
    r = subprocess.run(c, shell=True, capture_output=True, text=True); print("$", c[:100], "->", r.returncode, (r.stdout + r.stderr)[-1500:], flush=True); return r.returncode
sh("pip install -q 'bitsandbytes>=0.45' 'accelerate>=1.0'")
sh("nvidia-smi --query-gpu=name,memory.total --format=csv")
sh("python3 -c 'import torch,transformers,bitsandbytes;print(torch.__version__,transformers.__version__,bitsandbytes.__version__)'")
if sh("python3 build/part2e_label_kaggle.py a2e_sentences.jsonl smoke --limit 4"):
    json.dump({{"stopped": "smoke run crashed"}}, open("STATUS.json", "w")); sys.exit(0)
v = [json.loads(l) for l in open("smoke/a2e_votes.jsonl")]
print("SMOKE votes:", [(x["id"], x["vote"], x["ok"], x["topics"]) for x in v], flush=True)
if sum(x["ok"] for x in v) < 10:
    json.dump({{"stopped": "smoke: answers do not parse"}}, open("STATUS.json", "w")); sys.exit(0)
rc = sh("python3 build/part2e_label_kaggle.py a2e_sentences.jsonl judge")
json.dump({{"ok": rc == 0, "smoke_ok_votes": sum(x["ok"] for x in v)}}, open("STATUS.json", "w"))
'''
out = ROOT / "kaggle_p2e_judge"; out.mkdir(exist_ok=True); (out / "judge.py").write_text(src)
json.dump({"id": "mhmdrzaqjvnd/teich-v04-part2e-judge", "title": "teich-v04-part2e-judge", "code_file": "judge.py",
           "language": "python", "kernel_type": "script", "is_private": True, "enable_gpu": True, "enable_tpu": False,
           "enable_internet": True, "machine_shape": "NvidiaTeslaT4", "dataset_sources": [], "competition_sources": [],
           "kernel_sources": [], "model_sources": []}, open(out / "kernel-metadata.json", "w"), indent=1)
print(out, len(src), "bytes")
