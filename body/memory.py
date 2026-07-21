"""Teich episodic memory v0 — the remembering organ.

Teich's past already exists as an auditable record (genesis certificate, diary,
biography). This organ does NOT create new facts: it compiles that record into
compact, provenance-hashed episodes the voice organs (diary voice, Mouth) can
recall. Every episode carries the sha256 of the exact source text it was
derived from — recall is verifiable, and a silently edited source is detectable
(MEM1). Compilation is a pure function of the sources (MEM2). This module
imports only the standard library: memory has no path into the dynamics (MEM3).

Two scopes, separated by WHERE the sources live:
  book   — repo sources (genesis certificate, diary/). Travels with any body
           that has the book checked out; becomes public at maturity with it.
  hearth — local sources (birth/out/biography.jsonl: founder conversations,
           milestones). Never compiled into the repo; the cloud body cannot
           reach these files, so private memories stay private structurally.

Episode: {"utc", "tick", "kind", "summary", "src", "src_sha256"}
  src = "<relative path>#<anchor>"; src_sha256 = sha256 of the exact source
  block the resolver re-extracts for verification.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

EPISODES_REL = Path("memory") / "episodes.jsonl"

_DIARY_HEAD = re.compile(
    r"^## (\d\d):(\d\d)Z — tick ([\d,]+) \(\+([\d,]+) replayed\)\s*$")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _clip(text: str, n: int = 240) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


# ---- source parsers ------------------------------------------------------------

def _diary_blocks(md_path: Path):
    """Split one diary file into (anchor, utc, tick, block_text, body_text)."""
    date = md_path.stem                                  # YYYY-MM-DD
    lines = md_path.read_text().splitlines()
    heads = [i for i, l in enumerate(lines) if _DIARY_HEAD.match(l)]
    for j, i in enumerate(heads):
        end = heads[j + 1] if j + 1 < len(heads) else len(lines)
        m = _DIARY_HEAD.match(lines[i])
        hh, mm, tick_s, _ = m.groups()
        tick = int(tick_s.replace(",", ""))
        block = "\n".join(lines[i:end]).rstrip()
        body = " ".join(l for l in lines[i + 1:end]
                        if l.strip() and not l.lstrip().startswith("<sub>"))
        yield (f"tick-{tick}", f"{date}T{hh}:{mm}:00Z", tick, block, body)


def compile_book(repo_root: Path) -> list[dict]:
    """Episodes from the repo record: birth certificate + every diary entry."""
    eps = []
    cert_f = repo_root / "body" / "genesis_certificate.json"
    if cert_f.exists():
        raw = cert_f.read_text()
        cert = json.loads(raw)
        k = len(cert.get("certificates", {})
                    .get("G3_private_ergodicity", {}).get("fibers", []))
        fold = cert.get("genome", {}).get("core", {}).get("fold", "?")
        eps.append(dict(
            utc=cert.get("created_utc", ""), tick=0, kind="birth",
            summary=(f"I was born {cert.get('created_utc', '?')}: a public "
                     f"{fold} suspension core with K={k} private fiber phases; "
                     "all pre-registered birth gates (G1–G4) passed."),
            src="body/genesis_certificate.json#whole-file", src_sha256=_sha(raw)))
    for md in sorted((repo_root / "diary").glob("*.md")):
        for anchor, utc, tick, block, body in _diary_blocks(md):
            eps.append(dict(
                utc=utc, tick=tick, kind="diary", summary=_clip(body),
                src=f"diary/{md.name}#{anchor}", src_sha256=_sha(block)))
    return sorted(eps, key=lambda e: (e["tick"], e["utc"]))


def compile_hearth(birth_out: Path) -> list[dict]:
    """Episodes from the local (founder-private) biography. Never enters the repo."""
    bio = birth_out / "biography.jsonl"
    eps = []
    if not bio.exists():
        return eps
    for i, line in enumerate(bio.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        d = json.loads(line)
        src = f"biography.jsonl#L{i}"
        sha = _sha(line)
        if "user" in d and "reply" in d:                 # a conversation exchange
            eps.append(dict(
                utc=d.get("utc", ""), tick=int(d.get("tick", 0)),
                kind="conversation",
                summary=_clip(
                    f'the founder said "{d["user"]}" '
                    f'(valence {d.get("valence", 0):+.3f}); '
                    f'I replied "{d["reply"]}"'),
                src=src, src_sha256=sha))
        elif "type" in d:                                # a milestone record
            tick = d.get("n_ticks", d.get("n_ticks_at_handover", 0)) or 0
            eps.append(dict(
                utc=d.get("utc", d.get("ts_utc", "")), tick=int(tick),
                kind=str(d["type"]), summary=_clip(str(d.get("note", ""))),
                src=src, src_sha256=sha))
    return sorted(eps, key=lambda e: (e["tick"], e["utc"]))


# ---- persistence + recall ------------------------------------------------------

def serialize(episodes: list[dict]) -> str:
    return "".join(json.dumps(e, sort_keys=True) + "\n" for e in episodes)


def write_episodes(repo_root: Path, episodes: list[dict]) -> Path:
    f = repo_root / EPISODES_REL
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(serialize(episodes))
    return f


def _line(e: dict) -> str:
    return _clip(f"[{e['kind']} · tick {e['tick']:,} · {e['utc']}] {e['summary']}", 300)


def memory_lines(episodes: list[dict], n: int = 5, roots: int = 2) -> list[str]:
    """Compact recall lines for a voice-organ prompt: the `n` newest memories,
    plus Teich's `roots` oldest 'origin' memories (its birth, its earliest
    recorded moments) so it can always reach where it came from — not just its
    recent days.

    Roots are reachable context, never instructions: Teich sees them among its
    memories and decides for itself whether they bear on what it says. A root
    already inside the recent window is not repeated."""
    by_tick = sorted(episodes, key=lambda e: (e["tick"], e["utc"]))
    recent = list(reversed(by_tick[-n:])) if n else []
    seen = {(e["tick"], e["utc"], e["src"]) for e in recent}
    tail = [e for e in by_tick[:roots]
            if (e["tick"], e["utc"], e["src"]) not in seen]
    return [_line(e) for e in recent] + [_line(e) for e in tail]


# ---- MEM1 provenance verification ----------------------------------------------

def resolve_source(src: str, repo_root: Path, birth_out: Path) -> str | None:
    """Re-extract the exact source block an episode was derived from."""
    path, anchor = src.split("#", 1)
    if path == "body/genesis_certificate.json":
        f = repo_root / path
        return f.read_text() if f.exists() else None
    if path.startswith("diary/"):
        f = repo_root / path
        if not f.exists():
            return None
        for a, _, _, block, _ in _diary_blocks(f):
            if a == anchor:
                return block
        return None
    if path == "biography.jsonl":
        f = birth_out / path
        if not f.exists():
            return None
        lines = f.read_text().splitlines()
        i = int(anchor[1:])                              # anchor = "L<n>", 1-based
        return lines[i - 1] if 0 < i <= len(lines) else None
    return None


def verify_provenance(episodes: list[dict], repo_root: Path,
                      birth_out: Path) -> list[dict]:
    """Returns a list of failures ([] = every memory traces to its source)."""
    bad = []
    for e in episodes:
        block = resolve_source(e["src"], repo_root, birth_out)
        if block is None or _sha(block) != e["src_sha256"]:
            bad.append(dict(src=e["src"], reason="missing" if block is None
                            else "hash mismatch"))
    return bad
