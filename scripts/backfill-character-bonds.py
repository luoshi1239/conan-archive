#!/usr/bin/env python3
"""M16：给人物补结构化关系 bonds（带类型）。

背景：characters.json 里只有 14 人有 relations，且是裸 id 数组，没有关系类型，
关系图只能画「有连线」不能说明「什么关系」。本脚本按公开设定补 bonds：

    bonds: [{ "to": "character-x", "type": "family|love|colleague|subordinate|
              rival|nemesis|mentor|friend", "note": "可选说明" }]

只补有明确设定依据的；不猜。
旧的 relations 保留不动（前端和 verify 脚本仍读它）。
幂等：二遍跑输出 IDEMPOTENT_OK 且不写盘。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAR_PATH = ROOT / "data/entities/characters.json"

T = ("family", "love", "colleague", "subordinate", "rival", "nemesis", "mentor", "friend")

# 每项 (from, to, type, note)
PAIRS = [
    # —— 工藤家 / 毛利家 ——
    ("character-shinichi-kudo", "character-yusaku-kudo", "family", "父子"),
    ("character-shinichi-kudo", "character-yukiko-kudo", "family", "母子"),
    ("character-yusaku-kudo", "character-yukiko-kudo", "love", "夫妻"),
    ("character-ran-mouri", "character-kogoro-mouri", "family", "父女"),
    ("character-ran-mouri", "character-eri-kisaki", "family", "母女"),
    ("character-kogoro-mouri", "character-eri-kisaki", "love", "已分居的夫妻"),
    ("character-shinichi-kudo", "character-ran-mouri", "love", "青梅竹马"),
    ("character-conan-edogawa", "character-shinichi-kudo", "family", "同一人"),
    ("character-conan-edogawa", "character-ran-mouri", "love", "以柯南身份寄住"),
    ("character-conan-edogawa", "character-kogoro-mouri", "colleague", "寄住并代为破案"),
    ("character-conan-edogawa", "character-ai-haibara", "friend", "同为服药缩小者"),
    ("character-conan-edogawa", "character-hiroshi-agasa", "friend", "邻居与协助者"),
    ("character-conan-edogawa", "character-heiji-hattori", "rival", "东西名侦探"),
    ("character-conan-edogawa", "character-kaito-kid", "rival", "宿敌兼合作"),
    ("character-conan-edogawa", "character-masumi-sera", "friend", "同班同学"),
    ("character-shinichi-kudo", "character-heiji-hattori", "rival", "东西名侦探"),
    ("character-shinichi-kudo", "character-masumi-sera", "friend", "童年玩伴"),
    # —— 赤井家 ——
    ("character-shuichi-akai", "character-mary-sera", "family", "母子"),
    ("character-shuichi-akai", "character-masumi-sera", "family", "兄妹"),
    ("character-shuichi-akai", "character-shukichi-haneda", "family", "兄弟"),
    ("character-mary-sera", "character-masumi-sera", "family", "母女"),
    ("character-mary-sera", "character-shukichi-haneda", "family", "母子"),
    ("character-masumi-sera", "character-shukichi-haneda", "family", "兄妹"),
    ("character-shuichi-akai", "character-tsutomu-akai", "family", "父子"),
    ("character-tsutomu-akai", "character-mary-sera", "love", "夫妻"),
    ("character-shuichi-akai", "character-akemi-miyano", "love", "曾交往"),
    ("character-shuichi-akai", "character-hiromitsu-morofushi", "friend", "苏格兰威士忌"),
    # —— 宫野家 ——
    ("character-ai-haibara", "character-akemi-miyano", "family", "姐妹"),
    ("character-ai-haibara", "character-atsushi-miyano", "family", "父女"),
    ("character-ai-haibara", "character-elena-miyano", "family", "母女"),
    ("character-atsushi-miyano", "character-elena-miyano", "love", "夫妻"),
    ("character-akemi-miyano", "character-atsushi-miyano", "family", "父女"),
    ("character-akemi-miyano", "character-elena-miyano", "family", "母女"),
    # —— 黑衣组织 ——
    ("character-gin", "character-vodka", "colleague", "行动搭档"),
    ("character-gin", "character-chianti", "colleague", "狙击手"),
    ("character-gin", "character-korn", "colleague", "狙击手"),
    ("character-gin", "character-vermouth", "colleague", "同期但彼此猜疑"),
    ("character-gin", "character-rum", "subordinate", "听命于朗姆"),
    ("character-rum", "character-the-boss", "subordinate", "组织二号人物"),
    ("character-vermouth", "character-the-boss", "colleague", "Boss 的宠信者"),
    ("character-vermouth", "character-sharon-vineyard", "family", "同一人"),
    ("character-chianti", "character-korn", "colleague", "狙击组合"),
    ("character-vermouth", "character-shinichi-kudo", "nemesis", "被其救过、心存纠结"),
    ("character-vermouth", "character-ran-mouri", "friend", "称她为天使"),
    ("character-gin", "character-ai-haibara", "nemesis", "背叛者"),
    ("character-rei-furuya", "character-hidemi-hondou", "colleague", "同为卧底但互不知情"),
    # —— FBI / 公安 / 警视厅 ——
    ("character-shuichi-akai", "character-jodie-starling", "colleague", "FBI 同僚"),
    ("character-shuichi-akai", "character-james-black", "subordinate", "上级"),
    ("character-shuichi-akai", "character-andre-camel", "colleague", "FBI 同僚"),
    ("character-jodie-starling", "character-james-black", "subordinate", "上级"),
    ("character-jodie-starling", "character-andre-camel", "colleague", "FBI 同僚"),
    ("character-rei-furuya", "character-yuya-kazami", "subordinate", "公安部下"),
    ("character-rei-furuya", "character-hiromitsu-morofushi", "friend", "警校同窗"),
    ("character-rei-furuya", "character-wataru-date", "friend", "警校同窗"),
    ("character-rei-furuya", "character-jinpei-matsuda", "friend", "警校同窗"),
    ("character-rei-furuya", "character-kenji-hagiwara", "friend", "警校同窗"),
    ("character-hiromitsu-morofushi", "character-takaaki-morofushi", "family", "兄弟"),
    ("character-wataru-date", "character-naeko-miike", "love", "恋人"),
    ("character-wataru-date", "character-chihaya-hagiwara", "friend", "警校同窗"),
    ("character-kenji-hagiwara", "character-chihaya-hagiwara", "family", "姐弟"),
    ("character-juzo-megure", "character-wataru-takagi", "subordinate", "部下"),
    ("character-juzo-megure", "character-miwako-sato", "subordinate", "部下"),
    ("character-juzo-megure", "character-ninzaburo-shiratori", "subordinate", "部下"),
    ("character-juzo-megure", "character-kazunobu-chiba", "subordinate", "部下"),
    ("character-wataru-takagi", "character-miwako-sato", "love", "同僚伴侣"),
    ("character-ninzaburo-shiratori", "character-sumiko-kobayashi", "love", "恋人"),
    ("character-ninzaburo-shiratori", "character-miwako-sato", "friend", "警校同窗"),
    ("character-wataru-takagi", "character-naeko-miike", "friend", "警校同窗"),
    ("character-kazunobu-chiba", "character-naeko-miike", "love", "恋人"),
    ("character-yumi-miyamoto", "character-shukichi-haneda", "love", "恋人"),
    ("character-misao-yamamura", "character-yui-uehara", "colleague", "同僚"),
    ("character-kansuke-yamato", "character-yui-uehara", "colleague", "同僚搭档"),
    ("character-kansuke-yamato", "character-takaaki-morofushi", "friend", "长野三人组"),
    ("character-takaaki-morofushi", "character-yui-uehara", "friend", "长野三人组"),
    ("character-hyoue-kuroda", "character-rei-furuya", "subordinate", "上级"),
    # —— 高中生组 ——
    ("character-heiji-hattori", "character-kazuha-toyama", "love", "青梅竹马"),
    ("character-heiji-hattori", "character-heizo-hattori", "family", "父子"),
    ("character-kazuha-toyama", "character-ginshiro-toyama", "family", "父女"),
    ("character-ran-mouri", "character-sonoko-suzuki", "friend", "同学挚友"),
    ("character-sonoko-suzuki", "character-makoto-kyogoku", "love", "恋人"),
    ("character-ran-mouri", "character-masumi-sera", "friend", "同学"),
    ("character-ai-haibara", "character-mitsuhiko-tsuburaya", "friend", "少年侦探团"),
    ("character-ai-haibara", "character-ayumi-yoshida", "friend", "少年侦探团"),
    ("character-ai-haibara", "character-genta-kojima", "friend", "少年侦探团"),
    ("character-conan-edogawa", "character-mitsuhiko-tsuburaya", "friend", "少年侦探团"),
    ("character-conan-edogawa", "character-ayumi-yoshida", "friend", "少年侦探团"),
    ("character-conan-edogawa", "character-genta-kojima", "friend", "少年侦探团"),
    ("character-mitsuhiko-tsuburaya", "character-ayumi-yoshida", "friend", "少年侦探团"),
    ("character-mitsuhiko-tsuburaya", "character-genta-kojima", "friend", "少年侦探团"),
    ("character-ayumi-yoshida", "character-genta-kojima", "friend", "少年侦探团"),
    ("character-kaito-kid", "character-kaitou-kid", "family", "同一人"),
    ("character-kaito-kid", "character-ayako-suzuki", "love", "恋人"),
    ("character-kaito-kid", "character-ginzo-nakamori", "rival", "追捕者"),
    ("character-ginzo-nakamori", "character-ayako-suzuki", "family", "父女"),
    ("character-kaito-kid", "character-konosuke-jii", "mentor", "助手兼长辈"),
    ("character-yusaku-kudo", "character-kaito-kid", "mentor", "曾指点"),
    ("character-juzo-megure", "character-kiyonaga-matsumoto", "subordinate", "上级"),
    ("character-miwako-sato", "character-jinpei-matsuda", "love", "旧日恋人"),
    ("character-eri-kisaki", "character-reiko-kujo", "rival", "法庭对手"),
    ("character-hiroshi-agasa", "character-ai-haibara", "friend", "共同研究者"),
    ("character-hiroshi-agasa", "character-shinichi-kudo", "friend", "邻居"),
    ("character-wataru-takagi", "character-wataru-date", "friend", "前任搭档"),
]

BOND_TYPE_ZH = {
    "family": "家人", "love": "恋人", "colleague": "同僚", "subordinate": "上下级",
    "rival": "对手", "nemesis": "宿敌", "mentor": "师从", "friend": "朋友",
}


def uniq_bonds(seq):
    seen, out = set(), []
    for b in seq:
        key = (b.get("to"), b.get("type"))
        if key in seen:
            continue
        seen.add(key)
        out.append(b)
    return out


def main() -> int:
    data = json.loads(CHAR_PATH.read_text(encoding="utf-8"))
    is_list = isinstance(data, list)
    chars = data if is_list else (data.get("characters") or data.get("items"))
    by_id = {c["id"]: c for c in chars}

    # 全量校验：两端 id 都要存在，type 要合法，不能自连
    bad = []
    for a, b, t, _note in PAIRS:
        if a not in by_id:
            bad.append(f"from 不存在: {a}")
        if b not in by_id:
            bad.append(f"to 不存在: {b}")
        if t not in T:
            bad.append(f"非法 type: {t}")
        if a == b:
            bad.append(f"自连: {a}")
    if bad:
        print("FAIL 校验不通过，未写盘：")
        for x in sorted(set(bad)):
            print("  ", x)
        return 1

    # 双向登记：关系是对称的，两边都记，图才画得对称
    want = {}
    for a, b, t, note in PAIRS:
        want.setdefault(a, []).append({"to": b, "type": t, "note": note})
        want.setdefault(b, []).append({"to": a, "type": t, "note": note})

    changed = 0
    for cid, add in want.items():
        c = by_id[cid]
        merged = uniq_bonds(list(c.get("bonds") or []) + add)
        if merged == (c.get("bonds") or []):
            continue
        c["bonds"] = merged
        changed += 1

    if not changed:
        print(f"IDEMPOTENT_OK（无改动，不写盘）— {len(want)} 人关系均已是目标状态")
        return 0

    CHAR_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    edge_count = sum(len(v) for v in want.values()) // 2
    # 双向登记 + uniq_bonds 去重后，实际落库的对数可能与 PAIRS 条数不同
    real_edges = sum(len(c.get("bonds") or []) for c in chars) // 2
    print(f"WROTE characters.json：{changed} 人更新；{real_edges} 对关系（PAIRS 去重后）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
