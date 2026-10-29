#!/usr/bin/env python3
"""M4：案件 kind 枚举规范化。

问题
----
`kind` 只该取 `manga-case` / `anime-original-case` / `organization-case`，
但库里有 19 条脏值：
  - `动画案件` × 14：中文值混进英文枚举（早期人工录入遗留）
  - `None` × 5：从未填过

判定依据（只认原文，不猜）
--------------------------
`dcw-page-facts.json` 的 `mangaSource` 就是原文对「漫画改编 / TV 原创」的判定：
  - `TV Original`            → anime-original-case
  - `Volume N: ...` 等漫画卷 → manga-case
  - 空但 `isAnimeExclusive`  → anime-original-case
判定不了的一律保持原值并打印，不写。

幂等：已是合法枚举的跳过；判定结果与现值相同不写盘。
"""
import json
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data/entities/cases.json"
FACTS = ROOT / "data/raw/dcw-page-facts.json"
DRY = "--dry-run" in sys.argv

VALID = {"manga-case", "anime-original-case", "organization-case"}
ZH_ALIAS = {"动画案件": None}  # None = 需按原文重判


def judge(fact) -> Optional[str]:
    """按 DCW 原文判定 kind。判定不了返回 None。"""
    if not fact:
        return None
    ms = (fact.get("mangaSource") or "").strip()
    if ms.lower() == "tv original":
        return "anime-original-case"
    if ms:
        # Volume 16: File 10 (160) ~ ... / Special Volume 1: File ... / 漫画
        if ms.lower().startswith(("volume", "special volume")):
            return "manga-case"
    if fact.get("isAnimeExclusive") is True:
        return "anime-original-case"
    return None


def link_page_by_title(case, by_page):
    """案件缺 dcwPage 时，用 title.en 与页面 heading 精确匹配补上。

    这是原文对原文的对应（DCW 页面 heading 就是该案英文标题），
    不是推断。匹配不到返回 None，不猜。
    """
    t = case.get("title") or {}
    en = (t.get("en") or "").strip().lower()
    if not en:
        return None
    for page_name, fact in by_page.items():
        if (fact.get("heading") or "").strip().lower() == en:
            return page_name

    # 多案同页：标题带括号后缀，如
    #   "The Cornered Famous Detective! Two Big Murder Cases (Tsukumo Case)"
    # 页面 heading 只有前段，用前缀匹配。
    for page_name, fact in by_page.items():
        head = (fact.get("heading") or "").strip().lower()
        if not head or len(head) < 20:
            continue
        if en.startswith(head):
            return page_name
    return None



def main() -> int:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    facts = json.loads(FACTS.read_text(encoding="utf-8"))
    by_page = {p["page"]: p for p in facts["pages"]}

    changed = 0
    unresolved = []

    for c in cases:
        cur = c.get("kind")
        if cur in VALID:
            continue
        if cur not in (None, "动画案件"):
            continue  # 未知脏值，先不碰

        page = c.get("dcwPage")
        fact = by_page.get(page) if page else None

        # 缺 dcwPage 时按标题补链（原文对原文），补上了才能判定
        linked_page = None
        if fact is None:
            linked_page = link_page_by_title(c, by_page)
            if linked_page:
                fact = by_page[linked_page]

        new = judge(fact)

        if new is None:
            t = c.get("title") or {}
            label = t.get("zhHans") or t.get("ja") or t.get("en")
            unresolved.append((c.get("id"), cur, page, str(label)[:40]))
            continue

        if new == cur and not linked_page:
            continue
        if not DRY:
            c["kind"] = new
            if linked_page:
                c["dcwPage"] = linked_page
        changed += 1
        if linked_page:
            print(f"   补链 {c.get('id')} -> dcwPage={linked_page!r}  kind={new}")

    print(f"M4 案件 kind：修正 {changed} 条")
    if unresolved:
        print(f"   无法判定 {len(unresolved)} 条（保持原值，需人工）：")
        for cid, cur, page, label in unresolved:
            print(f"     {cid}  kind={cur!r}  page={page!r}  {label!r}")

    if DRY:
        print("   [dry-run] 未写盘")
        return 0
    if changed == 0:
        print("   IDEMPOTENT_OK（无改动，不写盘）")
        return 0

    CASES.write_text(
        json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("   已写入 cases.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
