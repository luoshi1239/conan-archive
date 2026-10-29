#!/usr/bin/env python3
"""Apply the reviewed overlapping Clash of Red and Black arc candidates."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAND = ROOT / "data/candidates/episodes.json"
EPISODES = ROOT / "data/episodes/episodes.json"
ARCS = ROOT / "data/manga/mainline-arcs.json"
BATCHES = ROOT / "docs/CONTENT-BATCHES.json"
BATCH = "p4-arc-clash-red-black-01"
ARC = "arc-kir-clash"
SOURCE = "src-detective-conan-world-clash-red-black"
TARGETS = {f"episode-{number:04d}" for number in range(491, 505)}
FIELDS = {"arcRefs", "summary", "spoiler"}

candidates = json.loads(CAND.read_text(encoding="utf-8"))
selected = [row for row in candidates if row.get("candidateId", "").startswith(BATCH + "-")]
if {row.get("targetId") for row in selected} != TARGETS:
    raise SystemExit("红与黑候选集数不完整")
if {row.get("field") for row in selected} != FIELDS:
    raise SystemExit("红与黑候选字段不完整")
for row in selected:
    if row.get("sourceRefs") != [SOURCE]:
        raise SystemExit("红与黑候选来源不一致")
    row["reviewStatus"] = "accepted"
    row["confidence"] = "medium"
    row["reviewNote"] = "已读取页面正文并核对EP.491—504边界；作为arcRefs子篇章关系，不写入单案深度剧透。"
CAND.write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

episodes = json.loads(EPISODES.read_text(encoding="utf-8"))
by_id = {row.get("id"): row for row in episodes}
summary = next(row["value"] for row in selected if row["field"] == "summary")
changes = 0
for target in sorted(TARGETS):
    row = by_id[target]
    refs = sorted(set(row.get("arcRefs", [])) | {ARC})
    if refs != row.get("arcRefs", []):
        row["arcRefs"] = refs
        changes += 1
    if row.get("arc") != ARC:
        row["arc"] = ARC
        changes += 1
    if row.get("summary") != summary:
        row["summary"] = summary
        changes += 1
    if int(row.get("spoiler") or 1) < 2:
        row["spoiler"] = 2
        changes += 1
    row["detailStatus"] = "reviewed"
    row["coverage"] = {
        **row.get("coverage", {}),
        "directory": True,
        "basicFacts": True,
        "structure": True,
        "deepSpoilers": bool(row.get("coverage", {}).get("deepSpoilers", False)),
    }
    if SOURCE not in row.setdefault("sources", []):
        row["sources"].append(SOURCE)
        changes += 1
EPISODES.write_text(json.dumps(episodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

arcs = json.loads(ARCS.read_text(encoding="utf-8"))
arc = next(row for row in arcs if row.get("id") == ARC)
if SOURCE not in arc.setdefault("sources", []):
    arc["sources"].append(SOURCE)
ARCS.write_text(json.dumps(arcs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

batches = json.loads(BATCHES.read_text(encoding="utf-8"))
if not any(row.get("batchId") == BATCH for row in batches.get("batches", [])):
    batches.setdefault("batches", []).append({
        "batchId": BATCH,
        "scope": "红与黑的碰撞子篇章关系",
        "targetLayer": "structure",
        "episodeNumbers": list(range(491, 505)),
        "arcIds": ["arc-kir", ARC],
        "sourceIds": [SOURCE],
        "status": "applied",
        "recordCount": len(selected),
        "effectiveChanges": changes,
        "validationResult": "pending-post-apply-validation",
        "createdAt": "2026-10-27",
        "appliedAt": "2026-10-27",
        "notes": "新增重叠子篇章arc-kir-clash；保留既有arc-kir，不写入单案L3字段。",
    })
BATCHES.write_text(json.dumps(batches, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"effective_changes={changes}")
