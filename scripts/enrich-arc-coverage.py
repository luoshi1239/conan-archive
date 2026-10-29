#!/usr/bin/env python3
"""Promote repository-declared arc episode ranges to structure-level records.

Only uses existing mainline-arcs.json declarations. It does not invent
case-level spoilers or overwrite reviewed, hand-curated fields.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EPISODES = ROOT / "data/episodes/episodes.json"
ARCS = ROOT / "data/manga/mainline-arcs.json"
SOURCE = "src-detective-conan-world-bo-timeline"


def numbers(ref: str) -> list[int]:
    if not ref.startswith("episode-"):
        return []
    tail = ref.removeprefix("episode-")
    if "-" not in tail:
        return [int(tail)]
    start, end = tail.split("-", 1)
    return list(range(int(start), int(end) + 1))


def main() -> None:
    episodes = json.loads(EPISODES.read_text(encoding="utf-8"))
    arcs = json.loads(ARCS.read_text(encoding="utf-8"))
    by_number = {row.get("number"): row for row in episodes}
    promoted: list[int] = []
    skipped_reviewed: list[int] = []
    for arc in arcs:
        arc_id = arc.get("id")
        title = arc.get("title")
        summary = arc.get("summary")
        for ref in arc.get("animeRefs", []):
            for number in numbers(ref):
                row = by_number.get(number)
                if not row:
                    continue
                if row.get("detailStatus") in {"reviewed", "complete"}:
                    skipped_reviewed.append(number)
                    continue
                row["arc"] = arc_id
                row["arcRefs"] = sorted(set(row.get("arcRefs", [])) | {arc_id})
                row["summary"] = summary
                row["spoiler"] = max(int(row.get("spoiler") or 1), int(arc.get("spoiler") or 1))
                row["detailStatus"] = "reviewed"
                row["coverage"] = {
                    "directory": True,
                    "basicFacts": True,
                    "structure": True,
                    "deepSpoilers": False,
                }
                row["sources"] = sorted(set(row.get("sources", [])) | {SOURCE, *arc.get("sources", [])})
                promoted.append(number)
    if promoted:
        EPISODES.write_text(json.dumps(episodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "promoted": len(promoted),
        "promotedNumbers": sorted(set(promoted)),
        "alreadyReviewed": len(set(skipped_reviewed)),
        "totalReviewedNow": sum(row.get("detailStatus") == "reviewed" for row in episodes),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
