#!/usr/bin/env python3
"""从 DCW 页面事实生成案件实体骨架，并回填 episodes.caseRefs。

铁律
====
1. caseType 只来自页面 Category 白名单映射，绝不用标题关键词猜测。
2. 不写 culprit / motive / method / evidence / resolution —— 这些要读正文，
   属于后续 L3 流水线，本脚本一律不碰。
3. 不新建 character 实体；caseCast 以 castNames 原文（英文）原样保留，
   等角色库扩充后再关联，避免为龙套造实体。
4. 幂等：第二次运行 cases_added=0、episode_refs_added=0。
5. 已有实体（人工核实过的 51 个）不覆盖，只补缺失的 animeRefs / mangaRefs。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FACTS = ROOT / "data" / "raw" / "dcw-page-facts.json"
CASES = ROOT / "data" / "entities" / "cases.json"
EPISODES = ROOT / "data" / "episodes" / "episodes.json"
REPORT = ROOT / "docs" / "CASE-GENERATION-REPORT.json"

TODAY = "2026-10-27"

# Category -> caseType，白名单。未列出的分类一律丢弃（不猜）。
CATEGORY_TO_TYPE = {
    "Locked Room Cases": "locked-room",
    "Serial Murder Cases": "serial-murder",
    "Closed Circle of Suspects": "closed-circle",
    "Impossible Crime Cases": "impossible-crime",
    "Mystery Tour Case": "mystery-tour",
}

# 纯地点类分类 -> locationRefs 候选（保留原文，不造地点实体）
PREFECTURES = {
    "Gunma Prefecture", "Shizuoka Prefecture", "Kanagawa Prefecture",
    "Nagano Prefecture", "Yamanashi Prefecture", "Osaka Prefecture",
    "Yamaguchi Prefecture", "Kyoto Prefecture", "Yamagata Prefecture",
    "Hyogo Prefecture", "Shimane Prefecture", "Saitama Prefecture",
    "Okinawa Prefecture", "Tottori Prefecture", "Ishikawa Prefecture",
    "Gifu Prefecture", "Okayama Prefecture", "Nagasaki Prefecture",
    "Chiba Prefecture", "Fukuoka Prefecture", "Hokkaido",
    "Fukui Prefecture", "Kumamoto Prefecture", "Tochigi Prefecture",
    "Kagoshima Prefecture", "Toyama Prefecture", "Ibaraki Prefecture",
    "Fukushima Prefecture", "Oita Prefecture", "Miyagi Prefecture",
    "Aichi Prefecture", "Wakayama Prefecture",
}


def load_json(p: Path):
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(p: Path, obj) -> None:
    with p.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def slug(page: str) -> str:
    s = page.replace("_", "-").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def ep_ref(n: int) -> str:
    return f"episode-{n:04d}"


def compress_ranges(nums: list[int]) -> list[str]:
    """[1,2,3,11,12] -> ['episode-0001-0003', 'episode-0011-0012']"""
    if not nums:
        return []
    nums = sorted(set(nums))
    out = []
    start = prev = nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
            continue
        out.append((start, prev))
        start = prev = n
    out.append((start, prev))
    return [
        ep_ref(a) if a == b else f"episode-{a:04d}-{b:04d}"
        for a, b in out
    ]


def file_refs(files: list[int]) -> list[str]:
    return compress_files(files)


def compress_files(nums: list[int]) -> list[str]:
    if not nums:
        return []
    nums = sorted(set(nums))
    out = []
    start = prev = nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
            continue
        out.append((start, prev))
        start = prev = n
    out.append((start, prev))
    return [
        f"file-{a:03d}" if a == b else f"file-{a:03d}-{b:03d}"
        for a, b in out
    ]


def main() -> None:
    facts = load_json(FACTS)["pages"]
    # 回退映射：部分多集主线页面的 infobox 没有 'Episode N' 行，
    # 但 DCW /wiki/Anime 剧集表的标题链接本身就给出了 集号 -> 页面。
    # 这不是推断，是同一来源另一页面的显式声明。
    page_map_path = Path("/tmp/ca/dcw-page-map.json")
    ep2pages: dict[str, list[str]] = {}
    page2eps_extra: dict[str, list[int]] = {}
    if page_map_path.exists():
        pm = load_json(page_map_path)
        ep2pages = pm.get("ep2pages", {})
        for num_s, pages in ep2pages.items():
            try:
                n = int(num_s)
            except ValueError:
                continue
            for pg in pages:
                page2eps_extra.setdefault(pg, []).append(n)

    for p in facts:
        if not p.get("episodeNumbers"):
            extra = sorted(page2eps_extra.get(p["page"], []))
            if extra:
                p["episodeNumbers"] = extra
                p["episodeNumbersSource"] = "dcw-anime-table-link"
    
    cases_raw = load_json(CASES)
    case_rows = cases_raw if isinstance(cases_raw, list) else cases_raw.get("cases", [])
    ep_raw = load_json(EPISODES)
    ep_rows = ep_raw if isinstance(ep_raw, list) else ep_raw.get("episodes", [])
    ep_by_num = {r["number"]: r for r in ep_rows if isinstance(r.get("number"), int)}

    existing_by_id = {r["id"]: r for r in case_rows}

    # 现有实体已声明的集号（展开区间），用于避免重复占位
    claimed: dict[int, str] = {}
    for r in case_rows:
        for ref in r.get("animeRefs", []) or []:
            m = re.match(r"episode-(\d{4})(?:-(\d{4}))?$", ref)
            if not m:
                continue
            a = int(m.group(1))
            b = int(m.group(2)) if m.group(2) else a
            for n in range(a, b + 1):
                claimed.setdefault(n, r["id"])

    cases_added = 0
    cases_skipped_nodata = 0
    type_mapped = 0
    conflicts = []

    for p in facts:
        nums = p.get("episodeNumbers") or []
        if not nums:
            cases_skipped_nodata += 1
            continue

        cid = "case-" + slug(p["page"])
        cats = set(p.get("categories") or [])

        types = [v for k, v in CATEGORY_TO_TYPE.items() if k in cats]
        if p.get("isAnimeExclusive"):
            types.append("anime-original")
        elif p.get("mangaFiles"):
            types.append("manga-adaptation")

        locs = sorted(c for c in cats if c in PREFECTURES)

        # 集号部分被占用时，只认领尚未被占用的集号。
        # 全被占用才跳过（那才是重复页面）。
        free = [n for n in nums if n not in claimed]

        new_anime = compress_ranges(free)
        new_manga = file_refs(p.get("mangaFiles") or [])

        if cid in existing_by_id:
            row = existing_by_id[cid]
            changed = False
            if not row.get("animeRefs") and new_anime:
                row["animeRefs"] = new_anime
                changed = True
            if not row.get("mangaRefs") and new_manga:
                row["mangaRefs"] = new_manga
                changed = True
            if changed:
                row["updatedAt"] = TODAY
            continue

        if not free:
            conflicts.append({
                "page": p["page"],
                "episodes": nums,
                "claimedBy": sorted({claimed[n] for n in nums}),
                "action": "skipped-new-entity",
            })
            continue
        partial = sorted({claimed[n] for n in nums if n in claimed})

        if partial:
            conflicts.append({
                "page": p["page"],
                "episodes": nums,
                "claimedBy": partial,
                "action": "partial-claim",
                "claimedFree": free,
            })

        row = {
            "id": cid,
            "title": {"en": p.get("heading") or p["page"].replace("_", " ")},
            "kind": "anime-original-case" if p.get("isAnimeExclusive") else "manga-case",
            "spoiler": 2,
            "status": "catalog",
            "animeRefs": new_anime,
            "mangaRefs": new_manga,
            "caseType": types or [],
            "castNames": p.get("caseCast") or [],
            "solvedBy": p.get("solvedBy"),
            "sources": ["src-detective-conan-world-anime"],
            "relatedEpisodes": [ep_ref(n) for n in sorted(set(free))],
            "dcwPage": p["page"],
            "updatedAt": TODAY,
        }
        if p.get("mangaCaseNumber"):
            row["dcwMangaCaseNumber"] = p["mangaCaseNumber"]
        if p.get("fillerCaseNumber"):
            row["dcwFillerCaseNumber"] = p["fillerCaseNumber"]
        if p.get("jpTitle"):
            row["title"]["ja"] = p["jpTitle"]
        if locs:
            row["dcwPrefectures"] = locs
        if p.get("airdate"):
            row["dcwAirDate"] = p["airdate"]

        case_rows.append(row)
        existing_by_id[cid] = row
        cases_added += 1
        if types:
            type_mapped += 1
        for n in free:
            claimed.setdefault(n, cid)

    if isinstance(cases_raw, dict):
        cases_raw["cases"] = case_rows
        save_json(CASES, cases_raw)
    else:
        save_json(CASES, case_rows)

    # ---- 回填 episodes.caseRefs ----
    ep_refs_added = 0
    for num, cid in sorted(claimed.items()):
        ep = ep_by_num.get(num)
        if not ep:
            continue
        refs = ep.get("caseRefs")
        if not isinstance(refs, list):
            refs = []
        if cid in refs:
            continue
        refs.append(cid)
        ep["caseRefs"] = refs
        ep_refs_added += 1

    save_json(EPISODES, ep_raw)

    covered = sum(1 for r in case_rows)
    report = {
        "version": 1,
        "generatedAt": TODAY,
        "pagesProcessed": len(facts),
        "casesTotal": len(case_rows),
        "casesAdded": cases_added,
        "casesSkippedNoEpisodeData": cases_skipped_nodata,
        "casesWithMappedType": type_mapped,
        "episodesClaimed": len(claimed),
        "episodeRefsAdded": ep_refs_added,
        "conflicts": conflicts[:200],
        "conflictCount": len(conflicts),
    }
    save_json(REPORT, report)

    print(f"pages={len(facts)} cases_total={len(case_rows)} cases_added={cases_added}")
    print(f"skipped_no_ep_data={cases_skipped_nodata} with_type={type_mapped}")
    print(f"episodes_claimed={len(claimed)}/{len(ep_rows)} episode_refs_added={ep_refs_added}")
    print(f"conflicts={len(conflicts)}")
    print(f"wrote {CASES.relative_to(ROOT)} / {EPISODES.relative_to(ROOT)} / {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
