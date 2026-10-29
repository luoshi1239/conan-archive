#!/usr/bin/env python3
"""M1 前置二：判定 situation / resolution 是否适合当 summary。

要点：
  - summary 应该是「案件设定」，不该是「解答」
  - 若 resolution 首行是 "Many people had a motive:" 这种引导句，
    说明它是分条解答，不宜当 summary
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


secs = load("data/raw/dcw-page-sections.json")["pages"]
cases = load("data/entities/cases.json")
no_sum = [c for c in cases if not c.get("summary")]

HEADING = re.compile(r"^[A-Z][A-Za-z' \-]{1,40}$")


def first_para(lst):
    for x in lst or []:
        s = str(x).strip()
        if not s:
            continue
        if HEADING.match(s) and len(s.split()) <= 5:
            continue  # 小节标题，跳过
        return s
    return None


print("=" * 72)
print("A. situation 首段（抽 5 个）")
print("=" * 72)
n = 0
for c in no_sum:
    sec = secs.get(c.get("dcwPage") or "")
    if not sec or not sec.get("situation"):
        continue
    p = first_para(sec["situation"])
    if p:
        print(f"\n  {c['id']}  ({len(p)} 字符)")
        print(f"    {p[:240]}")
        n += 1
    if n >= 5:
        break

print()
print("=" * 72)
print("B. 仅 resolution 的页，首段形态（抽 6 个）")
print("=" * 72)
n = 0
colon = 0
sentence = 0
for c in no_sum:
    sec = secs.get(c.get("dcwPage") or "")
    if not sec or sec.get("situation"):
        continue
    if not sec.get("resolution"):
        continue
    p = first_para(sec["resolution"])
    if not p:
        continue
    if p.rstrip().endswith(":"):
        colon += 1
    else:
        sentence += 1
    if n < 6:
        print(f"\n  {c['id']}  ({len(p)} 字符)")
        print(f"    {p[:240]}")
    n += 1

print(f"\n  统计：引导句(冒号结尾) {colon} / 叙述句 {sentence} / 共 {n}")

print()
print("=" * 72)
print("C. situation 首段长度分布")
print("=" * 72)
lens = []
for c in no_sum:
    sec = secs.get(c.get("dcwPage") or "")
    if not sec or not sec.get("situation"):
        continue
    p = first_para(sec["situation"])
    if p:
        lens.append(len(p))
lens.sort()
if lens:
    print(f"  可提取 {len(lens)} 条")
    print(f"  最短 {lens[0]} / 中位 {lens[len(lens)//2]} / 最长 {lens[-1]}")
    print(f"  <120 字符: {sum(1 for x in lens if x < 120)}")
