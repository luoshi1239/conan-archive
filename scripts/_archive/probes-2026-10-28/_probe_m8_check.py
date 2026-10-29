"""探针：用 M8 的解析函数抽查几个已知案件，人工核对对齐是否正确。"""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("m8", ROOT / "scripts/backfill-case-facts.py")
m8 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m8)

pages = json.loads((ROOT / "data/raw/dcw-page-sections.json").read_text(encoding="utf-8"))["pages"]

for name in ("A_Car_Carrying_a_Time_Bomb", "Furinkazan", "'Til_Death_Do_Us_Part",
             "Library_Murder_Case", "The_Mist_Goblin_Legend_Murder_Case"):
    p = pages.get(name)
    if not p:
        print("MISSING", name)
        continue
    v, a, c, s = m8.parse_situation(p.get("situation"))
    print("==", name)
    print("  victims :", v)
    print("  ages    :", a)
    print("  causes  :", c)
    print("  suspects:", [x[:80] for x in s])
    print()

# 检查有没有 Culprit 泄漏进 suspects
bad = 0
for name, p in pages.items():
    v, a, c, s = m8.parse_situation(p.get("situation"))
    for x in s:
        if "culprit" in x.lower():
            bad += 1
print("suspects containing 'culprit':", bad)
