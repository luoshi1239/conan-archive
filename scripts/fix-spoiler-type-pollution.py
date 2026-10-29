#!/usr/bin/env python3
"""修复 spoiler 字段被自由文本污染的问题。

历史原因：`fix-traverse-related-cases.py` 与 `neutralize-chisato-timeframe.py`
把 `relatedCases` 里混入的事件备注写进了 `spoiler`——而 `spoiler` 是 1/2/3 的剧透等级，
被写成 100+ 字的中文段落，导致：
    * 前端 `(record.spoiler || 1) <= activeLevel` 全部过滤掉（案件凭空消失）
    * `validate-data.py` 与排序逻辑拿到字符串

处置：把文本原样迁到 `case.spoilerNote`（新字段，纯文本），`spoiler` 恢复为数字等级。
原文一个字不改，只换存放位置。

用法：
    python3 scripts/fix-spoiler-type-pollution.py --dry-run
    python3 scripts/fix-spoiler-type-pollution.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "entities" / "cases.json"

# 案例库的历史默认剧透等级：deepSpoilers/catalog 的多数条目是 2（深入）
DEFAULT_LEVEL = 2


def main() -> None:
    import sys

    dry = "--dry-run" in sys.argv
    rows = json.loads(CASES.read_text(encoding="utf-8"))
    fixed = []

    for case in rows:
        value = case.get("spoiler")
        if isinstance(value, int):
            continue
        if value is None:
            # 缺省补默认等级，语义不变（前端本来就用 `|| 1` 兜底）
            if not dry:
                case["spoiler"] = DEFAULT_LEVEL
            fixed.append((case["id"], "null→2", 0))
            continue
        if isinstance(value, str):
            text = value.strip()
            # 已是数字字符串（如 "2"）就直接转回去
            if text.isdigit():
                if not dry:
                    case["spoiler"] = int(text)
                fixed.append((case["id"], f'"{text}"→{int(text)}', 0))
                continue
            # 自由文本：迁到 spoilerNote，不覆盖已有非空内容
            existing = (case.get("spoilerNote") or "").strip()
            note = text if not existing else f"{existing} {text}".strip()
            if not dry:
                case["spoilerNote"] = note
                case["spoiler"] = DEFAULT_LEVEL
                case["spoilerNoteSource"] = (
                    "fix-spoiler-type-pollution.py：原 spoiler 字段被自由文本污染，"
                    "文本迁此，等级恢复为同级默认值"
                )
            fixed.append((case["id"], f"文本{len(text)}字→spoilerNote", len(text)))

    print(f"{'[dry-run] ' if dry else ''}待修复 {len(fixed)} 条")
    for cid, how, n in fixed:
        print(f"  {cid:44s} {how}")

    if not dry:
        CASES.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"已写入 {CASES}")
    else:
        print("（未写盘）")


if __name__ == "__main__":
    main()
