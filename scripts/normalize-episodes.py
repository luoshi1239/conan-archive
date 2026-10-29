#!/usr/bin/env python3
"""Normalize the community episode catalog without inventing missing facts."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "conan_episodes.json"
OUT = ROOT / "data" / "episodes" / "episodes.json"
SPECIALS = ROOT / "data" / "specials" / "unnumbered.json"
SOURCE = "src-abiting-conan-database"


def text(value):
    return value.strip() if isinstance(value, str) and value.strip() else None


def normalize(row, index):
    raw_number = row.get("episode")
    number = int(raw_number) if raw_number is not None else None
    title_ja = text(row.get("title_ja")) or text(row.get("title_jp"))
    manga_source = text(row.get("manga"))
    adaptation = "anime-original" if manga_source == "動畫原創" else ("manga" if manga_source else "unknown")
    record = {
        "id": f"episode-{number:04d}" if number is not None else f"special-raw-{index:04d}",
        "kind": "tv-episode" if number is not None else "special-record",
        "number": number,
        "overseasNumber": row.get("overseas_ep"),
        "title": {
            "ja": title_ja,
            "zhHans": None,
            "zhHant": text(row.get("title_zh")),
            "en": None,
            "aliases": []
        },
        "year": int(row["year"]) if str(row.get("year", "")).isdigit() else None,
        "airDate": None,
        "mangaRefs": [],
        "adaptation": adaptation,
        "arc": None,
        "arcRefs": [],
        "caseRefs": [],
        "locationRefs": [],
        "spoiler": 1,
        "status": "catalog",
        "summary": None,
        "characters": [],
        "organizations": [],
        "locations": [],
        "gadgets": [],
        "caseTypes": [],
        "sources": [SOURCE],
        "detailStatus": "catalog",
        "coverage": {
            "directory": True,
            "basicFacts": bool(title_ja and row.get("year") and adaptation != "unknown"),
            "structure": False,
            "deepSpoilers": False
        },
        "raw": {
            "manga": row.get("manga"),
            "specialLabel": row.get("special_label"),
            "rawIndex": index
        }
    }
    return record


def main():
    rows = json.loads(RAW.read_text(encoding="utf-8"))
    previous = {}
    if OUT.exists():
        previous = {row.get("id"): row for row in json.loads(OUT.read_text(encoding="utf-8"))}

    # 逐字段「有值优先」保留策略：normalize 只负责把 raw 目录里缺的字段补上，
    # 绝不因为一条记录 detailStatus 还是 catalog 就丢掉已回填的 caseRefs / mangaRefs。
    # 这是修掉「跑一次 normalize 就把 DCW 回填成果清零」的伪幂等隐患。
    KEEP_IF_TRUTHY = (
        "title", "airDate", "mangaRefs", "adaptation", "arc", "arcRefs",
        "caseRefs", "locationRefs", "summary", "characters", "organizations",
        "locations", "gadgets", "caseTypes", "sources", "detailStatus",
        "coverage", "spoiler", "status", "year", "overseasNumber",
    )

    normalized = []
    special = []
    for index, row in enumerate(rows):
        record = normalize(row, index)
        prior = previous.get(record["id"], {})
        for field in KEEP_IF_TRUTHY:
            old = prior.get(field)
            if old in (None, "", [], {}):
                continue
            new = record.get(field)
            if field == "sources":
                record[field] = sorted(set(old) | set(new or []))
            elif field == "title" and isinstance(old, dict) and isinstance(new, dict):
                merged = dict(new)
                for k, v in old.items():
                    if v not in (None, "", []):
                        merged[k] = v
                record[field] = merged
            elif new in (None, "", [], {}):
                record[field] = old

        # raw 合并而非重建：保留 dcwMangaSource / dcwAirDate / dcwPage 等回填痕迹
        if isinstance(prior.get("raw"), dict):
            merged_raw = dict(record.get("raw") or {})
            merged_raw.update({k: v for k, v in prior["raw"].items() if v is not None})
            record["raw"] = merged_raw

        # adaptation 裁定保护（回退隐患修复）：
        # raw 目录把 EP.86/EP.113 标成「動畫原創」，但 DCW 与本地 files.json 双向佐证它们是
        # 特别篇漫画改编（SVFile.2 / SVFile.6，见 docs/FACT-CONFLICTS.json 已裁定项）。
        # 若 DCW 证据表明 manga-special-volume，则保留此前已裁定的 manga/mixed，不被打回 anime-original。
        raw_now = record.get("raw") or {}
        if (
            raw_now.get("dcwMangaKind") == "manga-special-volume"
            and str(raw_now.get("dcwMangaSource") or "").upper().startswith("SV")
        ):
            prev_adapt = prior.get("adaptation")
            if prev_adapt in ("manga", "mixed"):
                record["adaptation"] = prev_adapt

        (normalized if record["number"] is not None else special).append(record)

    # 把 OUT 里存在、但 RAW 源已不包含的集原样保留（例如新增集 EP.1217），
    # 否则 normalize 会静默删掉新集，造成 caseRefs 悬空。
    seen = {r.get("id") for r in normalized} | {r.get("id") for r in special}
    for rid, prior in previous.items():
        if rid in seen:
            continue
        if prior.get("kind") == "tv-episode" and prior.get("number") is not None:
            normalized.append(prior)
        else:
            special.append(prior)

    normalized.sort(key=lambda item: item["number"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    SPECIALS.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    SPECIALS.write_text(json.dumps(special, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"normalized={len(normalized)} specials={len(special)}")
    print(f"range={normalized[0]['number']}..{normalized[-1]['number']}")


if __name__ == "__main__":
    main()
