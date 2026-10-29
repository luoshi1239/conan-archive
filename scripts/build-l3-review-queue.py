#!/usr/bin/env python3
"""生成 L3 人工审核队列（Markdown + JSON），供用户一次性总审。

输出：
  docs/L3-REVIEW-QUEUE.md     人读，按「四字段齐全」优先排序
  docs/L3-REVIEW-QUEUE.json   机读

原则：只展示原文，不改写、不翻译。用户审核后由 apply 脚本写入。
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANDS = ROOT / "data" / "candidates" / "dcw-l3.json"
CASES = ROOT / "data" / "entities" / "cases.json"
MD = ROOT / "docs" / "L3-REVIEW-QUEUE.md"
JSON_OUT = ROOT / "docs" / "L3-REVIEW-QUEUE.json"

FIELDS = ("culprit", "motive", "method", "evidence")


def main() -> None:
    cands = json.loads(CANDS.read_text(encoding="utf-8"))["candidates"]
    cases_raw = json.loads(CASES.read_text(encoding="utf-8"))
    rows = cases_raw if isinstance(cases_raw, list) else cases_raw.get("cases", [])
    by_page = {r["dcwPage"]: r for r in rows if r.get("dcwPage")}

    bucket: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for c in cands:
        bucket[c["dcwPage"]][c["field"]].append(c)

    items = []
    for page, fields in bucket.items():
        row = by_page.get(page)
        have = [f for f in FIELDS if fields.get(f)]
        score = len(have)
        items.append({
            "page": page,
            "caseId": (row or {}).get("id"),
            "displayTitle": ((row or {}).get("title") or {}).get("en") or page.replace("_", " "),
            "episodes": (row or {}).get("animeRefs") or [],
            "currentDetailStatus": (row or {}).get("detailStatus"),
            "fieldsWithCandidate": have,
            "completeness": f"{score}/4",
            "readyToApprove": score == 4,
            "candidates": {
                f: [{"value": x["value"], "confidence": x["confidence"],
                     "quote": x.get("quote"), "block": x.get("sourceBlock")}
                    for x in fields[f]]
                for f in FIELDS if fields.get(f)
            },
        })

    items.sort(key=lambda x: (not x["readyToApprove"], x["page"]))
    ready = [i for i in items if i["readyToApprove"]]

    JSON_OUT.write_text(
        json.dumps({"total": len(items), "readyToApprove": len(ready), "items": items},
                   ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# L3 深度剧透 · 人工审核队列",
        "",
        f"- 待审案件：**{len(items)}**",
        f"- 四字段候选齐全（可直接批准）：**{len(ready)}**",
        "- 所有 value 均为 DCW 页面原文，**未翻译、未改写**。",
        "- 批准方式：在 `docs/L3-APPROVED.json` 中列出 caseId 与要写入的字段，再运行 apply 脚本。",
        "",
        "---",
        "",
    ]

    for it in items[:400]:
        mark = "✅" if it["readyToApprove"] else "◻"
        lines.append(f"## {mark} {it['displayTitle']}")
        lines.append("")
        lines.append(f"- page: `{it['page']}`")
        lines.append(f"- caseId: `{it['caseId']}`")
        lines.append(f"- 集: {', '.join(it['episodes'][:6]) or '—'}")
        lines.append(f"- 候选字段: {it['completeness']} ({', '.join(it['fieldsWithCandidate'])})")
        lines.append(f"- 当前状态: `{it['currentDetailStatus']}`")
        lines.append("")
        for f in FIELDS:
            if f not in it["candidates"]:
                continue
            for c in it["candidates"][f]:
                v = c["value"].replace("\n", " ")
                if len(v) > 700:
                    v = v[:700] + " …"
                lines.append(f"**{f}** `{c['confidence']}` — {v}")
                lines.append("")
        lines.append("---")
        lines.append("")

    if len(items) > 400:
        lines.append(f"> 仅列前 400 条，完整 {len(items)} 条见 `docs/L3-REVIEW-QUEUE.json`。")
        lines.append("")

    MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"items={len(items)} readyToApprove={len(ready)}")
    print(f"wrote {MD.relative_to(ROOT)} ({MD.stat().st_size} bytes)")
    print(f"wrote {JSON_OUT.relative_to(ROOT)} ({JSON_OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
