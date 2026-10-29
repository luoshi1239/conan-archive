#!/usr/bin/env python3
"""M2 前置：sources 结构 + 19 条缺来源案件的可匹配页。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


cases = load("data/entities/cases.json")
facts = load("data/raw/dcw-page-facts.json")
by_page = {p["page"]: p for p in facts["pages"]}

print("=" * 70)
print("现有 sources 形态（抽样 3 条）")
print("=" * 70)
n = 0
for c in cases:
    if c.get("sources"):
        print(f"  {c['id']}")
        print(f"    {json.dumps(c['sources'], ensure_ascii=False)}")
        n += 1
        if n >= 3:
            break

print()
print("=" * 70)
print("缺 sources 的案件 —— 逐条查可匹配页")
print("=" * 70)
eps_to_page = {}
for p in facts["pages"]:
    for e in p.get("episodeNumbers") or []:
        if isinstance(e, int):
            eps_to_page.setdefault(e, set()).add(p["page"])


def parse_refs(refs):
    out = []
    for r in refs or []:
        if not isinstance(r, str) or not r.startswith("episode-"):
            continue
        body = r[len("episode-"):]
        parts = body.split("-")
        try:
            if len(parts) == 1:
                out.append(int(parts[0]))
            elif len(parts) == 2:
                out.extend(range(int(parts[0]), int(parts[1]) + 1))
        except ValueError:
            pass
    return out


no_src = [c for c in cases if not c.get("sources")]
print(f"共 {len(no_src)} 条\n")
for c in no_src:
    t = c.get("title") or {}
    name = t.get("zhHans") or t.get("ja") or t.get("en")
    page = c.get("dcwPage")
    en = (t.get("en") or "").strip().lower()

    by_title = None
    if en:
        for pn, f in by_page.items():
            if (f.get("heading") or "").strip().lower() == en:
                by_title = pn
                break
    if by_title is None and en:
        for pn, f in by_page.items():
            h = (f.get("heading") or "").strip().lower()
            if len(h) >= 20 and en.startswith(h):
                by_title = pn
                break

    nums = parse_refs(c.get("animeRefs"))
    hits = set()
    for x in nums:
        hits |= eps_to_page.get(x, set())
    by_eps = hits.pop() if len(hits) == 1 else None

    print(f"  {c['id'][:44]:<44}")
    print(f"    dcwPage={page!r}  按标题={by_title!r}  按集号={by_eps!r}")
    print(f"    标题={str(name)[:40]!r}")
