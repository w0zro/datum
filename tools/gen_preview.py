#!/usr/bin/env python3
"""Render palette preview images from the derived palette.

Like the ports, these are generated from tools/derive.py so they cannot drift.
Renders a code sample in each mode via headless Chrome (no screen-recording
permission needed) using Monaspace, matching the recommended setup.

    python3 tools/gen_preview.py

Writes docs/preview-dark.png and docs/preview-light.png.

NOTE: these are faithful renders of the palette, not screenshots of a running
editor -- Tree-sitter in a real buffer is what actually assigns these roles.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from derive import palette  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# (text, role) -- role maps to a palette key, or a pseudo-role handled below.
SAMPLE = [
    [("# datum -- derived from color science, not taste", "comment")],
    [("from", "kw"), (" typing ", "plain"), ("import", "kw"), (" ", "plain"), ("Optional", "type")],
    [],
    [("MAX_RETRIES", "const"), (" ", "plain"), ("=", "op"), (" ", "plain"), ("3", "num")],
    [("DEFAULT_NAME", "const"), (" ", "plain"), ("=", "op"), (" ", "plain"), ('"datum"', "str")],
    [],
    [("def", "kw"), (" ", "plain"), ("load_config", "fn"), ("(", "punc"), ("path", "param"),
     (": ", "punc"), ("str", "type"), (") ", "punc"), ("->", "op"), (" ", "plain"),
     ("Optional", "type"), ("[", "punc"), ("dict", "type"), ("]:", "punc")],
    [("    attempts", "var"), (" ", "plain"), ("=", "op"), (" ", "plain"), ("0", "num")],
    [("    while", "kw"), (" ", "plain"), ("attempts", "var"), (" ", "plain"), ("<=", "op"),
     (" ", "plain"), ("MAX_RETRIES", "const"), (":", "punc")],
    [("        raw", "var"), (" ", "plain"), ("=", "op"), (" ", "plain"), ("read_file", "call"),
     ("(", "punc"), ("path", "param"), (")", "punc")],
    [("        if", "kw"), (" ", "plain"), ("raw", "var"), (" ", "plain"), ("is not", "kw"),
     (" ", "plain"), ("None", "const"), (" ", "plain"), ("and", "kw"), (" ", "plain"),
     ("len", "call"), ("(", "punc"), ("raw", "var"), (")", "punc"), (" ", "plain"),
     (">=", "op"), (" ", "plain"), ("0", "num"), (":", "punc")],
    [("            return", "kw"), (" ", "plain"), ("parse", "call"), ("(", "punc"),
     ("raw", "var"), (")", "punc"), (" ", "plain"), ("or", "kw"), (" ", "plain"),
     ("DEFAULT_NAME", "const")],
    [("        attempts", "var"), (" ", "plain"), ("+=", "op"), (" ", "plain"), ("1", "num")],
    [("    return", "kw"), (" ", "plain"), ("None", "const")],
]

ROLE_KEY = {
    "comment": "fg1", "plain": "fg0", "punc": "fg1",
    "kw": "blue", "str": "green", "num": "orange", "const": "yellow",
    "type": "cyan", "fn": "purple",
    "var": "var", "call": "call", "param": "param", "op": "op",
}


def render_html(mode):
    p = palette(mode)
    hx = lambda role: p[ROLE_KEY[role]]["hex"]  # noqa: E731
    lines = []
    for line in SAMPLE:
        if not line:
            lines.append('<div class="l">&nbsp;</div>')
            continue
        spans = "".join(
            '<span style="color:{c}{extra}">{t}</span>'.format(
                c=hx(role),
                extra=";font-style:italic" if role == "comment" else "",
                t=text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                       .replace(" ", "&nbsp;"),
            )
            for text, role in line
        )
        lines.append('<div class="l">%s</div>' % spans)
    return """<!doctype html><meta charset="utf-8"><style>
  html,body{{margin:0;padding:0;background:{bg0};}}
  .wrap{{padding:26px 30px;background:{bg0};}}
  .bar{{display:flex;gap:7px;margin-bottom:16px;align-items:center;}}
  .dot{{width:11px;height:11px;border-radius:50%;display:block;}}
  .name{{margin-left:10px;font:12px/1 'Monaspace Neon',monospace;color:{fg1};}}
  /* same font features as the recommended Ghostty config: texture healing,
     coding ligatures, slashed zero -- so the preview matches real rendering */
  .l{{font:14px/1.75 'Monaspace Neon',ui-monospace,monospace;white-space:pre;
     font-feature-settings:'calt','liga','ss01','ss02','ss03','ss04','ss05',
                           'ss06','ss07','ss08','ss09','cv01' 2;}}
  .tag{{margin-top:16px;font:11px/1 'Monaspace Neon',monospace;color:{fg1};}}
</style><div class="wrap">
  <div class="bar">
    <span class="dot" style="background:{red}"></span>
    <span class="dot" style="background:{yellow}"></span>
    <span class="dot" style="background:{green}"></span>
    <span class="name">datum &mdash; {mode}</span>
  </div>
  {body}
  <div class="tag">full chroma = reference points &nbsp;·&nbsp; pastel = the glue</div>
</div>""".format(
        bg0=p["bg0"]["hex"], fg1=p["fg1"]["hex"], red=p["red"]["hex"],
        yellow=p["yellow"]["hex"], green=p["green"]["hex"], mode=mode,
        body="\n  ".join(lines),
    )


def main():
    if not os.path.exists(CHROME):
        print("Google Chrome not found; cannot render previews.")
        return 1
    outdir = os.path.join(ROOT, "docs")
    os.makedirs(outdir, exist_ok=True)
    for mode in ("dark", "light"):
        html_path = "/tmp/datum_preview_%s.html" % mode
        png_path = os.path.join(outdir, "preview-%s.png" % mode)
        with open(html_path, "w") as fh:
            fh.write(render_html(mode))
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
             "--force-device-scale-factor=2", "--window-size=760,430",
             "--screenshot=" + png_path, html_path],
            check=True, capture_output=True,
        )
        print("wrote %s (%d bytes)" % (os.path.relpath(png_path, ROOT),
                                       os.path.getsize(png_path)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
