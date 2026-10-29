#!/usr/bin/env python3
"""Apply the cross-checked Diplomat Murder Case L3 batch idempotently."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAND = ROOT / "data/candidates/entities.json"
CASES = ROOT / "data/entities/cases.json"
EPISODES = ROOT / "data/episodes/episodes.json"
BATCHES = ROOT / "docs/CONTENT-BATCHES.json"
BATCH = "p4-deep-case-diplomat-01"
TARGET = "case-diplomat-murder"
SOURCE = "src-detective-conan-world-diplomat-case"
FIELDS = {"culprit", "motive", "method", "evidence", "resolution"}

rows = json.loads(CAND.read_text(encoding="utf-8"))
selected = [r for r in rows if r.get("candidateId", "").startswith(BATCH + "-")]
if {r.get("field") for r in selected} != FIELDS:
    raise SystemExit("外交官 L3 候选字段不完整")
if any(r.get("sourceRefs") != [SOURCE] for r in selected):
    raise SystemExit("外交官 L3 候选来源不一致")

for row in selected:
    row["reviewStatus"] = "accepted"
    row["confidence"] = "medium"
    row["reviewNote"] = "原页面正文与 MiMo 独立核对一致；L3 全剧透字段。"
CAND.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

cases = json.loads(CASES.read_text(encoding="utf-8"))
case = next(row for row in cases if row.get("id") == TARGET)
changes = 0
for row in selected:
    if case.get(row["field"]) != row["value"]:
        case[row["field"]] = row["value"]
        changes += 1
for key, value in {"spoiler": 3, "status": "reviewed", "deepSpoilers": True}.items():
    if case.get(key) != value:
        case[key] = value
        changes += 1
if SOURCE not in case.setdefault("sources", []):
    case["sources"].append(SOURCE)
    changes += 1
CASES.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

episodes = json.loads(EPISODES.read_text(encoding="utf-8"))
episode_changes = 0
for episode in episodes:
    if episode.get("number") in {48, 49}:
        if episode.get("spoiler") != 3:
            episode["spoiler"] = 3
            episode_changes += 1
        if episode.get("status") != "reviewed":
            episode["status"] = "reviewed"
            episode_changes += 1
        coverage = episode.setdefault("coverage", {})
        if coverage.get("deepSpoilers") is not True:
            coverage["deepSpoilers"] = True
            episode_changes += 1
        if SOURCE not in episode.setdefault("sources", []):
            episode["sources"].append(SOURCE)
            episode_changes += 1
EPISODES.write_text(json.dumps(episodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

batches = json.loads(BATCHES.read_text(encoding="utf-8"))
if not any(row.get("batchId") == BATCH for row in batches.get("batches", [])):
    batches.setdefault("batches", []).append({
        "batchId": BATCH,
        "scope": "外交官杀人事件 L3 深度剧透字段",
        "targetLayer": "deepSpoilers",
        "episodeNumbers": [48, 49],
        "entityIds": [TARGET],
        "sourceIds": [SOURCE],
        "status": "applied",
        "recordCount": len(selected),
        "effectiveChanges": changes + episode_changes,
        "validationResult": "pending-post-apply-validation",
        "createdAt": "2026-10-27",
        "appliedAt": "2026-10-27",
        "notes": "第二个深度剧透试点；仅应用外交官案件及 EP.49—50。",
    })
BATCHES.write_text(json.dumps(batches, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"case_changes={changes}")
print(f"episode_changes={episode_changes}")
