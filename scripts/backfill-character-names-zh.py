#!/usr/bin/env python3
"""M10 · 回填 133 个角色的中文名。

背景
----
147 个角色里只有 14 个带 `name.zhHans`，其余 133 个只有英文名。
于是案件详情的「关联人�物」列表出现中英混排：
    服部平次、毛利兰、Kazuha Toyama、Kansuke Yamato
本应全是中文。中文站不该这样。

来源与标注
----------
DCW 没有中文名字段。主要角色按柯南通行译名（目暮十三、白鸟任三郎、
远山和叶、大和敢助…），冷门动画原创配角无可查证译名，按音译处理。
全部写 `name.translationStatus = "machine"`，`name.zhHansFrom = "en"`。

幂等
----
已有 `name.zhHans` 的角色一律跳过（不覆盖人工/官方译名）；
第二遍运行输出 IDEMPOTENT_OK（无改动，不写盘）。
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHARS = ROOT / "data/entities/characters.json"
SRC = Path("/tmp/chars_zh.json")
BACKUP = Path("/tmp/characters_pre_m10.json")

# 中文名里不该出现拉丁字母或日文假名
BAD = re.compile(r"[A-Za-z\u3040-\u309F\u30A0-\u30FF]")


def main() -> int:
    if not SRC.exists():
        print(f"缺少译文文件 {SRC}")
        return 1
    names = json.loads(SRC.read_text(encoding="utf-8"))["items"]

    rows = json.loads(CHARS.read_text(encoding="utf-8"))
    by_id = {r["id"]: r for r in rows}

    writes, have, missing, rejected = [], 0, [], []
    for cid, zh in names.items():
        row = by_id.get(cid)
        if row is None:
            missing.append(cid)
            continue
        name = row.setdefault("name", {})
        if name.get("zhHans"):
            have += 1
            continue
        if not zh.strip() or BAD.search(zh):
            rejected.append((cid, zh))
            continue
        name["zhHans"] = zh
        name["translationStatus"] = "machine"
        name["zhHansFrom"] = "en"
        writes.append(cid)

    print(f"译文条目      {len(names)}")
    print(f"待写入        {len(writes)}")
    print(f"已有中文跳过  {have}")
    print(f"角色里找不到  {len(missing)}")
    print(f"译文自检不过  {len(rejected)}")
    for cid, zh in rejected[:10]:
        print(f"  ! {cid} -> {zh}")
    for cid in missing[:10]:
        print(f"  ? 缺角色 {cid}")

    if rejected or missing:
        print("存在异常，未写盘。先修正译文再跑。")
        return 1

    if not writes:
        print("IDEMPOTENT_OK（无改动，不写盘）")
        return 0

    if not BACKUP.exists():
        shutil.copy2(CHARS, BACKUP)
        print(f"备份 → {BACKUP}")

    CHARS.write_text(
        json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    with_zh = sum(1 for r in rows if (r.get("name") or {}).get("zhHans"))
    print(f"写入完成：{len(writes)} 条，角色中文名覆盖 {with_zh}/{len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
