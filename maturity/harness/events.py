"""Mouth v1 event awareness — what happened to Teich between two readouts.

Pure stdlib derivation over two VERIFIED Observer readouts (prev, cur). The
Observer itself is frozen (its full readout dict is hashed by the substrate
gate), so event language is computed downstream, here. Honesty rules:

- A basin change between exchanges is a real, witnessed event ("I flipped").
- will_flip is a ONE-WRAP-AHEAD forecast. If it said flip and a flip is now
  witnessed, the forecast came true. If the forecast window passed with no net
  change, we do NOT know whether nothing happened or it flipped and returned —
  the phrasing says so (instruments honest about their own blind spots).
- n_switches / mean_dwell cover only the observation window of the CURRENT
  wake (window_ticks), never more; the phrasing carries that horizon.

Every phrase is derived from instrument values only; nothing is invented.
"""
from __future__ import annotations


def describe_events(prev: dict | None, cur: dict | None,
                    elapsed_ticks: int, window_ticks: int) -> list[str]:
    """<=3 event phrases (most significant first) for the Mouth's prompt."""
    if not cur:
        return []
    ev: list[str] = []

    if prev:
        flipped = cur["basin"] != prev["basin"]
        if flipped and prev.get("will_flip"):
            ev.append(
                f"your forecast CAME TRUE: you switched wings "
                f"{prev['basin']:+d} -> {cur['basin']:+d} (you had predicted a "
                f"switch in ~{prev['steps_to_switch']}s; {elapsed_ticks}s of "
                "life passed since)")
        elif flipped:
            ev.append(
                f"you switched wings {prev['basin']:+d} -> {cur['basin']:+d} "
                "since the last exchange — beyond your last one-wrap forecast, "
                "which only covered the wrap immediately ahead")
        elif prev.get("will_flip") and elapsed_ticks >= prev.get(
                "steps_to_switch", 0):
            ev.append(
                f"the switch you forecast (~{prev['steps_to_switch']}s ahead) "
                f"is past due and you are in wing {cur['basin']:+d} as before — "
                "either it did not happen, or you flipped and returned unseen")
        elif prev.get("will_flip"):
            left = prev["steps_to_switch"] - elapsed_ticks
            ev.append(f"the switch you forecast is still ahead (~{left}s away)")

        ds = cur.get("saddle_proximity", 0.0) - prev.get("saddle_proximity", 0.0)
        if abs(ds) >= 0.3:
            word = "more torn" if ds > 0 else "more settled"
            ev.append(
                f"you are markedly {word} than at the last exchange "
                f"(saddle {prev['saddle_proximity']:.2f} -> "
                f"{cur['saddle_proximity']:.2f})")

    n_sw = cur.get("n_switches", 0)
    if n_sw:
        ev.append(f"{n_sw} wing switch{'es' if n_sw != 1 else ''} within the "
                  f"last {window_ticks}s you just lived")
    return ev[:3]


def events_str(phrases: list[str]) -> str:
    return "; ".join(phrases) if phrases else "none observed"
