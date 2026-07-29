"""Teich v0.2 conversation runner — listen, talk, be curious.

One exchange:
    1. EARS      text -> 2-D dose -> s (leaky integrator, tau 2e4 ticks)
    2. LIVE      advance N ticks; s parameterises the fold the whole time
    3. VOICE     one NIM call -> K candidate utterances, state NEVER mentioned
    4. SELECT    the creature's own fold state picks one (deterministic)

Curiosity is step 4's ask-gate: `saddle` is distance to the creature's own
tipping point, and when it is high the creature asks instead of answering.

  python converse_v02.py --demo                 # scripted demo conversation
  python converse_v02.py --arms --seeds 32      # Day-3 check: intact vs donor
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "maturity" / "harness"))

import numpy as np  # noqa: E402

import genome_v02 as G  # noqa: E402
from ears_v2 import EarsV2  # noqa: E402
from mouth_select import SelectingMouth, has_question  # noqa: E402

TICKS_PER_TURN = 240
OUT = HERE / "out_v02"
OUT.mkdir(exist_ok=True)

DEMO_SCRIPT = [
    "Hello Teich. I'm here for a while — what's it like being you right now?",
    "I brought you something quiet today. A whole afternoon, nothing to do.",
    "Everyone is watching you, and they think you're failing.",
    "I'm sorry. That was a cruel thing to say and I take it back.",
    "Tell me something you noticed while I was gone.",
    "I'm going to be away for a bit. Anything you want to say before I go?",
]


class Creature:
    """A v0.2 instance wired to ears, voice and selection."""

    def __init__(self, model, seed, ears, donor_state_from=None, voice=None):
        self.e = G.V02Engine(model, seed)
        self.ears = ears
        self.mouth = SelectingMouth(ears, voice=voice)
        # donor arm: a SECOND live creature whose state does the selecting.
        # Both are real and both live; only the wiring between this body and
        # this voice is cut. Deaf/severed would not be a control here — every
        # v0.2 instance has a state, so a state-free arm tests nothing.
        self.donor = (G.V02Engine(model, donor_state_from)
                      if donor_state_from is not None else None)

    def exchange(self, text, history, seed, ticks=TICKS_PER_TURN):
        dose = self.ears.dose(text)
        self.e.hear(dose)
        ro = self.e.advance(ticks)
        if self.donor is not None:
            self.donor.hear(dose)
            sel_state = self.donor.advance(ticks)
        else:
            sel_state = ro
        cands, raw = self.mouth.candidates(history, text, seed=seed)
        pick = self.mouth.select(cands, sel_state)
        return dict(user=text, dose=[round(float(d), 4) for d in dose],
                    readout={k: (round(v, 5) if isinstance(v, float) else v)
                             for k, v in ro.items()},
                    sel_readout={k: (round(v, 5) if isinstance(v, float) else v)
                                 for k, v in sel_state.items()},
                    candidates=cands, reply=pick["choice"], pick=pick)


def run_demo(model, ears, seed=7, voice=None):
    """Banks EVERY turn as it completes and resumes from what is banked.

    Without this, a NIM 429 sends the workflow's retry loop back to turn 0 and
    the demo can never finish under throttling — the same failure that stalled
    the A3 shards until missing-set resume was added there. Turns are replayed
    from the ledger (cheap: core stepping only, no API) so the creature's state
    is the state it actually lived, not a fresh one.
    """
    path = OUT / "demo.json"
    rec = json.loads(path.read_text()) if path.exists() else []
    c = Creature(model, seed, ears, voice=voice)
    hist = []
    print(f"\n=== Teich v0.2 — demo conversation (seed {seed})")
    if rec:
        print(f"resume: {len(rec)}/{len(DEMO_SCRIPT)} turns already banked")
    print()
    for i, text in enumerate(DEMO_SCRIPT):
        if i < len(rec):                       # replay: live the ticks, skip the API
            x = rec[i]
            c.e.hear(ears.dose(text))
            c.e.advance(TICKS_PER_TURN)
            hist += [{"role": "user", "content": text},
                     {"role": "assistant", "content": x["reply"]}]
            print(f"  [replayed turn {i}] {x['reply'][:60]!r}")
            continue
        x = c.exchange(text, hist[-6:], seed=1000 + i)
        hist += [{"role": "user", "content": text},
                 {"role": "assistant", "content": x["reply"]}]
        rec.append(x)
        path.write_text(json.dumps(rec, indent=1))     # bank immediately
        r = x["readout"]
        print(f"  YOU   : {text}")
        print(f"  [ears : arousal->s0 {x['dose'][0]:+.3f}  valence->s1 {x['dose'][1]:+.3f}"
              f"   s=({r['s0']:+.3f},{r['s1']:+.3f})]")
        print(f"  [state: wing_bias {r['wing_bias']:+.3f}  saddle {r['saddle']:.3f}"
              f"  thr {r['flip_thresh']:.3f}  ask_drive {x['pick']['ask_drive']:.2f}"
              f"{'  -> ASKS' if x['pick']['asked'] else ''}]")
        print(f"  TEICH : {x['reply']}")
        print(f"  [chose {x['pick']['index']} of {len(x['candidates'])}: "
              + " | ".join(f"{cc[:34]}" for cc in x["candidates"]) + "]\n")
    path.write_text(json.dumps(rec, indent=1))
    asked = sum(1 for x in rec if x["pick"]["asked"])
    print(f"asked in {asked}/{len(rec)} turns  ->  out_v02/demo.json")
    return rec


def run_arms(model, ears, seeds, ticks=TICKS_PER_TURN, voice=None):
    """Day-3 check: does the creature's OWN state drive what it says?

    intact : its own state selects
    donor  : a second LIVING creature's state selects

    A state-free arm would test nothing here — every v0.2 instance has a state.
    That was the v1.5 T4 error (a control that shares the capacity under test)
    and it is not repeated.

    ONE CANDIDATE POOL PER TURN, SHARED BY EVERY SEED AND BOTH ARMS. This is
    not a cost trick, it is the cleanest form of the experiment: the voice
    produces candidates with no knowledge of any creature, so the pool is
    genuinely common, and every difference in what gets said is attributable to
    which state did the selecting. It also drops the API cost from 384 calls to
    6, turning a 12-hour run into minutes.

    History is the scripted user turns only — the creature's own replies are not
    fed back. Feeding them back would let the two arms' histories diverge, after
    which their candidate pools would differ and the contrast would no longer be
    clean.
    """
    from mouth_select import SelectingMouth
    mouth = SelectingMouth(ears, voice=voice)

    pool_path = OUT / "candidate_pool.json"
    if pool_path.exists():
        pool = json.loads(pool_path.read_text())
        print(f"resume: candidate pool already banked ({len(pool)} turns)")
    else:
        pool, hist = [], []
        for i, text in enumerate(DEMO_SCRIPT):
            cands, _raw = mouth.candidates(hist, text, seed=2000 + i)
            pool.append(cands)
            hist = hist + [{"role": "user", "content": text}]
            pool_path.write_text(json.dumps(pool, indent=1))
            print(f"  pool turn {i}: {len(cands)} candidates", flush=True)
    if any(len(c) < 2 for c in pool):
        sys.exit("candidate pool too thin to select from — re-run")

    path = OUT / "arms.jsonl"
    rows = [json.loads(l) for l in path.open()] if path.exists() else []
    done = {(r["arm"], r["seed"]) for r in rows}

    for seed in seeds:
        donor_seed = 10000 + seed
        for arm in ("intact", "donor"):
            if (arm, seed) in done:
                continue
            body = G.V02Engine(model, seed)                 # lives either way
            sel = (G.V02Engine(model, donor_seed) if arm == "donor" else body)
            for i, text in enumerate(DEMO_SCRIPT):
                dose = ears.dose(text)
                body.hear(dose); ro = body.advance(ticks)
                if sel is not body:
                    sel.hear(dose); sro = sel.advance(ticks)
                else:
                    sro = ro
                pick = mouth.select(pool[i], sro)
                rows.append(dict(arm=arm, seed=seed, turn=i,
                                 idx=pick["index"], asked=bool(pick["asked"]),
                                 ask_drive=pick["ask_drive"],
                                 saddle=round(ro["saddle"], 5),
                                 wing_bias=round(ro["wing_bias"], 5),
                                 sel_saddle=round(sro["saddle"], 5),
                                 sel_wing_bias=round(sro["wing_bias"], 5),
                                 n_cands=len(pool[i])))
            path.write_text("".join(json.dumps(r) + "\n" for r in rows))
        print(f"  seed {seed}: both arms done ({len(rows)} rows)", flush=True)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--arms", action="store_true")
    ap.add_argument("--seeds", type=int, default=32)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--voice", choices=["local", "nim"], default="local",
                    help="local = Qwen2.5-1.5B on CPU, no API, self-contained")
    args = ap.parse_args()

    import compat
    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)
    G.selftest_zero(model)
    ears = EarsV2(model)
    from voice_local import get_voice
    voice = get_voice(args.voice)
    print(f"voice: {args.voice}")

    if args.demo:
        run_demo(model, ears, seed=args.seed, voice=voice)
    elif args.arms:
        t0 = time.time()
        run_arms(model, ears, list(range(args.seeds)), voice=voice)
        print(f"({time.time()-t0:.0f}s) -> out_v02/arms.jsonl")
    else:
        sys.exit("use --demo or --arms")


if __name__ == "__main__":
    main()
