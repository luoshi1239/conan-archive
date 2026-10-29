#!/usr/bin/env python3
"""M2：为缺 sources 的案件补来源引用。

背景
----
`cases[].sources` 是「来源 id 字符串数组」，不是 {page, sourceId} 对象。
`sources.json` 里其实早就登记了 19 个案件的**专属页面来源**
（`src-detective-conan-world-popular-artist-case` 等，url 指向各自 DCW 页），
只是案件记录没有引用它们——数据在，链没接上。

做法
----
1. 从 `sources.json` 的 url 建「DCW 页名 → source id」映射
   （url 形如 https://www.detectiveconanworld.com/wiki/<PageName>，页名原样可用）
2. 对 sources 为空的案件，按 `dcwPage` 找专属来源
3. 同时补一条按 `kind` 决定的通用来源（manga-case → -manga，anime-original-case → -anime），
   与库内既有案件的引用风格一致

只补空，不覆盖；页名对不上就跳过并打印，不猜。
幂等：sources 非空的一律跳过；内容不变不写盘。
"""
import json
import re
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data/entities/cases.json"
SOURCES = ROOT / "data/sources.json"
DRY = "--dry-run" in sys.argv

WIKI_RE = re.compile(r"detectiveconanworld\.com/wiki/([^/?#]+)")

GENERIC_BY_KIND = {
    "manga-case": "src-detective-conan-world-manga",
    "anime-original-case": "src-detective-conan-world-anime",
}


def main() -> int:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    sources_doc = json.loads(SOURCES.read_text(encoding="utf-8"))
    sources = sources_doc["sources"]
    known_ids = {s["id"] for s in sources}

    # DCW 页名 -> source id（只认专属页来源，即 url 指向具体 /wiki/<Page> 的）
    page_to_src: dict[str, str] = {}
    for s in sources:
        m = WIKI_RE.search(s.get("url") or "")
        if not m:
            continue
        page = unquote(m.group(1))
        # 一个页面对应多个来源时，取 id 里带 -case 的（专属案情页），否则取第一个
        prev = page_to_src.get(page)
        if prev is None or ("-case" in s["id"] and "-case" not in prev):
            page_to_src[page] = s["id"]

    filled = 0
    skipped_has = 0
    no_page = []
    no_src = []

    for c in cases:
        if c.get("sources"):
            skipped_has += 1
            continue

        page = c.get("dcwPage")
        if not page:
            no_page.append(c.get("id"))
            continue

        src_id = page_to_src.get(page)
        if not src_id or src_id not in known_ids:
            no_src.append((c.get("id"), page))
            continue

        ids = []
        generic = GENERIC_BY_KIND.get(c.get("kind"))
        if generic and generic in known_ids:
            ids.append(generic)
        ids.append(src_id)

        if not DRY:
            c["sources"] = ids
        filled += 1

    print(f"M2 案件 sources：补 {filled} 条（已有 {skipped_has} 条跳过）")
    if no_page:
        print(f"   缺 dcwPage 无法补 {len(no_page)} 条：{no_page}")
    if no_src:
        print(f"   有页但 sources.json 无对应来源 {len(no_src)} 条：")
        for cid, page in no_src:
            print(f"     {cid}  page={page!r}")

    if DRY:
        print("   [dry-run] 未写盘")
        return 0
    if filled == 0:
        print("   IDEMPOTENT_OK（无改动，不写盘）")
        return 0

    CASES.write_text(
        json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("   已写入 cases.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
