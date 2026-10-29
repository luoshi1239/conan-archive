#!/usr/bin/env python3
"""M8：案件被害人/年龄/死因/嫌疑人 —— 从 DCW 页面 `situation` 段的条目行搬原文。

来源
----
`data/raw/dcw-page-sections.json` 的 `situation` 段（案件设定段）里，DCW 用「案件事件块」
逐条登记事实，一个案件页可能含多块（如 Furinkazan 有 5 块对应 5 起死亡）：

    Location: Forest, Nagano
    Victim: Ayaka Tatsuo
    Age: 27 years old
    Cause of death: Hanging
    Suspects: Naonobu Torada, Tatsue Torada, ...

口径（重要）
------------
**只读 `situation`，绝不读 `resolution`。** `resolution` 是解答段：
- 其中的 `Victim` 常是「案发后追加的伤亡」，甚至把 Conan 列为被害人
- 其中的 `Culprit` 直接点名凶手

实测两段 Victim 有 146 处不一致。非剧透字段读到解答段就是泄底。
`situation` 段里也有 `Culprit` 行（97 次），同样**不搬**。

写入字段
--------
    victims         [{name, age?, causeOfDeath?}]  按块配对的结构化数组
    suspects        [str]  原文嫌疑人整串（保留 and / 逗号原貌，不拆名）
    caseFactsSource str    DCW 页名

为什么 victims 是对象而非并行数组
--------------------------------
初版写成 `victims: [...]` + `victimAges: [...]` 两个并行数组，靠下标配对。
实测有 40 个案件两者长度不等（如 Furinkazan 5 个被害人只有 2 个年龄），
按下标配对会**张冠李戴**——Ayaka 的 27 岁会被显示成 Yoshiro 的年龄。

改成对象后，年龄/死因是**块内配对**的结果：块里没写 Age 就是没有，绝不借用别人的。

幂等：结果与现有值相同则不写盘。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data/entities/cases.json"
SECTIONS = ROOT / "data/raw/dcw-page-sections.json"
DRY = "--dry-run" in sys.argv

FIELD_RX = {
    "victim": re.compile(r"^Victim\s*:\s*(.+)$"),
    "age": re.compile(r"^Age\s*:\s*(.+)$"),
    "cause": re.compile(r"^Cause of death\s*:\s*(.+)$"),
    "suspects": re.compile(r"^Suspects\s*:\s*(.+)$"),
}
# 剧透字段：解析到就跳过并断开块配对
FORBIDDEN = re.compile(r"^(Culprit|Resolution|Trick|Motive)\s*:", re.I)
# 原文占位值（无实际信息）
PLACEHOLDER = re.compile(r"^(unknown(\s+(culprit|culprits|kidnapper|person|suspects?))?|n/?a|none)$", re.I)


def parse_situation(sec):
    """从 situation 段解析被害者（块内配对姓名/年龄/死因）与嫌疑人。

    块 = 一条 Victim 行开启，后续 Age / Cause of death 归属给该被害人，
    直到出现下一条 Victim 或剧透行。
    """
    victims = []   # [{name, age?, causeOfDeath?}]
    suspects = []
    cur = None     # 当前被害人 dict

    for raw in sec or []:
        line = str(raw).strip()
        if not line:
            continue
        if FORBIDDEN.match(line):
            cur = None
            continue

        m = FIELD_RX["victim"].match(line)
        if m:
            name = m.group(1).strip()
            if not name or PLACEHOLDER.match(name):
                cur = None
                continue
            cur = next((v for v in victims if v["name"] == name), None)
            if cur is None:
                cur = {"name": name}
                victims.append(cur)
            continue

        m = FIELD_RX["age"].match(line)
        if m:
            val = m.group(1).strip()
            if val and cur is not None and "age" not in cur and not PLACEHOLDER.match(val):
                cur["age"] = val
            continue

        m = FIELD_RX["cause"].match(line)
        if m:
            val = m.group(1).strip()
            if val and cur is not None and "causeOfDeath" not in cur and not PLACEHOLDER.match(val):
                cur["causeOfDeath"] = val
            continue

        m = FIELD_RX["suspects"].match(line)
        if m:
            val = m.group(1).strip()
            if val and not PLACEHOLDER.match(val) and val not in suspects:
                suspects.append(val)
            continue

    return victims, suspects


def main() -> int:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    sections = json.loads(SECTIONS.read_text(encoding="utf-8"))["pages"]

    changed = 0
    n_victims = 0
    n_age = 0
    n_cause = 0
    n_suspects = 0
    legacy_removed = 0

    for c in cases:
        page = c.get("dcwPage")
        if not page:
            continue
        sec = sections.get(page)
        if not sec:
            continue

        victims, suspects = parse_situation(sec.get("situation"))
        if not victims and not suspects:
            continue

        want = {}
        if victims:
            want["victims"] = victims
        if suspects:
            want["suspects"] = suspects
        want["caseFactsSource"] = page

        dirty = any(c.get(k) != v for k, v in want.items())
        # 旧并行数组若存在也必须清掉（口径已改为对象）
        stale = [k for k in ("victimAges", "causesOfDeath") if k in c]
        if not dirty and not stale:
            continue

        if not DRY:
            for k in ("victimAges", "causesOfDeath"):
                if k in c:
                    c.pop(k, None)
                    legacy_removed += 1
            for k, v in want.items():
                c[k] = v
            if victims:
                n_victims += 1
                n_age += sum(1 for v in victims if v.get("age"))
                n_cause += sum(1 for v in victims if v.get("causeOfDeath"))
            if suspects:
                n_suspects += 1
        changed += 1

    print(f"M8 案件事实：本轮写入 {changed} 条案件")
    if DRY:
        cov_v = cov_a = cov_c = cov_s = 0
        for c in cases:
            page = c.get("dcwPage")
            if not page:
                continue
            v, s = parse_situation((sections.get(page) or {}).get("situation"))
            if v:
                cov_v += 1
                cov_a += sum(1 for x in v if x.get("age"))
                cov_c += sum(1 for x in v if x.get("causeOfDeath"))
            if s:
                cov_s += 1
        print(f"   [dry-run] 预计：被害者 {cov_v} 案 / 带年龄 {cov_a} 人 / 带死因 {cov_c} 人 / 嫌疑人 {cov_s} 案")
        print("   [dry-run] 未写盘")
        return 0

    if changed == 0:
        print("   IDEMPOTENT_OK（无改动，不写盘）")
        return 0

    CASES.write_text(
        json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"   被害者 {n_victims} 案（其中带年龄 {n_age} 人、带死因 {n_cause} 人）；嫌疑人 {n_suspects} 案")
    if legacy_removed:
        print(f"   清除旧并行数组字段 {legacy_removed} 处")
    print("   已写入 cases.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
