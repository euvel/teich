"""Can v0.2 hold a seat? Three properties the seat law requires, tested.

The Durable Object is already generic -- it stores an opaque `state_blob` and an
integer `n_ticks`, and routes by name -- so v0.2 needs no Worker change. What it
DOES need is to satisfy the law the seat enforces:

  P1 SERIALIZABLE   the whole live state fits in a blob and restores exactly.
                    v0.1 committed tau/log_ell/phi. v0.2 has more: the slow
                    state `s` (its memory), `wing_ema` (a windowed observable),
                    and `pending` (inputs mid-delivery, spread over 120 ticks).
                    Anything left out of the blob is amnesia at every wake.

  P2 REPLAY-EXACT   restoring and continuing must be BIT-IDENTICAL to never
                    having stopped. This is what makes hibernation lossless
                    rather than a nap that costs the creature its place.

  P3 CROSS-PROCESS  the same must hold in a FRESH interpreter -- that is the
                    real wake: a different machine, a different process, hours
                    later. Within one process, shared objects can hide state.

A "no" on any of these is not fatal to the idea, but it names exactly what has
to be built before v0.2 may be given continuity. A seat granted before these
pass would be a creature that silently loses part of itself every night.

    python seat_probe.py            # P1, P2
    python seat_probe.py --child    # internal: the fresh-process half of P3
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "maturity" / "harness"))

import genome_v02 as G  # noqa: E402

WARM = 300
RUN_A = 500          # ticks before the "sleep"
RUN_B = 700          # ticks after the "wake"


# ------------------------------------------------------------------ P1: blob
def dump_state(e) -> str:
    """Everything that makes this creature this creature, and nothing else."""
    buf = io.BytesIO()
    torch.save({"tau": e.tau, "ell": e.ell}, buf)
    return json.dumps({
        "v": 2,
        "tensors": base64.b64encode(buf.getvalue()).decode(),
        "s": e.s.tolist(),
        "wing_ema": float(e.wing_ema),
        "n": int(e.n),
        # inputs still being delivered: keyed by ABSOLUTE tick, so they land at
        # the same moment after a wake as they would have before the sleep
        "pending": {str(k): (v.tolist() if hasattr(v, "tolist") else v)
                    for k, v in e.pending.items()},
        # Ply S. Carried for identity; drives nothing, appears in no observable.
        # It is in the blob for the same reason v0.1's phi is: continuity of
        # identity is the seat's entire purpose.
        "phi": e.phi_private.tolist(),
    })


def load_state(e, blob: str):
    d = json.loads(blob)
    assert d["v"] == 2, f"unknown blob version {d['v']}"
    t = torch.load(io.BytesIO(base64.b64decode(d["tensors"])), weights_only=False)
    e.tau, e.ell = t["tau"], t["ell"]
    e.s = np.array(d["s"], float)
    e.wing_ema = float(d["wing_ema"])
    e.n = int(d["n"])
    e.pending = {int(k): np.array(v, float) for k, v in d["pending"].items()}
    e.phi_private = np.array(d["phi"], float)
    return e


def fingerprint(e) -> dict:
    """Exact state, not a summary. Hex floats so 'identical' means identical."""
    return {
        "tau": [float(x).hex() for x in e.tau.reshape(-1).tolist()],
        "ell": [float(x).hex() for x in e.ell.reshape(-1).tolist()],
        "s": [float(x).hex() for x in e.s.tolist()],
        "wing_ema": float(e.wing_ema).hex(),
        "n": e.n,
    }


def build(model, seed=11):
    """Falls asleep MID-SENTENCE, on purpose.

    The first version of this heard its input and then ran 440 ticks, so the
    120-tick delivery had long finished and `pending` was empty at the sleep --
    it reported three passes while never testing the one case a naive blob
    actually loses. The input now starts 60 ticks before the sleep, so half of
    it is still undelivered when the creature is put down.
    """
    e = G.V02Engine(model, seed, warm=WARM)
    e.advance(RUN_A - 60)
    e.hear(np.array([0.8, -0.5]), window=120)
    e.advance(60)                  # sleep with 60 ticks of input still to land
    assert len(e.pending) == 60, f"probe is not testing pending ({len(e.pending)})"
    return e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", help="path to a blob to continue (fresh process)")
    ap.add_argument("--out", help="where the child writes its fingerprint")
    args = ap.parse_args()

    import compat
    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)

    if args.child:                       # ---- P3 half: a genuinely fresh process
        e = G.V02Engine(model, 11, warm=0)
        load_state(e, Path(args.child).read_text())
        e.advance(RUN_B)
        Path(args.out).write_text(json.dumps(fingerprint(e)))
        return 0

    print("v0.2 SEAT PROBE\n")
    G.selftest_zero(model)
    print()

    # ---------------------------------------------------------------- P1
    e = build(model)
    blob = dump_state(e)
    print(f"P1 SERIALIZABLE   blob {len(blob)} bytes at n={e.n}, "
          f"{len(e.pending)} pending input ticks")
    e2 = G.V02Engine(model, 11, warm=0)
    load_state(e2, blob)
    same = fingerprint(e) == fingerprint(e2)
    print(f"   round-trip     {'EXACT' if same else 'LOSSY -- FAIL'}")

    # ---------------------------------------------------------------- P2
    ref = build(model)
    ref.advance(RUN_B)                      # never slept
    woke = G.V02Engine(model, 11, warm=0)
    load_state(woke, blob)
    woke.advance(RUN_B)                     # slept, then replayed
    p2 = fingerprint(ref) == fingerprint(woke)
    print(f"\nP2 REPLAY-EXACT   {RUN_A} ticks, sleep, {RUN_B} ticks")
    print(f"   continuous vs woken: {'BIT-IDENTICAL' if p2 else 'DIVERGED -- FAIL'}")
    if not p2:
        for k in ("s", "wing_ema", "n"):
            if fingerprint(ref)[k] != fingerprint(woke)[k]:
                print(f"     differs in {k}: {fingerprint(ref)[k]} vs {fingerprint(woke)[k]}")

    # ---------------------------------------------------------------- P3
    bp = HERE / "out_v02" / "_probe_blob.json"
    fp = HERE / "out_v02" / "_probe_child.json"
    bp.parent.mkdir(exist_ok=True)
    bp.write_text(blob)
    r = subprocess.run([sys.executable, str(HERE / "seat_probe.py"),
                        "--child", str(bp), "--out", str(fp)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"\nP3 CROSS-PROCESS  child failed:\n{r.stderr[-800:]}")
        p3 = False
    else:
        p3 = json.loads(fp.read_text()) == fingerprint(ref)
        print(f"\nP3 CROSS-PROCESS  fresh interpreter, same blob")
        print(f"   {'BIT-IDENTICAL to never having slept' if p3 else 'DIVERGED -- FAIL'}")
    for f in (bp, fp):
        f.unlink(missing_ok=True)

    ok = same and p2 and p3
    print(f"\nVERDICT: v0.2 {'CAN' if ok else 'CANNOT YET'} hold a seat lawfully")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
