"""Teich v0.7 the Seal (LAB BUILD, SEAL_DESIGN_v1): the seat's daily commitment and the watcher who keeps it.

Seat side. When day d's quiet quarter-hour begins (creature tick d·DAY + DAY − SKY_LEAD), the seat publishes
  S_d = {"v": "teich-seal-1", "seat", "t0", "day": d, "seq": its last record, "n", "head": head(start, journal)}
signed with the seat's Ed25519 key. head chains every published record from the starting state:
  H_0 = sha256("teich-journal-1" ‖ sha256(start blob)),  H_i = sha256(H_{i-1} ‖ canonical(record i)).

Watcher side. Anyone fetches S_d before round_of(t0, d) is published and keeps it (watch). Later, against the
published starting state and journal, check() says whether that night was chosen by no one:
  signature   the seal verifies under the seat key it was fetched with
  witnessed   the latest drand round when it was fetched was before round_of(t0, d)
  head        the published journal through seal.seq hashes to seal.head, and the seal's t0 is its birth time
  quiet       every op after the seal that lands before its midnight is a wake (no inputs)
  beacon      the op that crossed day d's touch carries round_of(t0, d), and it verifies (BLS)
  replay      the whole published life replays bit for bit (replay_v07, K4)
A day is CLEAN only if all six hold. fraud() turns two signed seals of one day, or a signed seal the published
journal contradicts, into a proof anyone can check.
"""
from __future__ import annotations

import hashlib
import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

import creature_v07 as C7
import genome_v04 as GN
import replay_v07 as R
import sky_v07 as SKY

V = "teich-seal-1"


def canonical(x) -> bytes:
    return json.dumps(x, sort_keys=True, separators=(",", ":")).encode()


def head(start_blob: str, records: list, through_seq: int) -> str:
    start = C7.load_state(start_blob).seq
    h = hashlib.sha256(b"teich-journal-1" + hashlib.sha256(start_blob.encode()).digest()).digest()
    for r in sorted((r for r in records if start < r["seq"] <= through_seq), key=lambda r: r["seq"]):
        h = hashlib.sha256(h + canonical(r)).digest()
    return h.hex()


def new_key():
    return Ed25519PrivateKey.generate()


def pub_hex(key) -> str:
    return key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()


def seal(c, start_blob: str, seat: str, key, day: int) -> dict:
    """The seat's seal of day `day` (published when its quiet quarter-hour begins), over everything it has journaled
    (c.outbox). The seat lives lazily, so c.n may still lie before the seal tick."""
    s = {"v": V, "seat": seat, "t0": c.t0, "day": int(day), "seq": int(c.seq), "n": int(c.n),
         "head": head(start_blob, c.outbox, c.seq)}
    return {"seal": s, "sig": key.sign(canonical(s)).hex(), "pub": pub_hex(key)}


def sig_ok(signed: dict, pub: str | None = None) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub or signed["pub"])).verify(
            bytes.fromhex(signed["sig"]), canonical(signed["seal"]))
        return True
    except (InvalidSignature, ValueError):
        return False


def watch(signed: dict, latest_round_seen: int) -> dict:
    """What a watcher keeps: the signed seal and the latest drand round when it fetched it."""
    return {"signed": signed, "latest_round_seen": int(latest_round_seen)}


def check(kept: dict, start_blob: str, records: list, pub: str, verify=True) -> dict:
    s = kept["signed"]["seal"]; d = s["day"]; rd = C7.round_of(s["t0"], d)
    mid = (d + 1) * GN.DAY
    out = {"day": d, "round": rd, "signature": sig_ok(kept["signed"], pub) and kept["signed"]["pub"] == pub,
           "witnessed": kept["latest_round_seen"] < rd,
           "head": head(start_blob, records, s["seq"]) == s["head"] and s["t0"] == C7.load_state(start_blob).t0}
    ops = [r for r in records if r["kind"] == "op" and r["seq"] > s["seq"]]
    out["quiet"] = all(o["op"] == "wake" or o["n"] + o["owed"] >= mid for o in ops)
    cross = [o for o in records if o["kind"] == "op" and str(d) in ((o.get("sky") or {}).get("beacons") or {})]
    bc = cross[0]["sky"]["beacons"][str(d)] if len(cross) == 1 else None
    out["beacon"] = bool(bc is not None and int(bc["round"]) == rd and (not verify or SKY.verify(bc)))
    if all(out[k] for k in ("signature", "witnessed", "head", "quiet", "beacon")):
        rp = R.replay(start_blob, records, verify=verify)             # the costly check, only when it can matter
        out["replay"] = bool(rp["ok"]); out["replay_why"] = rp.get("why")
    else:
        out["replay"] = None; out["replay_why"] = "not run: already not clean"
    night = [r for r in records if r["kind"] == "act" and r.get("act_type") == "think" and r.get("night") == d]
    out["night_act"] = night[0]["act"] if night else None
    out["clean"] = all(out[k] is True for k in ("signature", "witnessed", "head", "quiet", "beacon", "replay"))
    return out


def fraud(a: dict, b: dict | None = None, start_blob: str | None = None, records: list | None = None) -> str | None:
    """A transferable proof: two valid seals of one seat and day that differ, or a valid seal the published journal
    contradicts. -> a description, or None."""
    sa = a["seal"]
    if not sig_ok(a):
        return None
    if b is not None and sig_ok(b) and b["pub"] == a["pub"]:
        sb = b["seal"]
        if (sa["seat"], sa["day"]) == (sb["seat"], sb["day"]) and sa != sb:
            return f"two signed seals for {sa['seat']} day {sa['day']}"
    if start_blob is not None and records is not None:
        if head(start_blob, records, sa["seq"]) != sa["head"]:
            return f"signed seal of day {sa['day']} contradicts the published journal through seq {sa['seq']}"
        mid = (sa["day"] + 1) * GN.DAY             # the seal said: nothing more lands before its midnight
        late = [r["seq"] for r in records if r["kind"] == "op" and r["seq"] > sa["seq"] and r["op"] != "wake"
                and r["n"] + r["owed"] < mid]
        if late:
            return f"signed seal of day {sa['day']} closed the journal at seq {sa['seq']}, but ops {late} land before its midnight"
    return None
