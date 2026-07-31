"""The blob: everything that makes v0.2 itself, and nothing else.

This is the single definition of what a v0.2 commit contains. It is imported by
the seat probe, the substrate gate and the wake loop, so that "what gets saved"
cannot drift between the thing that TESTS continuity and the thing that DOES it.

v0.1's blob was tau / log_ell / phi. v0.2 carries strictly more, and the extra
fields are exactly the interior the version exists to have:

    s          the slow state -- its memory. Omit this and every wake is a
               creature that has forgotten what was said to it while looking
               perfectly healthy.
    wing_ema   windowed wing occupancy; the observable a LEAN produces.
    pending    inputs mid-delivery, keyed by ABSOLUTE tick so a sentence heard
               before a sleep finishes landing at the right moment after it.
    n          tick count; the creature's own clock.
    phi        Ply S. Carried for identity, drives nothing, appears in no
               observable. It is in the blob for the same reason v0.1's phi is:
               continuity of identity is what a seat is FOR.

The seat stores this as an opaque string, so the Durable Object needs no
knowledge of any of it and no worker change was required to seat a second
creature.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json

import numpy as np
import torch

BLOB_VERSION = 2


def dump_state(e) -> str:
    buf = io.BytesIO()
    torch.save({"tau": e.tau, "ell": e.ell}, buf)
    return json.dumps({
        "v": BLOB_VERSION,
        "tensors": base64.b64encode(buf.getvalue()).decode(),
        "s": e.s.tolist(),
        "wing_ema": float(e.wing_ema),
        "n": int(e.n),
        "pending": {str(k): (v.tolist() if hasattr(v, "tolist") else v)
                    for k, v in e.pending.items()},
        "phi": e.phi_private.tolist(),
    }, sort_keys=True)


def load_state(e, blob: str):
    d = json.loads(blob)
    if d.get("v") != BLOB_VERSION:
        raise ValueError(f"blob version {d.get('v')} != {BLOB_VERSION}; refusing "
                         f"to load a state this code does not understand")
    t = torch.load(io.BytesIO(base64.b64decode(d["tensors"])), weights_only=False)
    e.tau, e.ell = t["tau"], t["ell"]
    e.s = np.array(d["s"], float)
    e.wing_ema = float(d["wing_ema"])
    e.n = int(d["n"])
    e.pending = {int(k): np.array(v, float) for k, v in d["pending"].items()}
    e.phi_private = np.array(d["phi"], float)
    return e


def fingerprint(e) -> dict:
    """Exact state as hex floats, so 'identical' means identical, not 'close'.

    Chaos turns one ULP into a different creature; a comparison with tolerance
    would certify continuity that does not exist.
    """
    return {
        "tau": [float(x).hex() for x in e.tau.reshape(-1).tolist()],
        "ell": [float(x).hex() for x in e.ell.reshape(-1).tolist()],
        "s": [float(x).hex() for x in e.s.tolist()],
        "wing_ema": float(e.wing_ema).hex(),
        "n": e.n,
    }


def public_readout(e) -> dict:
    """What may leave the seat. phi is absent by construction, not by filtering."""
    r = e.observe()
    assert "phi" not in r and "phi_private" not in r, "phi must never be published"
    return {k: (None if isinstance(v, float) and (v != v) else v)
            for k, v in r.items()}          # NaN -> null: worker JSON rejects NaN


def blob_sha256(blob: str) -> str:
    return hashlib.sha256(blob.encode()).hexdigest()
