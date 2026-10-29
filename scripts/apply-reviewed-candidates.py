#!/usr/bin/env python3
"""Apply accepted candidate fields to normalized episode records."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data" / "candidates" / "episodes.json"
EPISODES = ROOT / "data" / "episodes" / "episodes.json"
BATCHES = ROOT / "docs" / "CONTENT-BATCHES.json"

SUPPORTED = {"title.zhHans", "airDate", "mangaRefs"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def set_field(row: dict, field: str, value) -> None:
    if field == "title.zhHans":
        row.setdefault("title", {})["zhHans"] = value
    elif field == "airDate":
        row["airDate"] = value
    elif field == "mangaRefs":
        row["mangaRefs"] = value
    else:
        raise ValueError(f"unsupported field: {field}")


def get_field(row: dict, field: str):
    if field == "title.zhHans":
        return (row.get("title") or {}).get("zhHans")
    elif field == "airDate":
        return row.get("airDate")
    if field == "mangaRefs":
        return row.get("mangaRefs")
    raise ValueError(f"unsupported field: {field}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-id", required=True)
    args = parser.parse_args()
    candidates = load(CANDIDATES)
    episodes = load(EPISODES)
    by_id = {row.get("id"): row for row in episodes}
    changes = []
    errors = []
    for candidate in candidates:
        if candidate.get("reviewStatus") != "accepted" or not candidate.get("candidateId", "").startswith(args.batch_id):
            continue
        field = candidate.get("field")
        target = candidate.get("targetId")
        if field not in SUPPORTED:
            errors.append(f"{candidate.get('candidateId')}: unsupported accepted field {field!r}")
            continue
        row = by_id.get(target)
        if row is None:
            errors.append(f"{candidate.get('candidateId')}: unknown target {target!r}")
            continue
        old = get_field(row, field)
        new = candidate.get("value")
        if old != new:
            set_field(row, field, new)
            changes.append({"candidateId": candidate.get("candidateId"), "targetId": target, "field": field, "old": old, "new": new})

    if errors:
        print("APPLY_CANDIDATES_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    EPISODES.write_text(json.dumps(episodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    batches = load(BATCHES)
    for batch in batches.get("batches", []):
        if batch.get("batchId") == args.batch_id:
            batch["status"] = "applied"
            batch["effectiveChanges"] = len(changes)
            batch["validationResult"] = "pending-post-apply-validation"
            batch["appliedAt"] = "2026-10-27"
            break
    BATCHES.write_text(json.dumps(batches, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"accepted_candidates={sum(1 for row in candidates if row.get('reviewStatus') == 'accepted')}")
    print(f"effective_changes={len(changes)}")
    print("APPLY_CANDIDATES_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
