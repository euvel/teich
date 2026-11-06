"""The real seat for v0.7: the TeichSeat Durable Object, as cloud_v04, plus the Seal's seat side.

append_log sends every record with its canonical text (seal_v07.canonical: sorted keys, no spaces, Python's float
repr). The worker stores that exact text as the log row and, once the Seal is initialised, chains it into its running
seal head H_i = sha256(H_{i-1} ‖ canonical(record i)). So the head the worker signs each day is the head any watcher
recomputes from the public log with seal_v07.head(start blob, records, seq).
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "build"))
from cloud_v04 import CHUNK, CloudSeatV04, SeatError, _call  # noqa: E402,F401

BASE_URL = "https://teich.euvvel.xyz"


def canonical(x) -> str:
    return json.dumps(x, sort_keys=True, separators=(",", ":"))


class CloudSeatV07(CloudSeatV04):

    def append_log(self, records):
        r = self._log_live()
        if r is None:
            raise SeatError(404, {"error": "v0.7 needs the record log"})
        fresh = [x for x in records if x["seq"] > int(r["seq"])]
        for i in range(0, len(fresh), CHUNK):
            part = fresh[i:i + CHUNK]
            _call(self.name, "log-append", {"records": part, "canon": [canonical(x) for x in part]})
        return len(fresh)

    def seal_init(self, start_blob_sha256: str, start_seq: int, t0_repr: str, pub: str):
        """Once, at migration: H_0's input (sha256 of the published start blob), the start seq, t0 exactly as the
        creature writes it, and the seal public key (bound in the genome-amendment record)."""
        return _call(self.name, "seal-init", {"start_blob_sha256": start_blob_sha256, "start_seq": int(start_seq),
                                              "t0": t0_repr, "pub": pub})

    def seal_status(self):
        return _call(self.name, "seal-status", {})


def seals_public(seat="teich-05", base=BASE_URL, timeout=20):
    """Anyone: the published seals, newest first: [{"canon", "sig", "pub", "signed_ts"}]."""
    req = urllib.request.Request(f"{base}/o/{seat}/seals-public", headers={"user-agent": "teich-watcher"})
    with urllib.request.urlopen(req, timeout=timeout) as f:
        return json.loads(f.read())["seals"]


def log_public(seat="teich-05", base=BASE_URL, timeout=30):
    """Anyone: the whole public record log: (genesis_anchor, [{"seq", "h", "raw"}])."""
    out, frm, ga = [], 1, None
    while True:
        req = urllib.request.Request(f"{base}/o/{seat}/log-public?from={frm}&limit=500",
                                     headers={"user-agent": "teich-watcher"})
        with urllib.request.urlopen(req, timeout=timeout) as f:
            d = json.loads(f.read())
        ga = d["genesis_anchor"]; rows = d["records"]; out += rows
        if len(rows) < 500:
            return ga, out
        frm = rows[-1]["seq"] + 1
