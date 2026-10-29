#!/usr/bin/env python3
"""Apply explicitly reviewed mainline episode mappings to normalized data."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data" / "episodes" / "episodes.json"
SOURCE = "src-detective-conan-world-anime"

# These mappings use only relations already present in the repository's reviewed
# arc/case/entity records. They intentionally do not invent culprit/motive data.
GROUPS = [
    {
        "numbers": [1],
        "arc": "arc-shrinking-event",
        "caseRefs": ["case-roller-coaster-murder"],
        "locationRefs": ["location-tropical-land"],
        "characters": ["character-shinichi-kudo", "character-ran-mouri", "character-conan-edogawa", "character-gin", "character-vodka"],
        "organizations": ["organization-black"],
        "caseTypes": ["murder", "organization", "identity-start"],
        "summary": "工藤新一在多罗碧加乐园目击可疑交易并遭到袭击，身体缩小后开始以江户川柯南的身份生活。",
        "spoiler": 1,
    },
    {
        "numbers": [11, 12],
        "caseRefs": ["case-moon-shadow-island"],
        "locationRefs": ["location-moon-shadow-island"],
        "characters": ["character-conan-edogawa"],
        "caseTypes": ["murder", "island", "music-clue"],
        "summary": "柯南受委托前往月影岛调查案件，岛屿、音乐线索和连续事件构成早期代表性案件。",
        "spoiler": 1,
    },
    {
        "numbers": [49, 50],
        "caseRefs": ["case-diplomat-murder"],
        "locationRefs": ["location-beika-town"],
        "characters": ["character-conan-edogawa", "character-heiji-hattori"],
        "caseTypes": ["murder", "rival-detectives"],
        "summary": "服部平次登场并与柯南展开推理较量，案件同时完成两位高中生侦探关系的建立。",
        "spoiler": 1,
    },
    {
        "numbers": [128, 129, 176, 177, 178],
        "arc": "arc-vermouth",
        "caseRefs": [],
        "locationRefs": ["location-beika-town"],
        "characters": ["character-conan-edogawa", "character-ai-haibara", "character-gin"],
        "organizations": ["organization-black"],
        "caseTypes": ["organization", "identity", "drug"],
        "summary": "组织相关事件逐步从背景威胁进入柯南与灰原身边，围绕药物、身份和组织追查展开。具体单案拆分仍待继续校对。",
        "spoiler": 2,
    },
    {
        "numbers": [309, 310, 311],
        "arc": "arc-vermouth",
        "caseRefs": [],
        "locationRefs": ["location-beika-town"],
        "characters": ["character-conan-edogawa", "character-ai-haibara", "character-gin"],
        "organizations": ["organization-black"],
        "caseTypes": ["organization", "identity", "surveillance"],
        "summary": "柯南与黑衣组织的接触线继续推进，谈判、追踪和决死行动交替出现，具体案件边界待拆分。",
        "spoiler": 2,
    },
    {
        "numbers": [462, 463, 464, 465],
        "arc": "arc-kir",
        "caseRefs": [],
        "locationRefs": ["location-beika-town"],
        "characters": ["character-conan-edogawa", "character-ai-haibara", "character-gin"],
        "organizations": ["organization-black"],
        "caseTypes": ["organization", "surveillance", "identity"],
        "summary": "黑衣组织之影系列以多组目击和线索展开组织相关调查，连接后续红与黑的碰撞线。",
        "spoiler": 2,
    },
    {
        "numbers": [345],
        "arc": "arc-vermouth",
        "caseRefs": [],
        "locationRefs": ["location-beika-town"],
        "characters": ["character-conan-edogawa", "character-ran-mouri", "character-ai-haibara", "character-vermouth"],
        "organizations": ["organization-black"],
        "caseTypes": ["organization", "disguise", "identity"],
        "summary": "贝尔摩德篇的重要篇章，组织、变装、身份秘密与新一及兰的关系在满月之夜交汇。",
        "spoiler": 2,
    },
    {
        "numbers": [425],
        "arc": "arc-kir",
        "caseRefs": [],
        "locationRefs": ["location-beika-town"],
        "characters": ["character-conan-edogawa", "character-shuichi-akai", "character-gin"],
        "organizations": ["organization-black", "organization-fbi"],
        "caseTypes": ["organization", "undercover", "intelligence-war"],
        "summary": "基尔与红黑对决线的前置节点，组织行动、FBI调查与长期卧底情报战开始集中交织。",
        "spoiler": 2,
    },
    {
        "numbers": list(range(491, 505)),
        "arc": "arc-kir",
        "caseRefs": ["case-red-black-clash"],
        "locationRefs": ["location-beika-town"],
        "characters": ["character-conan-edogawa", "character-shuichi-akai", "character-gin"],
        "organizations": ["organization-black", "organization-fbi"],
        "caseTypes": ["organization", "undercover", "intelligence-war"],
        "summary": "红与黑的碰撞篇章围绕水无怜奈、FBI与黑衣组织展开长期情报战，具体分集转折仍需按集核对。",
        "spoiler": 2,
    },
    {
        "numbers": [52],
        "caseRefs": ["case-fog-monster"],
        "locationRefs": ["location-beika-town"],
        "characters": ["character-conan-edogawa"],
        "caseTypes": ["murder", "locked-room", "legend"],
        "summary": "以寺院传说和密室现象为核心的早期案件，柯南需要在传说叙事与现场证据之间建立对应关系。",
        "spoiler": 1,
    },
    {
        "numbers": [76, 219, 356, 469, 470, 515, 537, 538, 587, 627, 628, 724, 725, 746, 747, 887, 888, 983, 984, 1105, 1106, 1150, 1151, 1193, 1194],
        "arc": "arc-kaito-kid",
        "caseRefs": [],
        "locationRefs": ["location-beika-town"],
        "characters": ["character-conan-edogawa", "character-kaito-kid"],
        "organizations": [],
        "caseTypes": ["disguise", "heist", "rival-detectives"],
        "summary": "怪盗基德相关作品以预告、变装、宝石目标和柯南的追踪对决为核心，属于独立角色专题线。",
        "spoiler": 1,
    },
    {
        "numbers": [469, 470],
        "arcRefs": ["arc-kir"],
        "caseRefs": [],
        "locationRefs": ["location-beika-town"],
        "characters": ["character-conan-edogawa", "character-shuichi-akai", "character-gin", "character-kaito-kid"],
        "organizations": ["organization-black", "organization-fbi"],
        "caseTypes": ["organization", "identity", "disguise", "rival-detectives"],
        "summary": "本组集数同时位于基尔组织线与怪盗基德专题的交叉范围，保留双重篇章引用，具体案件边界仍按来源校对。",
        "spoiler": 2,
    },
    {
        "numbers": [511],
        "arc": "arc-bourbon",
        "caseRefs": [],
        "locationRefs": ["location-beika-town"],
        "characters": ["character-conan-edogawa", "character-shinichi-kudo", "character-shuichi-akai", "character-rei-furuya"],
        "organizations": ["organization-fbi", "organization-public-security"],
        "caseTypes": ["identity", "rival-detectives", "surveillance"],
        "summary": "工藤新一与冲矢昴的身份线索发生交叉，柯南需要在推理对决和身份判断之间重新评估情报。",
        "spoiler": 2,
    },
    {
        "numbers": [699, 700],
        "arc": "arc-mystery-train",
        "caseRefs": [],
        "locationRefs": ["location-beika-town"],
        "characters": ["character-conan-edogawa", "character-ai-haibara", "character-rei-furuya"],
        "organizations": ["organization-black", "organization-public-security"],
        "caseTypes": ["organization", "identity", "surveillance"],
        "summary": "灰原哀的秘密再次成为调查焦点，组织威胁与安室透相关情报在列车篇章前后继续发酵。",
        "spoiler": 2,
    },
    {
        "numbers": [768],
        "arc": "arc-rum",
        "caseRefs": [],
        "locationRefs": ["location-beika-town"],
        "characters": ["character-conan-edogawa", "character-ai-haibara"],
        "organizations": ["organization-black"],
        "caseTypes": ["organization", "identity", "abduction"],
        "summary": "灰原哀再次面临被组织线索牵连的风险，案件从日常事件转向对其身份和安全的关注。",
        "spoiler": 2,
    },
    {
        "numbers": [1080],
        "arc": "arc-rum",
        "caseRefs": [],
        "locationRefs": ["location-beika-town"],
        "characters": ["character-conan-edogawa", "character-ai-haibara"],
        "organizations": ["organization-black"],
        "caseTypes": ["organization", "identity", "surveillance"],
        "summary": "围绕灰原哀的监视与身份风险展开的动画原创节点，作为组织线的补充记录，具体关联待继续校对。",
        "spoiler": 2,
    },
    {
        "numbers": [674],
        "arc": "arc-bourbon",
        "caseRefs": [],
        "locationRefs": ["location-beika-town"],
        "characters": ["character-conan-edogawa", "character-rei-furuya", "character-shuichi-akai"],
        "organizations": ["organization-black", "organization-public-security", "organization-fbi"],
        "caseTypes": ["organization", "undercover", "identity"],
        "summary": "侦探们的夜想曲围绕波本身份、组织情报和多方调查展开，是波本调查线的重要节点。",
        "spoiler": 2,
    },
    {
        "numbers": [706],
        "arc": "arc-bourbon",
        "caseRefs": [],
        "locationRefs": ["location-beika-town"],
        "characters": ["character-conan-edogawa", "character-rei-furuya", "character-shuichi-akai"],
        "organizations": ["organization-black", "organization-public-security", "organization-fbi"],
        "caseTypes": ["organization", "undercover", "identity", "disguise"],
        "summary": "漆黑的特快列车之后，波本调查线进入身份揭示和阵营判断阶段，安室、冲矢与组织线索相互牵引。",
        "spoiler": 2,
    },
    {
        "numbers": [701, 702, 703, 704],
        "arc": "arc-mystery-train",
        "caseRefs": ["case-mystery-train"],
        "locationRefs": ["location-mystery-train"],
        "characters": ["character-conan-edogawa", "character-ai-haibara", "character-gin", "character-vermouth", "character-rei-furuya", "character-shuichi-akai"],
        "organizations": ["organization-black", "organization-fbi", "organization-public-security"],
        "caseTypes": ["murder", "locked-room", "organization", "disguise"],
        "summary": "漆黑的特快列车篇章把列车案件与组织追查雪莉的行动并置，多方身份、变装和计划同时推进。",
        "spoiler": 2,
    },
    {
        "numbers": [1077, 1078, 1079],
        "arc": "arc-rum",
        "caseRefs": ["case-rum-investigation"],
        "locationRefs": ["location-beika-town"],
        "characters": ["character-conan-edogawa", "character-ai-haibara"],
        "organizations": ["organization-black"],
        "caseTypes": ["organization", "cold-case", "identity"],
        "summary": "朗姆调查线的组织事件群，围绕组织行动、身份判断和长期调查逐步推进，具体单案范围仍待拆分。",
        "spoiler": 2,
    },
]


def main() -> None:
    rows = json.loads(PATH.read_text(encoding="utf-8"))
    by_number = {row.get("number"): row for row in rows}
    updated = []
    for group in GROUPS:
        for number in group["numbers"]:
            row = by_number.get(number)
            if not row:
                raise SystemExit(f"missing episode number {number}")
            for field in ("arc", "arcRefs", "caseRefs", "locationRefs", "characters", "organizations", "caseTypes", "summary", "spoiler"):
                if field == "arcRefs" and field in group:
                    row[field] = sorted(set(row.get(field, [])) | set(group[field]))
                elif field in group:
                    row[field] = group[field]
            if group.get("arc"):
                row["arcRefs"] = sorted(set(row.get("arcRefs", [])) | {group["arc"]})
            row["detailStatus"] = "reviewed"
            row["coverage"] = {
                "directory": True,
                "basicFacts": True,
                "structure": True,
                "deepSpoilers": False,
            }
            row["sources"] = sorted(set(row.get("sources", [])) | {SOURCE})
            updated.append(number)
    PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"updated={len(updated)} episodes")
    print(f"range={min(updated)}..{max(updated)}")
    print(f"numbers={','.join(map(str, updated))}")

if __name__ == "__main__":
    main()
