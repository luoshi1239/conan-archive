#!/usr/bin/env python3
"""把 DCW 全集索引的 Manga source 原文回填到 episodes.json，并裁定 SV 特别篇改编标记。

裁定依据（两个独立来源相互印证，非择一）：
  local files.json rawLabel = 'SVFile.2特别篇漫画' / 'SVFile.6特别篇漫画'
  DCW /wiki/Anime Manga source = 'SV1 - F2' / 'SV1 - F6'
  → EP.86、EP.113 均为「特别篇漫画改编」，adaptation 应为 manga；
    此前误标 anime-original，属本地字段错误，不是来源冲突。

幂等：二次运行 edits=0。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPISODES = ROOT / "data" / "episodes" / "episodes.json"
RAW_INDEX = ROOT / "data" / "raw" / "dcw-anime-index.json"
CONFLICTS = ROOT / "docs" / "FACT-CONFLICTS.json"

SOURCE_ID = "src-detective-conan-world-anime"
TODAY = "2026-10-27"

# 已裁定：SV 特别篇漫画改编，本地 adaptation 误标为 anime-original
SV_FIX = {
    86: {
        "rawLabel": "SVFile.2",
        "dcwRaw": "SV1 - F2",
        "note": "特别篇漫画第 1 卷第 2 话改编；DCW Manga source 与本地 files.json rawLabel 互相印证",
    },
    113: {
        "rawLabel": "SVFile.6",
        "dcwRaw": "SV1 - F6",
        "note": "特别篇漫画第 1 卷第 6 话改编；DCW Manga source 与本地 files.json rawLabel 互相印证",
    },
}


def load(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def dump(path: Path, payload) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def main() -> None:
    episodes = load(EPISODES)
    if isinstance(episodes, dict):
        episodes = episodes.get("episodes", [])
    raw_index = load(RAW_INDEX)["episodes"]
    dcw_by_number = {int(r["number"]): r for r in raw_index}

    edits = 0
    for ep in episodes:
        number = ep.get("number")
        if number is None:
            continue
        dcw = dcw_by_number.get(int(number))
        if dcw is None:
            continue

        raw = ep.setdefault("raw", {})
        # 1) 原样搬运 DCW 的 Manga source 文本（纯事实，不做推断）
        if raw.get("dcwMangaSource") != dcw["mangaSourceRaw"]:
            raw["dcwMangaSource"] = dcw["mangaSourceRaw"]
            edits += 1
        if raw.get("dcwMangaKind") != dcw["mangaSourceKind"]:
            raw["dcwMangaKind"] = dcw["mangaSourceKind"]
            edits += 1
        if dcw.get("airDateIso") and raw.get("dcwAirDate") != dcw["dcwAirDate"]:
            raw["dcwAirDate"] = dcw["dcwAirDate"]
            edits += 1

        srcs = ep.setdefault("sources", [])
        if SOURCE_ID not in srcs:
            srcs.append(SOURCE_ID)
            edits += 1

    # 2) 裁定 SV 特别篇
    by_number = {int(e["number"]): e for e in episodes if e.get("number") is not None}
    for number, fix in SV_FIX.items():
        ep = by_number.get(number)
        if ep is None:
            continue
        changed = False
        if ep.get("adaptation") != "manga":
            ep["adaptation"] = "manga"
            changed = True
        raw = ep.setdefault("raw", {})
        if raw.get("specialLabel") != fix["rawLabel"]:
            raw["specialLabel"] = fix["rawLabel"]
            changed = True
        if raw.get("manga") != "特別篇漫畫":
            raw["manga"] = "特別篇漫畫"
            changed = True
        if changed:
            edits += 1

    dump(EPISODES, episodes)

    # 3) 记裁定入 FACT-CONFLICTS
    conflicts = load(CONFLICTS)
    entries = conflicts.get("conflicts", conflicts) if isinstance(conflicts, dict) else conflicts
    existing = {c.get("id") for c in entries} if isinstance(entries, list) else set()
    new_entries = []
    for number, fix in SV_FIX.items():
        cid = f"conflict-ep{number:04d}-sv-special-adaptation"
        if cid in existing:
            continue
        new_entries.append(
            {
                "id": cid,
                "targetId": f"episode-{number:04d}",
                "field": "adaptation",
                "localValue": "anime-original",
                "conflictingValue": "manga（特別篇漫畫改編）",
                "status": "resolved",
                "resolution": "manga",
                "resolutionBasis": [
                    f"本地 data/manga/files.json rawLabel = {fix['rawLabel']}",
                    f"DCW /wiki/Anime Manga source = {fix['dcwRaw']}",
                ],
                "resolutionNote": fix["note"],
                "resolvedAt": TODAY,
            }
        )
    if new_entries and isinstance(entries, list):
        entries.extend(new_entries)
        dump(CONFLICTS, conflicts)

    print(f"edits={edits} conflicts_appended={len(new_entries)}")


if __name__ == "__main__":
    main()
