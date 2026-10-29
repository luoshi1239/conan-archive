#!/usr/bin/env python3
"""Repair internal episode-number mappings for diplomat and library cases."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "data/entities/cases.json"
EPISODES = ROOT / "data/episodes/episodes.json"

cases = json.loads(CASES.read_text(encoding="utf-8"))
for case in cases:
    if case.get("id") == "case-diplomat-murder":
        case["animeRefs"] = ["episode-0048-0049"]
        case["relatedEpisodes"] = ["episode-0048", "episode-0049"]
    elif case.get("id") == "case-library-murder":
        case["animeRefs"] = ["episode-0050"]
        case["relatedEpisodes"] = ["episode-0050"]
CASES.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

episodes = json.loads(EPISODES.read_text(encoding="utf-8"))
for episode in episodes:
    number = episode.get("number")
    refs = set(episode.get("caseRefs", []))
    if number in {48, 49}:
        refs.discard("case-library-murder")
        refs.add("case-diplomat-murder")
        episode["caseRefs"] = sorted(refs)
        episode["spoiler"] = 3
        episode["status"] = "reviewed"
        episode["detailStatus"] = "reviewed"
        episode.setdefault("coverage", {})["deepSpoilers"] = True
    elif number == 50:
        refs.discard("case-diplomat-murder")
        refs.add("case-library-murder")
        episode["caseRefs"] = sorted(refs)
        episode["spoiler"] = 3
        episode["status"] = "reviewed"
        episode["detailStatus"] = "reviewed"
        episode.setdefault("coverage", {})["deepSpoilers"] = True
    elif number == 51:
        refs.discard("case-library-murder")
        episode["caseRefs"] = sorted(refs)
        episode["spoiler"] = min(int(episode.get("spoiler") or 1), 1)
        episode["status"] = "catalog"
        episode["detailStatus"] = "catalog"
        episode.setdefault("coverage", {})["deepSpoilers"] = False
EPISODES.write_text(json.dumps(episodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("repaired_internal_episode_mapping=true")
