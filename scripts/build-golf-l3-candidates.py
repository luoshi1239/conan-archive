#!/usr/bin/env python3
"""Append sourced L3 candidates for the Golf Driving Range Murder Case."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data/candidates/entities.json"
BATCH = "p4-deep-case-golf-01"
TARGET = "case-golf-driving-range"
SOURCE = "src-detective-conan-world-golf-case"
VALUES = {
    "culprit": "南智史。",
    "motive": "南智史因上司忽视自己的才能，并偏袒对阿部稔，于是杀害上司并试图嫁祸阿部。",
    "method": "把炸弹预先藏进修理过的球杆头内的高尔夫球中，使目标挥杆时发生爆炸；同时准备替代球，并假装胃痛让阿部收集目标要使用的球，以制造嫁祸条件。",
    "evidence": "南智史曾连续两晚接触并维修目标的球杆；现场发现的高尔夫球只是替代物；真正的爆炸球藏在球杆头内，爆炸方式与球杆机关相互印证。",
    "resolution": "柯南识破球杆头内高尔夫球炸弹和嫁祸阿部的计划，南智史作为犯人被揭发。",
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
        "reviewNote": "已读取TV Original案件页面正文；L3全剧透字段，应用后前端默认隐藏。",
    })
    added += 1
PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"added={added}")
