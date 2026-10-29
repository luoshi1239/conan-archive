#!/usr/bin/env python3
"""把 DCW /wiki/Anime 全集表格导入为结构化原始数据，并生成差异报告。

原则（不得违反）：
1. 只搬 DCW 页面 Manga source 列的原文，不做任何反向推断；
2. 不覆盖已有手工核实过的值，冲突一律记入报告交由人工复核；
3. 二次运行必须 edits=0（幂等）。

输入：/tmp/ca/dcw-episodes.json（由 HTMLParser 解析 /wiki/Anime 表格得到）
输出：
  data/raw/dcw-anime-index.json   —— 全量结构化原始索引
  docs/DCW-IMPORT-DIFF.json       —— 与本库 episodes.json 的差异与冲突清单
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPISODES = ROOT / "data" / "episodes" / "episodes.json"
RAW_OUT = ROOT / "data" / "raw" / "dcw-anime-index.json"
DIFF_OUT = ROOT / "docs" / "DCW-IMPORT-DIFF.json"
SRC_JSON = Path("/tmp/ca/dcw-episodes.json")

SOURCE_ID = "src-detective-conan-world-anime"
TODAY = "2026-10-27"

MONTHS = {
    m: i + 1
    for i, m in enumerate(
        [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
    )
}


def load_json(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def parse_air_date(text: str) -> str | None:
    """'May 25, 1998' -> '1998/05/25'"""
    m = re.fullmatch(r"([A-Z][a-z]+)\s+(\d{1,2}),\s*(\d{4})", (text or "").strip())
    if not m:
        return None
    mon, day, year = m.group(1), int(m.group(2)), m.group(3)
    if mon not in MONTHS:
        return None
    return f"{year}/{MONTHS[mon]:02d}/{day:02d}"


def classify_manga_source(raw: str) -> str:
    """把 Manga source 原文归类。只做形态归类，不推断缺失值。"""
    s = (raw or "").strip()
    if not s:
        return "unknown"
    if "Original" in s:
        return "anime-original"
    if s.startswith("SV") or " SV" in s:
        return "manga-special-volume"
    if s.startswith("MKV"):
        return "manga-magic-kaito"
    if s.startswith("V") or re.match(r"^V\d", s):
        return "manga"
    return "unknown"


def extract_file_range(raw: str) -> list[int]:
    """从 'V1 - F2~5(002-005)' 抽出 (002, 003, 004, 005)；抽不出返回 []。"""
    s = raw or ""
    m = re.search(r"\(([\d\-,\s]+)\)\s*$", s)
    nums: list[int] = []
    if m:
        for part in re.split(r"[,\s]+", m.group(1)):
            part = part.strip()
            if not part:
                continue
            rng = re.fullmatch(r"(\d{3,4})-(\d{3,4})", part)
            if rng:
                lo, hi = int(rng.group(1)), int(rng.group(2))
                if lo <= hi and hi - lo <= 20:
                    nums.extend(range(lo, hi + 1))
                    continue
            if part.isdigit():
                nums.append(int(part))
    if not nums:
        # 形如 'V1 ~ F1(001)' 之外的 'SV1 - F6' 没有括号号段，只能从 F 号推
        fm = re.findall(r"F(\d{1,4})", s)
        if len(fm) == 1:
            return []  # 单 File 无法确定全局 File 编号，留空不猜测
    return sorted({n for n in nums if n > 0})


def main() -> None:
    dcw_rows = load_json(SRC_JSON)
    episodes = load_json(EPISODES)
    if isinstance(episodes, dict):
        episodes = episodes.get("episodes", [])

    by_number = {int(e["number"]): e for e in episodes if e.get("number") is not None}
    dcw_by_number = {int(r["jp"]): r for r in dcw_rows}

    raw_index = []
    diffs = {
        "version": 1,
        "generatedAt": TODAY,
        "source": SOURCE_ID,
        "sourceUrl": "https://www.detectiveconanworld.com/wiki/Anime",
        "counts": {},
        "missingInDcw": [],
        "missingInLocal": [],
        "airDateConflicts": [],
        "adaptationConflicts": [],
        "mangaRefWithoutMangaSource": [],
        "notes": [],
    }

    kind_counter: Counter[str] = Counter()

    for number in sorted(dcw_by_number):
        row = dcw_by_number[number]
        kind = classify_manga_source(row["mangaRaw"])
        kind_counter[kind] += 1
        raw_index.append(
            {
                "number": number,
                "id": f"episode-{number:04d}",
                "dcwTitle": row["title"],
                "dcwIntNumber": row["int"],
                "dcwAirDate": row["airDate"],
                "airDateIso": parse_air_date(row["airDate"]),
                "mangaSourceRaw": row["mangaRaw"],
                "mangaSourceKind": kind,
                "mangaFiles": extract_file_range(row["mangaRaw"]),
                "nextConanHint": row["hint"],
                "sources": [SOURCE_ID],
            }
        )

    # ---- 逐集比对 ----
    for number, local in sorted(by_number.items()):
        dcw = dcw_by_number.get(number)
        if dcw is None:
            diffs["missingInDcw"].append(
                {"number": number, "localTitle": (local.get("title") or {}).get("ja")}
            )
            continue

        local_date = local.get("airDate")
        dcw_date = parse_air_date(dcw["airDate"])
        if dcw_date and local_date and dcw_date != local_date:
            diffs["airDateConflicts"].append(
                {"number": number, "local": local_date, "dcw": dcw_date}
            )
        if dcw_date and not local_date:
            local["airDate"] = dcw_date
            srcs = local.setdefault("sources", [])
            if SOURCE_ID not in srcs:
                srcs.append(SOURCE_ID)

        dcw_kind = classify_manga_source(dcw["mangaRaw"])
        local_adapt = local.get("adaptation")
        if dcw_kind in ("manga", "manga-special-volume", "manga-magic-kaito"):
            if local_adapt == "anime-original":
                diffs["adaptationConflicts"].append(
                    {
                        "number": number,
                        "local": local_adapt,
                        "dcw": dcw_kind,
                        "dcwRaw": dcw["mangaRaw"],
                        "localMangaRefs": local.get("mangaRefs") or [],
                        "resolution": "pending-human-review",
                    }
                )
        elif dcw_kind == "anime-original":
            if local_adapt == "manga" or (local.get("mangaRefs") or []):
                diffs["adaptationConflicts"].append(
                    {
                        "number": number,
                        "local": local_adapt,
                        "dcw": dcw_kind,
                        "dcwRaw": dcw["mangaRaw"],
                        "localMangaRefs": local.get("mangaRefs") or [],
                        "resolution": "pending-human-review",
                    }
                )

    for number in sorted(set(dcw_by_number) - set(by_number)):
        diffs["missingInLocal"].append(number)

    diffs["counts"] = {
        "dcwEpisodes": len(dcw_by_number),
        "localEpisodes": len(by_number),
        "mangaSources": sum(
            v for k, v in kind_counter.items()
            if k in ("manga", "manga-special-volume", "manga-magic-kaito")
        ),
        "animeOriginal": kind_counter.get("anime-original", 0),
        "unknownSource": kind_counter.get("unknown", 0),
        "airDateConflicts": len(diffs["airDateConflicts"]),
        "adaptationConflicts": len(diffs["adaptationConflicts"]),
        "missingInDcw": len(diffs["missingInDcw"]),
        "missingInLocal": len(diffs["missingInLocal"]),
    }
    diffs["notes"].append(
        "mangaFiles 仅收录 Manga source 括号内的全局 File 号；"
        "无括号号段（如 'SV1 - F6'）不推算，留空以免造假。"
    )

    dump_json(RAW_OUT, {"version": 1, "source": SOURCE_ID, "episodes": raw_index})
    dump_json(DIFF_OUT, diffs)
    dump_json(EPISODES, episodes)

    print(f"dcw_episodes={len(dcw_by_number)} local={len(by_number)}")
    print(f"manga={diffs['counts']['mangaSources']} anime_original={diffs['counts']['animeOriginal']} unknown={diffs['counts']['unknownSource']}")
    print(f"airDateConflicts={len(diffs['airDateConflicts'])} adaptationConflicts={len(diffs['adaptationConflicts'])}")
    print(f"missingInDcw={len(diffs['missingInDcw'])} missingInLocal={len(diffs['missingInLocal'])}")
    print(f"wrote {RAW_OUT.relative_to(ROOT)} and {DIFF_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
