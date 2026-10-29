#!/usr/bin/env python3
"""M1：为缺 summary 的案件补「案件设定」原文。

为什么只用 situation，不用 resolution
------------------------------------
实测 `resolution` 是**解答**，首句直接点名凶手：
    "Satoshi Miyahara is the kidnapper who wants to destroy Two-Mix..."
    "The killer is Akiko Yonehara, inspired by the death of..."
把它写进 summary，等于在列表页把底泄了。`resolution` 的内容已有
`resolution` / `deepSpoilers` 字段承载，不该再进 summary。

所以本脚本只从 `situation`（案件设定段）取原文，取不到就留空，
宁缺毋滥，不拿解答冒充摘要。

写入格式
--------
`summary = {en: "<原文>"}`（对象形态，与剧集 summary 一致）
  → 前端 `textOf()` 取 en、`langOf()` 返回 'en'
  → `labelOf()` 自动加「英文原文·待译」，不会伪装成中文
另写 `summarySource`（DCW 页名）+ `summaryQuote: true` 留痕。

拼接规则
--------
`situation` 是 [叙述段, 小节标题, 叙述段, ...] 结构。跳过纯标题行，
按顺序累积叙述段直到 ≥200 字符（最多 3 段），段间用空行连接。
全程逐字搬运，不改写、不删减、不补充。

幂等：summary 非空一律跳过；内容不变不写盘。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data/entities/cases.json"
SECTIONS = ROOT / "data/raw/dcw-page-sections.json"
DRY = "--dry-run" in sys.argv

TARGET_LEN = 200
MAX_PARAS = 3
# 小节标题：全大写/首字母大写、无句读、词数少（如 Murder / Conclusion / Aftermath）
HEADING = re.compile(r"^[A-Z][A-Za-z' \-]{1,40}$")


def is_heading(s: str) -> bool:
    return bool(HEADING.match(s)) and len(s.split()) <= 5


def compose(situation) -> str:
    """从 situation 段落序列里取设定段，逐字拼接。"""
    paras = []
    total = 0
    for raw in situation or []:
        s = str(raw).strip()
        if not s or is_heading(s):
            continue
        paras.append(s)
        total += len(s)
        if total >= TARGET_LEN or len(paras) >= MAX_PARAS:
            break
    return "\n\n".join(paras)


def main() -> int:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    sections = json.loads(SECTIONS.read_text(encoding="utf-8"))["pages"]

    filled = 0
    skipped_has = 0
    no_section = []
    no_situation = []

    for c in cases:
        if c.get("summary"):
            skipped_has += 1
            continue

        page = c.get("dcwPage")
        sec = sections.get(page) if page else None
        if not sec:
            no_section.append(c.get("id"))
            continue

        text = compose(sec.get("situation"))
        if not text:
            # 只有 resolution（解答）→ 不补，避免泄底
            no_situation.append(c.get("id"))
            continue

        if not DRY:
            c["summary"] = {"en": text}
            c["summarySource"] = page
            c["summaryQuote"] = True
        filled += 1

    print(f"M1 案件 summary：补 {filled} 条（已有 {skipped_has} 条跳过）")
    print(f"   无 sections 记录：{len(no_section)}")
    print(f"   仅有解答无设定段（不补）：{len(no_situation)}")

    if DRY:
        print("   [dry-run] 未写盘")
        return 0
    if filled == 0:
        print("   IDEMPOTENT_OK（无改动，不写盘）")
        return 0

    CASES.write_text(
        json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("   已写入 cases.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
