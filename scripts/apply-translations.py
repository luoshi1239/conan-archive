#!/usr/bin/env python3
"""把翻译稿写入案件字段的 zhHans 槽位。

翻译稿存放：`docs/translations/batch-XXX.json`，格式：

    {
      "batch": 1,
      "translator": "ai",
      "items": [
        {"caseId": "case-...", "field": "motive", "zhHans": "中文译文"}
      ]
    }

规则（铁律）：
    - **不覆盖**已有 zhHans；只填空白槽位（幂等，重跑零改动）；
    - 写入后 `translationStatus = "machine"`、`reviewed = false`，供人工抽检；
    - 译文必须与 en 原文对应；本脚本校验字段确实存在且有 en 原文，否则拒绝写入；
    - 写入后自动重跑 normalize-case-status.py（deepSpoilers 判定依赖五字段）。

输出：data/entities/cases.json；docs/TRANSLATION-APPLY-REPORT.json
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "entities" / "cases.json"
TRANSLATIONS = ROOT / "docs" / "translations"
REPORT = ROOT / "docs" / "TRANSLATION-APPLY-REPORT.json"
BACKUP = Path("/tmp/ca/cases_pre_translations.json")

FIELDS = ("culprit", "motive", "method", "evidence", "resolution")


def en_hash(text: str) -> str:
    """英文原文指纹：译文必须永远对应它被翻译时的那段原文。"""
    return hashlib.sha1((text or "").strip().encode("utf-8")).hexdigest()[:12]
MIN_RATIO = 0.15   # 译文长度不得低于原文的 15%（防占位式偷懒）
MAX_RATIO = 1.2    # 也不得离谱地长（防加戏）


def main() -> None:
    files = sorted(TRANSLATIONS.glob("batch-*.json"))
    if not files:
        print("没有找到 docs/translations/batch-*.json")
        return

    cases = json.loads(CASES.read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in cases}

    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    if not BACKUP.exists():
        shutil.copy2(CASES, BACKUP)

    written: list[dict] = []
    rejected: list[dict] = []
    skipped: list[dict] = []

    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data.get("items", []):
            case_id = item.get("caseId")
            field = item.get("field")
            zh = (item.get("zhHans") or "").strip()
            if field not in FIELDS:
                rejected.append({"caseId": case_id, "field": field, "reason": "unknown_field"})
                continue
            case = by_id.get(case_id)
            if not case:
                rejected.append({"caseId": case_id, "field": field, "reason": "case_not_found"})
                continue
            value = case.get(field)
            if not isinstance(value, dict):
                rejected.append({"caseId": case_id, "field": field, "reason": "field_not_bilingual"})
                continue
            if (value.get("zhHans") or "").strip():
                # 已有译文：校验原文是否变了（变了就作废该译文，重新入队）
                stored = value.get("translationSourceHash")
                current = en_hash(value.get("en") or "")
                if stored and stored != current:
                    value["zhHans"] = ""
                    value["translationStatus"] = "pending"
                    value["translationStale"] = True
                    rejected.append({"caseId": case_id, "field": field,
                                     "reason": "stale_cleared(原文已变更)"})
                else:
                    skipped.append({"caseId": case_id, "field": field, "reason": "already_translated"})
                continue
            en = (value.get("en") or "").strip()
            if not en:
                rejected.append({"caseId": case_id, "field": field, "reason": "no_english_source"})
                continue
            if not zh:
                rejected.append({"caseId": case_id, "field": field, "reason": "empty_translation"})
                continue
            ratio = len(zh) / max(1, len(en))
            if ratio < MIN_RATIO:
                rejected.append({"caseId": case_id, "field": field,
                                 "reason": f"too_short(ratio={ratio:.2f})"})
                continue
            if ratio > MAX_RATIO:
                rejected.append({"caseId": case_id, "field": field,
                                 "reason": f"too_long(ratio={ratio:.2f})"})
                continue
            value["zhHans"] = zh
            value["translationStatus"] = "machine"
            value["translationSourceHash"] = en_hash(en)
            value["reviewed"] = False
            value["translationBatch"] = data.get("batch")
            written.append({"caseId": case_id, "field": field, "chars": len(zh),
                            "ratio": round(ratio, 2), "file": path.name})

    CASES.write_text(json.dumps(cases, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    REPORT.write_text(
        json.dumps(
            {
                "generatedBy": "scripts/apply-translations.py",
                "policy": "只填空 zhHans；标记 machine + reviewed=false；长度比例校验防占位与加戏",
                "written": len(written),
                "skipped": len(skipped),
                "rejected": len(rejected),
                "items": written,
                "skippedItems": skipped,
                "rejectedItems": rejected,
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"written": len(written), "skipped": len(skipped),
                      "rejected": len(rejected)}, ensure_ascii=False))
    if rejected:
        for item in rejected[:10]:
            print("  rejected:", item)

    if written:
        subprocess.run([sys.executable, str(ROOT / "scripts" / "normalize-case-status.py")], check=False)


if __name__ == "__main__":
    main()
