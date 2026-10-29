#!/usr/bin/env python3
"""从缓存的 DCW 页面正文提取 Situation / Part 1 / Part 2 / People / Resolution 原文段落。

输出 data/raw/dcw-page-blocks.json —— 每个页面一份带块索引的原文，
供后续生成 L3 候选（culprit / motive / method / evidence / resolution）引用。

铁律：本脚本只搬运原文，不做任何总结、推断或改写。
"""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "data" / "raw" / "dcw-pages"
OUT = ROOT / "data" / "raw" / "dcw-page-blocks.json"

SKIP = {"script", "style", "noscript"}
BLOCK = {"p", "li", "tr", "div", "br", "h1", "h2", "h3", "h4", "td", "th"}

HEADINGS = (
    "Situation", "Part 1", "Part 2", "Part 3", "Part 4",
    "People", "Resolution", "Trivia", "BGM listing", "Gallery",
    "In other languages", "See also", "Staff", "Voice cast",
    "Music", "Notes", "References",
)


class TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.chunks: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip += 1
        if tag in BLOCK:
            self.chunks.append("\n")

    def handle_endtag(self, tag):
        if tag in SKIP and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.chunks.append(data)


def to_lines(html: str) -> list[str]:
    p = TextParser()
    p.feed(html)
    raw = "".join(p.chunks).split("\n")
    out = []
    for x in raw:
        s = re.sub(r"\s+", " ", x).strip()
        if s:
            out.append(s)
    return out


def extract_blocks(lines: list[str]) -> dict:
    """按大标题切段，返回 {heading: [段落...]}。只取出现两次以上的正文标题区。"""
    idx = [(i, l) for i, l in enumerate(lines) if l in HEADINGS]
    blocks: dict[str, list[str]] = {}
    for k, (i, name) in enumerate(idx):
        end = idx[k + 1][0] if k + 1 < len(idx) else len(lines)
        body = [x for x in lines[i + 1:end] if x not in HEADINGS]
        if not body:
            continue
        # 同名标题可能重复（导航 + 正文），保留最长的一份
        prev = blocks.get(name)
        if prev is None or len(body) > len(prev):
            blocks[name] = body
    return blocks


def main() -> None:
    out = {}
    stats = {"pages": 0, "withSituation": 0, "withResolution": 0, "withPeople": 0}
    for f in sorted(PAGES.glob("*.html")):
        html = f.read_text(encoding="utf-8", errors="replace")
        if len(html) < 20_000:
            continue
        blocks = extract_blocks(to_lines(html))
        page = f.stem
        out[page] = blocks
        stats["pages"] += 1
        if blocks.get("Situation"):
            stats["withSituation"] += 1
        if blocks.get("Resolution"):
            stats["withResolution"] += 1
        if blocks.get("People"):
            stats["withPeople"] += 1

    OUT.write_text(
        json.dumps({"stats": stats, "pages": out}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(stats, ensure_ascii=False))
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
