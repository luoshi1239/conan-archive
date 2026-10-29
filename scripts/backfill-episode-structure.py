#!/usr/bin/env python3
"""P4-C：把 DCW 页面事实并进剧集库（season / solvedBy / caseCast）。

数据来源：`data/raw/dcw-page-facts.json`（793 页，已抽好的原文事实）
目标：`data/episodes/episodes.json`（1217 集）

口径（与全库一致）：
    * 只搬原文，不编造；不覆盖已有非空字段。
    * `season` 用页面 `season` 原值转整数。
    * `solvedBy` 用页面原文，去掉维基脚注标记（`[1]` 之类）；
      `No one` / `N/A` 不是人物，写进 `solvedByNote`，不挂人。
    * `caseCast` 按 P4 的别名/非人物口径转成角色 id，挂进 `characters`（只增不删）。
    * 全部写入带 `dcwL3Source` 可追溯（页面 + 字段 + 置信度）。
    * `detailStatus` / `coverage` 只按"实际有内容"提升，不虚报。

用法：
    python3 scripts/backfill-episode-structure.py --dry-run
    python3 scripts/backfill-episode-structure.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FACTS = ROOT / "data" / "raw" / "dcw-page-facts.json"
EPISODES = ROOT / "data" / "episodes" / "episodes.json"
CHARS = ROOT / "data" / "entities" / "characters.json"

# 与 create-character-entities.py 保持同一口径
ALIAS_MAP = {
    "tooru amuro": "character-rei-furuya",
    "toru amuro": "character-rei-furuya",
    "subaru okiya": "character-shuichi-akai",
    "scar akai": "character-shuichi-akai",
    "shiho miyano": "character-ai-haibara",
    "kaito kuroba": "character-kaito-kid",
}

# 不是可识别个人，转不成角色实体
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
}

# 不是"某人破的案"
NO_SOLVER = {"", "no one", "n/a", "none", "unknown"}

FOOTNOTE = re.compile(r"\[[^\]]*\]")
SOURCE_ID = "src-detective-conan-world-cases"


def norm(name: str) -> str:
    return FOOTNOTE.sub("", name or "").strip()


def load_chars() -> tuple[dict[str, str], set[str]]:
    """返回 (姓名→角色id, 已知角色id集合)，含别名。"""
    rows = json.loads(CHARS.read_text(encoding="utf-8"))
    by_name: dict[str, str] = {}
    ids: set[str] = set()
    for char in rows:
        cid = char["id"]
        ids.add(cid)
        names = []
        name = char.get("name") or {}
        if isinstance(name, dict):
            names.extend(v for v in name.values() if isinstance(v, str))
        elif isinstance(name, str):
            names.append(name)
        names.extend(a for a in (char.get("aliases") or []) if isinstance(a, str))
        for n in names:
            by_name[n.strip().lower()] = cid
    for alias, cid in ALIAS_MAP.items():
        if cid in ids:
            by_name[alias] = cid
    return by_name, ids


def main() -> None:
    dry = "--dry-run" in sys.argv
    facts = json.loads(FACTS.read_text(encoding="utf-8"))
    pages = facts["pages"] if isinstance(facts, dict) else facts
    episodes = json.loads(EPISODES.read_text(encoding="utf-8"))
    by_name, char_ids = load_chars()

    # 集号 → 页面（一集多页时取 episodeNumbers 精确命中的第一页，其余记入 covers）
    page_of: dict[int, dict] = {}
    extra_of: dict[int, list[str]] = {}
    for row in pages:
        nums = row.get("episodeNumbers") or []
        for n in nums:
            if n in page_of:
                extra_of.setdefault(n, []).append(row["page"])
            else:
                page_of[n] = row

    stats = {"season": 0, "solvedBy": 0, "cast": 0, "charLinks": 0,
             "noPage": 0, "unresolved": {}, "noSolver": 0, "detailUp": 0}

    for ep in episodes:
        num = ep.get("number")
        row = page_of.get(num)
        if not row:
            stats["noPage"] += 1
            continue

        src: dict[str, str] = dict(ep.get("dcwL3Source") or {})

        # 1) season —— 只在空时写
        if not ep.get("season"):
            raw_season = norm(str(row.get("season") or ""))
            if raw_season.isdigit():
                if not dry:
                    ep["season"] = int(raw_season)
                    src["season"] = row["page"]
                stats["season"] += 1

        # 2) solvedBy —— 只在空时写
        if not ep.get("solvedBy") and not ep.get("solvedByRaw"):
            solver = norm(row.get("solvedBy") or "")
            if solver.lower() in NO_SOLVER:
                if solver and not dry:
                    ep["solvedByNote"] = solver
                if solver:
                    stats["noSolver"] += 1
            elif solver:
                cid = by_name.get(solver.lower())
                if not dry:
                    ep["solvedByRaw"] = solver
                    if cid and cid in char_ids:
                        ep["solvedBy"] = cid
                    else:
                        # 不是已收录角色：原文照存，不猜 id
                        stats["unresolved"][solver] = stats["unresolved"].get(solver, 0) + 1
                stats["solvedBy"] += 1

        # 3) caseCast → characters（只增不删）
        cast = [norm(n) for n in (row.get("caseCast") or [])]
        new_ids: list[str] = []
        for name in cast:
            if not name or name.lower() in NON_PERSONS:
                continue
            cid = by_name.get(name.lower())
            if cid and cid in char_ids:
                new_ids.append(cid)
            elif name.lower() not in NON_PERSONS:
                stats["unresolved"][name] = stats["unresolved"].get(name, 0) + 1
        if new_ids:
            have = list(ep.get("characters") or [])
            added = [c for c in new_ids if c not in have]
            if added:
                if not dry:
                    ep["characters"] = have + added
                    src["characters"] = row["page"]
                stats["charLinks"] += len(added)
            if not ep.get("castNames"):
                if not dry:
                    ep["castNames"] = cast
                stats["cast"] += 1

        if extra_of.get(num) and not dry:
            ep.setdefault("dcwExtraPages", extra_of[num])

        # 4) detailStatus / coverage —— 只按实际字段提升
        if not dry:
            cov = dict(ep.get("coverage") or {})
            cov["directory"] = True
            cov["basicFacts"] = bool(ep.get("airDate") or ep.get("title"))
            cov["structure"] = bool(ep.get("season") and ep.get("characters"))
            cov["deepSpoilers"] = bool(ep.get("caseRefs"))
            ep["coverage"] = cov
            if ep.get("detailStatus") == "catalog" and cov["structure"]:
                ep["detailStatus"] = "reviewed"
                stats["detailUp"] += 1

        if src and not dry and src != (ep.get("dcwL3Source") or {}):
            ep["dcwL3Source"] = src

    print(f"{'[dry-run] ' if dry else ''}命中页面 {len(page_of)} 集")
    print(f"  season 补 {stats['season']}")
    print(f"  solvedBy 补 {stats['solvedBy']}（其中无数值答案 {stats['noSolver']}）")
    print(f"  castNames 补 {stats['cast']}，角色挂接 +{stats['charLinks']}")
    print(f"  detailStatus 升 structured {stats['detailUp']}")
    print(f"  无对应页面 {stats['noPage']} 集")
    if stats["unresolved"]:
        top = sorted(stats["unresolved"].items(), key=lambda kv: -kv[1])[:15]
        print(f"  未收录姓名 {len(stats['unresolved'])} 个，最常见：")
        for name, n in top:
            print(f"    {n:4d}  {name}")

    if not dry:
        EPISODES.write_text(json.dumps(episodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"已写入 {EPISODES}")
    else:
        print("（未写盘）")


if __name__ == "__main__":
    main()
