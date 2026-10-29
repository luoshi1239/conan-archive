#!/usr/bin/env python3
"""把 DCW L3 候选中 confidence=high 的 culprit 写入案件实体。

只写 culprit。理由：
  - culprit 有明确句式（'The culprit is X.'）且 X 通过了人名形态校验，
    属于「页面原文明确陈述」，不是推断；
  - method / motive / evidence 的候选目前是整段原文（confidence=low），
    必须人工裁句，不得自动写入。

铁律
====
1. 只处理 confidence == 'high' 的 culprit 候选。
2. 已有 culprit 的实体一律跳过（人工核实优先）。
3. 写入时同时落 culpritSource（页面名 + 原句），保证可追溯。
4. detailStatus 只在五字段齐全时才升为 deepSpoilers，否则保持原状。
5. 幂等：第二次运行 applied=0。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "entities" / "cases.json"
CANDS = ROOT / "data" / "candidates" / "dcw-l3.json"
REPORT = ROOT / "docs" / "L3-APPLY-REPORT.json"

TODAY = "2026-10-27"
L3_FIELDS = ("culprit", "motive", "method", "evidence", "resolution")


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def save(p: Path, obj) -> None:
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main() -> None:
    cases_raw = load(CASES)
    rows = cases_raw if isinstance(cases_raw, list) else cases_raw.get("cases", [])
    by_page = {r["dcwPage"]: r for r in rows if r.get("dcwPage")}

    cands = load(CANDS)["candidates"]
    applied = 0
    skipped = []
    promoted = 0

    for c in cands:
        if c.get("field") != "culprit" or c.get("confidence") != "high":
            continue
        row = by_page.get(c.get("dcwPage"))
        if row is None:
            skipped.append({"page": c.get("dcwPage"), "reason": "no-entity"})
            continue
        if row.get("culprit"):
            skipped.append({"page": c.get("dcwPage"), "reason": "already-has-culprit"})
            continue

        row["culprit"] = c["value"]
        row["culpritSource"] = {
            "page": c["dcwPage"],
            "block": c.get("sourceBlock"),
            "quote": c.get("quote"),
            "sourceRefs": c.get("sourceRefs") or [],
            "confidence": "high",
        }
        row["updatedAt"] = TODAY
        applied += 1

        # 五字段齐全才升 deepSpoilers
        if all(row.get(f) for f in L3_FIELDS):
            if row.get("detailStatus") != "deepSpoilers":
                row["detailStatus"] = "deepSpoilers"
                row["deepSpoilers"] = True
                promoted += 1
        elif not row.get("detailStatus"):
            row["detailStatus"] = "partial"

    if isinstance(cases_raw, dict):
        cases_raw["cases"] = rows
        save(CASES, cases_raw)
    else:
        save(CASES, rows)

    full = sum(1 for r in rows if all(r.get(f) for f in L3_FIELDS))
    with_culprit = sum(1 for r in rows if r.get("culprit"))

    report = {
        "version": 1,
        "generatedAt": TODAY,
        "applied": applied,
        "promotedToDeepSpoilers": promoted,
        "casesWithCulprit": with_culprit,
        "casesWithFullL3": full,
        "casesTotal": len(rows),
        "skipped": skipped[:300],
        "skippedCount": len(skipped),
    }
    save(REPORT, report)
    print(f"applied={applied} promoted={promoted} skipped={len(skipped)}")
    print(f"casesWithCulprit={with_culprit} fullL3={full}/{len(rows)}")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
