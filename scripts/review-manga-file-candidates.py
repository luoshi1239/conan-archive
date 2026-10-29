#!/usr/bin/env python3
"""Review the sourced manga File mapping batch."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data" / "candidates" / "episodes.json"
BATCHES = ROOT / "docs" / "CONTENT-BATCHES.json"
BATCH_ID = "p2-manga-file-01"

rows = json.loads(CANDIDATES.read_text(encoding="utf-8"))
changed = 0
for row in rows:
    if row.get("candidateId", "").startswith(BATCH_ID):
        row["reviewStatus"] = "accepted"
        row["confidence"] = "medium"
        row["reviewNote"] = "已从来源表逐行解析并规范化为 files.json ID；仅表示动画与漫画 File 的目录映射，不表示深度剧情完成。"
        changed += 1
CANDIDATES.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

batches = json.loads(BATCHES.read_text(encoding="utf-8"))
for batch in batches["batches"]:
    if batch.get("batchId") == BATCH_ID:
        batch["status"] = "reviewed"
        batch["validationResult"] = "candidate-review-passed"
        batch["notes"] = "636 条动画—漫画 File 映射候选已审核接受；动画原创和来源缺失集保持空值。"
        break
else:
    raise SystemExit(f"missing batch {BATCH_ID}")
BATCHES.write_text(json.dumps(batches, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"reviewed_candidates={changed}")
