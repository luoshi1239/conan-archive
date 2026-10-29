#!/usr/bin/env python3
"""M17：补齐「出场多但 bonds 为 0」的人物关系（第三批）。

上一批（M16）覆盖了 102 对，但仍有 5 位高出场人物一条关系都没有：
  冲野洋子 61 案 / 十和警官 41 案 / 榎本梓 30 案 / 横沟参悟 29 案 / 比护隆佑 20 案
他们在关系图上都是孤立点，看着像「数据没录」。

原则：
  1. 只写原作中确定成立的关系，不做推测；
  2. 双向登记，脚本内去重（A→B 与 B→A 只落一条边上）；
  3. 任何一端 id 不存在 → 整个批次拒绝写盘，不猜测补 id；
  4. 幂等：二遍输出 IDEMPOTENT_OK 且不写盘。

用法：
  python3.14 scripts/backfill-character-bonds-batch2.py [--dry-run]
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHARS = ROOT / "data/entities/characters.json"

# (A, B, type, note)
# type ∈ family / love / colleague / subordinate / rival / nemesis / mentor / friend
PAIRS = [
    # ── 冲野洋子：偶像，毛利小五郎的偶像、柯南与小兰的熟人
    ("character-yoko-okino", "character-kogoro-mouri", "friend", "小五郎的偶像"),
    ("character-yoko-okino", "character-ran-mouri", "friend", "熟人"),
    ("character-yoko-okino", "character-conan-edogawa", "friend", "熟人"),
    # ── 十和警官（群马县警）：山村操的部下
    ("character-officer-tome", "character-misao-yamamura", "subordinate", "部下"),
    # ── 榎本梓：白罗咖啡厅店员，毛利侦探事务所楼下
    ("character-azusa-enomoto", "character-kogoro-mouri", "colleague", "楼下咖啡厅店员"),
    ("character-azusa-enomoto", "character-ran-mouri", "friend", "熟人"),
    ("character-azusa-enomoto", "character-conan-edogawa", "friend", "熟人"),
    # ── 横沟参悟 / 横沟重悟：兄弟，均为刑警
    ("character-sango-yokomizo", "character-jugo-yokomizo", "family", "兄弟"),
    ("character-sango-yokomizo", "character-juzo-megure", "colleague", "同系统刑警"),
    ("character-jugo-yokomizo", "character-juzo-megure", "colleague", "同系统刑警"),
    # ── 比护隆佑：职业足球选手，灰原哀的偶像
    ("character-ryusuke-higo", "character-ai-haibara", "friend", "灰原崇拜的球星"),
    # ── 目暮十三 — 白鸟任三郎：警视厅内部上下级
    ("character-juzo-megure", "character-ninzaburo-shiratori", "colleague", "警视厅同僚"),
    # ── 山村操 — 毛利小五郎：多次合作办案
    ("character-misao-yamamura", "character-kogoro-mouri", "colleague", "合作办案"),
    # ── 三池苗子 — 千叶和伸：已在 M16 登记为恋人，此处不重复
    # ── 诸伏高明 — 大和敢助：长野县警搭档
    ("character-takaaki-morofushi", "character-kansuke-yamato", "colleague", "长野县警搭档"),
]


def load():
    data = json.loads(CHARS.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else (data.get("items") or next(iter(data.values())))
    return data, items


def main():
    dry = "--dry-run" in sys.argv
    data, chars = load()
    by_id = {c["id"]: c for c in chars}

    # 先整体校验，任何一个 id 不存在就整批拒绝
    missing = sorted({i for a, b, _, _ in PAIRS for i in (a, b) if i not in by_id})
    if missing:
        print("REFUSE: 以下 id 不在角色库中，整批不写盘：")
        for m in missing:
            print("  -", m)
        return 1

    # 现有关系对（无序），用于幂等与去重
    existing = set()
    for c in chars:
        for b in c.get("bonds") or []:
            existing.add(tuple(sorted([c["id"], b["to"]])))

    added = 0
    for a, b, typ, note in PAIRS:
        key = tuple(sorted([a, b]))
        if key in existing:  # 已登记，跳过
            continue
        ca, cb = by_id[a], by_id[b]
        ca.setdefault("bonds", []).append({"to": b, "type": typ, "note": note})
        cb.setdefault("bonds", []).append({"to": a, "type": typ, "note": note})
        existing.add(key)
        added += 1

    real_edges = sum(len(c.get("bonds") or []) for c in chars) // 2
    print(f"PAIRS 定义 {len(PAIRS)} 对，本次新增 {added} 对，落库实际 {real_edges} 对")

    if added == 0:
        print("IDEMPOTENT_OK（无改动，不写盘）")
        return 0
    if dry:
        print("DRY_RUN：未写盘")
        return 0

    CHARS.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"WROTE {CHARS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
