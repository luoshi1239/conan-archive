#!/usr/bin/env python3
"""Report field presence, source support, and review status separately."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_IDS = {
    row.get("id")
    for row in json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8")).get("sources", [])
}

DATASETS = {
    "episodes": ROOT / "data" / "episodes" / "episodes.json",
    "characters": ROOT / "data" / "entities" / "characters.json",
    "organizations": ROOT / "data" / "entities" / "organizations.json",
    "cases": ROOT / "data" / "entities" / "cases.json",
    "gadgets": ROOT / "data" / "entities" / "gadgets.json",
    "locations": ROOT / "data" / "entities" / "locations.json",
    "arcs": ROOT / "data" / "manga" / "mainline-arcs.json",
    "movies": ROOT / "data" / "movies" / "movies.json",
    "specialMovies": ROOT / "data" / "movies" / "special-movies.json",
    "ovas": ROOT / "data" / "ovas" / "ovas.json",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def present(row: dict, field: str) -> bool:
    value = row.get(field)
    if field in {"summary", "airDate", "year", "adaptation"}:
        return value is not None and value != ""
    if field == "sources":
        return bool(value)
    if field in {"simplifiedTitle", "traditionalTitle"}:
        title = row.get("title")
        if isinstance(title, dict):
            key = "zhHans" if field == "simplifiedTitle" else "zhHant"
            return bool(title.get(key))
        return bool(title) if field == "simplifiedTitle" else False
    if field == "mangaRefs":
        return bool(row.get("mangaRefs"))
    return value is not None


def source_quality(row: dict) -> dict[str, object]:
    refs = row.get("sources") or []
    known = [ref for ref in refs if ref in SOURCE_IDS]
    unknown = [ref for ref in refs if ref not in SOURCE_IDS]
    return {
        "hasSources": bool(refs),
        "knownSourceRefs": len(known),
        "unknownSourceRefs": unknown,
        "allSourcesKnown": bool(refs) and not unknown,
    }


def dataset_report(name: str, rows: list[dict]) -> dict[str, object]:
    if name == "episodes":
        fields = [
            "simplifiedTitle",
            "traditionalTitle",
            "airDate",
            "year",
            "adaptation",
            "mangaRefs",
            "summary",
            "sources",
        ]
    else:
        fields = ["summary", "sources"]
        if rows and any("title" in row for row in rows):
            fields.extend(["simplifiedTitle", "traditionalTitle"])

    field_report = {}
    for field in fields:
        count = sum(1 for row in rows if present(row, field))
        with_sources = sum(1 for row in rows if present(row, field) and source_quality(row)["allSourcesKnown"])
        field_report[field] = {
            "present": count,
            "total": len(rows),
            "percent": round(count / len(rows) * 100, 1) if rows else 0,
            "presentWithKnownSources": with_sources,
        }

    statuses = Counter(row.get("detailStatus", row.get("status")) for row in rows)
    reviewed = sum(1 for row in rows if row.get("detailStatus") == "reviewed" or row.get("status") == "reviewed")
    rows_with_sources = sum(1 for row in rows if source_quality(row)["hasSources"])
    rows_with_known_sources = sum(1 for row in rows if source_quality(row)["allSourcesKnown"])
    coverage = {
        key: sum(1 for row in rows if (row.get("coverage") or {}).get(key) is True)
        for key in ("directory", "basicFacts", "structure", "deepSpoilers")
    }
    return {
        "total": len(rows),
        "status": dict(statuses),
        "reviewedRecords": reviewed,
        "recordsWithSources": rows_with_sources,
        "recordsWithKnownSources": rows_with_known_sources,
        "coverage": coverage,
        "fields": field_report,
    }


def main() -> int:
    report = {
        "generatedFrom": "normalized JSON files and data/sources.json",
        "sourceCount": len(SOURCE_IDS),
        "datasets": {},
    }
    for name, path in DATASETS.items():
        if path.exists():
            report["datasets"][name] = dataset_report(name, load(path))

    output = ROOT / "docs" / "FIELD-CONFIDENCE.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"WROTE {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
