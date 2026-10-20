"""DESIGN (Ears v9, S1 retry): self routing on SPENT data under the founder's broad reading (v9_design_labels.json).
Candidates: rule (any listener-you), organ 'generic vs this listener', and rule AND NOT organ-generic. Changes no verdict."""
import json
import numpy as np
import ears_v07 as E7
from generic_you import listener_you

GEN_Q = ("You classify sentences. Answer with one letter.",
         'A speaker says this to a listener: "{text}"\n'
         'Who does "you" (or "your") mean here?\n'
         "A) the listener personally - the specific person being spoken to (what they are, have, did, do, feel, "
         "think, or are asked about; or the speaker's feeling toward them). Examples: \"Have you ever been there?\" "
         "\"You should try the soup.\" \"What does your husband do?\" \"I'm proud of you.\"\n"
         "B) nobody in particular - 'you' means people in general, or is only a filler. Examples: \"You never know "
         "these days.\" \"You have to be fit to do that job.\" \"It can really get to you after a while.\"\n"
         "Answer A or B.")


def main():
    ears = E7.EarsV7(); T = ears.torch
    S = json.load(open("v9_design_labels.json"))
    y = np.array([s["label"] != "NONE" for s in S])
    rule = np.array([listener_you(ears.nlp(s["sentence"])) for s in S])
    def rep0(name, hit):
        tp, fp = (hit & y).sum(), (hit & ~y).sum()
        print(f"  {name:28s} caught {tp}/{y.sum()} = {tp / y.sum():.3f}   false {fp}/{(~y).sum()} = {fp / (~y).sum():.3f}", flush=True)
    rep0("rule (before organ)", rule)
    for k, s in enumerate(S):
        if y[k] != rule[k]:
            print("   rule miss" if y[k] else "   rule false", "|", s["sentence"][:110], flush=True)

    def odds(text):
        lp = ears._ask(GEN_Q[0], GEN_Q[1].format(text=text))
        return float(T.logsumexp(lp[ears.A], 0) - T.logsumexp(lp[ears.B], 0))
    o = np.array([odds(s["sentence"]) for s in S])
    json.dump({"rule": rule.tolist(), "o_gen": o.tolist(), "y": y.tolist()}, open("e9_design.json", "w"))

    def rep(name, hit):
        tp, fp = (hit & y).sum(), (hit & ~y).sum()
        print(f"  {name:28s} caught {tp}/{y.sum()} = {tp / y.sum():.3f}   false {fp}/{(~y).sum()} = {fp / (~y).sum():.3f}")
    print("design: mirrors", y.sum(), "none", (~y).sum())
    rep("rule", rule)
    for th in (-4, -3, -2, -1, 0, 1, 2):
        rep(f"organ > {th}", o > th); rep(f"rule AND organ > {th}", rule & (o > th))


if __name__ == "__main__":
    main()
