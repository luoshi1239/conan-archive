#!/usr/bin/env python3
"""M7 前置：Location 行能覆盖多少案件，以及值的长相分布。"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sections = json.loads((ROOT / "data/raw/dcw-page-sections.json").read_text(encoding="utf-8"))["pages"]
cases = json.loads((ROOT / "data/entities/cases.json").read_text(encoding="utf-8"))

LAB = re.compile(r"^Location:\s*(.+)$")


def locs_of(page):
    sec = sections.get(page)
    if not sec:
        return []
    out = []
    for key in ("situation", "resolution"):
        for raw in sec.get(key) or []:
            m = LAB.match(str(raw).strip())
            if m:
                v = m.group(1).strip()
                if v and v not in out:
                    out.append(v)
    return out


have_key = sum(1 for c in cases if "locations" in c)
print(f"案件里已存在 locations 键: {have_key} / {len(cases)}")

hit = 0
multi = 0
no_page = 0
samples = []
for c in cases:
    page = c.get("dcwPage")
    if not page:
        no_page += 1
        continue
    got = locs_of(page)
    if got:
        hit += 1
        if len(got) > 1:
            multi += 1
        if len(samples) < 8:
            samples.append((c["id"], got))
    else:
        pass

print(f"可补 locations 的案件: {hit}")
print(f"  其中多地点: {multi}")
print(f"  无 dcwPage: {no_page}")
print(f"  页面无 Location 行: {len(cases) - hit - no_page}")

print("\n样本:")
for cid, got in samples:
    print(f"  {cid[:44]:<44} {got}")
