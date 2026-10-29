#!/usr/bin/env python3
"""译文质量审计：自动挑出可疑译文，供人工复核。

检查项：
    1. 重复翻译：同一 (caseId, field) 在多个 batch 文件里出现且译文不同 → 后者静默覆盖前者
    2. 数字丢失：英文里的数字在中文里找不到（漏译/改写事实）
    3. 专名臆造：culprit 英文是纯拉丁名，中文却出现汉字（多半是自行拼了汉字名）
    4. 长度异常：zh/en 长度比过小或过大
    5. 空壳：translationStatus=machine 但 zhHans 为空

用法：
    python3 scripts/audit-translations.py            # 汇总
    python3 scripts/audit-translations.py --detail   # 列出具体条目
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "entities" / "cases.json"
TRANS_DIR = ROOT / "docs" / "translations"
FIELDS = ("culprit", "motive", "method", "evidence", "resolution")
CJK = re.compile(r"[\u4e00-\u9fff]")
NUM = re.compile(r"\d+(?:\.\d+)?")
# 中文数字：出现任意一个就认为数字被转写（一亿 / 九楼 / 八年前），不算丢失
CN_NUM = re.compile(r"[〇零一二三四五六七八九十百千万亿两]")


def load_cases() -> list:
    rows = json.loads(CASES.read_text(encoding="utf-8"))
    return rows if isinstance(rows, list) else rows.get("cases", [])


def duplicate_check() -> list:
    """同一字段被多个批次翻译过，且译文不一致。"""
    seen = {}
    dups = []
    for path in sorted(TRANS_DIR.glob("batch-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data.get("items", []):
            key = (item["caseId"], item["field"])
            zh = (item.get("zhHans") or "").strip()
            if not zh:
                continue
            if key in seen and seen[key][1] != zh:
                dups.append({"caseId": key[0], "field": key[1],
                             "files": [seen[key][0], path.name]})
            seen.setdefault(key, (path.name, zh))
    return dups


def field_checks(cases: list) -> dict:
    missing_num, fake_name, thin, empty = [], [], [], []
    for case in cases:
        for field in FIELDS:
            value = case.get(field)
            if not isinstance(value, dict):
                continue
            en = (value.get("en") or "").strip()
            zh = (value.get("zhHans") or "").strip()
            status = value.get("translationStatus")
            if status == "machine" and not zh:
                empty.append((case["id"], field))
                continue
            if not (en and zh):
                continue
            # 数字丢失（中文数字转写不算丢失）
            en_nums = set(NUM.findall(en))
            zh_nums = set(NUM.findall(zh))
            lost = {n for n in en_nums if n not in zh_nums}
            if lost and not CN_NUM.search(zh):
                missing_num.append((case["id"], field, sorted(lost)))
            # 专名臆造：culprit 纯拉丁 → 中文出现汉字
            if field == "culprit" and not CJK.search(en) and CJK.search(zh):
                fake_name.append((case["id"], en, zh))
            # 长度比
            ratio = len(zh) / max(len(en), 1)
            if ratio < 0.2 or ratio > 1.6:
                thin.append((case["id"], field, round(ratio, 2)))
    return {"missing_numbers": missing_num, "fake_names": fake_name,
            "length_outliers": thin, "empty_machine": empty}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--detail", action="store_true")
    args = parser.parse_args()

    cases = load_cases()
    dups = duplicate_check()
    checks = field_checks(cases)

    print(f"重复翻译冲突: {len(dups)}")
    print(f"数字丢失:     {len(checks['missing_numbers'])}")
    print(f"专名臆造:     {len(checks['fake_names'])}")
    print(f"长度异常:     {len(checks['length_outliers'])}")
    print(f"空壳 machine: {len(checks['empty_machine'])}")

    if not args.detail:
        return
    for title, key in (("重复翻译", "dups"), ("数字丢失", "missing_numbers"),
                       ("专名臆造", "fake_names"), ("长度异常", "length_outliers")):
        rows = dups if key == "dups" else checks[key]
        if not rows:
            continue
        print(f"\n--- {title} ---")
        for row in rows[:30]:
            print(row)


if __name__ == "__main__":
    main()
