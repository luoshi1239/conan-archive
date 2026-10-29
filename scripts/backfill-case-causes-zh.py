#!/usr/bin/env python3
"""M11 · 回填死者死因的中文（causeOfDeathZh）。

背景
----
`victims[].causeOfDeath` 是 DCW 原文英文（Blunt force trauma / Stab wound …），
前端 `formatVictim()` 直接拼进去，于是中文站的「被害者」分区读起来是
    Yoshiro Torada（Swept away by a tornado）
死因共 169 种说法，是封闭词表，可整体对照翻译。

做法
----
`/tmp/cods_zh.json` 是这 169 条的英→中对照（法医学通用表述）。
写 `victims[].causeOfDeathZh`，保留原 `causeOfDeath` 不动（可回溯、可复核）。

⚠ 与剧名不同：死因是可核验的固定术语，不是创作性译名，所以不标 machine。

幂等
----
已有 causeOfDeathZh 的条目一律跳过；第二遍输出 IDEMPOTENT_OK（无改动，不写盘）。
有任何一条英文死因查不到映射就整体不写盘，避免半截状态。
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data/entities/cases.json"
SRC = Path("/tmp/cods_zh.json")
BACKUP = Path("/tmp/cases_pre_m11.json")

# 中文死因里不该出现拉丁字母，但保留少量通用缩写：UFO、DNA、GPS 等在中文里就这么写
ALLOW = {"UFO", "DNA", "GPS", "AED"}
BAD = re.compile(r"[A-Za-z]+")


def bad_reason(zh: str) -> str:
    for word in BAD.findall(zh or ""):
        if word.upper() not in ALLOW:
            return f"英文残留 {word!r}"
    return ""


def main() -> int:
    if not SRC.exists():
        print(f"缺少词表 {SRC}")
        return 1
    table = json.loads(SRC.read_text(encoding="utf-8"))["items"]

    rows = json.loads(CASES.read_text(encoding="utf-8"))

    writes, already, unmapped, rejected = 0, 0, [], []
    for row in rows:
        for victim in row.get("victims") or []:
            if not isinstance(victim, dict):
                continue
            cause = victim.get("causeOfDeath")
            if not cause:
                continue
            if victim.get("causeOfDeathZh"):
                already += 1
                continue
            zh = table.get(cause)
            if not zh:
                unmapped.append((row["id"], cause))
                continue
            reason = bad_reason(zh)
            if reason:
                rejected.append((row["id"], cause, zh))
                continue
            victim["causeOfDeathZh"] = zh
            writes += 1

    print(f"词表条目      {len(table)}")
    print(f"待写入        {writes}")
    print(f"已有中文跳过  {already}")
    print(f"查不到映射    {len(unmapped)}")
    print(f"译文自检不过  {len(rejected)}")
    for cid, cause in unmapped[:15]:
        print(f"  ? {cid} -> {cause!r}")
    for cid, cause, zh in rejected[:10]:
        print(f"  ! {cid} -> {cause!r} => {zh!r}")

    if unmapped or rejected:
        print("存在未覆盖项，未写盘。补齐词表再跑。")
        return 1

    if not writes:
        print("IDEMPOTENT_OK（无改动，不写盘）")
        return 0

    if not BACKUP.exists():
        shutil.copy2(CASES, BACKUP)
        print(f"备份 → {BACKUP}")

    CASES.write_text(
        json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    total = sum(
        1
        for r in rows
        for v in (r.get("victims") or [])
        if isinstance(v, dict) and v.get("causeOfDeathZh")
    )
    print(f"写入完成：{writes} 条，带中文死因的死者 {total} 人")
    return 0


if __name__ == "__main__":
    sys.exit(main())
