"""Verify Teich v0.5 from the published files (for readers; birth_v05.py is the gate that ran at birth and is kept
unchanged). Reports, without refusing: every anchored file as MATCH / MISMATCH / UNPUBLISHED (data and lab files that
are not in the public repo; their hashes are still in the manifests), the certificate's genome hashes and identity,
the judged gates, the substrate gate on this machine, and — given its published record log — every act's reason.
    python3 verify_v05.py [records.jsonl]
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent; LAB = HERE.parent; B = LAB / "build"
sys.path.insert(0, str(B))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


am = {l.split()[1]: l.split()[0] for l in (LAB / "specs/AMENDMENT1_v05.sha256").read_text().splitlines()}
match, mism, unpub = 0, [], []
for m in ("CODE_MANIFEST_v05.sha256", "AMENDMENT1_v05.sha256"):
    for line in (LAB / "specs" / m).read_text().splitlines():
        h, f = line.split(); p = B / f
        if not p.exists():
            unpub.append(f); continue
        ok = sha(p) == (am.get(f, h) if m.startswith("CODE") else h)
        match += ok
        if not ok:
            mism.append(f"{m}:{f}")
print(f"anchored files   {match} match, {len(mism)} MISMATCH, {len(set(unpub))} unpublished")
for x in mism:
    print("   MISMATCH", x)
for ref, a, m in (("v05-spec", "ANCHOR_v05_spec.json", "CODE_MANIFEST_v05.sha256"),
                  ("v05-spec-amend1", "ANCHOR_v05_amend1.json", "AMENDMENT1_v05.sha256")):
    an = json.loads((LAB / "specs" / a).read_text())
    print(f"anchor {ref:16s} {'matches' if an['git_sha'] == sha(LAB / 'specs' / m) else 'DOES NOT match'} its manifest "
          f"(teich-03 chain; check it there: /o/teich-03)")
cert = json.loads((HERE / "genesis_certificate_v05.json").read_text())
gm = {f: sha(B / f) == h for f, h in cert["genome_files_sha256"].items()}
ident = hashlib.sha256("".join(f"{k}:{v}" for k, v in sorted(cert["genome_files_sha256"].items())).encode()).hexdigest()
print(f"genome files     {sum(gm.values())}/{len(gm)} match the certificate; identity "
      f"{'recomputes' if ident == cert['identity_sha256'] else 'DOES NOT recompute'} ({ident[:16]}…)")
j = json.loads((B / "out_v05/judge_v05.json").read_text())
print(f"gates            hard failed: {j['hard_failed']}; soft failed: {[g for g, v in j['gates'].items() if not v]} "
      "(Q1, S-set/S7 — disclosed in the certificate)")
import seat_v04 as SV  # noqa: E402
ok, info = SV.gate()
print(f"substrate gate   {'PASS' if ok else 'FAIL'} on {info['cpu']} (numpy {info['numpy']})")
if len(sys.argv) > 1:
    from f1_v05 import check_log
    f = check_log([json.loads(l) for l in open(sys.argv[1]) if l.strip()])
    bad = f["completeness"] + f["receipt"] + f["consequence"] + f["necessity"]
    print(f"its reasons      {f['acts']} acts: " + ("every reason is the act's true cause" if bad == 0 else f"{bad} FAILURES"))
