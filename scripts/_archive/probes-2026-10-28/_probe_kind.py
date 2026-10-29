#!/usr/bin/env python3
"""M4 前置：查看 kind 为 None 和 动画案件 的具体案件，按 DCW 原文定夺。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


cases = load("data/entities/cases.json")
facts = load("data/raw/dcw-page-facts.json")
by_page = {p["page"]: p for p in facts["pages"]}

print("=" * 70)
print("kind = None 的 5 条")
print("=" * 70)
for c in cases:
    if c.get("kind") is not None:
        continue
    t = c.get("title") or {}
    name = t.get("zhHans") or t.get("ja") or t.get("en")
    page = c.get("dcwPage")
    f = by_page.get(page) if page else None
    print(f"\n  {c.get('id')}")
    print(f"    title = {str(name)[:60]!r}")
    print(f"    dcwPage = {page!r}")
    if f:
        print(f"    mangaSource = {f.get('mangaSource')!r}")
        print(f"    isAnimeExclusive = {f.get('isAnimeExclusive')!r}")
        print(f"    mangaCaseNumber = {f.get('mangaCaseNumber')!r}")
        print(f"    fillerCaseNumber = {f.get('fillerCaseNumber')!r}")
    else:
        print("    ** DCW 页未找到 **")

print()
print("=" * 70)
print("kind = 动画案件 的 14 条")
print("=" * 70)
for c in cases:
    if c.get("kind") != "动画案件":
        continue
    t = c.get("title") or {}
    name = t.get("zhHans") or t.get("ja") or t.get("en")
    page = c.get("dcwPage")
    f = by_page.get(page) if page else None
    ms = f.get("mangaSource") if f else None
    print(f"  {c.get('id')[:40]:<40} ms={str(ms)[:22]:<24} {str(name)[:28]!r}")

print()
print("=" * 70)
print("全库 kind 分布")
print("=" * 70)
from collections import Counter
for k, v in Counter(str(c.get("kind")) for c in cases).most_common():
    print(f"  {k:<24} {v}")
