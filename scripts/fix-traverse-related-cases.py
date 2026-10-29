#!/usr/bin/env python3
"""Fix misused relatedCases candidates: fold incident notes into spoiler.

relatedCases is an entity-id reference field (validated as such). Free-text
incident notes must live in a text field instead, so migrate them.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAND = ROOT / "data" / "candidates" / "entities.json"
CASES = ROOT / "data" / "entities" / "cases.json"

TARGET = "case-fearful-traversing-murder"


def main() -> None:
    cand_data = json.loads(CAND.read_text(encoding="utf-8"))
    cands = cand_data["candidates"] if isinstance(cand_data, dict) else cand_data

    removed = 0
    kept = []
    for c in cands:
        if c.get("targetId") == TARGET and c.get("field") == "relatedCases":
            removed += 1
            continue
        kept.append(c)
    if isinstance(cand_data, dict):
        cand_data["candidates"] = kept
        CAND.write_text(json.dumps(cand_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        CAND.write_text(json.dumps(kept, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    case_data = json.loads(CASES.read_text(encoding="utf-8"))
    cases = case_data["cases"] if isinstance(case_data, dict) else case_data
    entity = next(c for c in cases if c["id"] == TARGET)

    bad = entity.get("relatedCases")
    if isinstance(bad, list):
        notes = [x for x in bad if isinstance(x, str) and not x.startswith("case-")]
        entity["relatedCases"] = [x for x in bad if isinstance(x, str) and x.startswith("case-")]
        if not entity["relatedCases"]:
            entity.pop("relatedCases")
        if notes:
            head = entity.get("spoiler") or ""
            body = "同一集的独立事件（不可并入本案）：" + "；".join(notes)
            entity["spoiler"] = (head + " " + body).strip() if head else body
    entity["updatedAt"] = "2026-10-27"

    if isinstance(case_data, dict):
        case_data["cases"] = cases
        payload = case_data
    else:
        payload = cases
    CASES.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"removed_candidates={removed}")


if __name__ == "__main__":
    main()
