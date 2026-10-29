#!/usr/bin/env python3
"""Normalize catalog-level completion metadata for movies and derivative works."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "data/movies/movies.json",
    ROOT / "data/movies/special-movies.json",
    ROOT / "data/ovas/ovas.json",
]


def enrich(row: dict) -> dict:
    has_title = bool(row.get("title", {}).get("ja") or row.get("title", {}).get("zhHans"))
    has_release = bool(row.get("releaseDate"))
    has_source = bool(row.get("sources"))
    row.setdefault("summary", None)
    row.setdefault("characters", [])
    row.setdefault("organizations", [])
    row.setdefault("locations", [])
    row.setdefault("caseRefs", [])
    row.setdefault("arc", None)
    row.setdefault("detailStatus", "reviewed" if has_title and has_release and has_source else "catalog")
    row.setdefault("coverage", {
        "directory": True,
        "basicFacts": has_title and has_release and has_source,
        "structure": False,
        "deepSpoilers": False,
    })
    return row


def main() -> None:
    total = 0
    for path in FILES:
        rows = json.loads(path.read_text(encoding="utf-8"))
        rows = [enrich(row) for row in rows]
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{path.relative_to(ROOT)}={len(rows)}")
        total += len(rows)
    print(f"enriched={total}")

if __name__ == "__main__":
    main()
