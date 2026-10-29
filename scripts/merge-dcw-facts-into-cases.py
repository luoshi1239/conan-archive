#!/usr/bin/env python3
"""把 DCW 页面事实合并进已有案件实体（按集号对齐，而非按 id 对齐）。

场景：原有 51 个实体用了自定义 id（如 case-crab-whale-kidnapping），
与 DCW 页面 slug（A_Crab_and_Whale_Kidnapping_Case）不同名，导致生成器
判定为「集号被占用」而跳过新建——数据没错，但 DCW 的 caseCast / caseType /
dcwPage 等元数据没有落进来。本脚本按「页面集号 ⊆ 实体集号」可靠对齐后合并。

铁律
====
1. 只补实体上缺失的字段，已有值一律不动（人工核实优先）。
2. caseType 只并集，不覆盖、不清空；不新增白名单外的类型。
3. 不写 culprit / motive / method / evidence / resolution。
4. 幂等：第二次运行 merged=0。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FACTS = ROOT / "data" / "raw" / "dcw-page-facts.json"
CASES = ROOT / "data" / "entities" / "cases.json"
REPORT = ROOT / "docs" / "CASE-MERGE-REPORT.json"

TODAY = "2026-10-27"

CATEGORY_TO_TYPE = {
    "Locked Room Cases": "locked-room",
    "Serial Murder Cases": "serial-murder",
    "Closed Circle of Suspects": "closed-circle",
    "Impossible Crime Cases": "impossible-crime",
    "Mystery Tour Case": "mystery-tour",
}


def load_json(p: Path):
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(p: Path, obj) -> None:
    with p.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def expand(refs) -> set[int]:
    out: set[int] = set()
    for ref in refs or []:
        m = re.match(r"episode-(\d{4})(?:-(\d{4}))?$", ref)
        if not m:
            continue
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else a
        out.update(range(a, b + 1))
    return out


def compress(nums: list[int]) -> list[str]:
    if not nums:
        return []
    nums = sorted(set(nums))
    spans = []
    start = prev = nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
            continue
        spans.append((start, prev))
        start = prev = n
    spans.append((start, prev))
    return [
        f"episode-{a:04d}" if a == b else f"episode-{a:04d}-{b:04d}"
        for a, b in spans
    ]


def main() -> None:
    facts = load_json(FACTS)["pages"]
    cases_raw = load_json(CASES)
    rows = cases_raw if isinstance(cases_raw, list) else cases_raw.get("cases", [])

    # 只对「已有 dcwPage」的实体判定是否已合并过，保证幂等
    merged = 0
    ambiguous = []
    unmatched = []

    for p in facts:
        nums = set(p.get("episodeNumbers") or [])
        if not nums:
            continue
        cands = [r for r in rows if expand(r.get("animeRefs")) & nums]
        if not cands:
            unmatched.append({"page": p["page"], "episodes": sorted(nums)})
            continue
        # 严格对齐：页面集号必须被某个实体的集号完全覆盖
        exact = [r for r in cands if nums <= expand(r.get("animeRefs"))]
        if len(exact) != 1:
            ambiguous.append({
                "page": p["page"],
                "episodes": sorted(nums),
                "candidates": [r["id"] for r in exact or cands][:6],
            })
            continue

        row = exact[0]
        changed = False

        # dcwPage：仅当唯一匹配时才写，避免把错页绑到实体上
        if not row.get("dcwPage"):
            row["dcwPage"] = p["page"]
            changed = True

        cats = set(p.get("categories") or [])
        new_types = [v for k, v in CATEGORY_TO_TYPE.items() if k in cats]
        if p.get("isAnimeExclusive"):
            new_types.append("anime-original")
        cur = row.get("caseType")
        cur_list = cur if isinstance(cur, list) else ([cur] if cur else [])
        if not isinstance(cur, list):
            row["caseType"] = cur_list
            changed = True
        added = [t for t in new_types if t not in cur_list]
        if added:
            row["caseType"] = cur_list + added
            changed = True

        if not row.get("castNames") and p.get("caseCast"):
            row["castNames"] = p["caseCast"]
            changed = True
        if not row.get("solvedBy") and p.get("solvedBy"):
            row["solvedBy"] = p["solvedBy"]
            changed = True
        if not row.get("dcwAirDate") and p.get("airdate"):
            row["dcwAirDate"] = p["airdate"]
            changed = True
        if not row.get("dcwMangaCaseNumber") and p.get("mangaCaseNumber"):
            row["dcwMangaCaseNumber"] = p["mangaCaseNumber"]
            changed = True
        if not row.get("dcwFillerCaseNumber") and p.get("fillerCaseNumber"):
            row["dcwFillerCaseNumber"] = p["fillerCaseNumber"]
            changed = True
        title = row.get("title")
        if isinstance(title, dict) and not title.get("ja") and p.get("jpTitle"):
            title["ja"] = p["jpTitle"]
            changed = True
        if not row.get("mangaRefs") and p.get("mangaFiles"):
            from itertools import groupby  # noqa: F401
            nums_m = sorted(set(p["mangaFiles"]))
            spans = []
            s = pv = nums_m[0]
            for n in nums_m[1:]:
                if n == pv + 1:
                    pv = n
                    continue
                spans.append((s, pv))
                s = pv = n
            spans.append((s, pv))
            row["mangaRefs"] = [
                f"file-{a:03d}" if a == b else f"file-{a:03d}-{b:03d}" for a, b in spans
            ]
            changed = True

        if changed:
            row["updatedAt"] = TODAY
            merged += 1

    if isinstance(cases_raw, dict):
        cases_raw["cases"] = rows
        save_json(CASES, cases_raw)
    else:
        save_json(CASES, rows)

    # 重新统计集覆盖
    cov: set[int] = set()
    for r in rows:
        cov |= expand(r.get("animeRefs"))
    missing = sorted(set(range(1, 1217)) - cov)

    report = {
        "version": 1,
        "generatedAt": TODAY,
        "mergedEntities": merged,
        "ambiguous": ambiguous[:200],
        "ambiguousCount": len(ambiguous),
        "unmatched": unmatched[:200],
        "unmatchedCount": len(unmatched),
        "episodesCovered": len(cov),
        "episodesMissing": len(missing),
        "missingRanges": compress(missing),
        "casesTotal": len(rows),
    }
    save_json(REPORT, report)

    print(f"merged={merged} ambiguous={len(ambiguous)} unmatched={len(unmatched)}")
    print(f"cases={len(rows)} covered={len(cov)}/1216 missing={len(missing)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
