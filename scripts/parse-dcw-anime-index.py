#!/usr/bin/env python3
"""把 DCW /wiki/Anime 剧集总表解析成结构化 JSON。

来源：https://www.detectiveconanworld.com/wiki/Anime（已存 /tmp/dcw_anime.md）
表结构（8 列）：
    Jp# | Int# | Episode title | Original broadcast | English dub broadcast
        | Plot | Manga source | Next Conan's Hint

输出 data/raw/dcw-anime-index.json：
    {"source": "...", "fetchedAt": "...", "rows": [{...}]}

只做解析，不碰任何数据文件。
"""
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

SRC = Path("/tmp/dcw_anime.md")
OUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "dcw-anime-index.json"

# markdown 转义还原
UNESCAPE = [
    ("\\-", "-"), ("\\(", "("), ("\\)", ")"), ("\\[", "["), ("\\]", "]"),
    ("\\'", "'"), ("\\*", "*"), ("\\!", "!"), ("\\_", "_"), ("\\&", "&"),
    ("\\.", "."), ("\\,", ","), ("\\#", "#"), ("\\/", "/"), ("\\\\", "\\"),
]

LINK = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
ITALIC = re.compile(r"^\*(.+)\*$")


def unesc(text: str) -> str:
    for a, b in UNESCAPE:
        text = text.replace(a, b)
    return text.strip()


def parse_title_cell(cell: str):
    """返回 (title, wiki_url)。标题可能是 *[X](url)* / [X](url) / *X* / X。"""
    raw = cell.strip()
    italic = bool(ITALIC.match(raw))
    if italic:
        raw = ITALIC.match(raw).group(1).strip()

    m = LINK.search(raw)
    if m:
        title = unesc(m.group(1))
        url = m.group(2)
    else:
        title = unesc(raw)
        url = None
    return title or None, url, italic


def parse_date(cell: str):
    """'August 14, 2010' → '2010-08-14'；解析不了返回 (None, raw)。"""
    raw = unesc(cell)
    if not raw or raw in ("", "TBA", "TBD"):
        return None, raw or None
    m = re.search(r"([A-Z][a-z]+)\s+(\d{1,2}),\s*(\d{4})", raw)
    if m:
        try:
            dt = datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%B %d %Y")
            return dt.strftime("%Y-%m-%d"), raw
        except ValueError:
            pass
    return None, raw


def parse_int(cell: str):
    """Int# 单元格：`583`、`11-12`（范围）、空。

    返回 (首个国际集号, 全部国际集号列表)。
    """
    raw = unesc(cell)
    if not raw:
        return None, []
    m = re.match(r"^(\d+)(?:\s*-\s*(\d+))?$", raw)
    if not m:
        return None, []
    start = int(m.group(1))
    if m.group(2):
        end = int(m.group(2))
        if end >= start and end - start < 20:
            return start, list(range(start, end + 1))
        return start, [start]
    return start, [start]


# 集号单元格三种形态：`583`、`1029 WPS1`（警察学校编）、`R133 WPS5`（重播）
JP_CELL = re.compile(r"^(R)?(\d+)(?:\s+WPS(\d+))?$")


def parse_jp_cell(cell: str):
    """返回 (jpNumber, wps序号, isRerun)。"""
    raw = unesc(cell)
    m = JP_CELL.match(raw)
    if not m:
        return None, None, False
    rerun = bool(m.group(1))
    num = int(m.group(2))
    wps = int(m.group(3)) if m.group(3) else None
    return num, wps, rerun


def main():
    if not SRC.exists():
        raise SystemExit(f"缺输入文件 {SRC}")
    lines = SRC.read_text(encoding="utf-8", errors="replace").splitlines()

    rows = []
    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            continue
        parts = [p.strip() for p in s.strip("|").split("|")]
        if len(parts) < 8:
            continue
        jp, wps, rerun = parse_jp_cell(parts[0])
        if jp is None:  # 表头/分隔行
            continue

        title, url, italic = parse_title_cell(parts[2])
        if not title:
            continue

        air, air_raw = parse_date(parts[3])
        dub, dub_raw = parse_date(parts[4])
        int_num, int_nums = parse_int(parts[1])

        rows.append({
            "jpNumber": jp,
            "intNumber": int_num,
            "intNumbers": int_nums,
            "titleEn": title,
            "titleItalic": italic,
            "page": unquote(url.split("/wiki/")[-1]) if url and "/wiki/" in url else None,
            "airDate": air,
            "airDateRaw": air_raw,
            "dubDate": dub,
            "dubDateRaw": dub_raw,
            "mangaSource": unesc(parts[6]) if len(parts) > 6 else None,
            "hint": unesc(parts[7]) if len(parts) > 7 else None,
            "wps": wps,
            "rerun": rerun,
        })

    # 去重：正片优先于重播；同集多条正片时保留首个
    seen = {}
    dups = []
    reruns = []
    for r in rows:
        key = r["jpNumber"]
        if key in seen:
            if r["rerun"] and not seen[key]["rerun"]:
                reruns.append(key)  # 重播行，丢弃
                continue
            if seen[key]["rerun"] and not r["rerun"]:
                dups.append(key)
                seen[key] = r  # 正片替换重播
                continue
            dups.append(key)
            continue
        seen[key] = r
    rows = [seen[k] for k in sorted(seen)]

    data = {
        "source": "https://www.detectiveconanworld.com/wiki/Anime",
        "sourceId": "src-detective-conan-world-anime",
        "fetchedAt": datetime.now().strftime("%Y-%m-%d"),
        "note": "DCW 剧集总表逐集原文；titleEn 为英文标题，page 为标题链接目标（即该集所属页面）",
        "rowCount": len(rows),
        "duplicates": dups,
        "rows": rows,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"解析行数 {len(rows)}，重复 Jp# {len(dups)} 个")
    print(f"有 titleEn  {sum(1 for r in rows if r['titleEn'])}")
    print(f"有 intNumber {sum(1 for r in rows if r['intNumber'])}")
    print(f"有 airDate  {sum(1 for r in rows if r['airDate'])}")
    print(f"有 page     {sum(1 for r in rows if r['page'])}")
    print(f"集号范围 {rows[0]['jpNumber']} – {rows[-1]['jpNumber']}")
    print()
    print("样例：")
    for r in rows:
        if r["jpNumber"] in (583, 584, 585, 586, 587):
            print(f"  {r['jpNumber']:4d} int={r['intNumber']} | {r['titleEn'][:44]:44s} | {r['page']}")
    print()
    print("缺 airDate 的：", [r["jpNumber"] for r in rows if not r["airDate"]][:20])
    print("缺 page 的：", [r["jpNumber"] for r in rows if not r["page"]][:20])


if __name__ == "__main__":
    main()
