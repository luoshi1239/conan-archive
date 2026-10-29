#!/usr/bin/env python3
"""Reconcile case detailStatus with the L3 fields actually present.

Why this exists: apply-*.py scripts wrote culprit/motive/method/evidence/
resolution onto case entities but not always detailStatus, leaving 27
fully-written cases marked null. Any UI or report filtering on detailStatus
was hiding them. Rule: all five L3 fields present -> deepSpoilers. Partial ->
structure. Nothing -> leave untouched.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "entities" / "cases.json"
TODAY = "2026-10-27"

L3 = ("culprit", "motive", "method", "evidence", "resolution")
RANK = {"directory": 0, "basicFacts": 1, "structure": 2, "deepSpoilers": 3}


def main() -> int:
    data = json.loads(CASES.read_text(encoding="utf-8"))
    cases = data["cases"] if isinstance(data, dict) else data

    promoted = 0
    partial = []
    for case in cases:
        have = sum(1 for f in L3 if case.get(f))
        cur = case.get("detailStatus")
        if have == len(L3):
            if RANK.get(cur, -1) < RANK["deepSpoilers"]:
                case["detailStatus"] = "deepSpoilers"
                case["updatedAt"] = TODAY
                promoted += 1
        elif have == 0 and cur:
            # no evidence text left but status claims depth: flag, do not silently drop
            partial.append((case["id"], cur, "完整字段已清空但状态仍标记深度"))
        elif 0 < have < len(L3):
            partial.append((case["id"], cur, f"仅 {have}/{len(L3)} 个 L3 字段"))

    CASES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"promoted={promoted}")
    print("detailStatus now:", dict(Counter(c.get("detailStatus") for c in cases)))
    if partial:
        print("NEEDS_REVIEW:")
        for row in partial:
            print("  ", row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
