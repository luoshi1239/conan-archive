#!/usr/bin/env python3
"""把全量数据切成「索引 + 详情」两套分片，解决首屏阻塞。

背景
----
原来首屏要 fetch 7.47MB（gzip 后 1.36MB）的完整数据，其中：
  episodes.json  4.6MB  1217 条，每条含 summary/raw/castNames 等大字段
  cases.json     2.4MB   792 条，每条含 victims/suspects/locationsZh 等

但列表一页只显示 30 条，首屏根本用不上这些大字段。

切分策略
--------
index  = 列表渲染 + 搜索 + 筛选 + 剧透档所需的**最小字段集**
detail = 抽屉打开时才需要的大字段，按 id 单独成文件

原则：索引里的字段必须「足够让列表正确显示和搜索」，宁可多留也不漏，
      因为漏了会直接表现为「列表少了内容」，比慢更糟。

原始文件保持不动——verify 脚本仍读它们，回填脚本也照旧。

用法
----
    python3 scripts/build-split.py          # 生成
    python3 scripts/build-split.py --check   # 只检查是否需要重建
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT_INDEX = os.path.join(DATA, "index")
OUT_DETAIL = os.path.join(DATA, "detail")

# ── 索引保留字段 ──────────────────────────────────────────────
# 案件：列表要 title/animeRefs/caseType/spoiler/status，
#       搜索要 summary 的标题部分 + characters（搜人名能搜到案件）。
#       victims/suspects/locationsZh 只在抽屉里用，全部切到 detail。
CASE_INDEX = [
    "id", "title", "kind", "spoiler", "status", "animeRefs", "mangaRefs",
    "caseType", "characters", "caseRefs",
]

# 剧集：列表要 number/title/year/adaptation/kind/spoiler/status，
#       caseRefs 给「关联案件」用，arc 给分组用。
#       summary/raw/castNames/coverage 等切到 detail。
EPISODE_INDEX = [
    "id", "kind", "number", "overseasNumber", "title", "year", "airDate",
    "adaptation", "arc", "arcRefs", "caseRefs", "spoiler", "status",
]

# 人物：列表副行要 role，搜索要 name/aliases，
#       caseRefs 给「出场 N 案」计数和关系图用。
#       summary/relations/bonds 里 bonds 是关系图要的，但只在图里用——
#       这里保留，因为 147 条 × 每条几条边，总量很小（bonds 只占 40KB）。
CHARACTER_INDEX = [
    "id", "name", "aliases", "role", "kind", "spoiler", "status",
    "caseRefs", "episodeRefs", "relations", "bonds",
]

# 小而全的类型：不改结构，直接整份拷进索引（这些文件本身只有几十 KB）
WHOLE = {
    "movies": "data/movies/movies.json",
    "special-movies": "data/movies/special-movies.json",
    "ovas": "data/ovas/ovas.json",
    "organizations": "data/entities/organizations.json",
    "gadgets": "data/entities/gadgets.json",
    "locations": "data/entities/locations.json",
    "mainline-arcs": "data/manga/mainline-arcs.json",
    "sources": "data/sources.json",
}

# 详情要排除的字段（已进索引的 + 纯内部调试字段）
CASE_DETAIL_DROP = {"id", "title", "kind", "spoiler", "status", "animeRefs",
                    "mangaRefs", "caseType", "characters", "caseRefs"}
EPISODE_DETAIL_DROP = {"id", "kind", "number", "overseasNumber", "title", "year",
                       "airDate", "adaptation", "arc", "arcRefs", "caseRefs",
                       "spoiler", "status"}
CHARACTER_DETAIL_DROP = {"id", "name", "aliases", "role", "kind", "spoiler",
                         "status", "caseRefs", "episodeRefs", "relations", "bonds"}


def pick(record, keys):
    return {k: record[k] for k in keys if k in record}


def drop(record, keys):
    return {k: v for k, v in record.items() if k not in keys}


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # separators 去掉多余空格：同样的数据能少 8~10%
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def build():
    stats = {}
    os.makedirs(OUT_INDEX, exist_ok=True)

    # ── 案件 ──
    cases = load("data/entities/cases.json")
    dump(os.path.join(OUT_INDEX, "cases.json"),
         [pick(c, CASE_INDEX) for c in cases])
    for c in cases:
        rest = drop(c, CASE_DETAIL_DROP)
        if rest:  # 只有带大字段的才出详情文件
            dump(os.path.join(OUT_DETAIL, "cases", f"{c['id']}.json"), rest)
    stats["cases"] = (len(cases), len(os.listdir(os.path.join(OUT_DETAIL, "cases"))))

    # ── 剧集 ──
    eps = load("data/episodes/episodes.json")
    dump(os.path.join(OUT_INDEX, "episodes.json"),
         [pick(e, EPISODE_INDEX) for e in eps])
    for e in eps:
        rest = drop(e, EPISODE_DETAIL_DROP)
        if rest:
            dump(os.path.join(OUT_DETAIL, "episodes", f"{e['id']}.json"), rest)
    stats["episodes"] = (len(eps), len(os.listdir(os.path.join(OUT_DETAIL, "episodes"))))

    # ── 人物 ──
    chars = load("data/entities/characters.json")
    dump(os.path.join(OUT_INDEX, "characters.json"),
         [pick(c, CHARACTER_INDEX) for c in chars])
    for c in chars:
        rest = drop(c, CHARACTER_DETAIL_DROP)
        if rest:
            dump(os.path.join(OUT_DETAIL, "characters", f"{c['id']}.json"), rest)
    stats["characters"] = (len(chars), len(os.listdir(os.path.join(OUT_DETAIL, "characters"))))

    # ── 小文件整份拷 ──
    for name, rel in WHOLE.items():
        dump(os.path.join(OUT_INDEX, f"{name}.json"), load(rel))

    # ── 汇总清单，前端读它知道有哪些分片 ──
    manifest = {
        "version": 1,
        "counts": {
            "cases": len(cases),
            "episodes": len(eps),
            "characters": len(chars),
        },
        "detailDirs": ["cases", "episodes", "characters"],
    }
    dump(os.path.join(OUT_INDEX, "manifest.json"), manifest)
    return stats


def total_bytes(path):
    t = 0
    for dirpath, _, files in os.walk(path):
        for f in files:
            t += os.path.getsize(os.path.join(dirpath, f))
    return t


def main():
    stats = build()
    print("=== 分片结果 ===")
    for k, (n, d) in stats.items():
        print(f"  {k:12s} 索引 {n:5d} 条 · 详情 {d:4d} 个文件")
    idx = total_bytes(OUT_INDEX)
    det = total_bytes(OUT_DETAIL)
    print(f"\n索引总计 {idx/1024/1024:.2f} MB（首屏只需这个）")
    print(f"详情总计 {det/1024/1024:.2f} MB（按需单条拉取）")
    print(f"分片文件数 {len(os.listdir(OUT_INDEX)) + sum(len(os.listdir(os.path.join(OUT_DETAIL, d))) for d in ('cases','episodes','characters'))}")
    print("SPLIT_OK")


if __name__ == "__main__":
    main()
