#!/usr/bin/env python3
"""从 L3 审核队列生成待批准清单 docs/L3-APPROVED.json。

用法：
    python3 scripts/build-l3-approved.py                 # 默认：四字段，只挑空字段
    python3 scripts/build-l3-approved.py --fields culprit,motive,method,evidence
    python3 scripts/build-l3-approved.py --min-confidence high

规则（不编造、不覆盖）：
    - 只挑「案件该字段当前为空」的候选，已有值的字段需要人先决定是否替换；
    - 只有一个候选的字段才自动列为 approved，多候选的进 needsHuman 清单；
    - 候选值一律保留原文 value + quote + block + confidence，不翻译不改写。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "docs" / "L3-REVIEW-QUEUE.json"
CASES = ROOT / "data" / "entities" / "cases.json"
OUT = ROOT / "docs" / "L3-APPROVED.json"

FIELDS = ("culprit", "motive", "method", "evidence")
CONF_RANK = {"high": 2, "medium": 1, "low": 0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fields", default=",".join(FIELDS))
    ap.add_argument("--min-confidence", default="medium", choices=list(CONF_RANK))
    ap.add_argument("--include-occupied", action="store_true",
                    help="已有值的字段也列入（默认跳过，避免覆盖人工内容）")
    ap.add_argument("--only-ready", action="store_true",
                    help="只批准审核队列里 readyToApprove=true 的案件（四字段候选齐全那批）")
    args = ap.parse_args()

    fields = [f.strip() for f in args.fields.split(",") if f.strip()]
    min_rank = CONF_RANK[args.min_confidence]

    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    cases = {c["id"]: c for c in json.loads(CASES.read_text(encoding="utf-8"))}

    approved: list[dict] = []
    skipped: list[dict] = []
    needs_human: list[dict] = []

    for item in queue["items"]:
        if args.only_ready and not item.get("readyToApprove"):
            continue
        case = cases.get(item["caseId"])
        if not case:
            skipped.append({"caseId": item["caseId"], "reason": "case_not_found"})
            continue
        picks: dict[str, dict] = {}
        for field in fields:
            if case.get(field) and not args.include_occupied:
                skipped.append(
                    {"caseId": item["caseId"], "field": field, "reason": "already_has_value"}
                )
                continue
            cands = [c for c in (item["candidates"].get(field) or [])
                     if CONF_RANK.get(c.get("confidence", "low"), 0) >= min_rank]
            if not cands:
                continue
            if len(cands) > 1:
                needs_human.append(
                    {"caseId": item["caseId"], "field": field,
                     "options": [{"value": c["value"], "confidence": c["confidence"]} for c in cands]}
                )
                continue
            picks[field] = cands[0]
        if len(picks) >= 2:  # 至少两个字段才值得升级为 deepSpoilers
            approved.append(
                {
                    "caseId": item["caseId"],
                    "page": item.get("page"),
                    "episodes": item.get("episodes"),
                    "fields": picks,
                }
            )

    out = {
        "generatedBy": "scripts/build-l3-approved.py",
        "params": {"fields": fields, "minConfidence": args.min_confidence,
                   "includeOccupied": args.include_occupied},
        "policy": "只挑空字段；候选为 DCW 原文；不翻译不改写；多候选不自动批准",
        "approvedCases": len(approved),
        "skippedEntries": len(skipped),
        "needsHumanEntries": len(needs_human),
        "cases": approved,
        "skipped": skipped,
        "needsHuman": needs_human,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if not isinstance(v, list)}, ensure_ascii=False))
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
