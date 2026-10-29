#!/usr/bin/env python3
"""P4：把案件页 castNames 里出现 ≥N 案的人物实体化。

口径（保守，只搬原文，不编造）：
    * 中文名一律留空（`translationStatus: "pending"`），不猜汉字写法
    * 不写 role/summary —— 原文没给的就不写
    * 已有角色的**化名**不新建实体，挂到该角色的 `aliases`
    * 无名路人、庭审角色、剧中虚构角色（假面超人/哥美拉）不建实体
    * 双向挂接：`character.caseRefs` ←→ `case.characters`

幂等：二次运行零改动。

用法：
    python3 scripts/create-character-entities.py [--threshold 5] [--dry-run]
"""
import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "entities" / "cases.json"
CHARS = ROOT / "data" / "entities" / "characters.json"

SOURCES = ["src-detective-conan-world-characters", "src-detective-conan-world-anime"]

# 化名 → 已有角色 id（不新建实体，只并入 aliases）
ALIAS = {
    "Tooru Amuro": "character-rei-furuya",
    "Subaru Okiya": "character-shuichi-akai",
    "Scar Akai": "character-shuichi-akai",
    "Shiho Miyano": "character-ai-haibara",
    "Kaito Kuroba": "character-kaito-kid",
}

# 不是「可识别的个人」，不建实体（理由见 docs/OPERATION-LOG-2026-10-28-P4-CHARACTERS.md）
SKIP = {
    "Detective Boys": "团体，应建 organization 实体（待办）",
    "Unnamed officer": "无名路人",
    "Policeman": "无名路人",
    "Police detective": "无名路人",
    "Female forensics member": "无名路人",
    "Presiding judge": "庭审功能角色，无姓名",
    "Side judge A": "庭审功能角色，无姓名",
    "Side judge B": "庭审功能角色，无姓名",
    "Professor": "泛称，无姓名",
    "Mrs. Kojima": "泛称（小岛的母亲），无姓名",
    "Goro": "指代不明",
    "Maro": "指代不明",
    "Kamen Yaiba": "剧中虚构角色（假面超人）",
    "Gomera": "剧中虚构角色（哥美拉）",
}


def slug(name: str) -> str:
    text = unicodedata.normalize("NFKD", name)
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    text = text.replace("'", "").replace("’", "")
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return f"character-{text}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cases = json.loads(CASES.read_text(encoding="utf-8"))
    chars = json.loads(CHARS.read_text(encoding="utf-8"))
    existing = {c["id"]: c for c in chars}
    existing_by_name = {}
    for c in chars:
        for value in (c.get("name") or {}).values():
            if isinstance(value, str) and value:
                existing_by_name[value.strip().lower()] = c["id"]
        for alias in c.get("aliases") or []:
            if isinstance(alias, str):
                existing_by_name.setdefault(alias.strip().lower(), c["id"])

    # 统计 castNames → 案件列表
    name_cases = defaultdict(list)
    for case in cases:
        for name in case.get("castNames") or []:
            if isinstance(name, str) and name.strip():
                name_cases[name.strip()].append(case["id"])

    ranked = sorted(name_cases.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    created, aliased, skipped, kept = [], [], [], []

    for name, case_ids in ranked:
        if len(case_ids) < args.threshold:
            continue
        key = name.lower()
        if key in existing_by_name:
            char = existing[existing_by_name[key]]
            # 化名并入已有角色
            if name != (char.get("name") or {}).get("en"):
                alias_list = char.setdefault("aliases", [])
                if name not in alias_list:
                    alias_list.append(name)
                    aliased.append(f"{name} → {char['id']}")
            existing_by_name[key] = char["id"]  # 同一轮内即可用于挂接
            refs = char.setdefault("caseRefs", [])
            for cid in case_ids:
                if cid not in refs:
                    refs.append(cid)
            kept.append(name)
            continue
        if name in ALIAS:
            char = existing[ALIAS[name]]
            alias_list = char.setdefault("aliases", [])
            if name not in alias_list:
                alias_list.append(name)
                aliased.append(f"{name} → {char['id']}")
            existing_by_name[key] = char["id"]  # 同一轮内即可用于挂接
            refs = char.setdefault("caseRefs", [])
            for cid in case_ids:
                if cid not in refs:
                    refs.append(cid)
            continue
        if name in SKIP:
            skipped.append(f"{name}（{SKIP[name]}）")
            continue

        char_id = slug(name)
        if char_id in existing:
            skipped.append(f"{name}（id 冲突 {char_id}）")
            continue
        entity = {
            "id": char_id,
            "kind": "character",
            "name": {"en": name},
            "aliases": [],
            "translationStatus": "pending",
            "status": "skeleton",
            "spoiler": 0,
            "caseRefs": list(case_ids),
            "sources": list(SOURCES),
            "note": f"由案件页 cast 列表实体化（出现 {len(case_ids)} 案）；中文名与角色定位待补，原文未给出故留空",
        }
        chars.append(entity)
        existing[char_id] = entity
        existing_by_name[key] = char_id
        created.append(f"{char_id}（{len(case_ids)} 案）")

    # 统一 kind 标记（前端据此判「人物」，缺失会被误判成「主线」）
    for char in chars:
        if char.get("kind") != "character":
            char["kind"] = "character"

    # 双向挂接：case.characters ← 新实体
    linked = 0
    for case in cases:
        names = [n.strip() for n in (case.get("castNames") or []) if isinstance(n, str)]
        ids = []
        for name in names:
            cid = existing_by_name.get(name.lower())
            if cid:
                ids.append(cid)
        current = list(case.get("characters") or [])
        for cid in ids:
            if cid not in current:
                current.append(cid)
                linked += 1
        case["characters"] = current

    print(f"新建角色 {len(created)} | 化名并入 {len(aliased)} | 跳过 {len(skipped)} | 已存在 {len(kept)}")
    print(f"新增案件↔角色挂接 {linked} 条 | 角色总数 {len(chars)}")
    for row in created[:8]:
        print("  NEW", row)
    if len(created) > 8:
        print(f"  ... 其余 {len(created) - 8} 个")
    for row in aliased:
        print("  ALIAS", row)
    for row in skipped:
        print("  SKIP", row)

    if args.dry_run:
        print("(dry-run，未写入)")
        return

    CHARS.write_text(json.dumps(chars, ensure_ascii=False, indent=2), encoding="utf-8")
    CASES.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
    print("已写入 characters.json / cases.json")


if __name__ == "__main__":
    main()
