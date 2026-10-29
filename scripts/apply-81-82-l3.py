#!/usr/bin/env python3
"""Apply accepted L3 candidates for case-popular-artist-kidnapping (EP.81-82).

Idempotent: re-running yields effective_changes=0.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data" / "candidates" / "entities.json"
CASES = ROOT / "data" / "entities" / "cases.json"
EPISODES = ROOT / "data" / "episodes" / "episodes.json"

CASE_ID = "case-popular-artist-kidnapping"
BATCH = "ep-81-82-l3"
EPS = (81, 82)


def main() -> None:
    cand_raw = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    candidates = cand_raw["candidates"] if isinstance(cand_raw, dict) else cand_raw
    accepted = [c for c in candidates if c.get("targetId") == CASE_ID and c.get("reviewStatus") == "accepted"]

    case_raw = json.loads(CASES.read_text(encoding="utf-8"))
    cases = case_raw["cases"] if isinstance(case_raw, dict) else case_raw
    case = next((c for c in cases if c["id"] == CASE_ID), None)
    if case is None:
        raise SystemExit(f"missing case {CASE_ID}")

    changed = 0
    for c in accepted:
        field, value = c["field"], c["value"]
        if case.get(field) != value:
            case[field] = value
            changed += 1
        srcs = case.setdefault("sourceRefs", [])
        for s in c.get("sourceRefs", []):
            if s not in srcs:
                srcs.append(s)
                changed += 1
    case["status"] = "reviewed"
    case["detailStatus"] = "deepSpoilers"
    case["updatedAt"] = "2026-10-27"
    if isinstance(case_raw, dict):
        case_raw["cases"] = cases
        case_payload = case_raw
    else:
        case_payload = cases
    CASES.write_text(json.dumps(case_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ep_raw = json.loads(EPISODES.read_text(encoding="utf-8"))
    episodes = ep_raw["episodes"] if isinstance(ep_raw, dict) else ep_raw
    for ep in episodes:
        if ep.get("number") not in EPS:
            continue
        refs = ep.setdefault("caseRefs", [])
        if CASE_ID not in refs:
            refs.append(CASE_ID)
            changed += 1
        if ep.get("status") == "catalog":
            ep["status"] = "structured"
            changed += 1
        if ep.get("detailStatus") in {"catalog", "structured", None}:
            ep["detailStatus"] = "reviewed"
            changed += 1
        cov = ep.setdefault("coverage", {})
        if not cov.get("structure"):
            cov["structure"] = True
            changed += 1
    if isinstance(ep_raw, dict):
        ep_raw["episodes"] = episodes
        ep_payload = ep_raw
    else:
        ep_payload = episodes
    EPISODES.write_text(json.dumps(ep_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"accepted_candidates={len(accepted)} effective_changes={changed}")


if __name__ == "__main__":
    main()
