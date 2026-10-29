#!/usr/bin/env python3
"""Backfill episode-side caseRefs from case-side animeRefs (bidirectional closure).

For every case whose animeRefs name an episode, ensure that episode's caseRefs
contains the case id. Idempotent.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "data" / "entities" / "cases.json"
EPISODES = ROOT / "data" / "episodes" / "episodes.json"


def episode_number(ref: str) -> int | None:
    m = re.fullmatch(r"episode-(\d{4})", ref)
    return int(m.group(1)) if m else None


def main() -> None:
    case_data = json.loads(CASES.read_text(encoding="utf-8"))
    cases = case_data["cases"] if isinstance(case_data, dict) else case_data
    ep_data = json.loads(EPISODES.read_text(encoding="utf-8"))
    episodes = ep_data["episodes"] if isinstance(ep_data, dict) else ep_data

    by_number = {e["number"]: e for e in episodes}
    changed = 0
    touched = []

    for case in cases:
        case_id = case["id"]
        for ref in case.get("animeRefs", []):
            num = episode_number(ref)
            if num is None:
                continue
            ep = by_number.get(num)
            if ep is None:
                raise SystemExit(f"{case_id}: animeRef {ref} has no episode record")
            refs = ep.setdefault("caseRefs", [])
            if case_id not in refs:
                refs.append(case_id)
                changed += 1
                touched.append((num, case_id))
            # 集数侧记录案件后，其状态至少升到 structured；
            # detailStatus 必须为 reviewed/complete，否则 normalize-episodes
            # 会整块丢弃 caseRefs（见 normalize-episodes.py:85）。
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

    if isinstance(ep_data, dict):
        ep_data["episodes"] = episodes
        payload = ep_data
    else:
        payload = episodes
    EPISODES.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"effective_changes={changed} links={len(touched)}")
    for num, cid in touched[:12]:
        print(f"  EP.{num} <- {cid}")


if __name__ == "__main__":
    main()
