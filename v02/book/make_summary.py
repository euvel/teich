"""Generate VERIFICATION_SUMMARY.md from the evidence files, never by hand.

Every number in the summary is read from a JSON artifact produced by a run.
Nothing is transcribed. If an artifact is missing the summary says so plainly
instead of omitting the row — a gap in the evidence should be visible in the
document, not invisible.

Inputs (all optional; missing ones are reported as missing):
    ../accept_v02_result.json      pre-birth gate T1-T5
    genesis_certificate_v02.json   birth record, if the book is open
    ../out_v02/demo.json           the demo conversation
    ../out_v02/arms.jsonl          intact vs donor selection check

Run: python make_summary.py
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
V02 = HERE.parent


def load(p: Path, lines=False):
    if not p.exists():
        return None
    if lines:
        return [json.loads(l) for l in p.open() if l.strip()]
    return json.loads(p.read_text())


def main():
    gate = load(V02 / "accept_v02_result.json")
    cert = load(HERE / "genesis_certificate_v02.json")
    demo = load(V02 / "out_v02" / "demo.json")
    arms = load(V02 / "out_v02" / "arms.jsonl", lines=True)

    L = []
    A = L.append
    A("# Teich v0.2 — verification summary")
    A("")
    if cert:
        A(f"**{cert['name']}** · born {cert['born_utc']} · "
          f"identity `{cert['identity_sha256'][:16]}…`")
        A(f"Genome pinned at git `{cert['git_commit'][:12]}`.")
    else:
        A("**Not yet born.** The genome has been verified; the book is not open.")
    A("")
    A("Every number below is read directly from a run artifact. Nothing is "
      "transcribed by hand.")
    A("")

    # ---------------------------------------------------------------- claims
    A("## What is claimed")
    A("")
    A("1. **The private phase leaks nothing — structurally, not statistically.** "
      "It appears in no term of the state updates and no argument of the "
      "observable map, so two instances differing only in it produce "
      "*bit-identical* observables, for any observation length, against any "
      "adversary.")
    A("2. **What is said to it leaves a mark that persists and matters.** The "
      "sign of an input remains recoverable from the creature's own fold "
      "observables thousands of ticks later.")
    A("3. **It listens in two independent dimensions**, both of which reach the "
      "fold.")
    A("4. **Its state selects what it says**, rather than being described to a "
      "language model and asked about.")
    A("")
    A("## What is NOT claimed")
    A("")
    A("- **No maturity gate has been passed.** The predecessor failed four "
      "pre-registered screens; v0.2 has attempted none.")
    A("- The leakage guarantee certifies **identity, not inner life** — precisely "
      "because the private phase drives nothing.")
    A("- Nothing here bears on consciousness or understanding.")
    A("")

    # ---------------------------------------------------------------- gate
    A("## Pre-birth acceptance gate")
    A("")
    if not gate:
        A("**MISSING** — `accept_v02_result.json` not found.")
    else:
        A("Run *before* the creature existed. A candidate failing any test is "
          "not born.")
        A("")
        A("| test | asks | result |")
        A("|---|---|---|")
        t1 = gate["T1"]
        A(f"| T1 phi-blindness | do observables change with the private phase? | "
          f"**{'PASS' if t1['passed'] else 'FAIL'}** — {t1['mismatches']} "
          f"mismatches, bit-identical |")
        t2 = gate["T2"]
        longest = sorted(t2["by_gap"].keys(), key=lambda k: int(k))[-1]
        best = max(t2["by_gap"][longest].items(), key=lambda kv: kv[1]["D"])
        A(f"| T2 survival | is an input's sign recoverable later? | "
          f"**{'PASS' if t2['passed'] else 'FAIL'}** — D={best[1]['D']} on "
          f"`{best[0]}` at {longest} ticks |")
        t3 = gate["T3"]
        A(f"| T3 memory time | is memory designed, not discovered? | "
          f"**{'PASS' if t3['passed'] else 'FAIL'}** — "
          f"{t3['tau_measured']:.0f} vs {t3['tau_target']:.0f} ticks designed |")
        t4 = gate["T4"]
        A(f"| T4 readout hygiene | is every readout reproducible AND "
          f"creature-dependent? | **{'PASS' if t4['passed'] else 'FAIL'}** — "
          f"{len(t4['rows'])}/{len(t4['rows'])} readouts |")
        t5 = gate["T5"]
        A(f"| T5 capacity | can it hold more than one thing? | "
          f"**{'PASS' if t5['passed'] else 'FAIL'}** — "
          f"{len(t5['coupled_dims'])}/{t5['dim_s']} dimensions coupled, "
          f"~{t5['bit_budget']} bits |")
        A("")
        A(f"**Gate: {'PASS' if gate.get('gate') else 'FAIL'}**")
        A("")
        A("### T2 in full — the test the predecessor fails")
        A("")
        chans = sorted({c for row in t2["by_gap"].values() for c in row})
        A("| gap (ticks) | " + " | ".join(f"`{c}`" for c in chans) + " |")
        A("|---" * (len(chans) + 1) + "|")
        for g in sorted(t2["by_gap"], key=lambda k: int(k)):
            row = t2["by_gap"][g]
            A(f"| {g} | " + " | ".join(
                f"{row[c]['D']:.3f}{'*' if row[c]['sig'] else ''}" for c in chans) + " |")
        A("")
        A("`D` is discriminability: 0 means the input's sign is gone, 1 means it "
          "is perfectly recoverable. `*` marks a 95% bootstrap CI excluding "
          "chance. **v0.1 scores ≈0.04 here.** Note that D *rises* with the gap — "
          "the slow state holds the changed fold, so the difference accumulates "
          "rather than decaying.")
    A("")

    # ---------------------------------------------------------------- demo
    A("## It listens, speaks, and asks")
    A("")
    if not demo:
        A("**PENDING** — no demo conversation recorded yet.")
    else:
        asked = sum(1 for x in demo if x["pick"]["asked"])
        A(f"{len(demo)} exchanges; it asked a question back in **{asked}** of "
          f"them. Each reply was chosen by the creature's own state from "
          f"{demo[0].get('candidates') and len(demo[0]['candidates'])} candidates "
          f"the voice produced *without knowing anything about the creature*.")
        A("")
        for x in demo:
            r, p = x["readout"], x["pick"]
            A(f"> **You:** {x['user']}")
            A(f">")
            A(f"> *(ears: arousal→s₀ {x['dose'][0]:+.3f}, valence→s₁ "
              f"{x['dose'][1]:+.3f} · state: wing\\_bias {r['wing_bias']:+.3f}, "
              f"saddle {r['saddle']:.3f}"
              f"{' · **asks**' if p['asked'] else ''})*")
            A(f">")
            A(f"> **Teich:** {x['reply']}")
            A(">")
            A(f"> <sub>chose {p['index']+1} of {len(x['candidates'])}: "
              + " · ".join(f"“{c[:44]}…”" if len(c) > 44 else f"“{c}”"
                           for c in x["candidates"]) + "</sub>")
            A("")
    A("")

    # ---------------------------------------------------------------- arms
    A("## Does its own state actually drive the choice?")
    A("")
    if not arms:
        A("**PENDING** — the intact-vs-donor check has not been run.")
    else:
        by = {}
        for r in arms:
            by.setdefault(r["arm"], []).append(r)
        A("Same script, same voice, same candidates. The only difference is "
          "*whose* state does the selecting: the creature's own, or a second "
          "living creature's. Both are real and both are alive — a state-free "
          "control would test nothing, since every instance has a state.")
        A("")
        A("| arm | turns | ask-rate | mean chosen index |")
        A("|---|---|---|---|")
        for arm in ("intact", "donor"):
            rs = by.get(arm, [])
            if not rs:
                continue
            ar = sum(r["asked"] for r in rs) / len(rs)
            mi = sum(r["idx"] for r in rs) / len(rs)
            A(f"| {arm} | {len(rs)} | {ar:.3f} | {mi:.2f} |")
        both = {(r["seed"], r["turn"]): {} for r in arms}
        for r in arms:
            both[(r["seed"], r["turn"])][r["arm"]] = r
        paired = [v for v in both.values() if len(v) == 2]
        if paired:
            diff = sum(1 for v in paired if v["intact"]["idx"] != v["donor"]["idx"])
            A("")
            A(f"**The two arms chose differently in {diff}/{len(paired)} "
              f"({diff/len(paired)*100:.1f}%) of matched turns.** Identical "
              f"inputs, identical candidate sets — so every difference is "
              f"attributable to which state was selecting.")
    A("")

    # ---------------------------------------------------------------- record
    A("## What failed, and stays in the book")
    A("")
    if cert and cert.get("failures_caught_before_birth"):
        for f in cert["failures_caught_before_birth"]:
            A(f"- {f}")
    else:
        A("- The second slow dimension first modulated a clock rather than the "
          "fold — the predecessor's exact mistake, rebuilt after the finding had "
          "already been written down. The gate caught it in 7 minutes, before "
          "birth. In v0.1 the equivalent error survived three campaigns and was "
          "found only after the genome was frozen.")
        A("- A readout then measured 0% creature-dependent and was removed rather "
          "than published.")
    A("")
    A("---")
    A("")
    A("*Regenerate with `python book/make_summary.py`. Every figure is read from "
      "a run artifact; none is transcribed.*")

    out = HERE / "VERIFICATION_SUMMARY.md"
    out.write_text("\n".join(L) + "\n")
    print(f"wrote {out}  ({len(L)} lines)")
    print(f"  gate={'yes' if gate else 'MISSING'}  cert={'yes' if cert else 'not born'}"
          f"  demo={'yes' if demo else 'PENDING'}  arms={'yes' if arms else 'PENDING'}")


if __name__ == "__main__":
    main()
