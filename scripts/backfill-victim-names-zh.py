#!/usr/bin/env python3
"""M12 · 回填死者姓名的中文（victims[].nameZh）。

背景
----
`victims[].name` 是 DCW 原文英文（Yoshiro Torada / Tetsu Yamazaki …），
中文站的「被害者」分区读起来仍是外文：
    Yoshiro Torada（被龙卷风卷走致死）
513 个不同姓名，其中约 460 个是日语人名（按音读转写汉字，沿用柯南译名习惯），
另外约 50 个是描述性短语（Businessman / An old woman / 10 men and a woman），按意译处理。

写 `victims[].nameZh`，保留原 `name` 不动（可回溯、可复核、可逐字对照）。
原 name 含有 `?` 的存疑项，中文也保留「（存疑）」。

幂等
----
已有 nameZh 的条目一律跳过；第二遍输出 IDEMPOTENT_OK（无改动，不写盘）。
有任何一条英文姓名查不到映射就整体不写盘。
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data/entities/cases.json"
SRC = Path("/tmp/vnames_zh_all.json")
BACKUP = Path("/tmp/cases_pre_m12.json")

# 中文姓名里不该出现拉丁字母
BAD = re.compile(r"[A-Za-z]+")


def main() -> int:
    if not SRC.exists():
        print(f"缺少词表 {SRC}")
        return 1
    table = json.loads(SRC.read_text(encoding="utf-8"))

    rows = json.loads(CASES.read_text(encoding="utf-8"))

    writes, already, unmapped, rejected = 0, 0, [], []
    for row in rows:
        for victim in row.get("victims") or []:
            if not isinstance(victim, dict):
                continue
            name = victim.get("name")
            if not name:
                continue
            if victim.get("nameZh"):
                already += 1
                continue
            zh = table.get(name)
            if not zh:
                unmapped.append((row["id"], name))
                continue
            if BAD.search(zh):
                rejected.append((row["id"], name, zh))
                continue
            victim["nameZh"] = zh
            writes += 1

    print(f"词表条目      {len(table)}")
    print(f"待写入        {writes}")
    print(f"已有中文跳过  {already}")
    print(f"查不到映射    {len(unmapped)}")
    print(f"译文自检不过  {len(rejected)}")
    for cid, name in unmapped[:15]:
        print(f"  ? {cid} -> {name!r}")
    for cid, name, zh in rejected[:10]:
        print(f"  ! {cid} -> {name!r} => {zh!r}")

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
        if isinstance(v, dict) and v.get("nameZh")
    )
    print(f"写入完成：{writes} 条，带中文名的死者 {total} 人")
    return 0


if __name__ == "__main__":
    sys.exit(main())
