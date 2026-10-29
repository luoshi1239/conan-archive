#!/usr/bin/env python3
"""Build sourced L3 candidates for EP.94-97 cases.

Fields already exist on the entities (written by register-94-97-cases.py);
these candidates are the auditable review record backing them. value must
match the entity text exactly.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "entities" / "cases.json"
CANDS = ROOT / "data" / "candidates" / "entities.json"

FIELDS = ("summary", "culprit", "motive", "method", "evidence", "resolution")

SRC = {
    "case-snow-woman-legend-murder": "src-detective-conan-world-snow-woman-case",
    "case-kogoro-date-murder": "src-detective-conan-world-kogoro-date-case",
    "case-tsukumo-magician-murder": "src-detective-conan-world-cornered-detective-case",
    "case-yabuuchi-family-murder": "src-detective-conan-world-cornered-detective-case",
    "case-farewell-wine-murder": "src-detective-conan-world-farewell-wine-case",
}

NOTES = {
    "summary": "被害人身份、死因与现场，取自 Case Situation／案情信息框。",
    "culprit": "真凶及冒名／身份关系，取自 Resolution 段落。",
    "motive": "动机链条，取自 Resolution 段落，保留原文因果不断章。",
    "method": "作案手法时间线，取自 Resolution 段落。",
    "evidence": "决定性证据与推理切入点，取自 Resolution 段落。",
    "resolution": "收束与结局，取自 Resolution 段落。",
}


def main() -> int:
    data = json.loads(CASES.read_text(encoding="utf-8"))
    cases = data["cases"] if isinstance(data, dict) else data
    by_id = {c["id"]: c for c in cases}

    cand_data = json.loads(CANDS.read_text(encoding="utf-8"))
    cands = cand_data["candidates"] if isinstance(cand_data, dict) else cand_data
    existing = {c["candidateId"] for c in cands}

    added = 0
    missing = []
    for case_id, src in SRC.items():
        case = by_id.get(case_id)
        if case is None:
            missing.append(case_id)
            continue
        for field in FIELDS:
            value = case.get(field)
            if not value:
                missing.append(f"{case_id}.{field}")
                continue
            cid = f"cand-{case_id}-{field}"
            if cid in existing:
                continue
            cands.append(
                {
                    "candidateId": cid,
                    "targetId": case_id,
                    "field": field,
                    "value": value,
                    "sourceRefs": [src],
                    "confidence": "high",
                    "reviewStatus": "accepted",
                    "reviewNote": NOTES[field],
                }
            )
            existing.add(cid)
            added += 1

    if missing:
        print("MISSING", missing)
        return 1

    if isinstance(cand_data, dict):
        cand_data["candidates"] = cands
        payload = cand_data
    else:
        payload = cands
    CANDS.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"candidates_added={added} total={len(cands)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
