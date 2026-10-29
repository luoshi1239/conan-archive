#!/usr/bin/env python3
"""Extract culprit/resolution sentences from a saved wiki episode page.

Used to verify that entity L3 text actually matches the source page rather
than a plausible reconstruction: prints every block containing verdict-like
words plus the Cast block, so names can be checked character by character.
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

KEYS = (
    "culprit", "murderer", "killer", "confessed", "arrested", "revealed",
    "the culprit", "guilty", "convicted", "poison", "stabbed", "strangled",
)


class Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        if tag in ("p", "li", "h2", "h3", "h4", "br", "div", "td", "tr"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
        if tag in ("p", "li", "h2", "h3", "h4", "div", "td", "tr"):
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def main(argv: list[str]) -> int:
    mode = argv[1] if len(argv) > 1 else "keys"
    for raw in argv[2:]:
        p = Text()
        p.feed(Path(raw).read_text(encoding="utf-8", errors="replace"))
        lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in "".join(p.parts).splitlines()]
        lines = [ln for ln in lines if ln]
        print(f"===== {raw} =====\n")
        if mode == "keys":
            for i, ln in enumerate(lines):
                low = ln.lower()
                if any(k in low for k in KEYS) and len(ln) > 60:
                    print(f"[{i}] {ln[:700]}\n")
        else:
            print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
