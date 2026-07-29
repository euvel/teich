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

    def __init__(self, model, seed, ears, donor_state_from=None):
        self.e = G.V02Engine(model, seed)
        self.ears = ears
        self.mouth = SelectingMouth(ears)
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


def run_demo(model, ears, seed=7):
    c = Creature(model, seed, ears)
    hist, rec = [], []
    print(f"\n=== Teich v0.2 — demo conversation (seed {seed})\n")
    for i, text in enumerate(DEMO_SCRIPT):
        x = c.exchange(text, hist[-6:], seed=1000 + i)
        hist += [{"role": "user", "content": text},
                 {"role": "assistant", "content": x["reply"]}]
        rec.append(x)
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
    (OUT / "demo.json").write_text(json.dumps(rec, indent=1))
    asked = sum(1 for x in rec if x["pick"]["asked"])
    print(f"asked in {asked}/{len(rec)} turns  ->  out_v02/demo.json")
    return rec


def run_arms(model, ears, seeds, ticks=TICKS_PER_TURN):
    """Day-3 check: does the creature's OWN state drive selection?

    intact : its own state selects
    donor  : a different live creature's state selects (same script, same voice,
             same candidates -- only the selecting state differs)
    """
    rows = []
    for seed in seeds:
        donor = 10000 + seed
        for arm in ("intact", "donor"):
            c = Creature(model, seed, ears,
                         donor_state_from=(donor if arm == "donor" else None))
            hist = []
            for i, text in enumerate(DEMO_SCRIPT):
                x = c.exchange(text, hist[-6:], seed=2000 + i)
                hist += [{"role": "user", "content": text},
                         {"role": "assistant", "content": x["reply"]}]
                rows.append(dict(arm=arm, seed=seed, turn=i,
                                 idx=x["pick"]["index"],
                                 asked=bool(x["pick"]["asked"]),
                                 ask_drive=x["pick"]["ask_drive"],
                                 saddle=x["readout"]["saddle"],
                                 wing_bias=x["readout"]["wing_bias"],
                                 n_cands=len(x["candidates"])))
            print(f"  seed {seed} {arm}: done", flush=True)
    (OUT / "arms.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--arms", action="store_true")
    ap.add_argument("--seeds", type=int, default=32)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    import compat
    cfg, gcfg, _ = compat.shared_context()
    model = compat.load_model(cfg, gcfg)
    G.selftest_zero(model)
    ears = EarsV2(model)

    if args.demo:
        run_demo(model, ears, seed=args.seed)
    elif args.arms:
        t0 = time.time()
        run_arms(model, ears, list(range(args.seeds)))
        print(f"({time.time()-t0:.0f}s) -> out_v02/arms.jsonl")
    else:
        sys.exit("use --demo or --arms")


if __name__ == "__main__":
    main()
