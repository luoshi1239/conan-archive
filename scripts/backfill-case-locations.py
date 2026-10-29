#!/usr/bin/env python3
"""M7：案件 locations —— 从 DCW 页面正文的 `Location:` 条目取原文。

背景更正
--------
此前判定「locations 零源、不可补」是错的。`dcw-page-facts.json` 里确实没有
location 字段，但 `dcw-page-sections.json` 的正文段落里有 `Location: <地点>` 条目，
覆盖 401 个案件页——这是 DCW 原文，可搬。

口径修正（2026-10-28 二次修订）
------------------------------
初版同时从 `situation`（案件设定段）和 `resolution`（解答段）取行，导致 **167 个案件**
的地点里混进了只出现在解答段的地点（如 `Shiki Island`、`hospital`、`party hall`）——
那是「案子后来才揭出来的地点」，放在非剧透字段等于泄底。

现在**只取 `situation`**。代价是覆盖从 491 降到 401，90 个案件会失去全部地点
（它们的地点原文只在解答段）。这是正确取舍：宁可少，不泄底。

旧值不直接丢弃：被剔除的地点记入 `locationsDropped`（数组），可回溯。

写入规则
--------
- 值若命中已有地点实体的 `name.en`，写实体 id（如 location-tropical-land）
- 否则写原文地点名（如 "Beika Library"）——不造实体，泛称
  （Apartment / Street / Unknown …）不值得各建一条
- 另写 `locationsSource` = DCW 页名，保证可追溯
- 多地点按出现顺序全部保留，去重

幂等：结果与现有值相同则不写盘。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data/entities/cases.json"
SECTIONS = ROOT / "data/raw/dcw-page-sections.json"
LOCATIONS = ROOT / "data/entities/locations.json"
DRY = "--dry-run" in sys.argv

LAB = re.compile(r"^Location:\s*(.+)$")


def collect(page, sections):
    """只读 situation 段。resolution 是解答段，其中的地点属剧透，不取。"""
    sec = sections.get(page)
    if not sec:
        return []
    out = []
    for raw in sec.get("situation") or []:
        m = LAB.match(str(raw).strip())
        if not m:
            continue
        v = m.group(1).strip()
        if v and v not in out:
            out.append(v)
    return out


def main() -> int:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    sections = json.loads(SECTIONS.read_text(encoding="utf-8"))["pages"]
    locs = json.loads(LOCATIONS.read_text(encoding="utf-8"))

    by_name = {}
    for e in locs:
        en = ((e.get("name") or {}).get("en") or "").strip().lower()
        if en:
            by_name[en] = e["id"]

    filled = 0
    changed = 0
    dropped_cases = 0
    dropped_total = 0
    mapped_ids = 0
    raw_names = 0

    for c in cases:
        page = c.get("dcwPage")
        if not page:
            continue
        vals = collect(page, sections)

        resolved = []
        for v in vals:
            eid = by_name.get(v.lower())
            if eid:
                resolved.append(eid)
                mapped_ids += 1
            else:
                resolved.append(v)
                raw_names += 1

        old = c.get("locations") or []
        # 旧值中不在新结果里的，记为剔除（仅当旧值非空且确实变了）
        dropped = [x for x in old if x not in resolved] if old != resolved else []

        if old == resolved and c.get("locationsSource") == (page if resolved else c.get("locationsSource")):
            continue

        changed += 1
        if not resolved:
            if old:
                dropped_cases += 1
            if not DRY:
                c.pop("locations", None)
                c.pop("locationsSource", None)
                if dropped:
                    c["locationsDropped"] = dropped
            dropped_total += len(dropped)
            continue

        if not DRY:
            c["locations"] = resolved
            c["locationsSource"] = page
            if dropped:
                c["locationsDropped"] = dropped
            else:
                c.pop("locationsDropped", None)
        filled += 1
        dropped_total += len(dropped)

    total_locs = sum(1 for c in cases if c.get("locations"))
    print(f"M7 案件 locations：本轮变更 {changed} 条；现有 {total_locs} 条有地点")
    print(f"   解析为实体 id：{mapped_ids} 次；保留原文：{raw_names} 次")
    print(f"   剔除的解答段地点：{dropped_total} 个，涉及案件 {dropped_cases} 个（失去全部地点）")

    if DRY:
        print("   [dry-run] 未写盘")
        return 0
    if changed == 0:
        print("   IDEMPOTENT_OK（无改动，不写盘）")
        return 0

    CASES.write_text(
        json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("   已写入 cases.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
