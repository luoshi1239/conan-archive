#!/usr/bin/env python3
"""把 docs/L3-APPROVED.json 里人工批准的字段写入案件实体。

铁律：
    - **绝不覆盖**已有非空字段（人工中文内容优先）；
    - 写入的是 DCW 页面原文（value 字段），不翻译不改写；
    - 同时记录 `dcwL3Source`（页面 + 段落类型 + 置信度）以便追溯；
    - 只处理 L3-APPROVED.json 中列出的 caseId，未列出的一律不动；
    - 幂等：二次运行零改动。

用法：
    python3 scripts/apply-l3-approved.py            # 执行写入
    python3 scripts/apply-l3-approved.py --dry-run  # 只报告将写入什么

输出：data/entities/cases.json；docs/L3-APPLY-APPROVED-REPORT.json
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "entities" / "cases.json"
APPROVED = ROOT / "docs" / "L3-APPROVED.json"
REPORT = ROOT / "docs" / "L3-APPLY-APPROVED-REPORT.json"
BACKUP = Path("/tmp/ca/cases_pre_l3_approved.json")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    approved = json.loads(APPROVED.read_text(encoding="utf-8"))
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in cases}

    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    if not BACKUP.exists():
        shutil.copy2(CASES, BACKUP)

    written: list[dict] = []
    skipped: list[dict] = []
    for entry in approved["cases"]:
        case = by_id.get(entry["caseId"])
        if not case:
            skipped.append({"caseId": entry["caseId"], "reason": "case_not_found"})
            continue
        src = case.setdefault("dcwL3Source", {})
        for field, cand in entry["fields"].items():
            if case.get(field):
                skipped.append({"caseId": entry["caseId"], "field": field,
                                "reason": "already_has_value"})
                continue
            case[field] = cand["value"]
            src[field] = {
                "page": entry.get("page"),
                "block": cand.get("block"),
                "confidence": cand.get("confidence"),
                "quote": cand.get("quote"),
                "lang": "en",
                "reviewedBy": "L3-APPROVED.json",
            }
            written.append({"caseId": entry["caseId"], "field": field,
                            "chars": len(cand["value"]), "confidence": cand.get("confidence")})

    if not args.dry_run:
        CASES.write_text(json.dumps(cases, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        REPORT.write_text(
            json.dumps(
                {
                    "generatedBy": "scripts/apply-l3-approved.py",
                    "approvedFile": str(APPROVED.relative_to(ROOT)),
                    "policy": "只写空字段；DCW 原文英文；不覆盖人工中文",
                    "writtenFields": len(written),
                    "skippedEntries": len(skipped),
                    "fields": written,
                    "skipped": skipped,
                },
                ensure_ascii=False,
                indent=1,
            )
            + "\n",
            encoding="utf-8",
        )

    print(json.dumps({"dryRun": args.dry_run, "writtenFields": len(written),
                      "skippedEntries": len(skipped)}, ensure_ascii=False))
    if written:
        import collections
        print("by field:", dict(collections.Counter(w["field"] for w in written)))
    if skipped:
        import collections
        print("skip reasons:", dict(collections.Counter(s["reason"] for s in skipped)))
    if args.dry_run:
        print("(dry-run：未写入文件)")


if __name__ == "__main__":
    main()
