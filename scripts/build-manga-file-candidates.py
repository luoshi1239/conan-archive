#!/usr/bin/env python3
"""Build a sourced manga File index and episode-to-File candidate mappings.

The source table's first numeric column is the Japanese TV episode number. Rows
with RTV/SPR-style replay labels are excluded by requiring a numeric second
column. Anime-original rows are not mapped to manga Files.
"""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://www.conanpedia.com/%E5%90%8D%E4%BE%A6%E6%8E%A2%E6%9F%AF%E5%8D%97%E7%94%B5%E8%A7%86%E5%8A%A8%E7%94%BB"
SOURCE_ID = "src-conanpedia-anime"
FILES = ROOT / "data" / "manga" / "files.json"
CANDIDATES = ROOT / "data" / "candidates" / "episodes.json"
BATCHES = ROOT / "docs" / "CONTENT-BATCHES.json"
BATCH_ID = "p2-manga-file-01"


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.row = None
        self.cell = None
        self.rows = []

    def handle_starttag(self, tag, attrs) -> None:
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []

    def handle_endtag(self, tag) -> None:
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


def fetch_rows():
    request = Request(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8", "replace")
    parser = TableParser()
    parser.feed(html)
    for row in parser.rows:
        if len(row) < 7:
            continue
        if not re.fullmatch(r"\d+", row[0]) or not re.fullmatch(r"\d+(?:-\d+)?", row[1]):
            continue
        yield int(row[0]), row[2], row[6]


def file_id(raw: str) -> str | None:
    match = re.search(r"(?:File|SVFile)\.([0-9]+(?:-[0-9]+)?)", raw)
    if not match:
        return None
    value = match.group(1)
    if "-" in value:
        start, end = value.split("-", 1)
        return f"file-{int(start):03d}-{int(end):03d}"
    return f"file-{int(value):03d}"


def main() -> int:
    source_rows = list(fetch_rows())
    files = {}
    episode_refs = {}
    for number, title, raw_manga in source_rows:
        ref = file_id(raw_manga)
        if not ref:
            continue
        files.setdefault(ref, {
            "id": ref,
            "rawLabel": raw_manga,
            "title": None,
            "kind": "manga-file-range",
            "animeRefs": [],
            "sources": [SOURCE_ID],
            "status": "catalog",
        })
        files[ref]["animeRefs"].append(f"episode-{number:04d}")
        episode_refs[number] = ref

    for row in files.values():
        row["animeRefs"] = sorted(set(row["animeRefs"]))

    FILES.write_text(json.dumps(sorted(files.values(), key=lambda row: row["id"]), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    existing = {row.get("candidateId") for row in candidates}
    added = 0
    for number, ref in sorted(episode_refs.items()):
        candidate_id = f"{BATCH_ID}-{number:04d}"
        if candidate_id in existing:
            continue
        candidates.append({
            "candidateId": candidate_id,
            "targetId": f"episode-{number:04d}",
            "field": "mangaRefs",
            "value": [ref],
            "sourceRefs": [SOURCE_ID],
            "confidence": "medium",
            "reviewStatus": "pending",
            "reviewNote": "由柯南百科电视动画表格的漫画来源列解析；File 区间已规范化为 manga/files.json ID。",
        })
        added += 1
    CANDIDATES.write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    batches = json.loads(BATCHES.read_text(encoding="utf-8"))
    if not any(batch.get("batchId") == BATCH_ID for batch in batches["batches"]):
        batches["batches"].append({
            "batchId": BATCH_ID,
            "scope": "动画到漫画 File 的来源映射",
            "targetLayer": "basicFacts",
            "episodeNumbers": [1, 1216],
            "entityIds": [],
            "sourceIds": [SOURCE_ID],
            "status": "candidate",
            "recordCount": added,
            "effectiveChanges": 0,
            "validationResult": None,
            "createdAt": "2026-10-27",
            "appliedAt": None,
            "notes": "只处理来源表明确给出 File/SVFile 的集数；动画原创和来源缺失集保持空值。",
        })
    BATCHES.write_text(json.dumps(batches, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"source_rows={len(source_rows)} unique_files={len(files)} mapped_episodes={len(episode_refs)} candidates_added={added}")


if __name__ == "__main__":
    main()
