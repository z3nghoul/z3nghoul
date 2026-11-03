"""Embed JetBrains Mono into the stats card SVGs.

GitHub shows the cards as images, so an SVG cannot load a web font from a
URL; the font has to travel inside the file. This puts the subset WOFF files
from assets/fonts into an @font-face rule and points every font declaration
of the card at it. Standard library only.

usage: python3 embed_font.py assets/stats.svg assets/top-langs.svg
"""

import base64
import pathlib
import re
import sys

FONTS = pathlib.Path(__file__).resolve().parents[2] / "assets" / "fonts"
FAMILY = "'JetBrains Mono Card', 'JetBrains Mono', ui-monospace, monospace"
MARKER = "/* jetbrains-mono-embedded */"


def face(weight: int, filename: str) -> str:
    data = base64.b64encode((FONTS / filename).read_bytes()).decode("ascii")
    return (
        "@font-face { font-family: 'JetBrains Mono Card'; "
        f"font-weight: {weight}; font-style: normal; "
        f"src: url(data:font/woff;base64,{data}) format('woff'); }}"
    )


FACES = "\n".join(
    [
        MARKER,
        face(400, "JetBrainsMono-Regular.subset.woff"),
        face(700, "JetBrainsMono-Bold.subset.woff"),
    ]
)

# `font: <weight> <size> <family list>;` and `font-family: <list>;`
FONT_SHORTHAND = re.compile(r"(font:\s*\d{3}\s+[\d.]+px\s+)[^;}]+")
FONT_FAMILY = re.compile(r"(font-family:\s*)[^;}\"]+")


# A monospace font is wider than the default one, so the longest labels of the
# stats card would run into their values. Shorter, lowercase labels fit and
# match the rest of the profile. A label that is not found is left as it is.
LABELS = {
    "Total Commits (last year):": "commits, last year:",
    "Total PRs:": "pull requests:",
    "Total Issues:": "issues:",
}


def embed(path: pathlib.Path) -> None:
    svg = path.read_text(encoding="utf-8")
    if MARKER in svg:
        return
    for old, new in LABELS.items():
        svg = svg.replace(">" + old + "<", ">" + new + "<")
    svg = FONT_SHORTHAND.sub(lambda m: m.group(1) + FAMILY, svg)
    svg = FONT_FAMILY.sub(lambda m: m.group(1) + FAMILY, svg)
    svg, count = re.subn(r"<style>", "<style>\n" + FACES + "\n", svg, count=1)
    if count != 1:
        sys.exit(f"{path}: no <style> block to put the font in")
    path.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        embed(pathlib.Path(arg))
