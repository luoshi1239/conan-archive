#!/usr/bin/env python3
"""P1：把剧集 `solvedByRaw` 原文解析成角色实体 id。

DCW 原文写法统计（1161 条有值）：
    Conan Edogawa                        299
    Kogoro Mouri (via Conan)             409
    Hiroshi Agasa (via Conan)             50
    Sonoko Suzuki (via Conan)             51
    Kogoro Mouri (partially on his own…)   4
    Conan Edogawa (x2)                     4
    No one / N/A                           4

括号里是"通过谁/怎么破的"，不是第二个作案人。因此：
    * 先剥掉所有括号与脚注，得到人名；
    * 人名能对上角色实体 → 写 `solvedBy`（角色 id）；
    * 剥完仍对不上 → 保留 `solvedByRaw`，`unresolved` 计数，不猜。
    * `No one` / `N/A` 之类早已写进 `solvedByNote`，不在此处理。

只写空字段，不覆盖任何已有 `solvedBy`。幂等：第二次运行 0 改动。

用法：
    python3 scripts/resolve-episode-solvedby.py --dry-run
    python3 scripts/resolve-episode-solvedby.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPISODES = ROOT / "data" / "episodes" / "episodes.json"
CHARS = ROOT / "data" / "entities" / "characters.json"

# 与 create-character-entities.py / backfill-episode-structure.py 同一口径
ALIAS_MAP = {
    "tooru amuro": "character-rei-furuya",
    "toru amuro": "character-rei-furuya",
    "subaru okiya": "character-shuichi-akai",
    "scar akai": "character-shuichi-akai",
    "shiho miyano": "character-ai-haibara",
    "kaito kuroba": "character-kaito-kid",
    # DCW 里对阿笠博士有全名/简称两种写法
    "professor agasa": "character-hiroshi-agasa",
    "hiroshi agasa": "character-hiroshi-agasa",
}

FOOTNOTE = re.compile(r"\[[^\]]*\]")
PAREN = re.compile(r"\([^)]*\)")
# 原文偶有半角/全角括号不配对（如 `Sonoko Suzuki (via Conan}`）
PAREN_LOOSE = re.compile(r"[\(（][^\)）]*[\)）}]")
# 「Conan Edogawa (x2)」这类倍数说明
MULTIPLIER = re.compile(r"\s*[xX×]\s*\d+\s*$")
# 「Kogoro Mouri : present case」这类补充说明
AFTER_COLON = re.compile(r"\s*[:：].*$")


def clean(raw: str) -> str:
    text = FOOTNOTE.sub("", raw or "")
    # 括号可能嵌套，反复剥到不动为止
    prev = None
    while prev != text:
        prev = text
        text = PAREN.sub("", text)
        text = PAREN_LOOSE.sub("", text)
    text = MULTIPLIER.sub("", text)
    text = AFTER_COLON.sub("", text)
    return " ".join(text.split())


def load_chars() -> dict[str, str]:
    rows = json.loads(CHARS.read_text(encoding="utf-8"))
    by_name: dict[str, str] = {}
    ids = set()
    for char in rows:
        cid = char["id"]
        ids.add(cid)
        names = []
        name = char.get("name") or {}
        if isinstance(name, dict):
            names.extend(v for v in name.values() if isinstance(v, str))
        elif isinstance(name, str):
            names.append(name)
        names.extend(a for a in (char.get("aliases") or []) if isinstance(a, str))
        for n in names:
            by_name[n.strip().lower()] = cid
    for alias, cid in ALIAS_MAP.items():
        if cid in ids:
            by_name[alias] = cid
    return by_name


def main() -> None:
    dry = "--dry-run" in sys.argv
    episodes = json.loads(EPISODES.read_text(encoding="utf-8"))
    by_name = load_chars()

    resolved = 0
    unresolved: dict[str, int] = {}
    skipped_has = 0

    for ep in episodes:
        if (ep.get("solvedBy") or "").startswith("character-"):
            skipped_has += 1
            continue
        raw = ep.get("solvedByRaw")
        if not raw:
            continue
        name = clean(raw)
        cid = by_name.get(name.lower())
        if cid:
            if not dry:
                ep["solvedBy"] = cid
                if name != raw:
                    ep["solvedByParsedFrom"] = raw
            resolved += 1
        else:
            unresolved[name or raw] = unresolved.get(name or raw, 0) + 1

    print(f"{'[dry-run] ' if dry else ''}已挂接 {skipped_has} 集，本次新解析 {resolved} 集")
    if unresolved:
        print(f"仍未解析 {len(unresolved)} 种写法，共 {sum(unresolved.values())} 集：")
        for name, n in sorted(unresolved.items(), key=lambda kv: -kv[1])[:12]:
            print(f"  {n:4d}  {name[:60]}")

    if not dry:
        EPISODES.write_text(json.dumps(episodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"已写入 {EPISODES}")
    else:
        print("（未写盘）")


if __name__ == "__main__":
    main()
