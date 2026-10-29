#!/usr/bin/env python3
"""用 DCW 页面标题补齐缺失的案件 title（19 个实体此前 title 全空）。

来源（只搬原文，不翻译、不推断）：
    data/raw/dcw-page-facts.json 的 `heading`（英文页面标题）
                                  `jpTitle`（日文原名 + 罗马字注音）

规则：
    - 只补 `title` 为空 / `en` 为空的案件，已有值一律不覆盖；
    - `zhHans`/`zhHant` 留空等人工，不自行翻译；
    - 无 dcwPage 的实体（EP.96 本地有意拆分的两案）跳过并记入报告，不猜。

输出：data/entities/cases.json 就地补 title；docs/CASE-TITLE-BACKFILL.json
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "entities" / "cases.json"
FACTS = ROOT / "data" / "raw" / "dcw-page-facts.json"
REPORT = ROOT / "docs" / "CASE-TITLE-BACKFILL.json"
BACKUP = Path("/tmp/ca/cases_pre_title_backfill.json")


def main() -> None:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    facts = {p["page"]: p for p in json.loads(FACTS.read_text(encoding="utf-8"))["pages"]}

    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    if not BACKUP.exists():
        shutil.copy2(CASES, BACKUP)

    filled: list[dict] = []
    skipped: list[dict] = []
    for c in cases:
        title = c.get("title") or {}
        if title.get("en"):
            continue
        page = c.get("dcwPage")
        fact = facts.get(page) if page else None
        if not fact or not fact.get("heading"):
            skipped.append({"caseId": c["id"], "dcwPage": page, "reason": "no_dcw_page_heading"})
            continue
        new_title = dict(title)
        new_title["en"] = fact["heading"]
        if fact.get("jpTitle") and not new_title.get("ja"):
            new_title["ja"] = fact["jpTitle"]
        new_title.setdefault("zhHans", "")
        new_title.setdefault("zhHant", "")
        c["title"] = new_title
        filled.append({"caseId": c["id"], "page": page, "en": new_title["en"], "ja": new_title.get("ja")})

    CASES.write_text(json.dumps(cases, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    REPORT.write_text(
        json.dumps(
            {
                "generatedBy": "scripts/backfill-case-titles.py",
                "policy": "只搬 DCW 页面 heading/jpTitle 原文；zhHans/zhHant 留空等人工",
                "filled": len(filled),
                "skipped": len(skipped),
                "items": filled,
                "skippedItems": skipped,
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"filled": len(filled), "skipped": len(skipped)}, ensure_ascii=False))
    for s in skipped:
        print("  skipped:", s)


if __name__ == "__main__":
    main()
