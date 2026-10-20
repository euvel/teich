"""Verify Teich v0.4 from the published files (for readers; birth_v04.py is the gate that ran at birth and is kept
unchanged). Reports, without refusing: every anchored file as MATCH / MISMATCH / UNPUBLISHED (data and founder files
that are not in the public repo; their hashes are still in the manifests), the certificate's genome hashes, the
scored verdicts and the substrate gate on this machine.
    python3 verify_v04.py
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent; LAB = HERE.parent; B = LAB / "build"
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(B))
from birth_v04 import APPEND_ONLY, REANCHORED, prefix_ok, sha  # noqa: E402

match, mism, unpub = 0, [], []
for m in sorted((LAB / "specs").glob("*.sha256")):
    for line in m.read_text().splitlines():
        h, f = line.split(None, 1); f = f.strip(); p = B / f
        if not p.exists():
            unpub.append(f); continue
        ok = sha(p) == h or (f in APPEND_ONLY and prefix_ok(p, h))
        re = REANCHORED.get((m.name, f))
        ok = ok or bool(re and any(l.split()[1] == f and l.split()[0] == sha(p)
                                   for l in (LAB / "specs" / re).read_text().splitlines()))
        match += ok
        if not ok:
            mism.append(f"{m.name}:{f}")
print(f"anchored files   {match} match, {len(mism)} MISMATCH, {len(set(unpub))} unpublished")
for x in mism:
    print("   MISMATCH", x)
cert = json.loads((HERE / "genesis_certificate_v04.json").read_text())
gm = {f: sha(B / f) == h for f, h in cert["genome_files_sha256"].items()}
ident = hashlib.sha256("".join(f"{k}:{v}" for k, v in sorted(cert["genome_files_sha256"].items())).encode()).hexdigest()
print(f"genome files     {sum(gm.values())}/{len(gm)} match the certificate; identity "
      f"{'recomputes' if ident == cert['identity_sha256'] else 'DOES NOT recompute'} ({ident[:16]}…)")
j3 = json.loads((B / "out_part3/judge_part3.json").read_text())
print(f"part 3 (self)    {sum(j3['gates'].values())}/{len(j3['gates'])} gates passed; hard failed: {j3['hard_failed']}")
import seat_v04 as SV  # noqa: E402
ok, info = SV.gate()
print(f"substrate gate   {'PASS' if ok else 'FAIL'} on {info['cpu']} (numpy {info['numpy']})")
