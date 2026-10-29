#!/usr/bin/env python3
"""把案件 L3 字段迁移为双语结构（zhHans / en / translationStatus）。

## 为什么

案件 `culprit` / `motive` / `method` / `evidence` / `resolution` 原先是纯字符串，
里面混着 288 条中文（人工）与 422 条英文（DCW 原文回填），无法区分语言、
也无法标记"翻译到哪一步"。迁移后与项目既有的 `title` / `summary` 约定一致：

    "culprit": {
      "zhHans": "浅井成实，真实身份为麻生成实…",
      "en": null,
      "translationStatus": "human"          // human | machine | pending | none
    }

## 判定规则（不猜、不编）

- 字段已带 `dcwL3Source.<field>` 且 `lang == "en"` → 该值来自 DCW 原文：
  写入 `en`，`zhHans` 留空，`translationStatus = "pending"`；
- 其余（原手工中文，或 dcwL3Source 缺失但内容是中文）→ 写入 `zhHans`，
  `en` 留 null，`translationStatus = "human"`；
- 已是对象 → 不动（幂等）。

输出：data/entities/cases.json；docs/CASE-L3-BILINGUAL-MIGRATION.json
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "entities" / "cases.json"
REPORT = ROOT / "docs" / "CASE-L3-BILINGUAL-MIGRATION.json"
BACKUP = Path("/tmp/ca/cases_pre_bilingual.json")

FIELDS = ("culprit", "motive", "method", "evidence", "resolution")
CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


def main() -> None:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    if not BACKUP.exists():
        shutil.copy2(CASES, BACKUP)

    stats = {"migrated": 0, "toEnglish": 0, "toChinese": 0, "alreadyObject": 0}
    items: list[dict] = []

    for c in cases:
        src = c.get("dcwL3Source") or {}
        for field in FIELDS:
            value = c.get(field)
            if value in (None, ""):
                continue
            if isinstance(value, dict):
                stats["alreadyObject"] += 1
                continue
            if not isinstance(value, str):
                continue
            meta = src.get(field) or {}
            is_en = meta.get("lang") == "en"
            if is_en:
                new = {"zhHans": "", "en": value, "translationStatus": "pending"}
                stats["toEnglish"] += 1
            else:
                # 无来源标注时用中日文字符判断，避免把英文当成中文写进 zhHans
                if CJK.search(value):
                    new = {"zhHans": value, "en": None, "translationStatus": "human"}
                    stats["toChinese"] += 1
                else:
                    new = {"zhHans": "", "en": value, "translationStatus": "pending"}
                    stats["toEnglish"] += 1
            c[field] = new
            stats["migrated"] += 1
            items.append(
                {
                    "caseId": c["id"],
                    "field": field,
                    "language": "en" if new["en"] else "zhHans",
                    "chars": len(value),
                }
            )

    CASES.write_text(json.dumps(cases, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    REPORT.write_text(
        json.dumps(
            {
                "generatedBy": "scripts/migrate-case-l3-bilingual.py",
                "policy": "有 dcwL3Source.lang==en 的进 en（pending）；其余中文进 zhHans（human）；已是对象不动",
                **stats,
                "items": items,
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()
