#!/usr/bin/env python3
"""补 `dcw-page-facts.json` 里缺失的 episodeNumbers（多集特别篇页面）。

背景：单集页面的 Ep number 在 infobox 里，`episodeNumbers` 能抽到；
但这三个**特别篇合并页**的 infobox 写法不同，抽成了空数组，
导致 21 集（188-193 / 425 / 491-504）在剧集库里没有 season / cast / solvedBy。

从原始 HTML 的原文抽取（不是我推理的集号）：
    The_Desperate_Revival    → "Episode 188-193 (Int. Episode 203-208)"
    Clash_of_Red_and_Black   → "Episode 491-504 (Int. Episode 538-551)"
    Black_Impact!            → "Episode 425 (Int. Episode ...)"

写入字段：
    episodeNumbers  完整集号列表
    episodeRange    原文范围表述（"188-193"）
    intEpisodes     国际集号列表
    intEpisode      起始国际集号（保持与原字段同义）
    factSource      标注这次是从 HTML 补的，便于追溯

幂等：已有非空 episodeNumbers 的页面一律不动。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FACTS = ROOT / "data" / "raw" / "dcw-page-facts.json"
RAW = ROOT / "data" / "raw" / "dcw-pages"

# 原文三种写法
RANGE = re.compile(
    r"Episode\s+(\d+)\s*[-–~]\s*(\d+)\s*\(\s*Int\.?\s*Episode\s+(\d+)\s*[-–~]\s*(\d+)\s*\)"
)
SINGLE = re.compile(r"Episode\s+(\d+)\s*\(\s*Int\.?\s*Episode\s+(\d+)\s*\)")
# 单集号 + 国际集号范围：Black Impact! → "Episode 425 (Int. Episode 459-463)"
SINGLE_WITH_INT_RANGE = re.compile(
    r"Episode\s+(\d+)\s*\(\s*Int\.?\s*Episode\s+(\d+)\s*[-–~]\s*(\d+)\s*\)"
)


def plain(html: str) -> str:
    text = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&#160;", " ")
    return re.sub(r"\s+", " ", text)


def main() -> None:
    data = json.loads(FACTS.read_text(encoding="utf-8"))
    pages = data["pages"]
    fixed = []

    for row in pages:
        if row.get("episodeNumbers"):
            continue  # 已有集号，绝不动
        path = RAW / f"{row['page']}.html"
        if not path.exists():
            continue
        text = plain(path.read_text(encoding="utf-8", errors="replace"))

        m = RANGE.search(text)
        if m:
            start, end, i_start, i_end = (int(g) for g in m.groups())
            nums = list(range(start, end + 1))
            ints = list(range(i_start, i_end + 1))
            row["episodeNumbers"] = nums
            row["episodeRange"] = f"{start}-{end}"
            row["intEpisodes"] = ints
            row["intEpisode"] = i_start
            row["factSource"] = f"html:{m.group(0)}"
            fixed.append((row["page"], f"{start}-{end}", len(nums)))
            continue

        # 单集号 + 国际集号范围（必须排在 SINGLE 之前，否则只吃到单集）
        m = SINGLE_WITH_INT_RANGE.search(text)
        if m:
            num, i_start, i_end = (int(g) for g in m.groups())
            row["episodeNumbers"] = [num]
            row["episodeRange"] = str(num)
            row["intEpisodes"] = list(range(i_start, i_end + 1))
            row["intEpisode"] = i_start
            row["factSource"] = f"html:{m.group(0)}"
            fixed.append((row["page"], str(num), 1))
            continue

        m = SINGLE.search(text)
        if m:
            num, i_num = int(m.group(1)), int(m.group(2))
            row["episodeNumbers"] = [num]
            row["episodeRange"] = str(num)
            row["intEpisodes"] = [i_num]
            row["intEpisode"] = i_num
            row["factSource"] = f"html:{m.group(0)}"
            fixed.append((row["page"], str(num), 1))

    print(f"补集号 {len(fixed)} 页（共 {len(pages)} 页）")
    for page, rng, n in fixed:
        print(f"    {rng:10s} （{n:2d} 集）  {page}")

    FACTS.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"已写入 {FACTS}")


if __name__ == "__main__":
    main()
