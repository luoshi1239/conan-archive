#!/usr/bin/env python3
"""统一剧集 summary 字段为字典结构，并补充剩余的英文原文摘要。

第一步：把旧格式字符串 summary 转成 {"zhHans": 原文, "en": "", "zhHant": ""}，不改中文内容。
第二步：对仍为空的集，从 DCW Situation 段搬运英文原文（宽松阈值，≥20 字符）。
幂等：二次运行 edits=0。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPISODES = ROOT / "data" / "episodes" / "episodes.json"
BLOCKS = ROOT / "data" / "raw" / "dcw-page-blocks.json"
PAGE_MAP_ALT = Path("/tmp/ca/dcw-page-map.json")


def clean_situation(paras: list[str]) -> list[str]:
    out = []
    for p in paras:
        p = p.strip()
        if re.fullmatch(r"[\d.]+\s*", p):
            continue
        if p.startswith("^ [") or p in ("Contents", "Show spoilers"):
            continue
        if len(p) < 20:
            continue
        out.append(p)
    return out


def main() -> None:
    blocks = json.loads(BLOCKS.read_text(encoding="utf-8"))["pages"]
    pm = json.loads(PAGE_MAP_ALT.read_text(encoding="utf-8"))
    ep2pages = pm["ep2pages"]

    raw = json.loads(EPISODES.read_text(encoding="utf-8"))
    rows = raw if isinstance(raw, list) else raw.get("episodes", [])
    by_num = {str(r["number"]): r for r in rows if r.get("number")}

    conv, filled, still_empty = 0, 0, 0
    for r in rows:
        s = r.get("summary")
        if isinstance(s, str):  # 旧格式中文
            zh = s
            r["summary"] = {"en": "", "zhHans": zh, "zhHant": "", "legacy": True}
            conv += 1
    for num_s, page_list in ep2pages.items():
        row = by_num.get(num_s)
        if row is None:
            continue
        s = row.get("summary")
        if isinstance(s, dict) and s.get("en"):
            continue  # 已有英文
        page = page_list[0]
        sit = clean_situation(blocks.get(page, {}).get("Situation") or [])
        joined = " ".join(sit).strip()
        if len(joined) < 40:
            still_empty += 1
            continue
        if not isinstance(s, dict):
            row["summary"] = {"en": joined, "zhHans": "", "zhHant": ""}
        else:
            s["en"] = joined
        filled += 1

    EPISODES.write_text(json.dumps(raw, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"converted_legacy={conv} filled_en={filled} still_empty={still_empty} rows={len(rows)}")


if __name__ == "__main__":
    main()