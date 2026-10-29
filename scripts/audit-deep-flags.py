#!/usr/bin/env python3
"""List episodes whose coverage.deepSpoilers flag is set but no case backs it.

Over-flagging means the frontend promises spoiler depth that has no sourced
content behind it. Diagnostic only; --clear drops the unsupported flag.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from lib_episode_refs import expand_case_episodes  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str]) -> int:
    clear = "--clear" in argv
    ep_data = json.loads((ROOT / "data/episodes/episodes.json").read_text(encoding="utf-8"))
    episodes = ep_data["episodes"] if isinstance(ep_data, dict) else ep_data
    case_data = json.loads((ROOT / "data/entities/cases.json").read_text(encoding="utf-8"))
    cases = case_data["cases"] if isinstance(case_data, dict) else case_data

    by_case = expand_case_episodes(c for c in cases if c.get("detailStatus") == "deepSpoilers")
    backed = {e for eps in by_case.values() for e in eps}

    orphans = []
    for ep in episodes:
        eid = ep.get("id")
        cov = ep.get("coverage") or {}
        if cov.get("deepSpoilers") is True and eid not in backed:
            orphans.append((eid, ep.get("number"), (ep.get("title") or {}).get("zhHans", "")))

    print(f"backed_deep_episodes={len(backed)} orphan_deep_flags={len(orphans)}")
    for row in orphans:
        print("  ", row)

    if clear and orphans:
        for ep in episodes:
            cov = ep.get("coverage") or {}
            if cov.get("deepSpoilers") is True and ep.get("id") not in backed:
                cov.pop("deepSpoilers", None)
                if ep.get("detailStatus") == "complete":
                    ep["detailStatus"] = "reviewed"
        (ROOT / "data/episodes/episodes.json").write_text(
            json.dumps(ep_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print("WROTE data/episodes/episodes.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
