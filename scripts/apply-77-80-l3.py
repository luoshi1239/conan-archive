#!/usr/bin/env python3
"""Apply accepted L3 field candidates for episodes 77-80 cases.

Idempotent: re-running with the same candidates yields effective_changes=0.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data" / "candidates" / "entities.json"
CASES = ROOT / "data" / "entities" / "cases.json"

TARGETS = {
    "case-distinguished-family-consecutive-death",
    "case-bank-heist-murder",
    "case-wandering-artist-murder",
}

DEEP_FIELDS = ("culprit", "motive", "method", "evidence", "resolution")


def main() -> None:
    cand_data = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    cands = cand_data["candidates"] if isinstance(cand_data, dict) else cand_data
    cases_data = json.loads(CASES.read_text(encoding="utf-8"))
    cases = cases_data["cases"] if isinstance(cases_data, dict) else cases_data

    by_id = {c["id"]: c for c in cases}
    accepted = 0
    changed = 0

    for cand in cands:
        if cand.get("reviewStatus") != "accepted":
            continue
        target = cand.get("targetId")
        if target not in TARGETS:
            continue
        field = cand.get("field")
        if field not in DEEP_FIELDS:
            continue
        accepted += 1
        case = by_id.get(target)
        if case is None:
            raise SystemExit(f"missing case entity: {target}")
        value = cand["value"]
        if case.get(field) != value:
            case[field] = value
            changed += 1
        # 关系补齐：案件需声明来源与承接动画
        src = cand["sourceRefs"][0]
        if src not in case.setdefault("sources", []):
            case["sources"].append(src)
            changed += 1

    for case_id in TARGETS:
        case = by_id[case_id]
        if all(case.get(f) for f in DEEP_FIELDS):
            if not case.get("deepSpoilers"):
                case["deepSpoilers"] = True
                changed += 1
        if case.get("status") != "reviewed":
            case["status"] = "reviewed"
            changed += 1

    if isinstance(cases_data, dict):
        cases_data["cases"] = cases
        payload = cases_data
    else:
        payload = cases
    CASES.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"accepted_candidates={accepted} effective_changes={changed}")


if __name__ == "__main__":
    main()
