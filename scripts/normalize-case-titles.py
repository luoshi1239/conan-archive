#!/usr/bin/env python3
"""规范化案件标题字段：把误写在 `titles`（复数）里的标题合并进 `title`（单数）。

## 隐患来源

`register-94-97-cases.py` / `register-98-101-cases.py` / `register-102-106-cases.py`
写实体时用了 `titles` 键，而数据规范（docs/DATA-SCHEMA.md）与其余 773 个实体用 `title`。
于是这 19 个案件的手写中文标题被静默丢弃，实体读起来像"没有标题"。

## 合并规则

- 目标字段 `title`（dict：en / ja / zhHans / zhHant / aliases）；
- `title` 已有的值优先（EN/JA 来自 DCW 页面 heading，是原页原文）；
- `title` 缺的语种用 `titles` 里的值补齐（手写中文优先于空值，不翻译不编造）；
- 合并后删除 `titles` 键，保持全库字段统一。

输出：data/entities/cases.json 就地规范化；docs/CASE-TITLE-NORMALIZE.json
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "entities" / "cases.json"
REPORT = ROOT / "docs" / "CASE-TITLE-NORMALIZE.json"
BACKUP = Path("/tmp/ca/cases_pre_title_normalize.json")
LANGS = ("en", "ja", "zhHans", "zhHant")


def main() -> None:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    if not BACKUP.exists():
        shutil.copy2(CASES, BACKUP)

    changes: list[dict] = []
    for c in cases:
        if "titles" not in c:
            continue
        stray = c.pop("titles") or {}
        title = dict(c.get("title") or {})
        added: list[str] = []
        for lang in LANGS:
            if not title.get(lang) and stray.get(lang):
                title[lang] = stray[lang]
                added.append(lang)
        aliases = list(title.get("aliases") or [])
        for lang in LANGS:
            v = stray.get(lang)
            if v and v not in (title.get(lang),) and v not in aliases:
                aliases.append(v)
        if aliases:
            title["aliases"] = aliases
        for lang in LANGS:
            title.setdefault(lang, "")
        c["title"] = title
        changes.append({"caseId": c["id"], "addedLangs": added, "title": title})

    CASES.write_text(json.dumps(cases, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    REPORT.write_text(
        json.dumps(
            {
                "generatedBy": "scripts/normalize-case-titles.py",
                "policy": "titles → title 合并；已有值优先；zh 手写值保留；不翻译不编造",
                "normalized": len(changes),
                "items": changes,
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"normalized": len(changes)}, ensure_ascii=False))
    remaining = sum(1 for c in json.loads(CASES.read_text(encoding="utf-8")) if "titles" in c)
    print("remaining stray titles keys:", remaining)


if __name__ == "__main__":
    main()
