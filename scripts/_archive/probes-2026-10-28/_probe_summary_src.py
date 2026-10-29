#!/usr/bin/env python3
"""M1 前置：dcw-page-sections 的段落形态、页名对应、可覆盖量。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


secs = load("data/raw/dcw-page-sections.json")
cases = load("data/entities/cases.json")

pages = secs["pages"]
print("sections.pages 类型:", type(pages).__name__, "数量:", len(pages))

# 取一个具体页看结构
name = pages[0]["page"] if isinstance(pages, list) else list(pages)[0]
one = pages[0] if isinstance(pages, list) else pages[name]
print(f"\n样例页: {name}")
print("键:", sorted(one.keys()))
for k, v in one.items():
    if k == "page":
        continue
    if isinstance(v, list):
        print(f"  {k}: list[{len(v)}]")
        for i, para in enumerate(v[:2]):
            print(f"    [{i}] {str(para)[:150]}")
    elif isinstance(v, str):
        print(f"  {k}: str({len(v)}) {v[:120]!r}")
    else:
        print(f"  {k}: {type(v).__name__} {v}")

# 页名集合
if isinstance(pages, list):
    sec_by_page = {p["page"]: p for p in pages if "page" in p}
else:
    sec_by_page = pages

print(f"\nsec_by_page: {len(sec_by_page)} 页")

# 案件覆盖统计
has_sum = [c for c in cases if c.get("summary")]
no_sum = [c for c in cases if not c.get("summary")]
print(f"\n案件 summary: 有 {len(has_sum)} / 无 {len(no_sum)}")

hit_sit = 0
hit_res = 0
hit_none = []
for c in no_sum:
    page = c.get("dcwPage")
    sec = sec_by_page.get(page) if page else None
    if not sec:
        hit_none.append((c.get("id"), page))
        continue
    sit = sec.get("situation") or []
    res = sec.get("resolution") or []
    if sit:
        hit_sit += 1
    elif res:
        hit_res += 1
    else:
        hit_none.append((c.get("id"), page))

print(f"  可用 situation: {hit_sit}")
print(f"  仅 resolution: {hit_res}")
print(f"  无正文: {len(hit_none)}")
for cid, page in hit_none[:10]:
    print(f"    {cid}  page={page!r}")

# 有 summary 的 45 条是什么形态
print("\n有 summary 的样例（确认是人工中文，不可覆盖）:")
for c in has_sum[:3]:
    s = c["summary"]
    print(f"  {c['id']}")
    print(f"    {json.dumps(s, ensure_ascii=False)[:160]}")
