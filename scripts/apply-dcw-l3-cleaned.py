#!/usr/bin/env python3
"""清洗中置信 culprit 候选并写入案件实体。

每条都必须人工逐句核对原文——本脚本内联了核对结论，不是自动规则。

清洗原则：
  - 只去掉原文里的职衔/从句/副词，不改人名本身；
  - 双凶手保留 "A and B"；
  - 原文若为误导性陈述（如柯南故意指控无辜者逼真凶现形），一律拒绝。

拒绝的候选写入 docs/L3-CULPRIT-REJECTED.json 并附理由。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANDS = ROOT / "data" / "candidates" / "dcw-l3.json"
CASES = ROOT / "data" / "entities" / "cases.json"
REJECTED = ROOT / "docs" / "L3-CULPRIT-REJECTED.json"
TODAY = "2026-10-27"

# page -> (清洗后的人名, 清洗说明)
CLEAN = {
    "A_Dangerous_Recipe": (
        "Yasuo Murakami",
        "原文 'The culprit's face revealed, Yasuo Murakami.' 直接点名，无需清洗，仅因句式非常规落入中置信",
    ),
    "Miracle_at_Koshien_Ball_Park!_The_Defiants_Face_the_Dark_Demon": (
        "Yukio Torimitsu",
        "原文 'The culprit is Yukio Torimitsu.' 为最强句式，中置信来自后续从句截断",
    ),
    "The_17-Year-Old_Truth": (
        "Rumi Wakasa",
        "原文 'Rumi Wakasa is the culprit of the robbery at the nearby firearm store...'，去掉作案对象后为人名",
    ),
    "The_Blind_Spot_in_the_Dressing_Room": (
        "Ayami Yamaki",
        "原文 'The culprit is Ayami Yamaki, Ritsuko Sashihara's assistant.' 去掉同位语职衔",
    ),
    "The_Detective_Boys'_Pursuit_of_the_Purse-snatcher": (
        "Shousaku Kume",
        "原文 'The culprit is Shousaku Kume, who killed Samura and Togane...' 去掉关系从句",
    ),
    "The_Detective_Boys_Get_Out_of_the_Rain": (
        "Maki Amamiya",
        "原文 'The real culprit is Maki Amamiya herself.' 去掉反身代词 herself",
    ),
    "The_Flying_Jack-o'-lantern": (
        "Satoshi Mizunuma and Tomomi Kashiyama",
        "原文 'The culprits are Satoshi Mizunuma and Tomomi Kashiyama.' 双凶手共同作案，保留两人",
    ),
    "The_Man_Who_Camped_Out_at_the_Police_Station": (
        "Yosuke Katsuki",
        "原文 'The culprit is really Yosuke Katsuki, while the culprit X never existed.' 去掉副词 really",
    ),
    "The_Night_Before_the_Wedding_Locked_Room_Case": (
        "Sakuraba",
        "原文 'They revealed that the culprit is Sakuraba.' 页面仅给出姓氏，照原文只存姓",
    ),
    "The_Secret_Rushed_Omission": (
        "Bunta Kuniyoshi",
        "原文 'Bunta Kuniyoshi (国吉文太' 括号未闭合，去掉残缺括号残留",
    ),
    "The_Witch_Enshrouded_by_Fog": (
        "Raito Egashira and Akira Mafune",
        "原文 'The culprits are revealed to be Raito Egashira and Akira Mafune.' 双凶手，保留两人",
    ),
}

# 人工核对后判定不得写入
REJECT = {
    "Nagasaki_Mystery_Theatre": (
        "Ran Mouri",
        "原文为误导性陈述：'That culprit is Ran Mouri. ... he knows that Ran is not the true culprit.'"
        "——柯南为逼真凶现身而故意指控无辜者，紧随其后的句子即否认。写入会制造事实错误。",
    ),
}


def main() -> None:
    cands = json.loads(CANDS.read_text(encoding="utf-8"))["candidates"]
    raw = json.loads(CASES.read_text(encoding="utf-8"))
    rows = raw if isinstance(raw, list) else raw.get("cases", [])
    by_page = {r["dcwPage"]: r for r in rows if r.get("dcwPage")}

    applied, skipped, missing = 0, 0, []
    for c in cands:
        if c["field"] != "culprit" or c["confidence"] == "high":
            continue
        page = c["dcwPage"]
        if page not in CLEAN:
            continue
        row = by_page.get(page)
        if row is None:
            missing.append(page)
            continue
        if row.get("culprit"):
            skipped += 1
            continue
        name, note = CLEAN[page]
        row["culprit"] = name
        row["culpritSource"] = {
            "page": page,
            "quote": c.get("quote"),
            "confidence": "medium-cleaned",
            "cleanNote": note,
            "reviewStatus": "cleaned-against-source",
            "reviewedAt": TODAY,
        }
        applied += 1

    CASES.write_text(json.dumps(raw, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    REJECTED.write_text(
        json.dumps(
            {
                "generatedAt": TODAY,
                "items": [
                    {"page": p, "value": v, "reason": r,
                     "decision": "rejected-do-not-write"}
                    for p, (v, r) in REJECT.items()
                ],
            },
            ensure_ascii=False, indent=1,
        ) + "\n",
        encoding="utf-8",
    )

    print(f"applied={applied} skipped_has_culprit={skipped} rejected={len(REJECT)}")
    if missing:
        print("missing case entity:", missing)


if __name__ == "__main__":
    main()
