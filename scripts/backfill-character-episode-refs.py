#!/usr/bin/env python3
"""M3：从剧集的 characters 反推角色 episodeRefs。

为什么这样做
------------
剧集侧的 `episodes[].characters` 已 100% 覆盖（1217/1217），而角色侧的
`episodeRefs` 一直是 0/147——同一份关联只建了一个方向。

这是纯粹的反向索引，不引入任何新信息、不推断任何关系：
角色出现在某集，当且仅当该集的 characters 里有它。

幂等：已有非空 episodeRefs 一律跳过；内容相同不写盘。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPS = ROOT / "data/episodes/episodes.json"
CHARS = ROOT / "data/entities/characters.json"
DRY = "--dry-run" in sys.argv


def main() -> int:
    episodes = json.loads(EPS.read_text(encoding="utf-8"))
    chars = json.loads(CHARS.read_text(encoding="utf-8"))

    # 反推：characterId -> [episodeNumber, ...]
    refs: dict[str, list[int]] = {}
    for e in episodes:
        num = e.get("number")
        if not isinstance(num, int):
            continue
        for cid in e.get("characters") or []:
            if not isinstance(cid, str):
                continue
            refs.setdefault(cid, []).append(num)

    for v in refs.values():
        v.sort()

    filled = 0
    skipped = 0
    orphan = []  # 剧集引用但角色表里没有

    known = {c.get("id") for c in chars}
    for cid in refs:
        if cid not in known:
            orphan.append(cid)

    for c in chars:
        cid = c.get("id")
        got = refs.get(cid)
        if not got:
            continue
        existing = c.get("episodeRefs")
        if existing:
            skipped += 1
            continue
        if not DRY:
            c["episodeRefs"] = got
        filled += 1

    print(f"M3 角色 episodeRefs：补 {filled} 个 / 跳过 {skipped} 个（已有）")
    print(f"   反推覆盖角色 {len(refs)}/{len(chars)}")
    if orphan:
        print(f"   警告：{len(orphan)} 个 id 被剧集引用但不在角色表：{orphan[:5]}")

    if DRY:
        print("   [dry-run] 未写盘")
        return 0

    if filled == 0:
        print("   IDEMPOTENT_OK（无改动，不写盘）")
        return 0

    CHARS.write_text(
        json.dumps(chars, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("   已写入 characters.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
