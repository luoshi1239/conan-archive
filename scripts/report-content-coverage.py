#!/usr/bin/env python3
"""Generate a factual content coverage report for the Conan archive."""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))

def ratio(rows, predicate):
    count = sum(1 for row in rows if predicate(row))
    return {"count": count, "total": len(rows), "percent": round(count / len(rows) * 100, 1) if rows else 0}

def main() -> None:
    episodes = load("data/episodes/episodes.json")
    groups = {
        "characters": load("data/entities/characters.json"),
        "organizations": load("data/entities/organizations.json"),
        "cases": load("data/entities/cases.json"),
        "gadgets": load("data/entities/gadgets.json"),
        "arcs": load("data/manga/mainline-arcs.json"),
        "mangaFiles": load("data/manga/files.json"),
        "movies": load("data/movies/movies.json") + load("data/movies/special-movies.json"),
        "ovas": load("data/ovas/ovas.json"),
    }
    report = {
        "generatedFrom": "normalized JSON files",
        "episodes": {
            "total": len(episodes),
            "adaptation": dict(Counter(row.get("adaptation") for row in episodes)),
            "detailStatus": dict(Counter(row.get("detailStatus") for row in episodes)),
            "directory": ratio(episodes, lambda row: row.get("coverage", {}).get("directory") is True),
            "basicFacts": ratio(episodes, lambda row: row.get("coverage", {}).get("basicFacts") is True),
            "structure": ratio(episodes, lambda row: row.get("coverage", {}).get("structure") is True),
            "deepSpoilers": ratio(episodes, lambda row: row.get("coverage", {}).get("deepSpoilers") is True),
            "fields": {
                "simplifiedTitle": ratio(episodes, lambda row: bool(row.get("title", {}).get("zhHans"))),
                "traditionalTitle": ratio(episodes, lambda row: bool(row.get("title", {}).get("zhHant"))),
                "mangaRefs": ratio(episodes, lambda row: bool(row.get("mangaRefs"))),
                "mangaRefsKnown": ratio(episodes, lambda row: bool(row.get("mangaRefs"))),
                "summary": ratio(episodes, lambda row: bool(row.get("summary"))),
                "characters": ratio(episodes, lambda row: bool(row.get("characters"))),
                "caseTypes": ratio(episodes, lambda row: bool(row.get("caseTypes"))),
            },
        },
        "collections": {},
    }
    for name, rows in groups.items():
        report["collections"][name] = {
            "total": len(rows),
            "status": dict(Counter(row.get("status") for row in rows)),
            "withSummary": ratio(rows, lambda row: bool(row.get("summary"))),
            # Entities store source ids under `sourceRefs`; some legacy rows used
            # `sources`. Accept both or the report undercounts provenance.
            "withSources": ratio(
                rows, lambda row: bool(row.get("sourceRefs") or row.get("sources"))
            ),
            "detailStatus": dict(Counter(row.get("detailStatus") for row in rows)),
            "directory": ratio(rows, lambda row: row.get("coverage", {}).get("directory") is True),
            "basicFacts": ratio(rows, lambda row: row.get("coverage", {}).get("basicFacts") is True),
            "structure": ratio(rows, lambda row: row.get("coverage", {}).get("structure") is True),
        }
    output = ROOT / "docs" / "CONTENT-COVERAGE.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"WROTE {output.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
