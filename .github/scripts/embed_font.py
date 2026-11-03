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


ROOT_SIZE = re.compile(r'(<svg\s+width="(\d+)"\s+height=")(\d+)("\s+viewBox=")[-\d.]+ [-\d.]+ (\d+) (\d+)(")')
CARD_BG_Y = re.compile(r'(data-testid="card-bg"[^>]*?\sy=")([-\d.]+)(")', re.S)


def height(path: pathlib.Path) -> int:
    match = ROOT_SIZE.search(path.read_text(encoding="utf-8"))
    if not match:
        sys.exit(f"{path}: no root <svg> size to read")
    return int(match.group(3))


def match_height(path: pathlib.Path, target: int) -> None:
    """Grow a card to `target` px and keep its content centred vertically.

    The background rect is drawn at 99% of the card height, so it grows with
    the card; the view box is moved up by half the extra space and the rect
    follows it, so the content sits in the middle instead of at the top.
    """
    svg = path.read_text(encoding="utf-8")
    current = height(path)
    if current >= target:
        return
    shift = (target - current) / 2
    svg = ROOT_SIZE.sub(
        lambda m: f"{m.group(1)}{target}{m.group(4)}0 {-shift:g} {m.group(5)} {target}{m.group(7)}",
        svg,
        count=1,
    )
    svg = CARD_BG_Y.sub(lambda m: f"{m.group(1)}{float(m.group(2)) - shift:g}{m.group(3)}", svg, count=1)
    path.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    paths = [pathlib.Path(arg) for arg in sys.argv[1:]]
    for path in paths:
        embed(path)
    # Cards shown side by side get one height: the tallest one's.
    tallest = max(height(path) for path in paths)
    for path in paths:
        match_height(path, tallest)
