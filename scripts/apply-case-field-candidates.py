#!/usr/bin/env python3
"""Apply the second case relation batch by deduplicated field merge."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data/candidates/entities.json"
CASES = ROOT / "data/entities/cases.json"
BATCHES = ROOT / "docs/CONTENT-BATCHES.json"
BATCH = "p3-case-relations-02"
FIELDS = {"characters", "locationRefs", "mangaRefs"}

candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
for row in candidates:
    if row.get("candidateId", "").startswith(BATCH):
        row["reviewStatus"] = "accepted"
        row["reviewNote"] = "已保留并应用现有案件字段；仅用于关系覆盖，不新增剧情。"
CANDIDATES.write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

cases = json.loads(CASES.read_text(encoding="utf-8"))
by_id = {row["id"]: row for row in cases}
changes = 0
for candidate in candidates:
    if not candidate.get("candidateId", "").startswith(BATCH):
        continue
    if candidate.get("reviewStatus") != "accepted":
        continue
    field = candidate.get("field")
    if field not in FIELDS:
        raise SystemExit(f"unsupported field: {field}")
    target = by_id.get(candidate.get("targetId"))
    if target is None:
        raise SystemExit(f"unknown case: {candidate.get('targetId')}")
    old = list(target.get(field, []))
    merged = list(dict.fromkeys(old + list(candidate.get("value") or [])))
    if merged != old:
        target[field] = merged
        changes += len(merged) - len(old)
CASES.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

batches = json.loads(BATCHES.read_text(encoding="utf-8"))
for batch in batches.get("batches", []):
    if batch.get("batchId") == BATCH:
        batch["status"] = "applied"
        batch["recordCount"] = 14
        batch["effectiveChanges"] = changes
        batch["validationResult"] = "pending-post-apply-validation"
        batch["appliedAt"] = "2026-10-27"
        break
BATCHES.write_text(json.dumps(batches, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"accepted_candidates={sum(r.get('candidateId','').startswith(BATCH) and r.get('reviewStatus') == 'accepted' for r in candidates)}")
print(f"effective_changes={changes}")
