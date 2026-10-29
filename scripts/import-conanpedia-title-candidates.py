#!/usr/bin/env python3
"""Import title/date candidates from Conanpedia's TV anime table.

Only rows whose first column is the Japanese episode number and whose second
column is a numeric Japanese episode number are accepted. Replay/special rows
such as RTV and SPR are intentionally ignored.
"""
from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
URL = "https://www.conanpedia.com/%E5%90%8D%E4%BE%A6%E6%8E%A2%E6%9F%AF%E5%8D%97%E7%94%B5%E8%A7%86%E5%8A%A8%E7%94%BB"
SOURCE = "src-conanpedia-anime"
CANDIDATES = ROOT / "data" / "candidates" / "episodes.json"
BATCHES = ROOT / "docs" / "CONTENT-BATCHES.json"


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.row: list[str] | None = None
        self.cell: list[str] | None = None
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self.row is not None and self.cell is not None:
            self.row.append("".join(self.cell).strip())
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.row:
                self.rows.append(self.row)
            self.row = None

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)


def fetch_rows() -> list[tuple[int, str, str]]:
    request = Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8", "replace")
    parser = TableParser()
    parser.feed(html)
    result = []
    for row in parser.rows:
        if len(row) < 5:
            continue
        if not re.fullmatch(r"\d+", row[0]):
            continue
        if not re.fullmatch(r"\d+(?:-\d+)?", row[1]):
            continue
        result.append((int(row[0]), row[2], row[4]))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--skip", type=int, action="append", default=[])
    args = parser.parse_args()
    skipped = set(args.skip)
    if args.start < 1 or args.end < args.start:
        raise SystemExit("invalid range")

    source_rows = {number: (title, date) for number, title, date in fetch_rows()}
    missing = [number for number in range(args.start, args.end + 1) if number not in source_rows and number not in skipped]
    if missing:
        raise SystemExit(f"source missing episode numbers: {missing[:20]}")

    rows = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    existing = {row.get("candidateId") for row in rows}
    added = 0
    for number in range(args.start, args.end + 1):
        if number in skipped:
            continue
        title, air_date = source_rows[number]
        target = f"episode-{number:04d}"
        values = [("title.zhHans", title), ("airDate", air_date)]
        for field, value in values:
            candidate_id = f"{args.batch_id}-{number:04d}-{field.replace('.', '-') }"
            if candidate_id in existing:
                continue
            rows.append({
                "candidateId": candidate_id,
                "targetId": target,
                "field": field,
                "value": value,
                "sourceRefs": [SOURCE],
                "confidence": "medium",
                "reviewStatus": "pending",
                "reviewNote": "柯南百科电视动画表格候选，待字段级审核。",
            })
            existing.add(candidate_id)
            added += 1
    CANDIDATES.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    batches = json.loads(BATCHES.read_text(encoding="utf-8"))
    for batch in batches.get("batches", []):
        if batch.get("batchId") == args.batch_id:
            batch["status"] = "candidate"
            batch["recordCount"] = (args.end - args.start + 1 - len(skipped)) * 2
            batch["sourceIds"] = [SOURCE]
            batch["notes"] = "已从柯南百科表格筛选原始播出行；跳过来源缺失编号：" + ", ".join(str(number) for number in sorted(skipped)) + "；只生成中文标题和首播日期候选。"
            break
    else:
        raise SystemExit(f"missing batch {args.batch_id}")
    BATCHES.write_text(json.dumps(batches, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"range={args.start}-{args.end} candidate_records_added={added}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
