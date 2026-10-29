#!/usr/bin/env python3
"""用 DCW 页面 Resolution 原文块补齐案件 `resolution` 字段（L3 第五字段）。

背景：`normalize-case-status.py` 的规则是「五字段齐全」才升 deepSpoilers
（culprit + motive + method + evidence + resolution）。L3 队列只产出前四个字段，
所以 106 个已写入四字段的案件仍停在 partial。本脚本用
`data/raw/dcw-page-sections.json` 的 `resolution` 原文块补第五字段。

铁律：
    - 只补空值，绝不覆盖已有中文 resolution；
    - 只搬 DCW 原文（英文），不翻译不改写；
    - 段落数按 MAX_PARAS 截取、总长按 MAX_CHARS 截断，保留原文顺序；
    - 记录 dcwL3Source.resolution 以便追溯（页面 + 段号）。

输出：data/entities/cases.json；docs/CASE-RESOLUTION-BACKFILL.json
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "entities" / "cases.json"
SECTIONS = ROOT / "data" / "raw" / "dcw-page-sections.json"
REPORT = ROOT / "docs" / "CASE-RESOLUTION-BACKFILL.json"
BACKUP = Path("/tmp/ca/cases_pre_resolution.json")

MAX_PARAS = 3
MAX_CHARS = 900
MIN_CHARS = 40


def main() -> None:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    sections = json.loads(SECTIONS.read_text(encoding="utf-8"))["pages"]

    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    if not BACKUP.exists():
        shutil.copy2(CASES, BACKUP)

    filled: list[dict] = []
    blocked: list[dict] = []
    for c in cases:
        if c.get("resolution"):
            continue
        # 只处理已经拿到 L3 四字段的案件，避免把整库 792 案都灌上长段英文
        if not (c.get("culprit") and c.get("motive") and c.get("method") and c.get("evidence")):
            continue
        page = c.get("dcwPage")
        paras = ((sections.get(page) or {}).get("resolution")) if page else None
        if not paras:
            blocked.append({"caseId": c["id"], "dcwPage": page, "reason": "no_resolution_block"})
            continue
        picked: list[str] = []
        total = 0
        for p in paras:
            if len(picked) >= MAX_PARAS:
                break
            if total and total + len(p) > MAX_CHARS:
                break
            picked.append(p)
            total += len(p) + 1
        text = " ".join(picked).strip()
        if len(text) < MIN_CHARS:
            blocked.append({"caseId": c["id"], "dcwPage": page, "reason": "resolution_too_short"})
            continue
        c["resolution"] = text
        c.setdefault("dcwL3Source", {})["resolution"] = {
            "page": page,
            "block": "Resolution",
            "paragraphs": len(picked),
            "lang": "en",
            "reviewedBy": "scripts/backfill-case-resolution.py",
        }
        filled.append({"caseId": c["id"], "page": page, "chars": len(text)})

    CASES.write_text(json.dumps(cases, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    REPORT.write_text(
        json.dumps(
            {
                "generatedBy": "scripts/backfill-case-resolution.py",
                "policy": "只补已完成 L3 四字段的空 resolution；DCW 原文；不翻译不覆盖",
                "filled": len(filled),
                "blocked": len(blocked),
                "items": filled,
                "blockedItems": blocked,
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"filled": len(filled), "blocked": len(blocked)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
