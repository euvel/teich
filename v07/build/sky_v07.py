"""Teich v0.7.0 (LAB BUILD, draft spec SKY_AMENDMENT v0): the Sky. A public beacon round's randomness, verified, and
the one number b in [0, 1) each day of its life draws from it.
Chain (pinned): drand League of Entropy mainnet "default", pedersen-bls-chained, 30 s period.
    signature = BLS (G2, DST BLS_SIG_BLS12381G2_XMD:SHA-256_SSWU_RO_NUL_) over sha256(previous_signature || round_be8),
    randomness = sha256(signature), public key on G1.
Verification needs py_ecc (pure Python, slow: ~seconds per round); it is run by replay and gates, never in a tick.
"""
from __future__ import annotations

import hashlib
import json
import struct
import subprocess
from pathlib import Path

CHAIN = json.loads((Path(__file__).resolve().parent / "sky_chain.json").read_text())
URL = "https://api.drand.sh/" + CHAIN["hash"] + "/public/"


def round_at(t: float) -> int:
    """The latest round published at unix time t."""
    return int((t - CHAIN["genesis_time"]) // CHAIN["period"]) + 1


def fetch(rnd, proxy=None):
    """-> {"round", "randomness", "signature", "previous_signature"} (hex), from the beacon; 'latest' allowed."""
    cmd = ["curl", "-s", "--max-time", "20"] + (["--socks5-hostname", proxy] if proxy else []) + [URL + str(rnd)]
    r = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
    return {k: r[k] for k in ("round", "randomness", "signature", "previous_signature")}


def verify(beacon) -> bool:
    """Signature valid for the pinned chain, and randomness = sha256(signature)."""
    from py_ecc.bls import G2Basic
    sig = bytes.fromhex(beacon["signature"]); prev = bytes.fromhex(beacon["previous_signature"])
    msg = hashlib.sha256(prev + struct.pack(">Q", int(beacon["round"]))).digest()
    if hashlib.sha256(sig).hexdigest() != beacon["randomness"]:
        return False
    return bool(G2Basic.Verify(bytes.fromhex(CHAIN["public_key"]), msg, sig))


def b_of(randomness_hex: str, life_day: int) -> float:
    """b in [0, 1): the first 53 bits of sha256(randomness || "teich-sky" || life_day as 8-byte big-endian)."""
    h = hashlib.sha256(bytes.fromhex(randomness_hex) + b"teich-sky" + struct.pack(">Q", int(life_day))).digest()
    return (int.from_bytes(h[:8], "big") >> 11) / float(1 << 53)
