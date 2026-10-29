#!/usr/bin/env python3
"""把 DCW 已收录、但本地剧集库缺失的已播出集补进 episodes.json。

判定条件（三条同时满足才补）：
  1. DCW 页面 infobox 明确给出 'Episode N'；
  2. N > 本地最大集号；
  3. 页面有 Original airdate，且日期不晚于本地最大集的播出日之后的合理范围
     —— 这里只要求日期存在且可解析，不猜未来集。

不补的情况：
  - 红链页（页面不存在，抓取 403）；
  - 无 airdate；
  - 集号不连续（中间缺集说明数据源不同步，应整体重抓而非单点补）。

幂等：已存在则不重复写。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FACTS = ROOT / "data" / "raw" / "dcw-page-facts.json"
EPISODES = ROOT / "data" / "episodes" / "episodes.json"
REPORT = ROOT / "docs" / "EPISODE-APPEND-REPORT.json"

SRC = "src-detective-conan-world-anime"


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def save(p: Path, obj) -> None:
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11,
    "December": 12,
}


def iso_date(text: str | None) -> str | None:
    if not text:
        return None
    m = re.search(r"([A-Z][a-z]+)\s+(\d{1,2}),\s*(\d{4})", text)
    if not m:
        return None
    mon = MONTHS.get(m.group(1))
    if not mon:
        return None
    return f"{int(m.group(3)):04d}/{mon:02d}/{int(m.group(2)):02d}"


def main() -> None:
    facts = load(FACTS)["pages"]
    raw = load(EPISODES)
    rows = raw if isinstance(raw, list) else raw.get("episodes", [])
    have = {r["number"] for r in rows if isinstance(r.get("number"), int)}
    max_no = max(have)

    added = []
    skipped = []

    for p in facts:
        nums = p.get("episodeNumbers") or []
        if len(nums) != 1:
            continue
        n = nums[0]
        if n in have or n <= max_no:
            continue
        iso = iso_date(p.get("airdate"))
        if not iso:
            skipped.append({"page": p["page"], "episode": n, "reason": "no-airdate"})
            continue
        # 只接受紧邻的下一集（连续补），避免数据源不同步时出现空洞
        if n != max_no + 1:
            skipped.append({
                "page": p["page"], "episode": n, "reason": "not-contiguous",
                "expectedNext": max_no + 1,
            })
            continue

        row = {
            "id": f"episode-{n:04d}",
            "kind": "tv-episode",
            "number": n,
            "overseasNumber": p.get("intEpisode"),
            "title": {
                "ja": p.get("jpTitle"),
                "zhHans": None,
                "zhHant": None,
                "en": p.get("heading"),
                "aliases": [],
            },
            "year": int(iso[:4]),
            "airDate": iso,
            "mangaRefs": [],
            "adaptation": "anime-original" if p.get("isAnimeExclusive") else "manga",
            "arc": None,
            "arcRefs": [],
            "caseRefs": [],
            "locationRefs": [],
            "spoiler": 1,
            "status": "catalog",
            "summary": None,
            "characters": [],
            "organizations": [],
            "locations": [],
            "gadgets": [],
            "caseTypes": [],
            "sources": [SRC],
            "detailStatus": "catalog",
            "coverage": {
                "directory": True,
                "basicFacts": True,
                "structure": False,
                "deepSpoilers": False,
            },
            "raw": {
                "dcwPage": p["page"],
                "dcwMangaSource": p.get("mangaSource"),
                "dcwAirDate": p.get("airdate"),
                "appendedBy": "append-dcw-new-episodes.py",
            },
        }
        rows.append(row)
        have.add(n)
        max_no = n
        added.append({"episode": n, "page": p["page"], "airDate": iso})

    rows.sort(key=lambda r: r.get("number") or 0)
    if isinstance(raw, dict):
        raw["episodes"] = rows
        save(EPISODES, raw)
    else:
        save(EPISODES, rows)

    report = {
        "version": 1,
        "episodesTotal": len(rows),
        "maxNumber": max(rows, key=lambda r: r.get("number") or 0).get("number"),
        "appended": added,
        "skipped": skipped,
    }
    save(REPORT, report)
    print(f"total={len(rows)} max={report['maxNumber']} appended={len(added)} skipped={len(skipped)}")
    for a in added:
        print(f"  + EP.{a['episode']}  {a['airDate']}  {a['page']}")
    for s in skipped:
        print(f"  - skipped EP.{s['episode']} {s['reason']} ({s['page']})")


if __name__ == "__main__":
    main()
