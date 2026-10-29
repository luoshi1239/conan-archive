#!/usr/bin/env python3
"""M15：补齐组织成员（members / formerMembers）。

背景：organizations.json 里 black 只有 5 人、FBI 1 人、公安 1 人、宫野家 1 人，
关系图的「组织成员」模式因此只有 10 个节点。案件数据里 organizations 字段
只被 6 个案件使用、且共现不等于成员身份，无法反推，只能按公开设定人工补。

规则：
- members：当前仍属该组织（卧底在暴露前仍算在职，备注标明）
- formerMembers：已叛离、已死亡、已暴露且脱离
- 不写 spoiler>2 的推断；角色 id 必须存在于 characters.json，否则整批不写盘
- 幂等：二遍跑输出 IDEMPOTENT_OK 且不写盘
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORG_PATH = ROOT / "data/entities/organizations.json"
CHAR_PATH = ROOT / "data/entities/characters.json"

# 组织 id -> (members, formerMembers, memberNotes)
PLAN = {
    "organization-black": {
        "members": [
            "character-gin",
            "character-vodka",
            "character-vermouth",
            "character-chianti",
            "character-korn",
            "character-rum",
            "character-the-boss",
            "character-rei-furuya",          # 波本，卧底身份未公开暴露
            "character-hidemi-hondou",        # 基尔，CIA 卧底
            "character-kanenori-wakita",      # 胁田兼则，朗姆的伪装身份之一
        ],
        "formerMembers": [
            "character-ai-haibara",           # 雪莉，已叛离
            "character-shuichi-akai",         # 曾以诸星大身份潜入，已脱离
            "character-akemi-miyano",         # 已身亡
            "character-atsushi-miyano",       # 宫野厚司，已身亡
            "character-elena-miyano",         # 宫野艾莲娜，已身亡
            "character-rikumichi-kusuda",     # 已身亡
            "character-kiichiro-numabuchi",   # 已身亡
            "character-sharon-vineyard",      # 贝尔摩德的公开身份
        ],
        "memberNotes": {
            "character-rei-furuya": "代号波本，日本公安卧底",
            "character-hidemi-hondou": "代号基尔，CIA 卧底",
            "character-kanenori-wakita": "朗姆的伪装身份之一",
            "character-ai-haibara": "代号雪莉，已叛离",
            "character-shuichi-akai": "曾以诸星大之名潜入",
            "character-sharon-vineyard": "贝尔摩德的对外身份",
        },
    },
    "organization-fbi": {
        "members": [
            "character-shuichi-akai",
            "character-jodie-starling",
            "character-james-black",
            "character-andre-camel",
        ],
        "formerMembers": ["character-tsutomu-akai"],
        "memberNotes": {
            "character-tsutomu-akai": "赤井务武，多年前失踪",
        },
    },
    "organization-public-security": {
        "members": [
            "character-rei-furuya",
            "character-yuya-kazami",
        ],
        "formerMembers": ["character-hiromitsu-morofushi"],
        "memberNotes": {
            "character-rei-furuya": "降谷零，代号波本，潜入黑衣组织",
            "character-hiromitsu-morofushi": "诸伏景光，卧底期间身亡",
        },
    },
    "organization-miyano-family": {
        "members": ["character-ai-haibara"],
        "formerMembers": [
            "character-atsushi-miyano",
            "character-elena-miyano",
            "character-akemi-miyano",
        ],
        "memberNotes": {
            "character-ai-haibara": "宫野志保，后改名灰原哀",
            "character-atsushi-miyano": "父亲，APTX4869 研究者",
            "character-elena-miyano": "母亲，代号地狱天使",
            "character-akemi-miyano": "姐姐",
        },
    },
}


def main() -> int:
    orgs = json.loads(ORG_PATH.read_text(encoding="utf-8"))
    is_list = isinstance(orgs, list)
    items = orgs if is_list else (orgs.get("organizations") or orgs.get("items"))

    chars = json.loads(CHAR_PATH.read_text(encoding="utf-8"))
    char_items = chars if isinstance(chars, list) else (chars.get("characters") or chars.get("items"))
    valid = {c["id"] for c in char_items}

    # 先全量校验，任何一个 id 不存在都不写盘
    bad = []
    for oid, plan in PLAN.items():
        for cid in plan["members"] + plan["formerMembers"]:
            if cid not in valid:
                bad.append(f"{oid} -> {cid}")
        for cid in plan["memberNotes"]:
            if cid not in valid:
                bad.append(f"{oid} [note] -> {cid}")
    if bad:
        print("FAIL 引用不存在的人物 id：")
        for b in bad:
            print("  ", b)
        return 1

    changed = 0
    for org in items:
        plan = PLAN.get(org.get("id"))
        if not plan:
            continue
        # 去重并保持顺序
        def uniq(seq):
            seen, out = set(), []
            for x in seq:
                if x not in seen:
                    seen.add(x)
                    out.append(x)
            return out

        # 原有成员与计划合并，不丢历史数据
        members = uniq(list(org.get("members") or []) + plan["members"])
        # 原 members 里被判定为已脱离的，移到 formerMembers
        former = uniq(list(org.get("formerMembers") or []) + plan["formerMembers"])
        members = [m for m in members if m not in former]

        before = (
            list(org.get("members") or []),
            list(org.get("formerMembers") or []),
            dict(org.get("memberNotes") or {}),
        )
        after = (members, former, dict(plan["memberNotes"]))
        if before == after:
            continue
        org["members"] = members
        org["formerMembers"] = former
        org["memberNotes"] = dict(plan["memberNotes"])
        changed += 1

    if not changed:
        print(f"IDEMPOTENT_OK（无改动，不写盘）— {len(PLAN)} 个组织均已是目标状态")
        return 0

    ORG_PATH.write_text(
        json.dumps(orgs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    total_m = sum(len(p["members"]) for p in PLAN.values())
    total_f = sum(len(p["formerMembers"]) for p in PLAN.values())
    print(f"WROTE {ORG_PATH.name}：{changed} 个组织更新；members {total_m} 条，formerMembers {total_f} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
