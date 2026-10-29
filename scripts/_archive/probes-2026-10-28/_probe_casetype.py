#!/usr/bin/env python3
"""M5 前置：列出 caseType 的脏值形态，确定归并规则。"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
cases = json.loads((ROOT / "data/entities/cases.json").read_text(encoding="utf-8"))

# 已知合法标签（从高频值里归纳，先打印全量分布）
ct = Counter()
for c in cases:
    v = c.get("caseType")
    key = tuple(v) if isinstance(v, list) else ("<非列表>", str(v))
    ct[key] += 1

print("=" * 70)
print("caseType 全量分布（按出现次数降序）")
print("=" * 70)
for k, n in ct.most_common():
    print(f"  {n:>4}  {list(k)}")

print()
print("=" * 70)
print("空数组的 25 条 —— 看 kind 能否推出")
print("=" * 70)
for c in cases:
    v = c.get("caseType")
    if v:
        continue
    t = c.get("title") or {}
    name = t.get("zhHans") or t.get("ja") or t.get("en")
    print(f"  {c.get('id')[:42]:<42} kind={str(c.get('kind')):<22} {str(name)[:24]!r}")

print()
print("=" * 70)
print("含 'manga' 但不是 'manga-adaptation' 的")
print("=" * 70)
for c in cases:
    v = c.get("caseType") or []
    if "manga" in v:
        print(f"  {c.get('id')}  {v}")
