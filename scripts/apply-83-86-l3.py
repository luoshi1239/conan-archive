#!/usr/bin/env python3
"""Apply accepted L3 candidates for EP.83-86 cases. Idempotent."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data" / "candidates" / "entities.json"
CASES = ROOT / "data" / "entities" / "cases.json"
EPISODES = ROOT / "data" / "episodes" / "episodes.json"

BATCH = "ep-83-86-l3"
CASE_EPS = {
    "case-general-hospital-murder": (83,),
    "case-ski-lodge-murder": (84, 85),
    "case-kidnapping-location": (86,),
}


def main() -> None:
    cand_raw = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    candidates = cand_raw["candidates"] if isinstance(cand_raw, dict) else cand_raw
    batch = [c for c in candidates if str(c.get("candidateId", "")).startswith(f"cand-{BATCH}-") and c.get("reviewStatus") == "accepted"]

    case_raw = json.loads(CASES.read_text(encoding="utf-8"))
    cases = case_raw["cases"] if isinstance(case_raw, dict) else case_raw
    by_id = {c["id"]: c for c in cases}

    changed = 0
    for c in batch:
        case = by_id.get(c["targetId"])
        if case is None:
            raise SystemExit(f"missing case {c['targetId']}")
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
    by_num = {e["number"]: e for e in episodes}
    for case_id, nums in CASE_EPS.items():
        for num in nums:
            ep = by_num.get(num)
            if ep is None:
                raise SystemExit(f"missing episode {num}")
            refs = ep.setdefault("caseRefs", [])
            if case_id not in refs:
                refs.append(case_id)
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

    print(f"accepted_candidates={len(batch)} effective_changes={changed}")


if __name__ == "__main__":
    main()
