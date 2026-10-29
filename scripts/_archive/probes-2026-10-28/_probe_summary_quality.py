#!/usr/bin/env python3
"""M1 质量抽检：打印合成后的 summary 样本，人眼确认。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib.machinery import SourceFileLoader

ROOT = Path(__file__).resolve().parent.parent
mod = SourceFileLoader("m1", str(ROOT / "scripts/backfill-case-summaries.py")).load_module()

sections = json.loads((ROOT / "data/raw/dcw-page-sections.json").read_text(encoding="utf-8"))["pages"]
cases = json.loads((ROOT / "data/entities/cases.json").read_text(encoding="utf-8"))

n = 0
lens = []
for c in cases:
    if c.get("summary"):
        continue
    sec = sections.get(c.get("dcwPage") or "")
    if not sec:
        continue
    text = mod.compose(sec.get("situation"))
    if not text:
        continue
    lens.append(len(text))
    if n < 6:
        print("=" * 74)
        print(f"{c['id']}   ({len(text)} 字符)")
        print("-" * 74)
        print(text[:420])
        print()
        n += 1

lens.sort()
print("=" * 74)
print(f"共 {len(lens)} 条；最短 {lens[0]} / 中位 {lens[len(lens)//2]} / 最长 {lens[-1]}")
print(f"<120 字符: {sum(1 for x in lens if x < 120)}")
