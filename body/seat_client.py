"""Client for the TeichSeat Durable Object (INFRA_DESIGN.md).

The seat stores the state as an opaque text blob; this client is the ONLY place
that serializes/deserializes TeichState for the wire, and it always ships the
exact JSON produced here (float64 repr round-trip = exact for IEEE754 doubles).

Founder key: ~/.teich_seat_key (chmod 600). Base URL: teich.euvvel.xyz (custom domain;
workers.dev route serves 1101 on this network — do not use it).
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

BASE = "https://teich.euvvel.xyz"
KEY_FILE = Path.home() / ".teich_seat_key"
SEAT_NAME = "teich"


def _seat_key() -> str:
    # cloud bodies carry the key as an env secret; the founder machine as a file
    return os.environ.get("SEAT_KEY") or KEY_FILE.read_text().strip()


class SeatError(RuntimeError):
    def __init__(self, status, payload):
        super().__init__(f"seat {status}: {payload}")
        self.status, self.payload = status, payload


def _call(name: str, endpoint: str, body: dict | None = None, auth: bool = True):
    req = urllib.request.Request(
        f"{BASE}/o/{name}/{endpoint}",
        data=json.dumps(body).encode() if body is not None else None,
        method="POST" if body is not None else "GET",
        headers={"content-type": "application/json",
                 # zone Browser Integrity Check 403s Python-urllib's default UA
                 "user-agent": "teich-seat-client/1.0"},
    )
    if auth:
        req.add_header("X-Seat-Key", _seat_key())
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SeatError(e.code, e.read().decode()[:500]) from None


class Seat:
    def __init__(self, name: str = SEAT_NAME):
        self.name = name

    def peek(self):
        return _call(self.name, "peek", auth=False)

    def genesis_import(self, state_blob: str, n_ticks: int, genesis_anchor: str):
        return _call(self.name, "genesis-import",
                     {"state_blob": state_blob, "n_ticks": n_ticks,
                      "genesis_anchor": genesis_anchor})

    def state(self):
        return _call(self.name, "state", {})

    def lease(self):
        return _call(self.name, "lease", {})

    def commit(self, lease_id: str, state_blob: str, n_ticks: int):
        return _call(self.name, "commit",
                     {"lease_id": lease_id, "state_blob": state_blob,
                      "n_ticks": n_ticks})

    def snapshot_now(self, reason: str = "manual"):
        return _call(self.name, "snapshot-now", {"reason": reason})

    def snapshots(self):
        return _call(self.name, "snapshots", {})

    def snapshot_blob(self, i: int):
        return _call(self.name, "snapshot-blob", {"i": i})

    def events(self, limit: int = 50):
        return _call(self.name, "events", {"limit": limit})

    def restore(self, i: int, cause: str):
        return _call(self.name, "restore", {"i": i, "cause": cause})

    def drill_destroy(self):
        return _call(self.name, "drill-destroy", {})
