#!/usr/bin/env python3
"""生成中文翻译队列（`docs/TRANSLATION-QUEUE.json` / `.md`），供分批翻译使用。

优先级（分值越高越先译）：
    1. 主线相关（案件挂了 arc / 与黑衣组织、FBI、主线角色相关）+50
    2. 知名案件白名单（早期经典名案）+40
    3. 集数越早越靠前（早期案件被引用最多）+ (1200 - 首集) // 20
    4. 字段越全越靠前（一次能补满一个案件的五个字段）+ 字段数 * 5
    5. 剧情为 TV Original（动画原创）的降权 -10（引用价值低）

只收集「en 有内容、zhHans 为空」的字段，绝不重复排已翻译的内容。

输出字段：caseId / field / priority / en(原文) / quote / page / block / caseTitle
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "entities" / "cases.json"
ARCS = ROOT / "data" / "manga" / "mainline-arcs.json"
OUT_JSON = ROOT / "docs" / "TRANSLATION-QUEUE.json"
OUT_MD = ROOT / "docs" / "TRANSLATION-QUEUE.md"

FIELDS = ("culprit", "motive", "method", "evidence", "resolution")

# 早期经典案件（中文社区讨论度最高，优先翻译）
FAMOUS = {
    "case-moon-shadow-island", "case-diplomat-murder", "case-library-murder",
    "case-golf-range-murder", "case-roller-coaster-murder", "case-kidnapping-of-a-popular-artist",
    "case-famous-potter-murder", "case-memories-of-first-love", "case-tsukumo-magician-murder",
    "case-yabuuchi-family-murder", "case-historical-actor-murder", "case-goblin-gang-mansion",
    "case-scoop-picture-murder", "case-farewell-wine-murder", "case-kogoro-date-murder",
}
MAINLINE_HINTS = ("black", "organization", "akai", "fbi", "bourbon", "rum", "kir", "vermouth", "haibara", "akai")


def main() -> None:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    arc_ids = {a["id"] for a in json.loads(ARCS.read_text(encoding="utf-8"))}

    items: list[dict] = []
    for c in cases:
        pending = []
        for field in FIELDS:
            value = c.get(field)
            if not isinstance(value, dict):
                continue
            en = (value.get("en") or "").strip()
            zh = (value.get("zhHans") or "").strip()
            if en and not zh:
                meta = (c.get("dcwL3Source") or {}).get(field) or {}
                pending.append(
                    {
                        "caseId": c["id"],
                        "field": field,
                        "en": en,
                        "quote": meta.get("quote"),
                        "page": meta.get("page") or c.get("dcwPage"),
                        "block": meta.get("block"),
                        "confidence": meta.get("confidence"),
                    }
                )
        if not pending:
            continue

        episodes = c.get("animeRefs") or []
        first_ep = 1200
        for ref in episodes:
            digits = "".join(ch for ch in ref if ch.isdigit())
            if digits:
                first_ep = min(first_ep, int(digits[:4]) if len(digits) >= 4 else 1200)

        score = 0
        if c.get("arc") in arc_ids:
            score += 50
        if c["id"] in FAMOUS:
            score += 40
        blob = " ".join([c["id"], (c.get("title") or {}).get("en") or ""]).lower()
        if any(h in blob for h in MAINLINE_HINTS):
            score += 30
        score += max(0, (1200 - first_ep) // 20)
        score += len(pending) * 5
        if c.get("kind") == "anime-original":
            score -= 10

        for p in pending:
            p["priority"] = score
            p["caseTitle"] = (c.get("title") or {}).get("en") or c["id"]
        items.extend(pending)

    items.sort(key=lambda x: (-x["priority"], x["caseId"], FIELDS.index(x["field"])))

    # 按案件分批：每批 20 案
    cases_order: list[str] = []
    for item in items:
        if item["caseId"] not in cases_order:
            cases_order.append(item["caseId"])
    batch_size = 20
    batch_of = {cid: i // batch_size + 1 for i, cid in enumerate(cases_order)}
    for item in items:
        item["batch"] = batch_of[item["caseId"]]

    total_batches = (len(cases_order) + batch_size - 1) // batch_size
    payload = {
        "generatedBy": "scripts/build-translation-queue.py",
        "policy": "只收集 en 有值且 zhHans 为空的字段；翻译须忠实原文，不增删事实",
        "totalFields": len(items),
        "totalCases": len(cases_order),
        "batchSize": batch_size,
        "totalBatches": total_batches,
        "items": items,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    lines = [
        "# L3 中文翻译队列",
        "",
        f"> 待译字段 **{len(items)}** 个，涉及 **{len(cases_order)}** 案，共 **{total_batches}** 批（每批 20 案）。",
        "> 生成：`python3 scripts/build-translation-queue.py`；写入：`scripts/apply-translations.py`。",
        "> 铁律：忠实英文原文，不增删事实；人名用通行中文译名，首次出现括注罗马字。",
        "",
        "| 批 | 案数 | 字段数 |",
        "|---|---|---|",
    ]
    for b in range(1, total_batches + 1):
        b_items = [i for i in items if i["batch"] == b]
        lines.append(f"| {b} | {len({i['caseId'] for i in b_items})} | {len(b_items)} |")
    lines += ["", "## 明细（按优先级）", ""]
    for item in items[:60]:
        lines.append(
            f"- **{item['caseId']}** · {item['field']} · 批 {item['batch']} · 优先级 {item['priority']}"
            f" · {len(item['en'])} 字符 · 页面 `{item['page']}`"
        )
    if len(items) > 60:
        lines.append(f"- …其余 {len(items) - 60} 条见 `docs/TRANSLATION-QUEUE.json`")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({k: payload[k] for k in ("totalFields", "totalCases", "totalBatches")}, ensure_ascii=False))
    print(f"wrote {OUT_JSON.relative_to(ROOT)} / {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
