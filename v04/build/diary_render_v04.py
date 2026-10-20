"""Render attention-diary entries to a static HTML page (LAB PREVIEW — not published; birth decides where it lives).

    python3 diary_render_v04.py DIARY.json OUT.html [title-note]
DIARY.json: a list of entries, or {"diary": [...]} (w2b/w3 output).
"""
import html
import json
import sys

src = json.load(open(sys.argv[1]))
entries = src["diary"] if isinstance(src, dict) else src
out = sys.argv[2]
note = sys.argv[3] if len(sys.argv) > 3 else "Lab preview from a simulated life on design seeds. Not the creature."
REG = {"LLL": "food & drink", "LLR": "body & matter", "LRL": "living things", "LRR": "objects & places",
       "RLL": "people & feeling", "RLR": "mind & society", "RRL": "arts & events", "RRR": "work & things made",
       "self": "itself"}
esc = html.escape


def bar(v, lo, hi):
    w = max(0.0, min(1.0, (v - lo) / (hi - lo))) * 100
    return f'<span class="bar"><span style="width:{w:.0f}%"></span></span>'


cards = []
for e in reversed(entries):
    att = "".join(f'<li><span class="nm">{esc(a["name"])}</span>{bar(a["length_vs_birth"], 1.0, 2.72)}'
                  f'<span class="num">+{a["read"]} · {a["nights"]} nights</span></li>' for a in e["attending_most"]) \
        or '<li class="quiet">Nothing stands out yet: every cluster it can read is at its birth length.</li>'
    sh = "".join(f'<li><span class="nm">{esc(s["name"])}</span><span class="num">{s["from"]} → {s["to"]}</span></li>'
                 for s in e["shifts"]) or '<li class="quiet">none</li>'
    still = ", ".join(esc(s["name"].split(" · ")[0]) for s in e["still_reading"]) or "—"
    heart = "".join(f'<div class="h"><span>{esc(REG.get(r, r))}</span>{bar(k, 0, 6)}<span class="num">{k}</span></div>'
                    for r, k in e["heart"].items())
    v = e["verification"]
    cards.append(f'''<article>
<header><h2>Day {e["day"] + 1}</h2><span class="meta">heard {e["heard"]["mentions"]} mentions · {e["heard"]["accepted"]} moved a dial</span></header>
<div class="grid"><section><h3>Attending most to</h3><ol>{att}</ol>
<h3>Shifts it read tonight</h3><ul>{sh}</ul>
<p class="still"><b>Still reading</b> (moved recently, not yet settled): {still}</p></section>
<section><h3>Heart</h3>{heart}</section></div>
<footer>Verification (for readers, not used by it): of {v["clusters_spoken"]} settled readings, {v["spoken_read_equals_ledger"]} equal its ledger; a single night alone read {v["tonight_read_equals_ledger"]} of 98 exactly.</footer>
</article>''')

page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Attention Diary Preview</title>
<style>
:root{{--bg:#fbfaf7;--fg:#1d1d1b;--mut:#6b6a66;--line:#e4e1da;--acc:#2f6f5e;--card:#fff}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#151614;--fg:#e9e7e1;--mut:#9a988f;--line:#2c2d2a;--acc:#7cc2ab;--card:#1c1d1b}}}}
:root[data-theme="dark"]{{--bg:#151614;--fg:#e9e7e1;--mut:#9a988f;--line:#2c2d2a;--acc:#7cc2ab;--card:#1c1d1b}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:880px;margin:0 auto;padding:32px 16px}}
h1{{font-size:24px;margin:0 0 4px}} .lede{{color:var(--mut);margin:0 0 24px}}
article{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:0 0 16px}}
article header{{display:flex;justify-content:space-between;align-items:baseline;gap:8px;flex-wrap:wrap}}
h2{{font-size:17px;margin:0}} h3{{font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--mut);margin:14px 0 6px}}
.meta,.num,.quiet,footer,.still{{color:var(--mut);font-size:13px}}
.grid{{display:grid;grid-template-columns:3fr 2fr;gap:24px}} @media (max-width:640px){{.grid{{grid-template-columns:1fr}}}}
ol,ul{{margin:0;padding-left:18px}} li{{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:2px 0}}
.nm{{min-width:0;flex:1 1 180px}} .bar{{display:inline-block;width:90px;height:6px;background:var(--line);border-radius:3px;overflow:hidden}}
.bar span{{display:block;height:100%;background:var(--acc)}} .h{{display:flex;gap:8px;align-items:center;font-size:13px;margin:3px 0}}
.h span:first-child{{flex:1}} footer{{border-top:1px solid var(--line);margin-top:12px;padding-top:8px}}
</style></head><body><main>
<h1>Teich v0.4 — attention diary</h1>
<p class="lede">{esc(note)} Each night it reads its own mind from the paths of its thoughts. A reading is spoken only after three quiet nights. No language model writes these entries.</p>
{"".join(cards)}
</main></body></html>'''
open(out, "w").write(page)
print(f"{len(entries)} entries -> {out}")
