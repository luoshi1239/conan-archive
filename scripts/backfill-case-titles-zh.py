#!/usr/bin/env python3
"""M9 · 回填 741 个案件的中文标题。

背景
----
中文站前端 `titleOf()` 的回落顺序是 zhHans → zhHant → ja → en。
792 个案件里有 741 个没有中文标题，于是列表和详情都直接显示日文长标题
（例如 `516 風林火山 迷宮の鎧武者 (Fūrinkazan Meikyū no Yoroimusha) 517 …`），
在中文界面里非常刺眼。

来源与标注
----------
这 741 条**没有任何官方中文译名可用**（DCW 只有英文/日文，YTV 只有日文，
维基中文不可达）。因此全部按英文 `title.en` 意译，术语沿用柯南常见译法
（… Murder Case → …杀人事件、Locked Room → 密室、Mystery Tour → 推理之旅 等）。

每条都写：
    title.zhHans                    译文
    title.translationStatus = "machine"
    title.zhHansFrom       = "en"   说明是从英文标题意译，不是官方译名

⚠ 这不是官方译名，前端与文档必须如实标注「机器意译」。
拿到官方译名后直接覆盖 zhHans 并把 translationStatus 改成 human 即可。

幂等
----
已有 zhHans 或 zhHant 的案件一律跳过（不覆盖人工/官方译名）；
第二遍运行输出 IDEMPOTENT_OK（无改动，不写盘）。
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data/entities/cases.json"
SRC = Path("/tmp/titles_zh_all.json")
BACKUP = Path("/tmp/cases_pre_m9.json")

# 译文里不该出现的残留：日文假名、或以拉丁字母开头的英文短语。
# 例外是中文语境里通用的缩写（VS / UFO / J联赛 / OK / SOS / FILE / Wild Police Story 等），
# 这些在中文标题里本来就这么写，不算漏译。
ALLOW_LATIN = {
    "VS", "UFO", "OK", "SOS", "ZERO", "Episode", "CASE", "Wild", "Police", "Story",
    "III", "II", "IV", "J", "File", "BARLS",
    # 单个字母：1年B班的班名、大阪三个K、可疑的首字母K —— 原文就是这样，译成中文反而失真
    "B", "K",
}
BAD_ZH = re.compile(r"[\u3040-\u309F\u30A0-\u30FF]")


def bad_reason(zh: str) -> str:
    """返回不合格原因，合格返回空串。"""
    if not zh or not zh.strip():
        return "空译文"
    if BAD_ZH.search(zh):
        return "含日文假名"
    for word in re.findall(r"[A-Za-z][A-Za-z'’]*", zh):
        if word not in ALLOW_LATIN:
            return f"英文残留 {word!r}"
    return ""


def main() -> int:
    if not SRC.exists():
        print(f"缺少译文文件 {SRC}")
        return 1
    titles = json.loads(SRC.read_text(encoding="utf-8"))

    rows = json.loads(CASES.read_text(encoding="utf-8"))
    by_id = {r["id"]: r for r in rows}

    writes, skipped_have, missing, rejected = [], 0, [], []
    for cid, zh in titles.items():
        row = by_id.get(cid)
        if row is None:
            missing.append(cid)
            continue
        title = row.setdefault("title", {})
        # 已有中文（官方或人工）就绝不覆盖
        if title.get("zhHans") or title.get("zhHant"):
            skipped_have += 1
            continue
        # 译文自检：不能夹带假名或未放行的英文词
        reason = bad_reason(zh)
        if reason:
            rejected.append((cid, zh, reason))
            continue
        title["zhHans"] = zh
        title["translationStatus"] = "machine"
        title["zhHansFrom"] = "en"
        writes.append(cid)

    print(f"译文条目      {len(titles)}")
    print(f"待写入        {len(writes)}")
    print(f"已有中文跳过  {skipped_have}")
    print(f"案件里找不到  {len(missing)}")
    print(f"译文自检不过  {len(rejected)}")
    for cid, zh, reason in rejected[:20]:
        print(f"  ! {cid} -> {zh}  ({reason})")
    for cid in missing[:10]:
        print(f"  ? 缺案件 {cid}")

    if rejected or missing:
        print("存在异常，未写盘。先修正译文再跑。")
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

    with_zh = sum(
        1 for r in rows if (r.get("title") or {}).get("zhHans") or (r.get("title") or {}).get("zhHant")
    )
    print(f"写入完成：{len(writes)} 条，案件中文标题覆盖 {with_zh}/{len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
