#!/usr/bin/env python3
"""Append sourced L3 candidates for the Library Murder Case."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data/candidates/entities.json"
BATCH = "p4-deep-case-library-01"
TARGET = "case-library-murder"
SOURCE = "src-detective-conan-world-library-case"
VALUES = {
    "culprit": "津川秀治。",
    "motive": "津川在米花图书馆的无书脊伪书中藏匿毒品并逐批出售；馆长玉田发现了毒品，因此津川为灭口杀害玉田。",
    "method": "津川杀害玉田后，将尸体从电梯井抛下并藏在电梯箱顶部；同时把藏毒的无书脊伪书排成儿童区的第三排，制造书架排列异常。",
    "evidence": "电梯在载荷看似不足时触发超重警报，提示电梯箱顶部有尸体；儿童区书架出现由无书脊伪书形成的第三排，且书籍排列不齐；书中藏有毒品。",
    "resolution": "柯南根据电梯超重警报、尸体位置和藏毒伪书的排列机关识破案件，津川作为犯人被揭发。",
}
rows = json.loads(PATH.read_text(encoding="utf-8"))
existing = {row.get("candidateId") for row in rows}
added = 0
for field, value in VALUES.items():
    cid = f"{BATCH}-{field}"
    if cid in existing:
        continue
    rows.append({
        "candidateId": cid,
        "targetId": TARGET,
        "field": field,
        "value": value,
        "sourceRefs": [SOURCE],
        "confidence": "medium",
        "reviewStatus": "pending",
        "reviewNote": "已读取案件页面正文；L3全剧透字段，应用后前端默认隐藏。",
    })
    added += 1
PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"added={added}")
