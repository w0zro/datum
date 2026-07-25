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
import struct
import subprocess
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from derive import fingerprint, palette  # noqa: E402

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


# ---------------------------------------------------------------- staleness stamp
# Rendering needs Chrome + Monaspace and only runs on a Mac, so CI cannot just
# re-render and diff. Instead each PNG carries the palette fingerprint it was
# rendered from, in a tEXt chunk; --check compares that against the palette
# today. A hue edit without a re-render is then a hard error instead of a
# README that quietly shows the old colors.
PNG_SIG = b"\x89PNG\r\n\x1a\n"
KEYWORD = b"datum-palette"


def _chunks(blob):
    i = len(PNG_SIG)
    while i < len(blob):
        (length,) = struct.unpack(">I", blob[i:i + 4])
        ctype = blob[i + 4:i + 8]
        yield ctype, blob[i + 8:i + 8 + length], blob[i:i + 12 + length]
        i += 12 + length


def stamp(png_path, fp):
    """Insert (or replace) the fingerprint tEXt chunk, just before IEND."""
    blob = open(png_path, "rb").read()
    out = bytearray(PNG_SIG)
    for ctype, _data, raw in _chunks(blob):
        if ctype == b"tEXt" and _data.startswith(KEYWORD + b"\x00"):
            continue  # drop a previous stamp
        if ctype == b"IEND":
            payload = KEYWORD + b"\x00" + fp.encode()
            out += struct.pack(">I", len(payload)) + b"tEXt" + payload
            out += struct.pack(">I", zlib.crc32(b"tEXt" + payload) & 0xFFFFFFFF)
        out += raw
    open(png_path, "wb").write(bytes(out))


def read_stamp(png_path):
    for ctype, data, _raw in _chunks(open(png_path, "rb").read()):
        if ctype == b"tEXt" and data.startswith(KEYWORD + b"\x00"):
            return data.split(b"\x00", 1)[1].decode()
    return None


def check():
    """Verify the committed previews were rendered from the current palette."""
    want = fingerprint()
    stale = []
    for mode in ("dark", "light"):
        png = os.path.join(ROOT, "docs", "preview-%s.png" % mode)
        got = read_stamp(png) if os.path.exists(png) else None
        if got != want:
            stale.append("preview-%s.png (stamped %s, palette is %s)"
                         % (mode, got or "unstamped", want))
    if stale:
        print("STALE previews -- re-run tools/gen_preview.py on a Mac:")
        for s in stale:
            print("  " + s)
        return 1
    print("previews match the current palette (%s)" % want)
    return 0


def main():
    if "--check" in sys.argv:
        return check()
    if not os.path.exists(CHROME):
        print("Google Chrome not found; cannot render previews.")
        return 1
    outdir = os.path.join(ROOT, "docs")
    os.makedirs(outdir, exist_ok=True)
    fp = fingerprint()
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
        stamp(png_path, fp)
        print("wrote %s (%d bytes, palette %s)"
              % (os.path.relpath(png_path, ROOT), os.path.getsize(png_path), fp))
    return 0


if __name__ == "__main__":
    sys.exit(main())
