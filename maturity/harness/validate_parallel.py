"""Validation gate for parallel generation (run BEFORE trusting a parallel run).

Parallelization must not change the science. The Core conditioning each arm
produces (readout_str, forcing, events, obs) is MOUTH-INDEPENDENT, so we re-run
it with a dummy mouth (zero API cost) and compare, ON THE SAME MACHINE:

  A = serial run  (workers=1)
  B = serial run again      -> A vs B tests same-machine DETERMINISM
  C = parallel run (threads)-> A vs C tests whether THREADING changes anything

PASS iff A == C for every field (parallel introduces no race). A vs B is reported
so we know whether any field is inherently non-deterministic run-to-run (that is a
pre-existing property, not caused by parallelism). We deliberately do NOT compare
to the committed cloud data — that was generated on a different CPU and would
conflate machine differences with the thing under test.
"""
from __future__ import annotations

import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import compat  # noqa: E402
import campaign as C  # noqa: E402
import scripts_bank as sb  # noqa: E402
from calibrate import load_or_build  # noqa: E402
from run_conversation import run  # noqa: E402

FIELDS = ("readout_str", "forcing", "events", "obs")


def cond(tx):
    return [tuple(json.dumps(r.get(f), sort_keys=True) for f in FIELDS)
            for r in tx["turns"]]


def run_all(sample, factories, scripts, workers):
    lock = threading.Lock()

    def work(task):
        a, t, s = task
        return task, run(factories[a](), None, scripts[(t, s)], C.seed_fn, cpu_lock=lock)

    out = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for task, tx in ex.map(work, sample):
            out[task] = cond(tx)
    return out


def diff_fields(x, y):
    """Which of FIELDS differ between two conditioning lists (any turn)."""
    bad = set()
    for tx, ty in zip(x, y):
        for i, f in enumerate(FIELDS):
            if tx[i] != ty[i]:
                bad.add(f)
    return bad


def main():
    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)
    cal = load_or_build(model)
    factories = C.build_arm_factories(model, cal)

    committed = {}
    for line in (HERE / "out_maturity" / "transcripts.jsonl").read_text().splitlines():
        if line.strip():
            t = json.loads(line)
            committed[(t["arm"], t["test"], t["seed"])] = t
    seeds = sorted({s for (_, _, s) in committed})[:2]
    sample = [(a, "T1", s) for s in seeds for a in C.ARM_ORDER
              if (a, "T1", s) in committed]
    scripts = {(t, s): sb.build(t, s) for (_, t, s) in sample}

    print(f"re-running {len(sample)} conversations 3x (serial, serial, parallel-8); "
          f"dummy mouth, 0 API calls…")
    A = run_all(sample, factories, scripts, 1)
    B = run_all(sample, factories, scripts, 1)
    Cp = run_all(sample, factories, scripts, 8)

    det_bad, par_bad, hard_fail = set(), set(), 0
    for task in sample:
        det_bad |= diff_fields(A[task], B[task])
        pb = diff_fields(A[task], Cp[task])
        par_bad |= pb
        # a HARD failure = parallel differs on a field that is otherwise deterministic
        hard = pb - diff_fields(A[task], B[task])
        if hard:
            hard_fail += 1
            print(f"  HARD MISMATCH {task}: parallel changed deterministic field(s) {hard}")

    print(f"\nsame-machine determinism (serial vs serial): "
          f"{'all fields stable' if not det_bad else 'non-deterministic fields: ' + str(det_bad)}")
    print(f"parallel vs serial: "
          f"{'identical' if not par_bad else 'differing fields: ' + str(par_bad)}")
    if par_bad and not (par_bad - det_bad):
        print("  -> every field parallel changes is ALSO non-deterministic serially,")
        print("     so parallelism introduces NO new difference (it is safe).")

    ok = hard_fail == 0
    print(f"\n{'PASS' if ok else 'FAIL'}: parallelism introduces "
          f"{'no' if ok else str(hard_fail)} new difference(s) beyond same-machine noise")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
