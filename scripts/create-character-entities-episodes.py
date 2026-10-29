#!/usr/bin/env python3
"""P2：把剧集页面 `caseCast` 里出现 ≥N 集、但还没有实体的人物建出来。

与 `create-character-entities.py`（P4，按**案件** castNames）同一口径，这次按**剧集** castNames：
    * 阈值默认 5 集；
    * 中文名一律留空（`translationStatus: "pending"`），不猜汉字；
    * 化名并入已有角色的 `aliases`，不新建；
    * 无名 / 群像 / 虚构角色跳过（复用 P4 的非个人清单）；
    * 只补空，不覆盖已有非空字段；
    * 幂等：第二次运行 0 改动。

用法：
    python3 scripts/create-character-entities-episodes.py --dry-run
    python3 scripts/create-character-entities-episodes.py
    python3 scripts/create-character-entities-episodes.py --min 10
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPISODES = ROOT / "data" / "episodes" / "episodes.json"
CHARS = ROOT / "data" / "entities" / "characters.json"

ALIAS_MAP = {
    "tooru amuro": "character-rei-furuya",
    "toru amuro": "character-rei-furuya",
    "subaru okiya": "character-shuichi-akai",
    "scar akai": "character-shuichi-akai",
    "shiho miyano": "character-ai-haibara",
    "kaito kuroba": "character-kaito-kid",
    "professor agasa": "character-hiroshi-agasa",
    "hiroshi agasa": "character-hiroshi-agasa",
}

# 不是可识别个人：无名者、群像、剧中剧虚构角色
NON_PERSONS = {
    "detective boys",
    "unnamed officer",
    "policeman",
    "police detective",
    "female forensics member",
    "presiding judge",
    "side judge a",
    "side judge b",
    "professor",
    "mrs. kojima",
    "goro",
    "maro",
    "kamen yaiba",
    "gomera",
    "night baron",
}

FOOTNOTE = re.compile(r"\[[^\]]*\]")
SOURCES = ["src-detective-conan-world-characters", "src-detective-conan-world-anime"]

# 只有姓氏 / 岗位，没有名字：不是可识别的个人，不建实体
SURNAME_ONLY = {"sasaki", "nakamichi", "tashiro", "hidaka", "oda", "shiota"}
# 明确"未知"的记录
ANONYMOUS = re.compile(r"^(unknown|unnamed|anonymous)\b", re.IGNORECASE)
# 岗位 / 编号式无名角色：Forensic member、FBI Agent 1、Police Officer 2 …
ROLE_LIKE = re.compile(
    r"\b(member|agent|officer|guard|attendant|staff|employee|worker|anchor|"
    r"announcer|reporter|nurse|doctor|teacher|driver|waiter|clerk|villager|cameraman)\b",
    re.IGNORECASE,
)


def is_person(name: str) -> tuple[bool, str]:
    key = name.strip().lower()
    text = name.strip()
    if key in NON_PERSONS:
        return False, "非个人"
    if ANONYMOUS.match(text):
        return False, "身份不明"
    if ROLE_LIKE.search(text) or re.search(r"\d+\s*$", text):
        return False, "岗位/编号"
    if key in SURNAME_ONLY or len(text.split()) < 2:
        return False, "仅姓氏/无全名"
    return True, ""


def slug(name: str) -> str:
    s = name.lower().replace("'", "").replace(".", "")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return f"character-{s}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    episodes = json.loads(EPISODES.read_text(encoding="utf-8"))
    chars = json.loads(CHARS.read_text(encoding="utf-8"))

    # 已有姓名索引（含别名）
    by_name: dict[str, dict] = {}
    taken_ids = set()
    for char in chars:
        taken_ids.add(char["id"])
        names = []
        name = char.get("name") or {}
        if isinstance(name, dict):
            names.extend(v for v in name.values() if isinstance(v, str))
        elif isinstance(name, str):
            names.append(name)
        names.extend(a for a in (char.get("aliases") or []) if isinstance(a, str))
        for n in names:
            by_name[n.strip().lower()] = char
    for alias, cid in ALIAS_MAP.items():
        for char in chars:
            if char["id"] == cid:
                by_name[alias] = char

    # 统计剧集 castNames
    counter: dict[str, int] = {}
    for ep in episodes:
        for raw in (ep.get("castNames") or []):
            name = FOOTNOTE.sub("", raw).strip()
            if name:
                counter[name] = counter.get(name, 0) + 1

    created, aliased, skipped = [], [], []
    for name, count in sorted(counter.items(), key=lambda kv: -kv[1]):
        if count < args.min:
            continue
        key = name.lower()
        ok, why = is_person(name)
        if not ok:
            skipped.append((name, count, why))
            continue
        if key in by_name:
            char = by_name[key]
            if key not in {n.lower() for n in (char.get("aliases") or [])} and name not in (char.get("name") or {}).values():
                aliased.append((name, count, char["id"]))
            continue
        cid = slug(name)
        if cid in taken_ids:
            # 同名 slug 已存在但名字对不上：跳过，绝不复用
            skipped.append((name, count, f"id 冲突 {cid}"))
            continue
        taken_ids.add(cid)
        entity = {
            "id": cid,
            "kind": "character",
            "name": {"en": name},
            "translationStatus": "pending",
            "status": "skeleton",
            "sources": list(SOURCES),
            "note": "由剧集 cast 列表自动实体化；中文名待补",
        }
        chars.append(entity)
        by_name[key] = entity
        created.append((name, count, cid))

    print(f"{'[dry-run] ' if args.dry_run else ''}阈值 >= {args.min} 集")
    print(f"  新建角色 {len(created)}")
    for name, count, cid in created:
        print(f"    {count:4d}  {name:34s} → {cid}")
    print(f"  化名并入 {len(aliased)}")
    for name, count, cid in aliased:
        print(f"    {count:4d}  {name:34s} → {cid}")
    print(f"  跳过 {len(skipped)}（非个人 / 冲突）")

    if args.dry_run:
        print("（未写盘）")
        return

    # 化名写入
    for name, count, cid in aliased:
        for char in chars:
            if char["id"] == cid:
                aliases = char.setdefault("aliases", [])
                if name not in aliases:
                    aliases.append(name)

    CHARS.write_text(json.dumps(chars, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"角色总数 → {len(chars)}")


if __name__ == "__main__":
    main()
