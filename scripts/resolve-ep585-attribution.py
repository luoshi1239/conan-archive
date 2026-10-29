#!/usr/bin/env python3
"""裁定 EP.585 归属：归 Kobayashi's Love，Kirin's Horn 页集号修正为 586-587。

证据（全部来自 DCW 原文）
------------------------
1. DCW `/wiki/Anime` 剧集总表逐集列明：
       585 | 636 | Timeless Sakura's Love                        → Kobayashi-sensei's_Love
       586 | 637 | The Kirin's Horn That Vanished into the Dark   → The_Kirin's_Horn_...
       587 | 638 | Kid vs. the Four Divine Detective Boys         → The_Kirin's_Horn_...
   （已存 data/raw/dcw-anime-index.json）

2. intEpisode 自洽性：Kobayashi 页 intEpisode=634，Kirin 页 intEpisode=637，
   相差 3；若 Kobayashi 占 583-585（3 集 = int 634/635/636），Kirin 必从 586 起。

3. Kirin 页自身的 airdate 写着 "August 28, 2010 (Timeless Sakura's Love)"——
   那是 EP.585 的日期与标题，说明该页 infobox 从 585 起算，实际内容是 586-587。

修正内容
--------
· dcw-page-facts.json：Kirin 页 episodeNumbers 585,586,587 → 586,587
  原值留档 episodeNumbersRaw + 修正依据 episodeNumbersNote
· episodes.json：EP.585 的 dcwExtraPages 清空（Kirin 页不再覆盖 585）
· docs/FACT-CONFLICTS.json：该冲突 open → resolved

幂等：二次运行零改动。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FACTS = ROOT / "data/raw/dcw-page-facts.json"
EPS = ROOT / "data/episodes/episodes.json"
CONFLICTS = ROOT / "docs/FACT-CONFLICTS.json"

KIRIN = "The_Kirin's_Horn_That_Vanished_into_the_Dark"
WRONG = [585, 586, 587]
RIGHT = [586, 587]
CONFLICT_ID = "conflict-kirin-horn-585-overlap"

RESOLUTION = {
    "decision": "EP.585 归 Kobayashi-sensei's Love；Kirin's Horn 覆盖 586-587",
    "basis": [
        "DCW /wiki/Anime 剧集总表逐集列明：585→Kobayashi-sensei's_Love，"
        "586/587→The_Kirin's_Horn_That_Vanished_into_the_Dark",
        "intEpisode 自洽：Kobayashi=634 与 Kirin=637 相差 3 集，"
        "583-585 占满 634-636，Kirin 必从 586（int 637）起",
        "Kirin 页自身 airdate 为 'August 28, 2010 (Timeless Sakura's Love)'，"
        "即 EP.585 的日期与标题，证明该页 infobox 从 585 起算属页面自身错位",
    ],
    "action": (
        "dcw-page-facts.json 中该页 episodeNumbers 由 [585,586,587] 修正为 [586,587]，"
        "原值留档 episodeNumbersRaw；EP.585 的 dcwExtraPages 清空。"
        "本地剧集数据（585 归 Kobayashi、586/587 归 Kirin）原本即正确，未改动归属。"
    ),
    "decidedAt": "2026-10-28",
}


def main():
    changed = []

    # 1) 修正 facts
    facts_doc = json.loads(FACTS.read_text(encoding="utf-8"))
    for row in facts_doc["pages"]:
        if row["page"] != KIRIN:
            continue
        cur = row.get("episodeNumbers")
        if cur == RIGHT:
            print("facts：已是正确值，跳过")
            break
        if "episodeNumbersRaw" not in row:
            row["episodeNumbersRaw"] = list(cur) if cur else []
        row["episodeNumbers"] = RIGHT
        row["episodeNumbersNote"] = (
            "原 infobox 写作 585-587，但 DCW /wiki/Anime 总表将 585 归 "
            "Kobayashi-sensei's Love、586-587 归本页；intEpisode 637 亦对应 586。"
            "见 docs/FACT-CONFLICTS.json conflict-kirin-horn-585-overlap"
        )
        changed.append(("facts.episodeNumbers", cur, RIGHT))
        break
    else:
        print(f"警告：facts 里没有页面 {KIRIN}")

    # 2) 清 EP.585 的 dcwExtraPages
    episodes = json.loads(EPS.read_text(encoding="utf-8"))
    for ep in episodes:
        if ep.get("number") != 585:
            continue
        extra = ep.get("dcwExtraPages")
        if extra:
            ep.pop("dcwExtraPages", None)
            changed.append(("EP.585.dcwExtraPages", extra, None))
        break

    # 3) 冲突收口
    conflicts = json.loads(CONFLICTS.read_text(encoding="utf-8"))
    for c in conflicts["conflicts"]:
        if c["id"] != CONFLICT_ID:
            continue
        if c.get("status") == "resolved" and c.get("resolution") == RESOLUTION:
            print("冲突：已是 resolved，跳过")
            break
        c["status"] = "resolved"
        c["resolution"] = RESOLUTION
        changed.append(("conflict.status", "open", "resolved"))
        break
    else:
        print(f"警告：冲突文件里没有 {CONFLICT_ID}")

    print()
    if not changed:
        print("IDEMPOTENT_OK：无改动")
        return

    for what, before, after in changed:
        print(f"  {what}: {before!r} → {after!r}")

    FACTS.write_text(json.dumps(facts_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    EPS.write_text(json.dumps(episodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CONFLICTS.write_text(json.dumps(conflicts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n已写入 3 个文件（{len(changed)} 项改动）")


if __name__ == "__main__":
    main()
