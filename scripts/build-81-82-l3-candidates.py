#!/usr/bin/env python3
"""Build sourced L3 candidates for case-popular-artist-kidnapping (EP.81-82).

Facts taken from detectiveconanworld.com wiki article body only.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data" / "candidates" / "entities.json"

CASE_ID = "case-popular-artist-kidnapping"
SRC = "src-detective-conan-world-popular-artist-case"
BATCH = "ep-81-82-l3"

FIELDS = [
    (
        "culprit",
        "宫原悟史（Satoshi Miyahara）及其助手",
        "Wiki Plot/Resolution：Culprits 写作 Satoshi Miyahara and his assistant；Resol...[truncated]",
    ),
    (
        "motive",
        "灭口与销毁证据：宫原在跨年夜于正觉寺附近枪杀一名曾共同抢劫后逃往国外又回来勒索他的男子，Two-Mix 听到枪声后误当作烟花写进歌词，歌词意外暴露了作案细节；他绑架两人是要在警方找到她们前连人带样带一并毁掉。",
        "Wiki Resolution：歌词意外揭示其杀人真相，故决定 destroy the Two-Mix along with the demo tape。",
    ),
    (
        "method",
        "先枪杀受害者，再把重新装填的枪塞进死者手中朝地面开一枪，使警方在其手上检出硝烟痕迹，从而被判定为正当防卫；助手在其报警期间带走一发子弹与第一枪的空弹壳。绑架阶段则在录音室外将两名成员强行押上车。",
        "Wiki Resolution：描述枪械布置、助手取走子弹与弹壳、以及绑架过程。",
    ),
    (
        "evidence",
        "Two-Mix 的样带歌词与案发当夜所听到的时间、声响细节吻合；柯南借手机机关定位并救出人质；寺院住持虽是聋人整夜在寺中，仍看到过宫原的脸。",
        "Wiki Resolution：歌词来源、住持目击、柯南用手机机关救人。",
    ),
    (
        "resolution",
        "柯南用手机机关救出少年侦探团与 Two-Mix 两名成员，30 分钟后警方逮捕两名绑架者；宫原供认杀人，被害人是当年抢劫同伙、回国后勒索他。演唱会得以按时开始。",
        "Wiki Resolution 末段：人质获救、逮捕、供述、演唱会顺利举行。",
    ),
]


def main() -> None:
    raw = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    candidates = raw["candidates"] if isinstance(raw, dict) else raw

    existing = {c.get("candidateId") for c in candidates}
    added = 0
    for field, value, note in FIELDS:
        cid = f"cand-{BATCH}-{field}"
        if cid in existing:
            continue
        candidates.append(
            {
                "candidateId": cid,
                "targetId": CASE_ID,
                "field": field,
                "value": value,
                "sourceRefs": [SRC],
                "confidence": "high",
                "reviewStatus": "accepted",
                "reviewNote": note,
            }
        )
        added += 1

    if isinstance(raw, dict):
        raw["candidates"] = candidates
        payload = raw
    else:
        payload = candidates
    CANDIDATES.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"added={added} total={len(candidates)}")


if __name__ == "__main__":
    main()
