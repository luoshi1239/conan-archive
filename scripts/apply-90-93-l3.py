#!/usr/bin/env python3
"""Apply accepted L3 candidates for EP.90-93 cases. Idempotent."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAND = ROOT / "data" / "candidates" / "entities.json"
CASES = ROOT / "data" / "entities" / "cases.json"

TARGETS = {
    "case-flower-scent-murder",
    "case-bank-robber-hospitalization",
    "case-fearful-traversing-murder",
}

# 这些字段承载多条并列事实，用列表保存；其余为单值字符串
LIST_FIELDS = {"relatedCases"}


def main() -> None:
    cand_data = json.loads(CAND.read_text(encoding="utf-8"))
    cands = cand_data["candidates"] if isinstance(cand_data, dict) else cand_data

    case_data = json.loads(CASES.read_text(encoding="utf-8"))
    cases = case_data["cases"] if isinstance(case_data, dict) else case_data
    by_id = {c["id"]: c for c in cases}

    applied = 0
    changed = 0
    for c in cands:
        if c.get("reviewStatus") != "accepted":
            continue
        tid = c.get("targetId")
        if tid not in TARGETS:
            continue
        entity = by_id.get(tid)
        if entity is None:
            print(f"SKIP missing entity {tid}")
            continue
        field = c["field"]
        value = c["value"]
        applied += 1

        if field in LIST_FIELDS:
            cur = entity.get(field)
            if not isinstance(cur, list):
                cur = []
            if value not in cur:
                cur.append(value)
                changed += 1
            entity[field] = cur
        else:
            if entity.get(field) != value:
                entity[field] = value
                changed += 1

        if entity.get("detailStatus") != "deepSpoilers":
            entity["detailStatus"] = "deepSpoilers"
        entity["status"] = "reviewed"
        entity["updatedAt"] = "2026-10-27"
        refs = entity.setdefault("sourceRefs", [])
        for src in c.get("sourceRefs", []):
            if src not in refs:
                refs.append(src)

    if isinstance(case_data, dict):
        case_data["cases"] = cases
        payload = case_data
    else:
        payload = cases
    CASES.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"accepted_candidates={applied} effective_changes={changed}")


if __name__ == "__main__":
    main()
