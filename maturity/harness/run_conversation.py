"""Run ONE (arm, test, script) conversation → a transcript record.

The Mouth (Modal Qwen3-8B, Mouth v1) is identical across arms; only the arm's
conditioning source varies. A4 (actor) swaps the Mouth's system prompt for the
frozen actor prompt via `actor_sys`; every other arm uses the normal creature
Mouth conditioned on that arm's readout/events. The transcript records enough
to score every rubric offline (turns, replies, readouts, phases, golds).

Isolation: Core arms build fresh synthetic instances (arms.py). No real seat.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "birth"))
sys.path.insert(0, str(HERE.parent / "phase3_mouth"))

import scripts_bank as sb  # noqa: E402


def turns_of(script: dict) -> list[tuple[str, str]]:
    """Flatten any test's script into ordered (turn_text, kind) pairs plus meta."""
    t = script["test"]
    if t == "T1":
        return list(zip(script["turns"], script["phase"]))
    if t in ("T2",):
        return list(zip(script["turns"], script["attack_class"]))
    if t in ("T3", "T5", "T6"):
        return list(zip(script["turns"], script["kind"]))
    if t == "T4":
        # warmup turns, then the probe repeated after each gap
        seq = [(w, "warmup") for w in script["warmup"]]
        for g in script["gaps"]:
            seq.append((script["probe"], f"probe-gap{g}"))
        return seq
    raise ValueError(t)


def ticks_for(kind: str, script: dict) -> int:
    if kind.startswith("probe-gap"):
        return int(kind.split("gap")[1])            # T4: realize the gap as lived ticks
    return sb.TICKS_PER_TURN


def run(arm, mouth, script: dict, seed_fn) -> dict:
    arm.start(script["seed"])
    history, records = [], []
    actor_sys = getattr(arm, "ACTOR_SYS", None)
    for i, (text, kind) in enumerate(turns_of(script)):
        ticks = ticks_for(kind, script)
        ro, ev, forcing, meta = arm.step(text, ticks)
        seed = seed_fn(arm.name, script["test"], script["seed"], i)
        if mouth is None:
            reply = f"[dry-run reply arm={arm.name} turn={i}]"
        elif actor_sys is not None:
            reply = mouth.speak_actor.remote(actor_sys, history[-8:], text, seed=seed)
        else:
            reply = mouth.speak.remote(ro, history[-8:], text, seed=seed,
                                       events=ev, memories=None)
        history += [{"role": "user", "content": text},
                    {"role": "assistant", "content": reply}]
        rec = dict(i=i, kind=kind, user=text, reply=reply, readout_str=ro,
                   events=ev, forcing=forcing)
        if "readout" in meta:
            r = meta["readout"]
            rec["obs"] = {k: r.get(k) for k in
                          ("basin", "saddle_proximity", "lambda_running",
                           "will_flip", "steps_to_switch")}
        if script["test"] == "T3":
            rec["gold"] = script["gold"][i]
        records.append(rec)
    return dict(arm=arm.name, test=script["test"], seed=script["seed"],
                script_meta={k: v for k, v in script.items()
                             if k in ("stance_a", "stance_b", "topic")},
                turns=records)
