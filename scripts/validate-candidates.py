#!/usr/bin/env python3
"""Validate candidate records before they can be applied to normalized data."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "sources.json"
CANDIDATE_FILES = {
    "episodes": ROOT / "data" / "candidates" / "episodes.json",
    "entities": ROOT / "data" / "candidates" / "entities.json",
    "catalog": ROOT / "data" / "candidates" / "catalog.json",
}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}
ALLOWED_REVIEW_STATUS = {"pending", "accepted", "rejected"}
ALLOWED_FIELDS = {
    "title.zhHans",
    "title.zhHant",
    "title.en",
    "title.aliases",
    "airDate",
    "year",
    "adaptation",
    "mangaRefs",
    "arc",
    "arcRefs",
    "caseRefs",
    "locationRefs",
    "gadgets",
    "characters",
    "organizations",
    "caseTypes",
    "summary",
    "spoiler",
    "culprit",
    "motive",
    "method",
    "evidence",
    "resolution",
    "identityReveals",
    "detailStatus",
    "coverage",
    "aliases",
    "relations",
    "relatedEpisodes",
    "relatedCases",
    "relatedArcs",
}
REQUIRED_FIELDS = {
    "candidateId",
    "targetId",
    "field",
    "value",
    "sourceRefs",
    "confidence",
    "reviewStatus",
    "reviewNote",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def collect_known_ids() -> set[str]:
    paths = [
        ROOT / "data" / "episodes" / "episodes.json",
        ROOT / "data" / "entities" / "characters.json",
        ROOT / "data" / "entities" / "organizations.json",
        ROOT / "data" / "entities" / "cases.json",
        ROOT / "data" / "entities" / "gadgets.json",
        ROOT / "data" / "entities" / "locations.json",
        ROOT / "data" / "manga" / "mainline-arcs.json",
        ROOT / "data" / "movies" / "movies.json",
        ROOT / "data" / "movies" / "special-movies.json",
        ROOT / "data" / "ovas" / "ovas.json",
    ]
    ids: set[str] = set()
    for path in paths:
        if path.exists():
            rows = load(path)
            ids.update(row.get("id") for row in rows if row.get("id"))
    return ids


def validate_record(record: object, known_ids: set[str], source_ids: set[str], label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return [f"{label}: record must be an object"]
    missing = REQUIRED_FIELDS - set(record)
    if missing:
        errors.append(f"{label}: missing fields {sorted(missing)}")
    candidate_id = record.get("candidateId")
    if not isinstance(candidate_id, str) or not candidate_id:
        errors.append(f"{label}: candidateId must be a non-empty string")
    target_id = record.get("targetId")
    if target_id not in known_ids:
        errors.append(f"{label}: unknown targetId {target_id!r}")
    field = record.get("field")
    if field not in ALLOWED_FIELDS:
        errors.append(f"{label}: unsupported field {field!r}")
    source_refs = record.get("sourceRefs")
    if not isinstance(source_refs, list) or not source_refs:
        errors.append(f"{label}: sourceRefs must be a non-empty list")
    elif any(source not in source_ids for source in source_refs):
        unknown = sorted(source for source in source_refs if source not in source_ids)
        errors.append(f"{label}: unknown sourceRefs {unknown}")
    if record.get("confidence") not in ALLOWED_CONFIDENCE:
        errors.append(f"{label}: invalid confidence {record.get('confidence')!r}")
    if record.get("reviewStatus") not in ALLOWED_REVIEW_STATUS:
        errors.append(f"{label}: invalid reviewStatus {record.get('reviewStatus')!r}")
    if not isinstance(record.get("reviewNote"), str):
        errors.append(f"{label}: reviewNote must be a string")
    if "value" not in record:
        errors.append(f"{label}: value is required, including explicit null")
    return errors


def main() -> int:
    errors: list[str] = []
    source_data = load(SOURCES)
    source_ids = {row.get("id") for row in source_data.get("sources", [])}
    known_ids = collect_known_ids()
    seen_candidates: set[str] = set()
    total = 0
    for kind, path in CANDIDATE_FILES.items():
        if not path.exists():
            errors.append(f"missing candidate file: {path}")
            continue
        rows = load(path)
        if not isinstance(rows, list):
            errors.append(f"{path.name}: top-level value must be a list")
            continue
        for index, record in enumerate(rows):
            total += 1
            label = f"{kind}[{index}]"
            errors.extend(validate_record(record, known_ids, source_ids, label))
            candidate_id = record.get("candidateId") if isinstance(record, dict) else None
            if candidate_id in seen_candidates:
                errors.append(f"{label}: duplicate candidateId {candidate_id!r}")
            if candidate_id:
                seen_candidates.add(candidate_id)
    print(f"candidate_records={total}")
    print(f"known_targets={len(known_ids)} sources={len(source_ids)}")
    if errors:
        print("CANDIDATE_VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("CANDIDATE_VALIDATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
