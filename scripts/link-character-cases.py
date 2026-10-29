#!/usr/bin/env python3
"""把已知 14 个角色实体与案件实体双向挂接（只做事实关系，不新建实体）。

依据：案件实体的 `castNames`（DCW 页面 Case 段的 Cast 原文，英文），
与角色实体 `name.en` / `aliases` 精确匹配（不模糊匹配、不做姓名推断）。

写入：
    case.characters      += characterId（去重、保持既有顺序、追加在后）
    character.caseRefs   += caseId（反向索引，字段由本脚本建立）

铁律：
    - 只增不删：已有内容一律保留；
    - 匹配必须完全一致（大小写不敏感），不做同姓/缩写推断；
    - 幂等：二次运行零改动。

输出：data/entities/cases.json、data/entities/characters.json；docs/CHARACTER-CASE-LINKS.json
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "entities" / "cases.json"
CHARS = ROOT / "data" / "entities" / "characters.json"
REPORT = ROOT / "docs" / "CHARACTER-CASE-LINKS.json"
BACKUP_CASES = Path("/tmp/ca/cases_pre_char_links.json")
BACKUP_CHARS = Path("/tmp/ca/chars_pre_char_links.json")


def main() -> None:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    chars = json.loads(CHARS.read_text(encoding="utf-8"))

    BACKUP_CASES.parent.mkdir(parents=True, exist_ok=True)
    if not BACKUP_CASES.exists():
        shutil.copy2(CASES, BACKUP_CASES)
    if not BACKUP_CHARS.exists():
        shutil.copy2(CHARS, BACKUP_CHARS)

    by_name: dict[str, str] = {}
    for ch in chars:
        for lang in ("en", "ja", "zhHans", "zhHant"):
            v = (ch.get("name") or {}).get(lang)
            if v:
                by_name.setdefault(v.strip().lower(), ch["id"])
        for a in ch.get("aliases") or []:
            if a:
                by_name.setdefault(a.strip().lower(), ch["id"])

    added_case_links = 0
    per_char: dict[str, int] = {}
    for c in cases:
        linked = c.get("characters")
        if not isinstance(linked, list):
            linked = []
        existing = set(linked)
        new_ids = []
        for name in c.get("castNames") or []:
            cid = by_name.get(str(name).strip().lower())
            if cid and cid not in existing:
                new_ids.append(cid)
                existing.add(cid)
        if new_ids:
            c["characters"] = linked + new_ids
            added_case_links += len(new_ids)
            for cid in new_ids:
                per_char[cid] = per_char.get(cid, 0) + 1

    # 反向索引
    char_by_id = {ch["id"]: ch for ch in chars}
    for c in cases:
        for cid in c.get("characters") or []:
            ch = char_by_id.get(cid)
            if not ch:
                continue
            refs = ch.get("caseRefs")
            if not isinstance(refs, list):
                refs = []
                ch["caseRefs"] = refs
            if c["id"] not in refs:
                refs.append(c["id"])

    for ch in chars:
        if isinstance(ch.get("caseRefs"), list):
            ch["caseRefs"].sort()

    # 剧集角色：由「剧集 → 案件 → 案件角色」推导（纯关系传递，无新事实）
    eps_path = ROOT / "data" / "episodes" / "episodes.json"
    added_episode_links = 0
    if eps_path.exists():
        episodes = json.loads(eps_path.read_text(encoding="utf-8"))
        case_chars = {c["id"]: set(c.get("characters") or []) for c in cases}
        for e in episodes:
            linked = e.get("characters")
            if not isinstance(linked, list):
                linked = []
            existing = set(linked)
            new_ids: list[str] = []
            for cid in e.get("caseRefs") or []:
                for char_id in case_chars.get(cid, ()):
                    if char_id not in existing:
                        new_ids.append(char_id)
                        existing.add(char_id)
            if new_ids:
                e["characters"] = linked + new_ids
                added_episode_links += len(new_ids)
        eps_path.write_text(
            json.dumps(episodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    CASES.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CHARS.write_text(json.dumps(chars, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(
        json.dumps(
            {
                "generatedBy": "scripts/link-character-cases.py",
                "policy": "castNames 与角色 name/aliases 精确匹配；只增不删；不新建角色实体",
                "addedCaseLinks": added_case_links,
                "perCharacter": per_char,
                "characterCount": len(chars),
                "casesWithCharacters": sum(1 for c in cases if c.get("characters")),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"addedCaseLinks": added_case_links, "perCharacter": per_char}, ensure_ascii=False))


if __name__ == "__main__":
    main()
