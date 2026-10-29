#!/usr/bin/env python3
"""最后一批探测：sections 能否提案件正文 + 19 个缺来源案件能否补 + episodeRefs 可行性。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


secs = load("data/raw/dcw-page-sections.json")
facts = load("data/raw/dcw-page-facts.json")
cases = load("data/entities/cases.json")
eps = load("data/episodes/episodes.json")

print("=" * 60)
print("A. sections 单页结构")
print("=" * 60)
print("stats:", json.dumps(secs["stats"], ensure_ascii=False))
pages = secs["pages"]
print(f"pages 类型 {type(pages).__name__}, 数量 {len(pages)}")
first = pages[0] if isinstance(pages, list) else pages[list(pages)[0]]
print("单页键:", sorted(first.keys()) if isinstance(first, dict) else type(first))
if isinstance(first, dict):
    for k, v in first.items():
        s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
        print(f"  {k} = {s[:110]}")

print()
print("=" * 60)
print("B. 45 个有 summary 的案件 vs 747 个没有")
print("=" * 60)
has = [c for c in cases if c.get("summary")]
no = [c for c in cases if not c.get("summary")]
print(f"有 {len(has)} / 无 {len(no)}")
c = has[0]
print("有 summary 的样例:", c.get("id"))
print("  summary 结构:", json.dumps(c.get("summary"), ensure_ascii=False)[:220])

print()
print("=" * 60)
print("C. 案件 → 剧集映射可用吗（能否借剧集 summary）")
print("=" * 60)
k = cases[0]
print("案件键:", sorted(k.keys()))
print("剧集号字段:", [x for x in k if "pisode" in x or "number" in x.lower()])

mapped = 0
for c in cases:
    refs = c.get("episodes") or c.get("episodeNumbers") or []
    if refs:
        mapped += 1
print(f"带剧集引用的案件: {mapped}/{len(cases)}")

print()
print("=" * 60)
print("D. 19 个缺来源案件 —— 能否按标题匹配 DCW 页")
print("=" * 60)
no_src = [c for c in cases if not c.get("sources")]
fact_pages = {p["page"]: p for p in facts["pages"]}
fact_heads = {p["heading"].strip().lower(): p for p in facts["pages"]}
en_titles = {}
for p in facts["pages"]:
    en_titles[p["heading"].strip().lower()] = p

hit = 0
for c in no_src:
    t = c.get("title") or {}
    ja = (t.get("ja") or "").strip()
    en = (t.get("en") or "").strip()
    m = None
    if en and en.lower() in en_titles:
        m = en_titles[en.lower()]
    print(f"  {c.get('id')[:38]:<38} ja={ja[:26]!r:<28} en={en[:30]!r}")
    if m:
        hit += 1
print(f"\n  标题精确命中 DCW 页: {hit}/{len(no_src)}")

print()
print("=" * 60)
print("E. episodeRefs 可行性（本地反推）")
print("=" * 60)
ref = {}
for e in eps:
    for cid in e.get("characters") or []:
        ref.setdefault(cid, []).append(e["number"])
print(f"可反推出 episodeRefs 的角色: {len(ref)}")
multi = sorted(((len(v), k) for k, v in ref.items()), reverse=True)
for n, cid in multi[:5]:
    print(f"  {cid} -> {n} 集")
print(f"caseRefs 已有 145/147，episodeRefs 现在 0/147 → 可补 {len(ref)}")
