#!/usr/bin/env python3
"""Report explicit relation closure for the Conan archive."""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def episode_numbers(ref: str) -> list[int]:
    if not ref.startswith("episode-"):
        return []
    tail = ref.removeprefix("episode-")
    if "-" not in tail:
        return [int(tail)]
    start, end = tail.split("-", 1)
    return list(range(int(start), int(end) + 1))

def main() -> None:
    episodes = load("data/episodes/episodes.json")
    cases = load("data/entities/cases.json")
    arcs = load("data/manga/mainline-arcs.json")
    by_number = {row["number"]: row for row in episodes}
    case_forward = {}
    case_reverse = Counter()
    case_uncovered = {}
    for case in cases:
        numbers = sorted({n for ref in case.get("animeRefs", []) for n in episode_numbers(ref)})
        case_forward[case["id"]] = numbers
        for number in numbers:
            row = by_number.get(number)
            if row and case["id"] in row.get("caseRefs", []):
                case_reverse[case["id"]] += 1
        case_uncovered[case["id"]] = [n for n in numbers if not by_number.get(n) or case["id"] not in by_number[n].get("caseRefs", [])]
    arc_forward = {}
    arc_reverse = Counter()
    arc_uncovered = {}
    for arc in arcs:
        numbers = sorted({n for ref in arc.get("animeRefs", []) for n in episode_numbers(ref)})
        arc_forward[arc["id"]] = numbers
        for number in numbers:
            row = by_number.get(number)
            if row and (row.get("arc") == arc["id"] or arc["id"] in row.get("arcRefs", [])):
                arc_reverse[arc["id"]] += 1
        arc_uncovered[arc["id"]] = [n for n in numbers if not by_number.get(n) or (by_number[n].get("arc") != arc["id"] and arc["id"] not in by_number[n].get("arcRefs", []))]
    reviewed = [row["number"] for row in episodes if row.get("detailStatus") == "reviewed"]
    report = {
        "generatedFrom": "repository-declared animeRefs and episode relations",
        "episodes": {"total": len(episodes), "reviewed": len(reviewed), "reviewedNumbers": reviewed},
        "cases": {"forward": case_forward, "reverseReviewed": dict(case_reverse), "uncovered": case_uncovered},
        "arcs": {"forward": arc_forward, "reverseReviewed": dict(arc_reverse), "uncovered": arc_uncovered},
    }
    output = ROOT / "docs" / "RELATION-CLOSURE.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    uncovered = sum(map(len, case_uncovered.values())) + sum(map(len, arc_uncovered.values()))
    print(f"WROTE {output.relative_to(ROOT)} cases_uncovered={sum(map(len, case_uncovered.values()))} arcs_uncovered={sum(map(len, arc_uncovered.values()))} total={uncovered}")

if __name__ == "__main__":
    main()
