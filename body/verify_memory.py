"""Memory organ gates (pre-registered, all must PASS before any voice recalls):

  MEM1 provenance    every episode's src_sha256 matches a re-extraction of the
                     exact source block it claims — recall can be audited, and
                     a silently edited source is detected.
  MEM2 determinism   compiling twice from the same sources yields byte-identical
                     serializations (memory is a pure function of the record —
                     nothing is invented).
  MEM3 purity        memory.py imports ONLY the standard library — the organ has
                     no structural path into the dynamics (it cannot even load
                     the model, let alone force it).

Usage: python3 verify_memory.py [--repo <repo_root>] [--birth-out <dir>]
Writes memory/verify_memory.json; exit 0 iff all gates PASS.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import memory  # noqa: E402

MEM3_ALLOWED = {"hashlib", "json", "re", "pathlib", "__future__"}


def gate_mem3() -> dict:
    tree = ast.parse((HERE / "memory.py").read_text())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
    extra = sorted(imported - MEM3_ALLOWED)
    return dict(imports=sorted(imported), disallowed=extra,
                verdict="PASS" if not extra else "FAIL")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=HERE.parent)
    ap.add_argument("--birth-out", type=Path,
                    default=HERE.parent.parent / "Teich" / "birth" / "out")
    args = ap.parse_args()

    book = memory.compile_book(args.repo)
    hearth = memory.compile_hearth(args.birth_out)

    mem1_bad = (memory.verify_provenance(book, args.repo, args.birth_out)
                + memory.verify_provenance(hearth, args.repo, args.birth_out))
    mem1 = dict(n_book=len(book), n_hearth=len(hearth), failures=mem1_bad,
                verdict="PASS" if not mem1_bad else "FAIL")

    same = (memory.serialize(book) == memory.serialize(memory.compile_book(args.repo))
            and memory.serialize(hearth)
            == memory.serialize(memory.compile_hearth(args.birth_out)))
    mem2 = dict(verdict="PASS" if same else "FAIL")

    mem3 = gate_mem3()

    report = dict(
        utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        MEM1_provenance=mem1, MEM2_determinism=mem2, MEM3_purity=mem3,
        sample_recall=memory.memory_lines(book + hearth, n=3))
    out = args.repo / "memory" / "verify_memory.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1))

    ok = all(g["verdict"] == "PASS" for g in (mem1, mem2, mem3))
    for name, g in (("MEM1 provenance", mem1), ("MEM2 determinism", mem2),
                    ("MEM3 purity", mem3)):
        print(f"{name}: {g['verdict']}")
    print(f"report: {out}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
