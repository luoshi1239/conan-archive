"""探针：列出 suspects 里含 culprit 的原文，判断是原文本身还是解析错误。"""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("m8", ROOT / "scripts/backfill-case-facts.py")
m8 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m8)

pages = json.loads((ROOT / "data/raw/dcw-page-sections.json").read_text(encoding="utf-8"))["pages"]

for name, p in pages.items():
    v, a, c, s = m8.parse_situation(p.get("situation"))
    for x in s:
        if "culprit" in x.lower():
            print("PAGE:", name)
            print("  suspects原串:", x)
            for l in (p.get("situation") or []):
                if l.strip().startswith("Suspects"):
                    print("  原文行:", l[:200])
            print()
