#!/usr/bin/env python3
"""用 DCW 剧集总表补全剧集英文标题 title.en。

背景
----
库里 1217 集只有 1 集有 title.en，而 DCW `/wiki/Anime` 总表逐集给出英文标题。
比对结果：英文标题冲突 0、播出日期冲突 0、页面归属不一致 0，可直接补。

清理规则（沿用库里 zhHans 的既有惯例，不加工内容）
------------------------------------------------
原标题形如 `*主标题* (后缀)`，斜体是剧集标题，括号是标注：
  · `(1 Hour Special)` / `(2 Hour Special)` / `(2.5 Hour Special)` —— 播出时长，
    中文标题里也没译出来，故去掉（与 zhHans 去掉「（2 時間スペシャル）」一致）
  · `(Part 1)` / `(Part 2)` / `(The Case)` / `(The Resolution)` —— 分段标记，
    中文保留了「前篇/后篇」，故保留
原始串始终存入 `title.enRaw`，来源记 `title.enSource`，可逐集回溯。

写入
----
episodes[].title.en      清理后的英文标题（**只填空，不覆盖非空值**）
episodes[].title.enRaw   总表原始串（同上）
episodes[].title.enSource 来源页 URL

幂等：二次运行零改动。
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPISODES = ROOT / "data/episodes/episodes.json"
INDEX = ROOT / "data/raw/dcw-anime-index.json"
SOURCE_URL = "https://www.detectiveconanworld.com/wiki/Anime"

# 播出时长类后缀：去掉
SPECIAL_SUFFIX = re.compile(
    r"\s*\(\s*(?:[\d.]+\s*Hour\s*Special|Hour\s*Special|Rerun|Remastered[^)]*)\s*\)\s*$",
    re.IGNORECASE,
)
# 斜体包裹：*X* → X（只剥最外层一对）
ITALIC_WRAP = re.compile(r"^\*(.+)\*\s*$")


def clean_title(raw: str) -> str:
    """`*A* (1 Hour Special)` → `A`；`*A* (Part 1)` → `A (Part 1)`；`A` → `A`。

    斜体在 DCW 只用于包裹剧集标题（763 集），是纯 markdown 标记，
    柯南标题本身不含 `*`，故直接全部剥离；再去掉尾部播出时长标注。
    """
    t = raw.replace("*", "").strip()
    return SPECIAL_SUFFIX.sub("", t).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="只处理前 N 集（调试用）")
    args = ap.parse_args()

    episodes = json.loads(EPISODES.read_text(encoding="utf-8"))
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    rows = {r["jpNumber"]: r for r in index["rows"]}

    stats = {"filled": 0, "kept": 0, "no_index": 0, "empty_after_clean": 0, "not_in_db": 0}
    samples = []
    changed = []

    for ep in episodes:
        num = ep["number"]
        row = rows.get(num)
        if not row:
            stats["no_index"] += 1
            continue

        title = ep.setdefault("title", {})
        raw_title = row["titleEn"]
        cleaned = clean_title(raw_title)

        if not cleaned:
            stats["empty_after_clean"] += 1
            continue

        cur = (title.get("en") or "").strip()
        if cur:
            stats["kept"] += 1
            # 已有值不覆盖；顺手补 enRaw 便于回溯
            if not title.get("enRaw"):
                title["enRaw"] = raw_title
                title["enSource"] = SOURCE_URL
                changed.append(num)
            continue

        title["en"] = cleaned
        title["enRaw"] = raw_title
        title["enSource"] = SOURCE_URL
        stats["filled"] += 1
        changed.append(num)
        if len(samples) < 12:
            samples.append((num, raw_title, cleaned))

    for n in rows:
        if n not in {e["number"] for e in episodes}:
            stats["not_in_db"] += 1

    print("=== 统计 ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"  改动集数: {len(changed)}")
    print()
    print("=== 样例（原文 → 清理后） ===")
    for n, raw, cleaned in samples:
        print(f"  EP.{n:4d}")
        print(f"    原文  : {raw!r}")
        print(f"    清理后: {cleaned!r}")
    print()

    if args.dry_run:
        print("DRY-RUN：未写入")
        return

    if not changed:
        print("IDEMPOTENT_OK：无改动")
        return

    EPISODES.write_text(
        json.dumps(episodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已写入 {EPISODES}（{len(changed)} 集）")
    print("IDEMPOTENT_CHECK：请再跑一次确认零改动")


if __name__ == "__main__":
    main()
