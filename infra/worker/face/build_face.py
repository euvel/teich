"""Build the public face into the Worker. Edit face/ (face.html, face.css, face.js, delib.js, duduk_words.json), never
the built line in index.js. The page goes in as one JSON string literal, so nothing in it needs escaping by hand.
    python3 face/build_face.py            -> rewrites PANEL_HTML in index.js, writes face/dist/index.html
"""
import json
import re
from pathlib import Path

F = Path(__file__).resolve().parent
W = F.parent / "index.js"
CONST = F.parents[2] / "v06" / "build" / "deliberation_constants_v06.json"


def page():
    html = (F / "face.html").read_text()
    legacy = {k: (F / "legacy" / f"{k.lower()}.html").read_text() for k in ("V05", "V04", "V03", "V02", "V01")}
    words = json.loads((F / "duduk_words.json").read_text()) if (F / "duduk_words.json").exists() else {}
    selftest = json.loads((F / "test" / "selftest_vectors.json").read_text())
    js = "\n".join([
        (F / "delib.js").read_text(),
        "const DELIB_CONSTANTS = " + json.dumps(json.loads(CONST.read_text()), separators=(",", ":")) + ";",
        "const SELFTEST = " + json.dumps(selftest, separators=(",", ":")) + ";",
        "const DUDUK_WORDS = " + json.dumps(words, ensure_ascii=False) + ";",
        (F / "face.js").read_text(),
    ])
    assert "</script" not in js.lower(), "a closing script tag inside the inline script would end it early"
    out = html.replace("{{CSS}}", (F / "face.css").read_text()).replace("{{JS}}", js)
    for k, v in legacy.items():
        out = out.replace("{{LEGACY_" + k + "}}", v)
    left = re.findall(r"\{\{[A-Z0-9_]+\}\}", out)
    assert not left, f"unfilled placeholders: {left}"
    return out


def main():
    out = page()
    (F / "dist").mkdir(exist_ok=True)
    (F / "dist" / "index.html").write_text(out)
    s = W.read_text()
    begin, end = "// FACE:BEGIN", "// FACE:END"
    line = (f"{begin} (built by face/build_face.py from face/: edit those, not this line)\n"
            f"const PANEL_HTML = {json.dumps(out, ensure_ascii=False)};\n{end}")
    if begin in s:
        s = re.sub(re.escape(begin) + r".*?" + re.escape(end), lambda m: line, s, flags=re.S)
    else:
        a = s.index("const PANEL_HTML = `")
        b = s.index("</script></body></html>`;", a) + len("</script></body></html>`;")
        s = s[:a] + line + s[b:]
    W.write_text(s)
    print(f"face built: {len(out):,} bytes -> index.js + face/dist/index.html")


if __name__ == "__main__":
    main()
