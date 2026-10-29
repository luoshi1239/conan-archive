#!/usr/bin/env python3
"""M5 前置二：统计 caseType 缺来源标签的条目，以及 25 条空数组的 kind 分布。"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
cases = json.loads((ROOT / "data/entities/cases.json").read_text(encoding="utf-8"))

SRC = {"anime-original", "manga-adaptation"}

empty = [c for c in cases if not c.get("caseType")]
print(f"空数组: {len(empty)}")
print("  kind 分布:", Counter(str(c.get("kind")) for c in empty).most_common())

no_src = []
for c in cases:
    v = c.get("caseType") or []
    if v and not (set(v) & SRC):
        no_src.append(c)

print(f"\n有标签但缺来源标签: {len(no_src)}")
print("  kind 分布:", Counter(str(c.get("kind")) for c in no_src).most_common())
for c in no_src[:12]:
    t = c.get("title") or {}
    name = t.get("zhHans") or t.get("ja") or t.get("en")
    print(f"  {c.get('id')[:44]:<44} kind={str(c.get('kind')):<22} {c.get('caseType')}")

alias = [c for c in cases if "manga" in (c.get("caseType") or [])]
print(f"\n别名 'manga': {len(alias)}")
for c in alias:
    print(f"  {c.get('id')}  {c.get('caseType')}")
