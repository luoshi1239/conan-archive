#!/usr/bin/env python3
"""Rewrite the Ushio/Chisato timeframe to a neutral statement.

Source conflict (docs/FACT-CONFLICTS.json :: conflict-ushio-chisato-timeframe):
the same wiki page says "six months ago" in the Situation section and "two
years ago" in the Resolution section for the identical event. With no
independent second source reachable, the data must not pick a winner.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "entities" / "cases.json"
CASE_ID = "case-fearful-traversing-murder"

OLD_CLAUSE = "半年前他在刺杀某企业社长时令对方车辆失控撞上校车，造成牛尾年仅 5 岁的女儿千纱死亡，「狐狸」由此隐姓埋名避风头。"
NEW_CLAUSE = (
    "他在刺杀某企业社长时令对方车辆失控撞上校车，造成牛尾年仅 5 岁的女儿千纱死亡，"
    "「狐狸」由此隐姓埋名避风头；该事件距今多久，来源自身有两种说法，见 docs/FACT-CONFLICTS.json "
    "conflict-ushio-chisato-timeframe，数据不取其一。"
)

NOTE = (
    "时间线存疑（未裁定）：同一来源 Situation 段记「半年前」、Resolution 段记「两年前」，"
    "指的都是暗杀时目标车辆撞上校车致千纱死亡这同一件事，二者互不相容。"
    "本库暂不写具体时长，冲突原文与可核验线索见 docs/FACT-CONFLICTS.json。"
)


def main() -> int:
    data = json.loads(CASES.read_text(encoding="utf-8"))
    cases = data["cases"] if isinstance(data, dict) else data
    hits = 0
    for case in cases:
        if case.get("id") != CASE_ID:
            continue
        motive = case.get("motive") or ""
        if OLD_CLAUSE in motive:
            case["motive"] = motive.replace(OLD_CLAUSE, NEW_CLAUSE)
            hits += 1
        elif "FACT-CONFLICTS" not in motive:
            print("!! motive clause not found; inspect manually")
            print(motive)
        spoiler = case.get("spoiler") or ""
        if "时间线存疑" not in spoiler:
            case["spoiler"] = (spoiler + "；" + NOTE) if spoiler else NOTE
            hits += 1
        case["updatedAt"] = "2026-10-27"

    if hits:
        CASES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"edits={hits}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
