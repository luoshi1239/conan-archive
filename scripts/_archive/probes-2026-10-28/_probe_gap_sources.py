#!/usr/bin/env python3
"""探测 DCW page facts / sections 能支撑哪些缺口字段。

目标：
  1. 案件 locations 0/792 —— DCW 有地点信息吗？
  2. 案件 summary 45/792 —— 正文段落能提取吗？
  3. 案件 sources 缺 19 个 —— 缺的是什么？
  4. 角色 role/summary/name.ja 只有 14 个 —— 原文有没有？
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


facts = load("data/raw/dcw-page-facts.json")
secs = load("data/raw/dcw-page-sections.json")
cases = load("data/entities/cases.json")
chars = load("data/entities/characters.json")

print("=" * 64)
print("A. page facts 结构")
print("=" * 64)
print("顶层键:", list(facts.keys()))
for k, v in facts.items():
    if isinstance(v, list):
        print(f"  {k}: list[{len(v)}]")
    elif isinstance(v, dict):
        print(f"  {k}: dict[{len(v)}]")
    else:
        print(f"  {k}: {v!r}")

# 找页面容器
pages = None
for k in ("pages", "items", "data"):
    if isinstance(facts.get(k), (list, dict)):
        pages = facts[k]
        break
if pages is None:
    pages = {k: v for k, v in facts.items() if isinstance(v, dict)}
if isinstance(pages, dict):
    page_list = list(pages.values())
    page_names = list(pages.keys())
else:
    page_list = pages
    page_names = [p.get("page") or p.get("name") for p in pages]

print(f"\n页数: {len(page_list)}")
print("单页键:", sorted(page_list[0].keys()))

# 统计每个键的非空率
print("\n各字段非空率:")
tot = len(page_list)
for key in sorted(page_list[0].keys()):
    filled = sum(1 for p in page_list if p.get(key) not in (None, "", [], {}))
    if filled:
        print(f"  {key:<22} {filled}/{tot}")

print()
print("=" * 64)
print("B. 有没有地点相关字段")
print("=" * 64)
LOC_KEYS = ("location", "locations", "place", "places", "setting", "venue")
for key in sorted(page_list[0].keys()):
    if any(w in key.lower() for w in LOC_KEYS):
        print(f"  命中键 {key}")

sample = page_list[0]
print("\n样例页全部键值（前 14 个非空）:")
n = 0
for k, v in sample.items():
    if v in (None, "", [], {}):
        continue
    s = json.dumps(v, ensure_ascii=False)
    print(f"  {k} = {s[:150]}")
    n += 1
    if n >= 14:
        break

print()
print("=" * 64)
print("C. sections 结构（能否提正文）")
print("=" * 64)
print("顶层键:", list(secs.keys())[:8] if isinstance(secs, dict) else type(secs))
sk = list(secs.keys())[0] if isinstance(secs, dict) else None
if sk:
    v = secs[sk]
    print(f"样例 {sk}: type={type(v).__name__}")
    if isinstance(v, dict):
        print("  键:", list(v.keys())[:12])
    elif isinstance(v, list):
        print(f"  长度 {len(v)}")
        if v and isinstance(v[0], dict):
            print("  单元键:", list(v[0].keys()))

print()
print("=" * 64)
print("D. 案件 sources 缺的 19 个")
print("=" * 64)
no_src = [c for c in cases if not c.get("sources")]
print(f"  数量 {len(no_src)}")
for c in no_src[:20]:
    t = c.get("title")
    t = t.get("zhHans") or t.get("ja") or t.get("en") if isinstance(t, dict) else t
    print(f"    {c.get('id')}  {str(t)[:44]}")

print()
print("=" * 64)
print("E. 角色 14 个有 role/summary，133 个没有 —— 原文有吗")
print("=" * 64)
rich = [c for c in chars if c.get("role")]
poor = [c for c in chars if not c.get("role")]
print(f"  有 role: {len(rich)} / 无 role: {len(poor)}")
print("\n  有 role 的样例:")
for c in rich[:2]:
    print(f"    {c.get('id')}")
    print(f"      name={json.dumps(c.get('name'), ensure_ascii=False)[:110]}")
    print(f"      role={str(c.get('role'))[:110]}")
print("\n  无 role 的样例:")
for c in poor[:4]:
    print(f"    {c.get('id')}  name={json.dumps(c.get('name'), ensure_ascii=False)[:90]}")
    print(f"      全部键: {sorted(c.keys())}")

print()
print("=" * 64)
print("F. 角色页在 DCW 有正文吗（抽 3 个无 role 的查）")
print("=" * 64)
# page facts 里找角色页
names_en = []
for c in poor[:3]:
    nm = c.get("name")
    en = nm.get("en") if isinstance(nm, dict) else nm
    names_en.append((c.get("id"), en))
print("  抽查:", names_en)
for cid, en in names_en:
    hits = [p for p in page_names if en and en.replace(" ", "_") in str(p)]
    print(f"    {cid} -> 页命中 {hits[:3]}")
