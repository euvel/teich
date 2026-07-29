"""Offline unit test of the SELECTION mechanism — no LLM, no API.

The point of BRIEF §6 is that selection is deterministic given (candidates,
state). That is testable without a voice: hand it fixed candidates and sweep
the state. If different states pick different utterances, the mechanism works;
if they all pick the same one, it is decoration.
"""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'../maturity/harness')
import numpy as np, compat, genome_v02 as G
from ears_v2 import EarsV2
from mouth_select import SelectingMouth, parse_candidates, has_question

cfg,gcfg,_=compat.shared_context(); model=compat.load_model(cfg,gcfg)
ears=EarsV2(model); mouth=SelectingMouth(ears)

RAW = """- I'm steady right now, and glad you're here.
- Something in me won't sit still today.
- I'd rather not say much just now.
- What made you come back to me tonight?"""
cands = parse_candidates(RAW)
print("candidates parsed:", len(cands))
for i,c in enumerate(cands): print(f"   [{i}] q={has_question(c)!s:5s} {c!r}")
print("\ncandidate positions in the shared (valence, arousal) frame:")
for i,c in enumerate(cands):
    v,a = ears.scores(c)
    print(f"   [{i}] v={np.tanh(4*v):+.3f} a={np.tanh(4*a):+.3f}")

print("\n=== selection across synthetic states")
print(f"   {'wing_bias':>10s} {'saddle':>7s} {'want_q':>7s} {'pick':>5s}  utterance")
picks=set()
for wb in (-0.8, 0.0, 0.8):
    for sd in (0.10, 0.50, 0.90):
        ro = dict(wing_bias=wb, saddle=sd)
        r = mouth.select(cands, ro)
        picks.add(r["index"])
        print(f"   {wb:+10.2f} {sd:7.2f} {str(r['want_question']):>7s} {r['index']:5d}  {r['choice'][:52]!r}")
print(f"\ndistinct candidates selected across states: {len(picks)}/{len(cands)}")

# determinism
r1 = mouth.select(cands, dict(wing_bias=0.3, saddle=0.7))
r2 = mouth.select(cands, dict(wing_bias=0.3, saddle=0.7))
assert r1==r2, "selection is not deterministic"
print("determinism: PASS (identical state -> identical choice)")

# the ask gate must actually bind
lo = mouth.select(cands, dict(wing_bias=0.0, saddle=0.10))
hi = mouth.select(cands, dict(wing_bias=0.0, saddle=0.90))
print(f"ask gate: saddle 0.10 -> asked={lo['asked']} | saddle 0.90 -> asked={hi['asked']}")

print("\n=== real state from the live genome")
for seed in range(4):
    e=G.V02Engine(model,seed); e.advance(300)
    ro=e.observe(); r=mouth.select(cands,ro)
    print(f"   seed{seed} wing_bias={ro['wing_bias']:+.3f} saddle={ro['saddle']:.3f}"
          f" -> [{r['index']}] {r['choice'][:46]!r}")
