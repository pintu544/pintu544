#!/usr/bin/env python3
"""Generate a self-hosted profile-views badge (profile-views.svg).

Why: GitHub renders README images through its camo proxy, which caches
whatever it first fetches for a URL. The komarev counter service is slow
(~1-2s), so camo regularly caches a failed fetch and serves a broken badge
until the URL changes. Serving the badge from this repo instead (fast,
GitHub-hosted origin) removes that failure mode entirely.

This script reads the current count from komarev (server-side, with
retries) and renders a shields-style flat badge. Run daily by
.github/workflows/profile-views.yml, which publishes the SVG to the
`output` branch (same pattern as the snake animation).

On any fetch/parse failure it exits without writing, so the workflow
keeps yesterday's badge instead of publishing a broken one.
"""

import re
import sys
import time
import urllib.request

KOMAREV_URL = "https://komarev.com/ghpvc/?username=pintu544"
LABEL = "Profile views"
COLOR = "#0e75b6"
OUT = sys.argv[1] if len(sys.argv) > 1 else "profile-views.svg"


def fetch_count() -> int | None:
    for attempt in range(3):
        try:
            req = urllib.request.Request(KOMAREV_URL, headers={"User-Agent": "Mozilla/5.0 (views-badge-generator)"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                svg = resp.read().decode("utf-8", "ignore")
            numbers = re.findall(r"<text[^>]*>(\d+)</text>", svg)
            if numbers:
                return int(numbers[-1])
            print(f"Attempt {attempt + 1}: no count found in komarev response")
        except Exception as exc:
            print(f"Attempt {attempt + 1}: fetch failed: {exc}")
        time.sleep(5)
    return None


def render_badge(count: int) -> str:
    count_text = str(count)
    label_text_w = 72  # fits "Profile views" at 11px Verdana via textLength
    count_text_w = 8 * len(count_text) + 6
    w1 = label_text_w + 12
    w2 = count_text_w + 12
    total = w1 + w2
    x1 = w1 / 2
    x2 = w1 + w2 / 2
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="20" role="img" aria-label="{LABEL}: {count_text}">
  <title>{LABEL}: {count_text}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-color="#000" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r"><rect width="{total}" height="20" rx="3" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="{w1}" height="20" fill="#555"/>
    <rect x="{w1}" width="{w2}" height="20" fill="{COLOR}"/>
    <rect width="{total}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
    <text aria-hidden="true" x="{x1}" y="15" fill="#010101" fill-opacity=".3" textLength="{label_text_w}" lengthAdjust="spacingAndGlyphs">{LABEL}</text>
    <text x="{x1}" y="14" textLength="{label_text_w}" lengthAdjust="spacingAndGlyphs">{LABEL}</text>
    <text aria-hidden="true" x="{x2}" y="15" fill="#010101" fill-opacity=".3" textLength="{count_text_w}" lengthAdjust="spacingAndGlyphs">{count_text}</text>
    <text x="{x2}" y="14" textLength="{count_text_w}" lengthAdjust="spacingAndGlyphs">{count_text}</text>
  </g>
</svg>
'''


def main() -> int:
    count = fetch_count()
    if count is None:
        print("Could not read the counter; keeping the existing badge.")
        return 0
    with open(OUT, "w") as fh:
        fh.write(render_badge(count))
    print(f"Wrote {OUT} with count {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
