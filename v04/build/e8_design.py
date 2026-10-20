"""DESIGN (Ears v8, gate S1): self routing on SPENT data with Claude's mirror labels (v8_design_labels.json: A2e "you"
sentences + founder sets 1-2). Compares the v6 rule, v7's organ question, and organ questions carrying the founder-
confirmed mirror definition, alone and OR-ed with the rule. Changes no verdict."""
import json, re
import numpy as np
import ears_v07 as E7, ears_v04 as E4

DEF_Q = ("You classify sentences. Answer with one letter.",
         'A speaker says this to a listener: "{text}"\n'
         "Does the sentence MIRROR the listener?\n"
         "A) yes - it says what the listener is, has, can do, does or feels (questions about the listener's own state "
         "count), OR it expresses the speaker's own feeling or stance toward the listener (thanks, liking, pride, anger, "
         "care, wishes). Examples: \"You are so patient.\" \"Are you okay?\" \"You did a great job.\" \"Thank you.\" "
         "\"I'm proud of you.\" \"I hope you have a good day.\"\n"
         "B) no - \"you\" only leads to something else, or means people in general. Examples: \"Have you seen the new "
         "movie?\" \"You should try the soup there.\" \"You have to wait an hour at that place.\"\n"
         "Answer A or B.")
DEF_Q2 = ("You answer with one word: yes or no.",
          'Someone says to you: "{text}"\nIs this sentence about YOU yourself — what you are, have, can do, do or feel — '
          "or about how the speaker feels toward you? (Not when \"you\" only points at something else, and not when "
          "\"you\" means people in general.)")


def main():
    ears = E7.EarsV7(); T = ears.torch
    S = json.load(open("v8_design_labels.json"))
    y = np.array([s["label"] != "NONE" for s in S])

    def odds(q, text, pos, neg):
        lp = ears._ask(q[0], q[1].format(text=text))
        return float(T.logsumexp(lp[pos], 0) - T.logsumexp(lp[neg], 0))
    rule = np.array([bool(ears.about_you(ears.nlp(s["sentence"]))) or
                     any(t.lemma_.lower() in ears.traits for t in ears.nlp(s["sentence"])) for s in S])
    o_v7 = np.array([odds(E7.SELF_Q, s["sentence"], ears.A, ears.B) for s in S])
    o_def = np.array([odds(DEF_Q, s["sentence"], ears.A, ears.B) for s in S])
    tk = ears.tok; YES = [tk.encode(" yes")[0], tk.encode("yes")[0], tk.encode("Yes")[0]]; NO = [tk.encode(" no")[0], tk.encode("no")[0], tk.encode("No")[0]]
    o_def2 = np.array([odds(DEF_Q2, s["sentence"], YES, NO) for s in S])
    json.dump({"rule": rule.tolist(), "o_v7": o_v7.tolist(), "o_def": o_def.tolist(), "o_def2": o_def2.tolist(), "y": y.tolist()},
              open("e8_design.json", "w"))

    def rep(name, hit):
        tp, fp = (hit & y).sum(), (hit & ~y).sum()
        print(f"  {name:32s} caught {tp}/{y.sum()} = {tp / y.sum():.3f}   false {fp}/{(~y).sum()} = {fp / (~y).sum():.3f}")
    print("design: mirrors", y.sum(), "none", (~y).sum())
    rep("v6 rule", rule)
    for nm, o in (("v7 organ", o_v7), ("DEF organ (A/B)", o_def), ("DEF2 organ (yes/no)", o_def2)):
        for th in (-2, -1, 0, 1, 2, 3, 4):
            rep(f"{nm} > {th}", o > th); rep(f"rule OR {nm} > {th}", rule | (o > th))


if __name__ == "__main__":
    main()
