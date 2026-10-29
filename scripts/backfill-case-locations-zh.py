#!/usr/bin/env python3
"""M13：案件 locations 英译中（496 条，来自 /tmp/locs_zh.json）。

设计要点
- 只新增 `locationsZh` 平行数组，长度与 `locations` 严格一致，原文保留可回溯。
- 三条内部 id 泄漏（location-beika-town 等）同样按译文写入，前端优先读 locationsZh。
- 幂等：已存在且内容相同的字段跳过；二遍运行应输出 IDEMPOTENT_OK。
- 自检不通过整批不写盘。
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data/entities/cases.json"
MAP_FILE = Path("/tmp/locs_zh.json")
BACKUP = Path("/tmp/cases_pre_m13.json")
BACKUP_2 = Path("/tmp/cases_pre_m14.json")  # M14 备用，本脚本只用 M13

# 中文语境允许的拉丁缩写
ALLOW = {"RESO", "OK", "N", "U", "T", "TOMO", "P", "JR", "J", "TV", "TO", "KO"}


def bad_reason(text: str):
    """返回拒绝理由；None 表示通过。"""
    if not text or not text.strip():
        return "空值"
    latin = re.findall(r"[A-Za-z]+", text)
    leftover = [w for w in latin if w.upper() not in ALLOW]
    if leftover:
        return f"残留拉丁字母 {leftover[:3]}"
    return None


def main() -> int:
    mapping = json.loads(MAP_FILE.read_text(encoding="utf-8"))
    cases = json.loads(CASES.read_text(encoding="utf-8"))

    before = CASES.read_bytes()
    shutil.copyfile(CASES, BACKUP)

    unmapped = set()
    rejected = []
    written = 0
    for case in cases:
        locs = case.get("locations")
        if not isinstance(locs, list) or not locs:
            continue
        out = []
        for name in locs:
            zh = mapping.get(name)
            if zh is None:
                unmapped.add(name)
                out.append(None)
                continue
            reason = bad_reason(zh)
            if reason:
                rejected.append((case.get("id"), name, zh, reason))
                out.append(None)
                continue
            out.append(zh)
        if any(v is None for v in out):
            continue  # 有一条没译好就整案不写，避免半截数据
        if case.get("locationsZh") == out:
            continue
        case["locationsZh"] = out
        written += 1

    if unmapped or rejected:
        print(f"未映射 {len(unmapped)}: {sorted(unmapped)[:5]}")
        print(f"被拒 {len(rejected)}: {rejected[:3]}")
        print("自检未通过，不写盘")
        return 1

    payload = json.dumps(cases, ensure_ascii=False, indent=2) + "\n"
    if CASES.read_text(encoding="utf-8") == payload:
        print("IDEMPOTENT_OK（无改动，不写盘）")
        return 0

    CASES.write_text(payload, encoding="utf-8")
    total = sum(len(c["locationsZh"]) for c in cases if c.get("locationsZh"))
    print(f"M13_OK 词条 {len(mapping)}、写入 {written} 案、{total} 条地点中文")
    print(f"备份 {BACKUP}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
