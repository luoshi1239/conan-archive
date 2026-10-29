#!/usr/bin/env python3
"""Resolve conflict-ushio-chisato-timeframe with two independent sources.

Evidence (all fetched and re-read locally, not from search snippets):
  1. conan-no-sekai.com/file93 — Japanese episode plot + verbatim dialogue.
     Cast block: "潮 千里…潮の一人娘。半年前に事故で他界。"
     Block [136] (Conan's in-show explanation): "半年前、フォックスはサラ金
     会社の社長を殺害した。その時、幼稚園の送迎バスが巻き込まれ…"
  2. conanpedia.com/TV93 — Chinese case table: 死亡时间：半年前
  3. DCW own Situation section: "Six months ago …"

Only DCW's Resolution section says "Two years ago", and a reverse search for
"2年前 / 两年 / two years ago" + case name returns no independent support.
Therefore: timeframe = 半年前; the victim in the assassination was the
president of a loan company (サラ金会社社長), not a generic major company.

This script also registers the two new sources and flips the conflict record
to resolved. Idempotent: re-running makes no further edits.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "sources.json"
CASES = ROOT / "data" / "entities" / "cases.json"
CONFLICTS = ROOT / "docs" / "FACT-CONFLICTS.json"

NEW_SOURCES = [
    {
        "id": "src-conan-no-sekai-file93",
        "type": "wiki",
        "title": "第93話「戦慄の登山道殺人事件（後編）」あらすじ・ネタバレ",
        "url": "https://conan-no-sekai.com/file93/",
        "language": "ja",
        "publisher": "conan-no-sekai.com",
        "accessedAt": "2026-10-27",
        "notes": "按话数复述剧情并保留台词原文，日文。正文块 [136] 为柯南向潮文三说明前情的台词原文，是本案时间线的最高证据层级。",
    },
    {
        "id": "src-conanpedia-tv93",
        "type": "wiki",
        "title": "名侦探柯南 TV93 恐怖登山杀人事件（后篇）",
        "url": "https://www.conanpedia.com/TV93",
        "language": "zh",
        "publisher": "conanpedia.com",
        "accessedAt": "2026-10-27",
        "notes": "中文案件资料库，含死者表、死亡时间、作案手法条目，与日文来源互相独立。",
    },
]

CASE_ID = "case-fearful-traversing-murder"

NEW_MOTIVE = (
    "平井长期往返该山道，认识真正的岩田重吉，是「狐狸」冒名顶替计划中的变数，"
    "因此在计划推进前被灭口。「狐狸」本身是受雇杀手，与牛尾文三之间另有因果："
    "半年前他刺杀高利贷公司社长时，对方车辆失控撞上幼儿园接送巴士，"
    "造成牛尾独生女、5 岁的千纱死亡；「狐狸」由此销声匿迹避风头。"
    "文三查不到他的脸和身份，只能拿自己的命当诱饵把他引出来。"
)

NEW_SPOILER = (
    "同一集的独立事件（不可并入本案）：凉子（Kyoko Saegusa）之死与「狐狸」无关——"
    "川边肇（Akira Kawabe）为灭口而杀害她，二人此前共同犯下抢劫杀人案；"
    "牛尾文三雇凶杀自己的委托与本次登山均为其复仇布局的一部分，文三本人不构成杀人既遂；"
    "在毛利侦探事务所遭狙击、以及小五郎在睡梦中被刺，原文均记为未遂事件。"
)

RESOLUTION_NOTE = (
    "已裁定为「半年前」。依据：conan-no-sekai.com（日文，含剧中台词原文）与 "
    "conanpedia.com（中文案件库）两个独立来源一致记为半年前，DCW 本页 Situation 段亦为 "
    "Six months ago；仅 Resolution 段写 Two years ago，反查无任何独立佐证，判定该段为"
    "后加的二手概述错误（同段还把千纱年龄写作约 7 岁，与角色栏及 Situation 段的 5 岁冲突）。"
    "同时据日文原名サラ金会社社長／中文站「高利贷公司社长」，把 DCW 的 "
    "president of a major company 细化为高利贷公司社长。"
)


def add_sources() -> int:
    data = json.loads(SOURCES.read_text(encoding="utf-8"))
    bucket = data["sources"] if isinstance(data, dict) else data
    have = {s["id"] for s in bucket}
    added = 0
    for src in NEW_SOURCES:
        if src["id"] in have:
            continue
        idx = next(
            (i for i, s in enumerate(bucket) if s["id"] == "src-detective-conan-world-movies"),
            len(bucket),
        )
        bucket.insert(idx, src)
        added += 1
    if added:
        SOURCES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return added


def fix_case() -> int:
    data = json.loads(CASES.read_text(encoding="utf-8"))
    cases = data["cases"] if isinstance(data, dict) else data
    changed = 0
    for case in cases:
        if case.get("id") != CASE_ID:
            continue
        if case.get("motive") != NEW_MOTIVE:
            case["motive"] = NEW_MOTIVE
            changed += 1
        if case.get("spoiler") != NEW_SPOILER:
            case["spoiler"] = NEW_SPOILER
            changed += 1
        for sid in ("src-conan-no-sekai-file93", "src-conanpedia-tv93"):
            refs = case.setdefault("sourceRefs", [])
            if sid not in refs:
                refs.append(sid)
                changed += 1
        if changed:
            case["updatedAt"] = "2026-10-27"
        break
    if changed:
        CASES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def resolve_conflict() -> int:
    data = json.loads(CONFLICTS.read_text(encoding="utf-8"))
    changed = 0
    for item in data.get("conflicts", []):
        if item.get("id") != "conflict-ushio-chisato-timeframe":
            continue
        if item.get("resolution") == "resolved":
            break
        item["secondSourceStatus"] = (
            "已取得两个独立来源：conan-no-sekai.com/file93（日文，含剧中台词原文）与 "
            "conanpedia.com/TV93（中文案件库）。另有 DCW 本页 Situation 段同为半年前。"
        )
        item["resolution"] = "resolved"
        item["resolvedValue"] = "半年前"
        item["resolutionNote"] = RESOLUTION_NOTE
        item["resolvedAt"] = "2026-10-27"
        item["appliedToData"] = (
            "motive 与 spoiler 已改写为明确表述「半年前」；同时把 assassination 受害者"
            "细化为高利贷公司社长；spoiler 中不再保留时间存疑提示。"
        )
        item["reviewStatus"] = "reviewed"
        item["secondaryDiscrepancy"] = {
            "subject": "千纱年龄",
            "statements": [
                {"text": "the young 5 year old Chisato Ushio", "value": "5 岁", "location": "Situation 段与 People 角色栏"},
                {"text": "a girl around Conan's (physical) age", "value": "约 7 岁", "location": "Resolution 段"},
            ],
            "resolution": "resolved",
            "resolvedValue": "5 岁",
            "resolutionNote": "角色栏与 Situation 段一致为 5 岁；Resolution 段的「约柯南年龄」是同一段二手概述的连带错误。",
            "resolvedAt": "2026-10-27",
        }
        data["conflictsResolved"] = sum(
            1 for c in data["conflicts"] if c.get("resolution") == "resolved"
        )
        changed = 1
        break
    if changed:
        CONFLICTS.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def main() -> int:
    s = add_sources()
    c = fix_case()
    r = resolve_conflict()
    print(f"sources_added={s} case_edits={c} conflict_resolved={r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
