#!/usr/bin/env python3
"""Build a candidate for the overlapping Clash of Red and Black arc."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data/candidates/episodes.json"
BATCH = "p4-arc-clash-red-black-01"
SOURCE = "src-detective-conan-world-clash-red-black"
VALUES = {
    "arcRefs": ["arc-kir", "arc-kir-clash"],
    "summary": "红与黑的碰撞篇章对应 EP.491—504，围绕水无怜奈、CIA、FBI与黑衣组织的情报战展开；页面同时将其拆分为 The Beginning、Deceased Mother's Memento、Fake Patient、Last Resort、Thirteenth 等子段。",
    "spoiler": 2,
}
rows = json.loads(PATH.read_text(encoding="utf-8"))
existing = {row.get("candidateId") for row in rows}
added = 0
for number in range(491, 505):
    target = f"episode-{number:04d}"
    for field, value in VALUES.items():
        cid = f"{BATCH}-ep{number}-{field}"
        if cid in existing:
            continue
        rows.append({
            "candidateId": cid,
            "targetId": target,
            "field": field,
            "value": value,
            "sourceRefs": [SOURCE],
            "confidence": "medium",
            "reviewStatus": "pending",
            "reviewNote": "来源正文明确给出 EP.491—504；arcRefs 保留既有 arc-kir 并新增子篇章候选。",
        })
        added += 1
PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"added={added}")
