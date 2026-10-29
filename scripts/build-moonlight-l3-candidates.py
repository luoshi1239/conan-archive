#!/usr/bin/env python3
"""Append sourced L3 candidates for the Moonlight Sonata case."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data/candidates/entities.json"
SOURCE = "src-detective-conan-world-moonlight-sonata"
BATCH = "p4-deep-case-moonlight-01"
TARGET = "case-moon-shadow-island"
VALUES = {
    "culprit": "浅井成实，真实身份为麻生成实；以女性身份在月影岛行医。",
    "motive": "为十二年前被杀害的父亲麻生圭二及家人复仇；相关岛上人物曾利用父亲的国际演奏活动掩护毒品交易。",
    "method": "利用钢琴房、录音播放、月光奏鸣曲乐谱暗号、现场布置和伪造自杀痕迹制造连续案件与不在场效果。",
    "evidence": "乐谱暗号、钢琴调音痕迹、录音播放时间、现场拖拽痕迹以及与旧案和受害者关系相互印证。",
    "resolution": "身份和案件真相被柯南推理揭示后，成实在燃烧的钢琴房中自杀；临终将柯南抛出窗外，并留下感谢侦探的音乐暗号。",
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
        "reviewNote": "基于 Detective Conan World 月影岛案件正文；L3 全剧透字段，应用后前端必须默认隐藏。",
    })
    added += 1
PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"added={added}")
