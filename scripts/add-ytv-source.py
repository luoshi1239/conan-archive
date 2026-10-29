#!/usr/bin/env python3
"""登记読売テレビ（YTV）官方站点为来源。

为什么需要这一步
----------------
`scripts/validate-data.py` 会校验引用到的 source id 必须存在于
`data/sources.json`。YTV 的 `data/case.json` 提供了 1217 集的官方日文
剧情简介（`conan_story`），是 DCW 之外的第二个官方来源，用来补 DCW
正文缺失的 5 集（713/714/882/1061/1187）。

幂等：已存在则不改动（只补缺失字段）。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
P = ROOT / "data/sources.json"

SRC = {
    "id": "src-yomiuri-tv-conan",
    "title": "読売テレビ · 名探偵コナン 公式サイト",
    "url": "https://www.ytv.co.jp/conan/",
    "type": "official",
    "scope": "各话官方日文剧情简介（conan_story）、日文标题、播出日期",
    "accessed": "2026-10-28",
    "notes": (
        "データは data/case.json（サイト内静的 JSON）から取得。"
        "官方台方站点，供 DCW 正文缺失的剧集补日文简介；不提供破案者字段。"
    ),
}

doc = json.loads(P.read_text(encoding="utf-8"))
sources = doc["sources"]
have = {s.get("id") for s in sources}

if SRC["id"] in have:
    existing = next(s for s in sources if s.get("id") == SRC["id"])
    added = []
    for k, v in SRC.items():
        if k not in existing or existing[k] in ("", None):
            existing[k] = v
            added.append(k)
    if added:
        P.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"已补字段: {added}")
    else:
        print("已存在且完整，0 改动")
else:
    sources.append(SRC)
    P.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"新增来源 {SRC['id']}，共 {len(sources)} 条")
