#!/usr/bin/env python3
"""全库进度核查：按维度统计覆盖率与缺口分布，供排期用。"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


eps = load("data/episodes/episodes.json")
cases = load("data/entities/cases.json")
chars = load("data/entities/characters.json")
orgs = load("data/entities/organizations.json")
gadgets = load("data/entities/gadgets.json")
places = load("data/entities/locations.json")
sources = load("data/sources.json")
conflicts = load("docs/FACT-CONFLICTS.json")


def pct(a, b):
    return f"{a}/{b} ({a * 100 // max(b, 1)}%)"


def has_lang(v, key):
    if isinstance(v, dict):
        return bool((v.get(key) or "").strip())
    return False


print("=" * 62)
print("A. 实体规模")
print("=" * 62)
print(f"剧集   {len(eps)}")
print(f"案件   {len(cases)}")
print(f"角色   {len(chars)}")
print(f"组织   {len(orgs)}")
print(f"道具   {len(gadgets)}")
print(f"地点   {len(places)}")
print(f"实体合计 {len(eps) + len(cases) + len(chars) + len(orgs) + len(gadgets) + len(places)}")
print(f"来源   {len(sources['sources'])}")

print()
print("=" * 62)
print("B. 剧集字段覆盖（分母 1217）")
print("=" * 62)
n = len(eps)
fields = {
    "title.en": lambda e: has_lang(e.get("title"), "en"),
    "title.ja": lambda e: has_lang(e.get("title"), "ja"),
    "title.zhHans": lambda e: has_lang(e.get("title"), "zhHans"),
    "title.zhHant": lambda e: has_lang(e.get("title"), "zhHant"),
    "summary 任意": lambda e: bool(e.get("summary")),
    "summary.en": lambda e: has_lang(e.get("summary"), "en"),
    "summary.ja": lambda e: has_lang(e.get("summary"), "ja"),
    "summary.zhHans": lambda e: has_lang(e.get("summary"), "zhHans"),
    "airDate": lambda e: bool(e.get("airDate")),
    "overseasNumber": lambda e: bool(e.get("overseasNumber")),
    "season": lambda e: e.get("season") is not None,
    "solvedBy": lambda e: bool(e.get("solvedBy")),
    "solvedByRaw": lambda e: bool(e.get("solvedByRaw")),
    "castNames": lambda e: bool(e.get("castNames")),
    "characters(挂接)": lambda e: bool(e.get("characters")),
    "caseRefs": lambda e: bool(e.get("caseRefs")),
}
for k, f in fields.items():
    print(f"  {k:<20} {pct(sum(1 for e in eps if f(e)), n)}")

# 缺 title.zhHans 的集
miss_hans = [e["number"] for e in eps if not has_lang(e.get("title"), "zhHans")]
miss_hant = [e["number"] for e in eps if not has_lang(e.get("title"), "zhHant")]
print(f"\n  缺 title.zhHans: {miss_hans}")
print(f"  缺 title.zhHant: {miss_hant}")

print()
print("=" * 62)
print("C. solvedBy 缺口分类（60 集）")
print("=" * 62)
gap = [e for e in eps if not e.get("solvedBy")]
pure_null = [e["number"] for e in gap if not e.get("solvedByRaw")]
print(f"  总数 {len(gap)}")
print(f"  solvedByRaw 也空: {len(pure_null)} 集 -> {pure_null[:20]}{' ...' if len(pure_null) > 20 else ''}")
named = [(e["number"], e.get("solvedByRaw")) for e in gap if e.get("solvedByRaw")]
print(f"  有原文但无实体: {len(named)}")
for num, raw in named:
    print(f"    EP.{num}: {raw!r}")

print()
print("=" * 62)
print("D. 案件字段覆盖")
print("=" * 62)
cn = len(cases)
cf = {
    "title 任意": lambda c: bool(c.get("title")),
    "title.en": lambda c: has_lang(c.get("title"), "en"),
    "title.ja": lambda c: has_lang(c.get("title"), "ja"),
    "title.zhHans": lambda c: has_lang(c.get("title"), "zhHans"),
    "title.zhHant": lambda c: has_lang(c.get("title"), "zhHant"),
    "characters": lambda c: bool(c.get("characters")),
    "locations": lambda c: bool(c.get("locations")),
    "summary": lambda c: bool(c.get("summary")),
    "resolution": lambda c: bool(c.get("resolution")),
    "deepSpoilers": lambda c: bool(c.get("deepSpoilers")),
    "spoilerNote": lambda c: bool(c.get("spoilerNote")),
    "sources": lambda c: bool(c.get("sources")),
}
for k, f in cf.items():
    print(f"  {k:<20} {pct(sum(1 for c in cases if f(c)), cn)}")

print("\n  detailStatus 分布:")
for k, v in Counter(c.get("detailStatus") for c in cases).most_common():
    print(f"    {k!r:<14} {v}")
print("\n  kind 分布:")
for k, v in Counter(c.get("kind") for c in cases).most_common():
    print(f"    {k!r:<28} {v}")

only_ja = [c for c in cases if has_lang(c.get("title"), "ja")
           and not has_lang(c.get("title"), "zhHans")
           and not has_lang(c.get("title"), "zhHant")]
print(f"\n  案件标题只有日文（无中文）: {len(only_ja)}")

print()
print("=" * 62)
print("E. 角色字段覆盖")
print("=" * 62)
an = len(chars)
for k, f in {
    "name 任意": lambda c: bool(c.get("name")),
    "name.zhHans": lambda c: has_lang(c.get("name"), "zhHans"),
    "name.ja": lambda c: has_lang(c.get("name"), "ja"),
    "name.en": lambda c: has_lang(c.get("name"), "en"),
    "role": lambda c: bool(c.get("role")),
    "summary": lambda c: bool(c.get("summary")),
    "caseRefs": lambda c: bool(c.get("caseRefs")),
    "episodeRefs": lambda c: bool(c.get("episodeRefs")),
}.items():
    print(f"  {k:<16} {pct(sum(1 for c in chars if f(c)), an)}")

print("\n  translationStatus 分布:")
for k, v in Counter(c.get("translationStatus") for c in chars).most_common():
    print(f"    {k!r:<12} {v}")

print()
print("=" * 62)
print("F. 冲突与来源")
print("=" * 62)
for k, v in Counter(c.get("status") for c in conflicts.get("conflicts", conflicts)).most_common():
    print(f"  {k}: {v}")
print(f"  来源类型: ", dict(Counter(s.get("type") for s in sources["sources"])))

print()
print("=" * 62)
print("G. 其他缺口")
print("=" * 62)
all_cast = Counter()
for e in eps:
    for c in e.get("castNames") or []:
        all_cast[c] += 1
names = {c.get("name", {}).get("en") if isinstance(c.get("name"), dict) else c.get("name") for c in chars}
low = {k: v for k, v in all_cast.items() if v < 5}
print(f"  castNames 去重 {len(all_cast)}；出现<5 集 {len(low)}")
print(f"  Detective Boys 出现集数: {all_cast.get('Detective Boys', 0)}")
