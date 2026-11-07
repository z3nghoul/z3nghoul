"""Puts 8 random splash lines from z3n1337.dev into the typing line of README.md.

Usage: python3 splashes.py README.md
"""
import json
import random
import re
import sys
import urllib.parse
import urllib.request

SOURCE = "https://raw.githubusercontent.com/z3nghoul/z3n1337.dev/main/js/splashes.js"
COUNT = 8

readme = sys.argv[1]

with urllib.request.urlopen(SOURCE, timeout=30) as r:
    js = r.read().decode()

# the array in js/splashes.js: const SPLASHES = [ "...", "...", ];
body = js[js.index("[") + 1:js.index("];")]
splashes = [json.loads(s) for s in re.findall(r'"(?:[^"\\]|\\.)*"', body)]
if len(splashes) < COUNT:
    sys.exit(f"only {len(splashes)} splashes found in {SOURCE}")

picked = random.sample(splashes, COUNT)
lines = ";".join(urllib.parse.quote_plus(s) for s in picked)

text = open(readme, encoding="utf-8").read()
new, n = re.subn(r'(readme-typing-svg\.demolab\.com\?[^"]*?&lines=)[^"&]*', lambda m: m.group(1) + lines, text)
if n != 1:
    sys.exit(f"expected one typing line in {readme}, found {n}")

open(readme, "w", encoding="utf-8").write(new)
print("\n".join(picked))
