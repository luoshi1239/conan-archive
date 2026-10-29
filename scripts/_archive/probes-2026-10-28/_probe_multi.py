"""探针：看 situation 段中多值 Victim/Age/Suspects 的原貌，决定写入形态。"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
pages = json.loads((ROOT / "data/raw/dcw-page-sections.json").read_text(encoding="utf-8"))["pages"]


def lines(sec, field):
    rx = re.compile(r"^%s\s*:\s*(.+)$" % re.escape(field))
    return [m.group(1).strip() for m in (rx.match(str(r).strip()) for r in sec or []) if m]


shown = 0
for name, p in pages.items():
    sit = p.get("situation") or []
    vs = lines(sit, "Victim")
    if len(vs) >= 3 and shown < 8:
        shown += 1
        print("==", name)
        print("   raw situation:")
        for l in sit:
            print("     |", l[:150])
        print("   -> victims:", vs)
        print()
