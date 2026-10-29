#!/usr/bin/env python3
"""M14：案件 suspects 英译中（374 条，来自 /tmp/sus_zh_all.json）。

设计要点
- 只新增 `suspectsZh` 平行数组，长度与 `suspects` 严格一致，原文保留可回溯。
- 嫌疑人是描述性短语（"Bearded guy with sunglasses"、"Torada and Tatsuo families"），
  与人名不同，必须逐条意译而非音译。
- 幂等：二遍运行应输出 IDEMPOTENT_OK。
- 自检不通过整批不写盘。
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data/entities/cases.json"
MAP_FILE = Path("/tmp/sus_zh_all.json")
BACKUP = Path("/tmp/cases_pre_m14.json")

# 中文语境允许保留的拉丁缩写
ALLOW = {"OK", "TV", "JR", "J", "P", "C", "B", "N"}


def bad_reason(text: str):
    if not text or not text.strip():
        return "空值"
    leftover = [w for w in re.findall(r"[A-Za-z]+", text) if w.upper() not in ALLOW]
    if leftover:
        return f"残留拉丁字母 {leftover[:3]}"
    return None


def main() -> int:
    mapping = json.loads(MAP_FILE.read_text(encoding="utf-8"))
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    shutil.copyfile(CASES, BACKUP)

    unmapped, rejected, written = set(), [], 0
    for case in cases:
        sus = case.get("suspects")
        if not isinstance(sus, list) or not sus:
            continue
        out = []
        for name in sus:
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
            continue
        if case.get("suspectsZh") == out:
            continue
        case["suspectsZh"] = out
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
    total = sum(len(c["suspectsZh"]) for c in cases if c.get("suspectsZh"))
    print(f"M14_OK 词条 {len(mapping)}、写入 {written} 案、{total} 条嫌疑人中文")
    print(f"备份 {BACKUP}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
