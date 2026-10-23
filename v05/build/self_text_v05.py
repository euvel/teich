"""Teich v0.5 — its questions (with their true reasons) and its new account lines. Templates only; no language model.
A question's reason line is rendered FROM ITS REASON RECORD (the inputs its rule saw), so the reason shown is the
reason that caused the question — the same record live verify checks."""
import self_text_v04 as T4

REGION = {k: v for k, v in T4.REG.items() if isinstance(k, int) and k < 9}


def question(q, inputs):
    """q: the ask act (["region", k] | ["word", w]); inputs: its reason record's inputs. -> (question, reason line)."""
    if q[0] == "word":
        w = q[1]; count = next(c for x, c, _ in inputs["door"] if x == w)
        days = next(d for x, _, d in inputs["door"] if x == w)
        why = f"I heard it {count} times and no concept of mine was close enough"
        if days:
            why += "; you answered once before, and one more answer on another day would let me keep it"
        return f"I could not place '{w}'. What is it?", why
    k = q[1]; lo, hi = next((l, h) for kk, l, h in inputs["unresolved"] if kk == k)
    need = max(0, inputs["n_g"] - lo) + max(0, inputs["n_g"] - hi)
    more = f"{need} more answer{'s' if need != 1 else ''}"
    if k == 8:
        return "What am I to you?", (f"I have heard little about myself: {more} would let me tell whether "
                                     f"my mistakes in hearing about myself are mine")
    return f"What is {REGION[k]} to you?", (f"{more} would let me tell whether my mistakes in hearing about "
                                            f"{REGION[k]} are mine")


XTEXT = {("BODY-MEMORY", "FINE"): "My memory is foreseeable: I predicted my own readings and they held.",
         ("BODY-MEMORY", "GIVEN"): "My memory was not foreseeable tonight.",
         ("BODY-PATH", "GIVEN"): "The paths of my thoughts are not foreseeable: they are new every night.",
         ("BODY-PATH", "FINE"): "The paths of my thoughts were foreseeable.",
         ("THINK", "GIVEN"): "What my thinking does cannot be foreseen without thinking it.",
         ("THINK", "FINE"): "What my thinking does could be foreseen cheaply."}


def sentences(block):
    out = list(T4.sentences(block))
    x = block.get("self5")
    if not x:
        return out
    for ch in x["changes"]:
        line = XTEXT.get((ch["kind"], ch["to"]))
        if ch["wrong_about_myself"]:
            out.append(f"I was wrong about myself: I thought {ch['kind'].lower()} was {ch['from'].lower()}, "
                       f"and it is {ch['to'].lower()}.")
        if line:
            k = x["kinds"][ch["kind"]]
            out.append(f"{line} ({k['n'] - k['miss']} of {k['n']} predictions held.)")
    h = x.get("hearing")
    if h and h["asked"][0]:
        out.append(f"When I asked, you struck {h['asked'][1]} of {h['asked'][0]} of my hearings; "
                   f"when I did not, {h['free'][1]} of {h['free'][0]}.")
    return out
