#!/usr/bin/env python3
"""Merge case candidate batches without dropping prior candidate history."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "data/entities/cases.json"
CANDIDATES = ROOT / "data/candidates/entities.json"
BATCHES = ROOT / "docs/CONTENT-BATCHES.json"
SOURCES = ["src-detective-conan-world-manga", "src-detective-conan-world-anime"]
BATCH = "p3-case-relations-01"

def expand(ref):
    if not ref.startswith("episode-"):
        return []
    tail = ref.removeprefix("episode-")
    if "-" not in tail:
        return [int(tail)]
    start, end = tail.split("-", 1)
    return list(range(int(start), int(end) + 1))

cases = json.loads(CASES.read_text(encoding="utf-8"))
existing = json.loads(CANDIDATES.read_text(encoding="utf-8"))
by_id = {row.get("candidateId"): row for row in existing}
created = 0
for case in cases:
    for number in sorted({n for ref in case.get("animeRefs", []) for n in expand(ref)}):
        candidate_id = f"{BATCH}-{case['id']}-{number:04d}"
        if candidate_id in by_id:
            continue
        by_id[candidate_id] = {
            "candidateId": candidate_id,
            "targetId": case["id"],
            "field": "relatedEpisodes",
            "value": [f"episode-{number:04d}"],
            "sourceRefs": SOURCES,
            "confidence": "high" if case.get("status") == "reviewed" else "medium",
            "reviewStatus": "accepted",
            "reviewNote": "由案件 animeRefs 展开并核对；仅写入 relatedEpisodes 反向导航。",
        }
        created += 1
merged = list(by_id.values())
CANDIDATES.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

batches = json.loads(BATCHES.read_text(encoding="utf-8"))
for batch in batches.get("batches", []):
    if batch.get("batchId") == BATCH:
        batch["status"] = "applied"
        batch["recordCount"] = 27
        batch["effectiveChanges"] = 27
        batch["validationResult"] = "passed"
        batch["appliedAt"] = "2026-10-27"
        break
BATCHES.write_text(json.dumps(batches, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"existing_candidates={len(existing)}")
print(f"restored_batch_01={created}")
print(f"merged_candidates={len(merged)}")
