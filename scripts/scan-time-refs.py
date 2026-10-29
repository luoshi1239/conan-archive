#!/usr/bin/env python3
"""Print every time reference in a saved wiki HTML page, with surrounding text.

The point is to separate distinct events that share approximate phrases
("six months ago" / "two years ago") instead of assuming they contradict.
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

WORDS = (
    "month", "months", "year", "years", "week", "weeks", "day", "days",
    "ago", "before", "after", "half a", "previously", "earlier", "later",
)


class Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        if tag in ("p", "li", "h2", "h3", "h4", "br", "div"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
        if tag in ("p", "li", "h2", "h3", "h4", "div"):
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: scan-time-refs.py <html>...")
        return 2
    pat = re.compile(r"\b(?:[a-z\-]+[\s\-]){0,3}(?:months?|years?|weeks?|days?)\b", re.I)
    for raw in argv[1:]:
        path = Path(raw)
        if not path.exists():
            print(f"!! missing {path}")
            continue
        p = Text()
        p.feed(path.read_text(encoding="utf-8", errors="replace"))
        text = re.sub(r"[ \t]+", " ", "".join(p.parts))
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        print(f"===== {path} ({len(lines)} blocks) =====")
        for i, ln in enumerate(lines):
            if pat.search(ln):
                print(f"[{i}] {ln[:600]}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
