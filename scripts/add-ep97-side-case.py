#!/usr/bin/env python3
"""Append the EP.97 side-case facts that the source states but the entity missed.

Source (/tmp/ep97.html, blocks 249/252/254):
  - Culprit row for a SECOND matter: Mizue Ichikawa, for illegally selling the
    company's shares; she is investigated for embezzlement and her inheritance
    is withheld.
  - Kogoro loses the rest of his fee after the case.

These belong in spoiler (free text), not in culprit (reserved for the murder).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "entities" / "cases.json"
CASE_ID = "case-farewell-wine-murder"

ADDITION = (
    "本案之外另有一事：次女瑞江（Mizue Ichikawa）因擅自出售公司股份被以侵占罪调查、"
    "继承份额被冻结，是独立于命案的经济犯罪，不并入杀人案；命案告破后小五郎也没能拿到约定的剩余报酬。"
)


def main() -> int:
    data = json.loads(CASES.read_text(encoding="utf-8"))
    cases = data["cases"] if isinstance(data, dict) else data
    changed = 0
    for case in cases:
        if case.get("id") != CASE_ID:
            continue
        spoiler = case.get("spoiler") or ""
        if "瑞江（Mizue Ichikawa）" in spoiler:
            print("already present")
            break
        case["spoiler"] = (spoiler + "；" + ADDITION) if spoiler else ADDITION
        case["updatedAt"] = "2026-10-27"
        changed = 1
        break
    if changed:
        CASES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"edits={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
