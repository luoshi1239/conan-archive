#!/usr/bin/env python3
"""M6：剧集缺 4 个中文标题 —— 分两种来源，绝不混淆。

    EP.1077  zhHans  由本集既有 zhHant「黑衣組織的謀略（狩獵）」转简体  → 来源=库内繁中稿
    EP.1203  zhHans  由本集既有 zhHant「園子與柯南的怪談之夜」转简体      → 来源=库内繁中稿
    EP.1217  zhHans  /  zhHant  无任何中文稿，按日文标题人工自译          → 标 translationStatus=machine

为什么分两类
------------
前两条**不是翻译**，库内已有繁体中文官方译名，只做简繁字形转换，可逐字回验
（`title.zhHant` 就在同一条记录里）。
EP.1217 没有可转换的稿子，日文原文是「背中を押す手」、DCW 英文是
`The Hands Pushing Their Back`，只能译，因此**必须**标 `translationStatus: machine`，
让前端与读者都知道这不是官方译名。

来源可用性（2026-10-28 复核）
-----------------------------
DCW 英文/日文、YTV 日文均无中文译名；zh.wikipedia / 百度百科 curl 均不可达（连接重置/超时）。
所以 1217 没有可搬的中文原文，只有这一条是自译。

写入规则
--------
- 只补空，任何已有值一律不动
- 简繁转换用一张显式字表，不引第三方库、不做模糊替换，转换后**逐字比对长度**
- 结果与现值相同则不写盘（幂等）
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPS = ROOT / "data/episodes/episodes.json"
DRY = "--dry-run" in sys.argv

# 显式繁→简字表：只收录本批实际出现的字，避免用大词表引入不可解释的改动
T2S = {
    "黑": "黑", "組": "组", "織": "织", "謀": "谋", "略": "略", "獵": "猎",
    "園": "园", "與": "与", "談": "谈", "夜": "夜", "怪": "怪",
}

# EP.1217 无中文源，按日文原文自译（machine）
MANUAL = {
    1217: {"zhHans": "推背的手", "zhHant": "推背的手"},
}
MANUAL_NOTE = (
    "日文原题「背中を押す手」，DCW 英文 The Hands Pushing Their Back；"
    "无官方中文译名，本条为人工自译"
)


def t2s(text):
    return "".join(T2S.get(ch, ch) for ch in text)


def main() -> int:
    eps = json.loads(EPS.read_text(encoding="utf-8"))
    rows = eps if isinstance(eps, list) else eps.get("episodes", eps)

    changed = 0
    filled_hans = []
    filled_hant = []

    for e in rows:
        num = e.get("number")
        title = e.get("title") or {}
        before = json.dumps(title, ensure_ascii=False, sort_keys=True)

        # 1) 有繁中稿、缺简中 → 字形转换（可回验）
        hant = (title.get("zhHant") or "").strip()
        hans = (title.get("zhHans") or "").strip()
        if hant and not hans:
            conv = t2s(hant)
            if len(conv) != len(hant):
                print(f"  EP.{num}: 简繁转换长度不符，跳过（{hant} → {conv}）")
            else:
                title["zhHans"] = conv
                title["zhHansFrom"] = "zhHant-transliteration"
                filled_hans.append((num, conv, hant))

        # 2) 1217 等无中文源的，按人工自译补
        if num in MANUAL:
            for lang, val in MANUAL[num].items():
                if not (title.get(lang) or "").strip():
                    title[lang] = val
                    if lang == "zhHans":
                        filled_hans.append((num, val, None))
                    else:
                        filled_hant.append((num, val))
            title.setdefault("translationStatus", "machine")
            title["translationNote"] = MANUAL_NOTE

        after = json.dumps(title, ensure_ascii=False, sort_keys=True)
        if before != after:
            e["title"] = title
            changed += 1

    print(f"M6 剧集标题：变更 {changed} 条")
    for num, val, src in filled_hans:
        note = f"（由繁中「{src}」转）" if src else "（人工自译 · machine）"
        print(f"   EP.{num} zhHans = {val} {note}")
    for num, val in filled_hant:
        print(f"   EP.{num} zhHant = {val}（人工自译 · machine）")

    if DRY:
        print("   [dry-run] 未写盘")
        return 0
    if changed == 0:
        print("   IDEMPOTENT_OK（无改动，不写盘）")
        return 0

    EPS.write_text(json.dumps(eps, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("   已写入 episodes.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
