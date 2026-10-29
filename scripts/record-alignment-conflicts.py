#!/usr/bin/env python3
"""记录 DCW 页面与本地实体之间无法自动裁定的对齐冲突。

政策：同一来源内部互不相容的表述，不得自行择一，必须留档待人工复核。
本脚本只写 docs/FACT-CONFLICTS.json，不改动任何实体数据。
幂等：按 id 去重。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFLICTS = ROOT / "docs" / "FACT-CONFLICTS.json"
TODAY = "2026-10-27"

NEW = [
    {
        "id": "conflict-kirin-horn-585-overlap",
        "entityType": "case",
        "entityIds": ["case-kobayashi-sensei-s-love", "case-kirin-s-horn-that-vanished"],
        "field": "animeRefs",
        "description": (
            "EP.585 的归属在两个 DCW 来源之间存在分歧："
            "《Anime》剧集表的 Episode title 单元格把 EP.583/584/585 链到 "
            "Kobayashi-sensei's_Love，EP.586/587 链到 The_Kirin's_Horn_That_Vanished_into_the_Dark；"
            "而 The_Kirin's_Horn 页面自己的 infobox 声明 'Episode 585-587'，"
            "即认为 EP.585 属于麒麟角案（对应漫画 File.712-715）。"
            "两个页面的漫画 File 号完全不重叠（705/708 vs 712-715），可确认是两个独立案件，"
            "争议仅在 EP.585 这一个集号的归属。"
        ),
        "values": [
            {"value": "EP.585 归 Kobayashi-sensei's Love", "source": "DCW /wiki/Anime 剧集表链接"},
            {"value": "EP.585 归 The Kirin's Horn", "source": "DCW The_Kirin's_Horn_That_Vanished_into_the_Dark 页 infobox"},
        ],
        "status": "open",
        "resolution": None,
        "action": "两个实体均保留现有 animeRefs 声明，不做删除或改写；待人工核对 EP.585 实际剧情归属后再裁定。",
        "recordedAt": TODAY,
    },
    {
        "id": "conflict-ep96-two-cases-one-page",
        "entityType": "case",
        "entityIds": ["case-tsukumo-magician-murder", "case-yabuuchi-family-murder"],
        "field": "animeRefs",
        "description": (
            "EP.96 是两小时特别篇，包含两个独立案件。本地库已按其内容拆分为两个实体"
            "（九十九魔术师杀人 / 薮内家族杀人），两者 animeRefs 都声明 EP.96；"
            "但 DCW 只提供一个合并页面 The_Cornered_Famous_Detective!_Two_Big_Murder_Cases。"
            "因此 DCW 页面无法与单一实体一一对齐，也无法自动挂接 castNames / caseType。"
        ),
        "values": [
            {"value": "拆分为两个案件实体", "source": "本地既有实体（人工拆分）"},
            {"value": "单个合并页面", "source": "DCW The_Cornered_Famous_Detective!_Two_Big_Murder_Cases"},
        ],
        "status": "open",
        "resolution": None,
        "action": "保留拆分结构，不为对齐而合并实体；DCW 该页的 castNames/caseType 不自动挂接。",
        "recordedAt": TODAY,
    },
]


def main() -> None:
    data = json.loads(CONFLICTS.read_text(encoding="utf-8"))
    rows = data if isinstance(data, list) else data.get("conflicts", [])
    have = {r.get("id") for r in rows}
    added = 0
    for row in NEW:
        if row["id"] in have:
            continue
        rows.append(row)
        have.add(row["id"])
        added += 1
    if isinstance(data, dict):
        data["conflicts"] = rows
        out = data
    else:
        out = rows
    CONFLICTS.write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(f"conflicts_total={len(rows)} added={added}")


if __name__ == "__main__":
    main()
