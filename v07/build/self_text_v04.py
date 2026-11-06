"""The second self's nightly account in plain sentences — fixed templates over the `self` block, no language model.
Every sentence is one claim of the block, and the block carries its receipt."""
from fractions import Fraction

import self_v04 as S

REG = {0: "food & drink", 1: "body & matter", 2: "living things", 3: "objects & places", 4: "people & feeling",
       5: "mind & society", 6: "arts & events", 7: "work & things made", 8: "itself", S.READINGS: "my readings"}


def pct(q):
    return f"{round(100 * Fraction(*q))}%"


def sentences(block):
    out = []
    for f in block["facts"]:
        k = f["kind"]
        out.append(f"I spoke {f['acts']} reading{'s' * (f['acts'] != 1)}; {f['struck']} were later revised with no new step between."
                   if k == S.READINGS else
                   f"About {REG[k]}, I offered {f['acts']} hearing{'s' * (f['acts'] != 1)}; you struck {f['struck']}.")
    for v in block["verdicts"]:
        k, o = v["kind"], v["receipt"]["out"]; to = v["to"]
        lo, hi = f"{o['s_lo']} of {o['n_lo']}", f"{o['s_hi']} of {o['n_hi']}"
        out.append({"MINE": f"About {REG[k]}, my errors look like mine: when I was unsure, {lo} were struck; when sure, {hi}.",
                    "GIVEN": f"About {REG[k]}, my errors look given: struck as often when I was sure ({hi}) as when unsure "
                             f"({lo}). The input is hard there; more caution would not help.",
                    "FINE": f"About {REG[k]}, I am rarely wrong ({o['s_lo'] + o['s_hi']} of {o['n_lo'] + o['n_hi']}).",
                    "UNRESOLVED": f"About {REG[k]}, I don't know yet whether my errors are mine."}[to])
    for v in block["will"]:
        a, b = v["caution"]
        out.append(f"I became more careful about {REG[v['kind']]} (caution {a} → {b})." if b > a else
                   f"I eased my caution about {REG[v['kind']]} ({a} → {b}): " + v["why"].split(": ", 1)[1] + ".")
    for v in block["curiosity"]:
        out.append(f"I tested myself {v['probes']} time(s) about {REG[v['kind']]}, showing what my caution would hide; "
                   f"you struck {v['struck']}.")
    for v in block["comparisons"]:
        out.append(f"I expected {pct(v['predicted'])} of my {'readings' if v['kind'] == S.READINGS else 'hearings about ' + REG[v['kind']]}"
                   f" to go wrong; it was {pct(v['actual'])} ({v['receipt']['out']['struck']} of {v['receipt']['out']['n']}).")
    if block["calibration"]:
        c = block["calibration"]
        b, k = float(Fraction(*c["brier"])), float(Fraction(*c["without_self_knowledge"]))
        out.append(f"How well I foresee myself: error {b:.3f}, against {k:.3f} if I knew only how often I am wrong, not "
                   f"where ({'knowing where helps' if b < k else 'knowing where does not help yet'}).")
    return out
