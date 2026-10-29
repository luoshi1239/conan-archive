#!/usr/bin/env python3
"""Validate normalized Conan archive data and raw episode coverage."""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
EPISODES = ROOT / "data" / "episodes"
SOURCES = ROOT / "data" / "sources.json"

# 剧透字段名混进非剧透字段 = 泄底或切块错位
SPOILER_LABEL = re.compile(r"(?i)\b(culprit|murderer|the killer|killer is)\b")


def load(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    errors: list[str] = []
    raw_path = RAW / "conan_episodes.json"
    if not raw_path.exists():
        errors.append(f"missing raw source: {raw_path}")
    else:
        rows = load(raw_path)
        numbers: list[int] = []
        special = 0
        for index, row in enumerate(rows):
            value = row.get("episode")
            if value is None:
                special += 1
                continue
            try:
                numbers.append(int(value))
            except (TypeError, ValueError):
                errors.append(f"raw row {index}: invalid episode={value!r}")
        counts = {n: numbers.count(n) for n in set(numbers)}
        duplicates = sorted(n for n, count in counts.items() if count > 1)
        if duplicates:
            errors.append(f"duplicate episode numbers: {duplicates}")
        if numbers:
            expected = set(range(min(numbers), max(numbers) + 1))
            gaps = sorted(expected - set(numbers))
            if gaps:
                errors.append(f"episode gaps: {gaps[:20]}")
        print(f"raw_records={len(rows)} tv_numbers={len(numbers)} special_or_unnumbered={special}")
        if numbers:
            print(f"range={min(numbers)}..{max(numbers)} unique={len(set(numbers))}")

    if SOURCES.exists():
        source_data = load(SOURCES)
        source_ids = [item.get("id") for item in source_data.get("sources", [])]
        if len(source_ids) != len(set(source_ids)):
            errors.append("duplicate source ids")
        print(f"sources={len(source_ids)}")
    else:
        errors.append(f"missing sources file: {SOURCES}")

    normalized = EPISODES / "episodes.json"
    file_ids = set()
    file_path = ROOT / "data" / "manga" / "files.json"
    if file_path.exists():
        file_ids = {row.get("id") for row in load(file_path)}
    if normalized.exists():
        rows = load(normalized)
        ids = [row.get("id") for row in rows]
        if any(not item for item in ids):
            errors.append("normalized episodes contain empty ids")
        if len(ids) != len(set(ids)):
            errors.append("normalized episodes contain duplicate ids")
        allowed_detail = {"catalog", "reviewed", "complete"}
        for row in rows:
            if row.get("detailStatus") not in allowed_detail:
                errors.append(f"{row.get('id')}: invalid detailStatus {row.get('detailStatus')!r}")
            coverage = row.get("coverage") or {}
            for field in ("directory", "basicFacts", "structure", "deepSpoilers"):
                if not isinstance(coverage.get(field), bool):
                    errors.append(f"{row.get('id')}: coverage.{field} must be boolean")
            for ref in row.get("mangaRefs", []):
                if file_ids and ref not in file_ids:
                    errors.append(f"{row.get('id')}: unknown mangaRefs reference {ref}")
            if row.get("detailStatus") == "complete" and not coverage.get("structure"):
                errors.append(f"{row.get('id')}: complete record missing structure coverage")
        print(f"normalized_episodes={len(rows)}")
    else:
        print("normalized_episodes=not-created-yet")

    catalog_files = [
        ROOT / "data" / "movies" / "movies.json",
        ROOT / "data" / "movies" / "special-movies.json",
        ROOT / "data" / "ovas" / "ovas.json",
    ]
    known_source_ids = set()
    if SOURCES.exists():
        known_source_ids = {
            item.get("id") for item in load(SOURCES).get("sources", [])
        }
    for catalog in catalog_files:
        if not catalog.exists():
            continue
        rows = load(catalog)
        ids = [row.get("id") for row in rows]
        if any(not item for item in ids):
            errors.append(f"{catalog.name}: empty id")
        if len(ids) != len(set(ids)):
            errors.append(f"{catalog.name}: duplicate ids")
        for row in rows:
            if row.get("detailStatus") not in {"catalog", "reviewed", "complete"}:
                errors.append(f"{catalog.name}/{row.get('id')}: invalid detailStatus {row.get('detailStatus')!r}")
            coverage = row.get("coverage") or {}
            for field in ("directory", "basicFacts", "structure", "deepSpoilers"):
                if not isinstance(coverage.get(field), bool):
                    errors.append(f"{catalog.name}/{row.get('id')}: coverage.{field} must be boolean")
            missing = set(row.get("sources", [])) - known_source_ids
            if missing:
                errors.append(
                    f"{catalog.name}/{row.get('id')}: unknown sources {sorted(missing)}"
                )
        print(f"{catalog.relative_to(ROOT)}={len(rows)}")

    movie_ids = set()
    movie_path = ROOT / "data" / "movies" / "movies.json"
    if movie_path.exists():
        movie_ids = {row.get("id") for row in load(movie_path)}
    ova_path = ROOT / "data" / "ovas" / "ovas.json"
    if ova_path.exists():
        for row in load(ova_path):
            link = row.get("movieLink")
            if link and link not in movie_ids:
                errors.append(f"{row.get('id')}: unknown movieLink {link}")

    entity_files = [
        ROOT / "data" / "entities" / "characters.json",
        ROOT / "data" / "entities" / "organizations.json",
        ROOT / "data" / "entities" / "cases.json",
        ROOT / "data" / "entities" / "gadgets.json",
        ROOT / "data" / "entities" / "locations.json",
        ROOT / "data" / "manga" / "mainline-arcs.json",
    ]
    entity_ids = set()
    case_ids = set()
    arc_ids = set()
    location_ids = set()
    entity_rows = []
    raw_location_names = 0
    for entity_file in entity_files:
        if not entity_file.exists():
            continue
        rows = load(entity_file)
        ids = [row.get("id") for row in rows]
        if any(not item for item in ids):
            errors.append(f"{entity_file.name}: empty id")
        if len(ids) != len(set(ids)):
            errors.append(f"{entity_file.name}: duplicate ids")
        entity_ids.update(ids)
        if entity_file.name == "cases.json":
            case_ids.update(ids)
        elif entity_file.name == "mainline-arcs.json":
            arc_ids.update(ids)
        elif entity_file.name == "locations.json":
            location_ids.update(ids)
        entity_rows.extend(rows)
        for row in rows:
            # 两种字段名都在用（历史遗留），必须同时校验，否则 sourceRefs 记录会逃检
            refs = list(row.get("sources") or []) + list(row.get("sourceRefs") or [])
            if not refs:
                errors.append(f"{entity_file.name}/{row.get('id')}: no sources or sourceRefs")
            missing = set(refs) - known_source_ids
            if missing:
                errors.append(f"{entity_file.name}/{row.get('id')}: unknown sources {sorted(missing)}")
        print(f"{entity_file.relative_to(ROOT)}={len(rows)}")
    for row in entity_rows:
        for field in ("relations", "members", "characters", "userRefs"):
            for ref in row.get(field, []):
                if ref not in entity_ids:
                    errors.append(f"{row.get('id')}: unknown {field} reference {ref}")
        for ref in row.get("relatedCases", []):
            if ref not in case_ids:
                errors.append(f"{row.get('id')}: unknown relatedCases reference {ref}")
        for ref in row.get("relatedArcs", []):
            if ref not in arc_ids:
                errors.append(f"{row.get('id')}: unknown relatedArcs reference {ref}")
        for ref in row.get("locations", []):
            # 两种合法形态（见 DATA-SCHEMA）：
            #   1) 地点实体 id，如 location-tropical-land → 必须存在
            #   2) DCW 原文地点名，如 "Beika Library" → 不是 id，按原文收录，不校验存在性
            if ref in location_ids:
                continue
            if ref.startswith("location-"):
                errors.append(f"{row.get('id')}: unknown locations reference {ref}")
            else:
                raw_location_names += 1
        # 角色 caseRefs 反向索引必须指向真实案件
        for ref in row.get("caseRefs", []):
            if ref not in case_ids:
                errors.append(f"{row.get('id')}: unknown caseRefs reference {ref}")

    # 案件 L3 字段必须是双语结构（zhHans/en/translationStatus），且不得写成 [object Object] 源头
    L3_FIELDS = ("culprit", "motive", "method", "evidence", "resolution")
    ALLOWED_STATUS = {"human", "machine", "pending", "none"}
    if case_ids:
        cases_path = ROOT / "data" / "entities" / "cases.json"
        for row in load(cases_path):
            for field in L3_FIELDS:
                value = row.get(field)
                if value in (None, ""):
                    continue
                if not isinstance(value, dict):
                    errors.append(f"{row.get('id')}: {field} must be bilingual object, got {type(value).__name__}")
                    continue
                for lang in ("zhHans", "en"):
                    lang_value = value.get(lang)
                    if lang_value is not None and not isinstance(lang_value, str):
                        errors.append(f"{row.get('id')}: {field}.{lang} must be string or null")
                status = value.get("translationStatus")
                if status not in ALLOWED_STATUS:
                    errors.append(f"{row.get('id')}: {field}.translationStatus invalid {status!r}")
                if not (value.get("zhHans") or value.get("en")):
                    errors.append(f"{row.get('id')}: {field} has no text in either language")
                if value.get("en") and not value.get("zhHans") and status != "pending":
                    errors.append(f"{row.get('id')}: {field} is english-only but status={status!r}")

            # M8 案件事实字段：victims 是 [{name, age?, causeOfDeath?}]，其余是原文串数组
            for field in ("suspects", "locationsDropped"):
                value = row.get(field)
                if value in (None, ""):
                    continue
                if not isinstance(value, list):
                    errors.append(f"{row.get('id')}: {field} must be list, got {type(value).__name__}")
                    continue
                for item in value:
                    if not isinstance(item, str) or not item.strip():
                        errors.append(f"{row.get('id')}: {field} has non-string/empty item {item!r}")
                        continue
                    if SPOILER_LABEL.search(item):
                        errors.append(f"{row.get('id')}: {field} contains spoiler label {item[:40]!r}")

            # suspectsZh（M14）：中文平行数组，必须与 suspects 等长，逐项非空字符串
            sus_zh = row.get("suspectsZh")
            if sus_zh is not None:
                sus = row.get("suspects")
                if not isinstance(sus_zh, list):
                    errors.append(f"{row.get('id')}: suspectsZh must be a list")
                elif not isinstance(sus, list) or len(sus_zh) != len(sus):
                    errors.append(f"{row.get('id')}: suspectsZh length {len(sus_zh)} != suspects length {len(sus or [])}")
                else:
                    for idx, text in enumerate(sus_zh):
                        if not isinstance(text, str) or not text.strip():
                            errors.append(f"{row.get('id')}: suspectsZh[{idx}] must be non-empty string")

            victims = row.get("victims")
            if victims not in (None, ""):
                if not isinstance(victims, list):
                    errors.append(f"{row.get('id')}: victims must be list, got {type(victims).__name__}")
                else:
                    for item in victims:
                        if not isinstance(item, dict):
                            errors.append(f"{row.get('id')}: victims item must be object, got {type(item).__name__}")
                            continue
                        name = item.get("name")
                        if not isinstance(name, str) or not name.strip():
                            errors.append(f"{row.get('id')}: victims item missing name")
                        for key in ("age", "causeOfDeath", "causeOfDeathZh", "nameZh"):
                            val = item.get(key)
                            if val is not None and (not isinstance(val, str) or not val.strip()):
                                errors.append(f"{row.get('id')}: victims.{key} must be non-empty string")
                        # causeOfDeathZh / nameZh 是 M11 / M12 加的中文展示字段；原英文保留不动
                        if item.get("causeOfDeathZh") and not item.get("causeOfDeath"):
                            errors.append(f"{row.get('id')}: victims.causeOfDeathZh without causeOfDeath")
                        if item.get("nameZh") and not item.get("name"):
                            errors.append(f"{row.get('id')}: victims.nameZh without name")
                        unknown = set(item) - {"name", "nameZh", "age", "causeOfDeath", "causeOfDeathZh"}
                        if unknown:
                            errors.append(f"{row.get('id')}: victims item has unknown keys {sorted(unknown)}")

            # 案件 summary 允许字符串（历史人工中文）或 {en: ...} 对象（M1 搬原文）
            summary = row.get("summary")
            if summary not in (None, "") and not isinstance(summary, (str, dict)):
                errors.append(f"{row.get('id')}: summary must be string or object, got {type(summary).__name__}")
            if isinstance(summary, dict) and not (summary.get("en") or summary.get("zhHans")):
                errors.append(f"{row.get('id')}: summary object has no text")

            # locationsZh（M13）：中文平行数组，必须与 locations 等长，逐项非空字符串
            locs_zh = row.get("locationsZh")
            if locs_zh is not None:
                locs = row.get("locations")
                if not isinstance(locs_zh, list):
                    errors.append(f"{row.get('id')}: locationsZh must be a list")
                elif not isinstance(locs, list) or len(locs_zh) != len(locs):
                    errors.append(
                        f"{row.get('id')}: locationsZh length {len(locs_zh)} != locations length {len(locs or [])}"
                    )
                else:
                    for idx, text in enumerate(locs_zh):
                        if not isinstance(text, str) or not text.strip():
                            errors.append(f"{row.get('id')}: locationsZh[{idx}] must be non-empty string")

    if errors:
        print("VALIDATION_FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALIDATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
