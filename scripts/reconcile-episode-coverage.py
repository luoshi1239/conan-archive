#!/usr/bin/env python3
"""Reconcile episode coverage flags with the case data that backs them.

Reports mismatches where an episode's case points at a deepSpoilers case but
the episode's own coverage.deepSpoilers flag is not set, and lists which
episodes legitimately have no deep case. Diagnostic + optional --fix.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from lib_episode_refs import expand_episode_refs  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str]) -> int:
    fix = "--fix" in argv
    ep_data = json.loads((ROOT / "data/episodes/episodes.json").read_text(encoding="utf-8"))
    episodes = ep_data["episodes"] if isinstance(ep_data, dict) else ep_data
    case_data = json.loads((ROOT / "data/entities/cases.json").read_text(encoding="utf-8"))
    cases = case_data["cases"] if isinstance(case_data, dict) else case_data

    deep = {c["id"] for c in cases if c.get("detailStatus") == "deepSpoilers"}
    structured = {c["id"] for c in cases if c.get("detailStatus") in ("structure", "deepSpoilers")}
    by_id = {c["id"]: c for c in cases}

    deep_eps_cases = {e for cid in deep for e in expand_episode_refs(by_id[cid].get("animeRefs"))}
    struct_eps_cases = {e for cid in structured for e in expand_episode_refs(by_id[cid].get("animeRefs"))}

    problems = []
    for ep in episodes:
        eid = ep.get("id")
        cov = ep.setdefault("coverage", {})
        wants_deep = eid in deep_eps_cases
        wants_struct = eid in struct_eps_cases
        changed = False
        if wants_struct and cov.get("structure") is not True:
            problems.append((eid, ep.get("number"), "structure", cov.get("structure")))
            if fix:
                cov["structure"] = True
                changed = True
        if wants_deep and cov.get("deepSpoilers") is not True:
            problems.append((eid, ep.get("number"), "deepSpoilers", cov.get("deepSpoilers")))
            if fix:
                cov["deepSpoilers"] = True
                changed = True
        if changed:
            ds = ep.get("detailStatus")
            if wants_deep and ds not in ("reviewed", "complete"):
                ep["detailStatus"] = "reviewed"

    deep_flag = sum(1 for e in episodes if (e.get("coverage") or {}).get("deepSpoilers") is True)
    struct_flag = sum(1 for e in episodes if (e.get("coverage") or {}).get("structure") is True)
    print(f"deep_cases={len(deep)} deep_episodes_expected={len(deep_eps_cases)} deep_flag={deep_flag}")
    print(f"struct_cases={len(structured)} struct_episodes_expected={len(struct_eps_cases)} struct_flag={struct_flag}")
    print(f"mismatches={len(problems)}")
    for row in problems[:40]:
        print("  ", row)

    if fix and problems:
        (ROOT / "data/episodes/episodes.json").write_text(
            json.dumps(ep_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print("WROTE data/episodes/episodes.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
