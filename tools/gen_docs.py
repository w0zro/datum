#!/usr/bin/env python3
"""Push the derived palette into the docs site and the brand marks.

The site used to keep its own copy of every hex -- in the CSS custom
properties, in the TOKENS array behind the swatches, and in the gem's facets.
That is three more places to forget, and they were all left 13 colors behind by
one palette edit. Nothing here is authored: every value is rewritten from
derive.py, keyed by role, so the page can only ever show the real palette.

    python3 tools/gen_docs.py          # rewrite
    python3 tools/gen_docs.py --check  # non-zero exit if anything is stale (CI)
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from derive import palette  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The ideas page calls the type colour "teal"; the landing page calls it "cyan".
ALIAS = {"teal": "cyan"}

# Gem facets, clockwise from the top-right wedge. Two tier-2 colours are in
# here on purpose: the mark shows the whole palette, not just tier 1.
FACETS = ["yellow", "green", "cyan", "blue", "purple", "call", "red", "orange"]


def _css(text, mode_of_block):
    """Rewrite every `--role:#hex` to the palette value for its block's mode."""
    out, mode = [], "dark"
    for line in text.split("\n"):
        if ":root[data-theme=\"light\"]" in line or "prefers-color-scheme: light" in line:
            mode = "light"
        elif ":root[data-theme=\"dark\"]" in line or re.match(r"\s*:root\s*\{", line):
            mode = "dark"
        p = palette(mode)

        def swap(m):
            role = ALIAS.get(m.group(1), m.group(1))
            return f"--{m.group(1)}:{p[role]['hex']}" if role in p else m.group(0)

        out.append(re.sub(r"--([a-z0-9]+):#[0-9a-fA-F]{6}", swap, line))
    return "\n".join(out)


def _tokens(text):
    """Rewrite the TOKENS array: dark:['#hex',cterm], light:['#hex',cterm]."""
    def entry(m):
        role, body = m.group(1), m.group(0)
        for mode in ("dark", "light"):
            v = palette(mode)[role]
            body = re.sub(rf"{mode}:\['#[0-9a-fA-F]{{6}}',\s*\d+\]",
                          f"{mode}:['{v['hex']}',{v['cterm']}]", body)
        return body
    return re.sub(r"\{n:'([a-z0-9]+)'.*?\},", entry, text)


def _svg(text):
    """Rewrite the gem's facet fills in document order.

    Some variants (the favicon, the avatar) sit on a bg0 tile and some are
    transparent, so the background <rect> is matched separately rather than
    being counted as a facet."""
    dark = palette("dark")
    text = re.sub(r'(<rect[^>]*?fill=")#[0-9a-fA-F]{6}(")',
                  lambda m: m.group(1) + dark["bg0"]["hex"] + m.group(2), text)
    it = iter(FACETS)
    return re.sub(r'(<polygon[^>]*?fill=")#[0-9a-fA-F]{6}(")',
                  lambda m: m.group(1) + dark[next(it)]["hex"] + m.group(2), text)


TARGETS = {
    "docs/index.html": lambda t: _tokens(_css(t, None)),
    "docs/ideas/index.html": lambda t: _css(t, None),
    "docs/mark.svg": _svg,
    "docs/favicon.svg": _svg,
    "assets/icon.svg": _svg,
}


def main():
    check = "--check" in sys.argv
    stale = []
    for rel, rewrite in sorted(TARGETS.items()):
        path = os.path.join(ROOT, rel)
        current = open(path).read()
        new = rewrite(current)
        if check:
            if current != new:
                stale.append(rel)
            continue
        if current != new:
            open(path, "w").write(new)
        print(("unchanged " if current == new else "wrote     ") + rel)
    if check:
        print("STALE: " + ", ".join(stale) if stale
              else "docs match the palette")
        return 1 if stale else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
