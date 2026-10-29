#!/usr/bin/env python3
"""Report planned batches and measurable candidate progress."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCHES = ROOT / "docs" / "CONTENT-BATCHES.json"
CANDIDATE_FILES = [
    ROOT / "data" / "candidates" / "episodes.json",
    ROOT / "data" / "candidates" / "entities.json",
    ROOT / "data" / "candidates" / "catalog.json",
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def candidate_summary() -> dict[str, object]:
    rows = []
    for path in CANDIDATE_FILES:
        if path.exists():
            values = load(path)
            if isinstance(values, list):
                rows.extend(values)
    statuses = Counter(row.get("reviewStatus") for row in rows)
    fields = Counter(row.get("field") for row in rows)
    return {
        "total": len(rows),
        "reviewStatus": dict(sorted(statuses.items(), key=lambda item: str(item[0]))),
        "accepted": statuses.get("accepted", 0),
        "pending": statuses.get("pending", 0),
        "rejected": statuses.get("rejected", 0),
        "fields": dict(sorted(fields.items())),
    }


def main() -> int:
    data = load(BATCHES)
    batches = data.get("batches", [])
    ids = [batch.get("batchId") for batch in batches]
    duplicate_ids = sorted(batch_id for batch_id in set(ids) if ids.count(batch_id) > 1)
    summary = candidate_summary()
    report = {
        "generatedFrom": ["docs/CONTENT-BATCHES.json", "data/candidates/*.json"],
        "batchCount": len(batches),
        "batchStatus": dict(sorted(Counter(batch.get("status") for batch in batches).items(), key=lambda item: str(item[0]))),
        "duplicateBatchIds": duplicate_ids,
        "candidateSummary": summary,
        "effectiveChanges": sum(int(batch.get("effectiveChanges") or 0) for batch in batches),
        "batches": batches,
    }
    output = ROOT / "docs" / "BATCH-PROGRESS.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"WROTE {output.relative_to(ROOT)}")
    return 1 if duplicate_ids else 0


if __name__ == "__main__":
    raise SystemExit(main())
