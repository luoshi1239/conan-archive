#!/usr/bin/env python3
"""探：sections 正文里的 "Location:" / "Victim:" 等条目行，能否支撑 locations 字段。"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sections = json.loads((ROOT / "data/raw/dcw-page-sections.json").read_text(encoding="utf-8"))["pages"]
cases = json.loads((ROOT / "data/entities/cases.json").read_text(encoding="utf-8"))

LABEL = re.compile(r"^([A-Z][A-Za-z /]{2,24}):\s*(.+)$")

labels = Counter()
pages_with_loc = 0
samples = []

for page, sec in sections.items():
    found_loc = None
    for key in ("situation", "resolution"):
        for raw in sec.get(key) or []:
            s = str(raw).strip()
            m = LABEL.match(s)
            if not m:
                continue
            lab, val = m.group(1).strip(), m.group(2).strip()
            labels[lab] += 1
            if lab.lower() in ("location", "place", "setting") and found_loc is None:
                found_loc = val
    if found_loc:
        pages_with_loc += 1
        if len(samples) < 10:
            samples.append((page, found_loc))

print(f"sections 页数: {len(sections)}")
print(f"含 Location 类条目的页: {pages_with_loc}")
print("\n出现最多的条目标签:")
for lab, n in labels.most_common(15):
    print(f"  {lab:<22} {n}")

print("\nLocation 样本:")
for page, loc in samples:
    print(f"  {page:<48} -> {loc!r}")

# 这些页对应多少案件
page_set = {p for p, _ in samples}
case_pages = {c.get("dcwPage") for c in cases if c.get("dcwPage")}
print(f"\n案件覆盖：{len(page_set & case_pages)} / {len(cases)}（样本口径，非全量）")
