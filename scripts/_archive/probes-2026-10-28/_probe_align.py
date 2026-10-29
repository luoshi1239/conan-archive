"""探针：验证 M8 对象结构下，块内年龄/死因配对是否正确。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
cases = {c["id"]: c for c in json.loads((ROOT / "data/entities/cases.json").read_text(encoding="utf-8"))}

for cid in ("case-furinkazan", "case-roller-coaster-murder", "case-a-car-carrying-a-time-bomb",
            "case-tsukumo-magician-murder"):
    c = cases.get(cid)
    if not c:
        print("MISSING", cid)
        continue
    print("==", cid, "|", c.get("title", {}).get("zhHans") or c.get("title", {}).get("en"))
    for v in c.get("victims") or []:
        print("   ", v)
    print("    suspects:", [x[:70] for x in (c.get("suspects") or [])])
    print()

# 全库体检：有没有 name 不在原文 Victim 行里的
import re
pages = json.loads((ROOT / "data/raw/dcw-page-sections.json").read_text(encoding="utf-8"))["pages"]
bad = 0
for c in cases.values():
    page = c.get("dcwPage")
    sit = " ".join((pages.get(page) or {}).get("situation") or [])
    for v in c.get("victims") or []:
        if v["name"] not in sit:
            bad += 1
            print("NOT IN RAW:", c["id"], v["name"])
print("\nvictim names not found verbatim in situation:", bad)
