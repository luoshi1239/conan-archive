#!/usr/bin/env python3
"""统一案件实体的状态字段，消除 None / 布尔不一致。

规则（唯一真相）：
  detailStatus  ∈ {catalog, partial, deepSpoilers}
      catalog      —— 只有目录/基础事实
      partial      —— 已有部分 L3（如仅有 culprit）
      deepSpoilers —— 五字段齐全
  deepSpoilers(布尔) 仅当 detailStatus == 'deepSpoilers' 时为 True，否则必须删除
  status        ∈ {catalog, reviewed}；None 视为 catalog（除非有 L3 内容）

幂等：第二次运行 changed=0。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "entities" / "cases.json"
REPORT = ROOT / "docs" / "CASE-STATUS-NORMALIZE.json"

L3 = ("culprit", "motive", "method", "evidence", "resolution")


def filled(value) -> bool:
    """字段是否有内容：兼容纯字符串（旧）与 {zhHans, en, translationStatus}（新）。"""
    if isinstance(value, dict):
        return any(isinstance(value.get(k), str) and value[k].strip() for k in ("zhHans", "en"))
    return bool(value)


def main() -> None:
    raw = json.loads(CASES.read_text(encoding="utf-8"))
    rows = raw if isinstance(raw, list) else raw.get("cases", [])

    changed = 0
    fixed_detail = 0
    fixed_status = 0
    fixed_flag = 0

    for r in rows:
        before = (r.get("detailStatus"), r.get("status"), "deepSpoilers" in r)

        full = all(filled(r.get(f)) for f in L3)
        any_l3 = any(filled(r.get(f)) for f in L3)

        if full:
            ds = "deepSpoilers"
        elif any_l3:
            ds = "partial"
        else:
            ds = "catalog"
        if r.get("detailStatus") != ds:
            r["detailStatus"] = ds
            fixed_detail += 1

        # 布尔标志只在 deepSpoilers 时存在，且必须与 detailStatus 同步
        if ds == "deepSpoilers":
            if r.get("deepSpoilers") is not True:
                r["deepSpoilers"] = True
                fixed_flag += 1
        else:
            if "deepSpoilers" in r:
                r.pop("deepSpoilers")
                fixed_flag += 1

        st = r.get("status")
        if st not in ("catalog", "reviewed"):
            r["status"] = "reviewed" if any_l3 else "catalog"
            fixed_status += 1

        if (r.get("detailStatus"), r.get("status"), "deepSpoilers" in r) != before:
            changed += 1

    if isinstance(raw, dict):
        raw["cases"] = rows
        CASES.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        CASES.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = {
        "cases": len(rows),
        "changed": changed,
        "fixedDetailStatus": fixed_detail,
        "fixedStatus": fixed_status,
        "fixedDeepFlag": fixed_flag,
        "distribution": {
            ds: sum(1 for r in rows if r.get("detailStatus") == ds)
            for ds in ("catalog", "partial", "deepSpoilers")
        },
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
