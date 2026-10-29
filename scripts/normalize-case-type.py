#!/usr/bin/env python3
"""M5：案件 caseType 规范化。

caseType 是「题材标签 + 来源标签」的混合数组：
  - 题材：locked-room / serial-murder / closed-circle / kidnapping / murder ...
  - 来源：anime-original / manga-adaptation（有且只该有一个）

三类脏值，各自有原文依据：
  1. `['manga']` ×2        —— 别名，同义归并为 `manga-adaptation`
  2. `[]` ×25              —— 全为 manga-case，按 kind 补 `manga-adaptation`
  3. 有题材无来源 ×27      —— 24 条 manga-case 按 kind 补；
                              3 条 organization-case 按 DCW `mangaSource` 判，
                              判不了就留空（不猜）

来源标签一律追加到末尾，与既有 `['locked-room','manga-adaptation']` 风格一致。
幂等：已有来源标签的不动；内容不变不写盘。
"""
import json
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data/entities/cases.json"
FACTS = ROOT / "data/raw/dcw-page-facts.json"
DRY = "--dry-run" in sys.argv

SRC_TAGS = {"anime-original", "manga-adaptation"}


def source_from_kind(kind: str) -> Optional[str]:
    if kind == "manga-case":
        return "manga-adaptation"
    if kind == "anime-original-case":
        return "anime-original"
    return None  # organization-case 的来源与 kind 无关，需查原文


def source_from_fact(fact) -> Optional[str]:
    """按 DCW 原文判来源。判不了返回 None。"""
    if not fact:
        return None
    ms = (fact.get("mangaSource") or "").strip()
    if ms.lower() == "tv original":
        return "anime-original"
    if ms.lower().startswith(("volume", "special volume")):
        return "manga-adaptation"
    if fact.get("isAnimeExclusive") is True:
        return "anime-original"
    return None


def parse_anime_refs(refs) -> list:
    """`episode-0491-0504` / `episode-0001` -> [491,492,...,504] / [1]"""
    out = []
    for r in refs or []:
        if not isinstance(r, str) or not r.startswith("episode-"):
            continue
        body = r[len("episode-"):]
        parts = body.split("-")
        try:
            if len(parts) == 1:
                out.append(int(parts[0]))
            elif len(parts) == 2:
                a, b = int(parts[0]), int(parts[1])
                out.extend(range(a, b + 1))
        except ValueError:
            continue
    return out


def link_page_by_episodes(case, eps_to_page) -> Optional[str]:
    """缺 dcwPage 时按 animeRefs 的集号反查 DCW 页。

    页面 episodeNumbers 就是该页覆盖的集号，属原文对原文，不是推断。
    多个候选时只认唯一命中，否则返回 None。
    """
    nums = parse_anime_refs(case.get("animeRefs"))
    if not nums:
        return None
    hits = set()
    for n in nums:
        p = eps_to_page.get(n)
        if p:
            hits.add(p)
    if len(hits) == 1:
        return hits.pop()
    return None



def main() -> int:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    facts = json.loads(FACTS.read_text(encoding="utf-8"))
    by_page = {p["page"]: p for p in facts["pages"]}

    # 集号 -> 页名（一个集号可能被多页声明，故用 set 判唯一性）
    eps_to_page = {}
    for p in facts["pages"]:
        for n in p.get("episodeNumbers") or []:
            if isinstance(n, int):
                eps_to_page.setdefault(n, set()).add(p["page"])

    def lookup_page(case):
        """按 dcwPage，缺失则按集号反查。返回 (pageName, fact) 或 (None, None)。"""
        page = case.get("dcwPage")
        if page and page in by_page:
            return page, by_page[page]
        nums = parse_anime_refs(case.get("animeRefs"))
        hits = set()
        for n in nums:
            for cand in eps_to_page.get(n, ()):  # 展开 set
                hits.add(cand)
        if len(hits) == 1:
            name = hits.pop()
            return name, by_page.get(name)
        return None, None


    alias_fixed = 0
    filled_empty = 0
    filled_tagless = 0
    unresolved = []

    for c in cases:
        v = c.get("caseType")

        # 1. 别名归并
        if isinstance(v, list) and "manga" in v:
            if not DRY:
                c["caseType"] = [
                    "manga-adaptation" if x == "manga" else x for x in v
                ]
            alias_fixed += 1
            continue

        if not isinstance(v, list):
            continue

        # 2/3. 缺来源标签
        if set(v) & SRC_TAGS:
            continue

        src = source_from_kind(c.get("kind"))
        if src is None:
            page_name, fact = lookup_page(c)
            src = source_from_fact(fact)
            if src is not None and page_name and not c.get("dcwPage") and not DRY:
                c["dcwPage"] = page_name

        if src is None:
            t = c.get("title") or {}
            label = t.get("zhHans") or t.get("ja") or t.get("en")
            unresolved.append((c.get("id"), c.get("kind"), v, str(label)[:36]))
            continue

        if not DRY:
            c["caseType"] = v + [src]
        if v:
            filled_tagless += 1
        else:
            filled_empty += 1

    total = alias_fixed + filled_empty + filled_tagless
    print(f"M5 案件 caseType：修正 {total} 条")
    print(f"   别名归并 'manga'→'manga-adaptation'：{alias_fixed}")
    print(f"   空数组补来源：{filled_empty}")
    print(f"   有题材缺来源：{filled_tagless}")
    if unresolved:
        print(f"   无法判定 {len(unresolved)} 条（保持原值）：")
        for cid, kind, v, label in unresolved:
            print(f"     {cid}  kind={kind!r}  {v}  {label!r}")

    if DRY:
        print("   [dry-run] 未写盘")
        return 0
    if total == 0:
        print("   IDEMPOTENT_OK（无改动，不写盘）")
        return 0

    CASES.write_text(
        json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("   已写入 cases.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
