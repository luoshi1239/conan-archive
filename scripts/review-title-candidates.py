#!/usr/bin/env python3
"""Review the first title/date candidate batch after source inspection."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data" / "candidates" / "episodes.json"
BATCHES = ROOT / "docs" / "CONTENT-BATCHES.json"
BATCH_ID = "p1-title-01"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-id", required=True)
    args = parser.parse_args()
    batch_id = args.batch_id
    rows = json.loads(PATH.read_text(encoding="utf-8"))
    changed = 0
    for row in rows:
        if row.get("candidateId", "").startswith(batch_id):
            row["reviewStatus"] = "accepted"
            row["confidence"] = "medium"
            row["reviewNote"] = (
                "已从柯南百科电视动画逐集表格核对；第二来源当前网络握手失败，"
                "保留 medium 可信度，后续补充交叉核对。"
            )
            changed += 1
    PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    batches = json.loads(BATCHES.read_text(encoding="utf-8"))
    for batch in batches.get("batches", []):
        if batch.get("batchId") == batch_id:
            batch["status"] = "reviewed"
            batch["validationResult"] = "candidate-review-passed"
            batch["notes"] = (
                "标题和首播日期候选已审核接受；单一可读取来源，medium 可信度；"
                "漫画 File 因尚无规范化 File ID 暂不应用。"
            )
            break
    else:
        raise SystemExit(f"missing batch {batch_id}")
    BATCHES.write_text(json.dumps(batches, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"reviewed_candidates={changed}")
    print("REVIEW_TITLE_CANDIDATES_OK")


if __name__ == "__main__":
    main()
