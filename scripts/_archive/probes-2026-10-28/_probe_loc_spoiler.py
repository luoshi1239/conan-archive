"""探针：检查现有 cases.json 的 locations 是否混入了 resolution 段独有的地点（疑似剧透/错位）。"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
cases = json.loads((ROOT / "data/entities/cases.json").read_text(encoding="utf-8"))
pages = json.loads((ROOT / "data/raw/dcw-page-sections.json").read_text(encoding="utf-8"))["pages"]
locs = json.loads((ROOT / "data/entities/locations.json").read_text(encoding="utf-8"))
id2name = {e["id"]: ((e.get("name") or {}).get("en") or "").lower() for e in locs}

LAB = re.compile(r"^Location:\s*(.+)$")


def vals(sec):
    out = []
    for raw in sec or []:
        m = LAB.match(str(raw).strip())
        if m:
            v = m.group(1).strip()
            if v:
                out.append(v)
    return out


bad = []
for c in cases:
    if not c.get("locations") or not c.get("dcwPage"):
        continue
    p = pages.get(c["dcwPage"]) or {}
    sit = {v.lower() for v in vals(p.get("situation"))}
    res = {v.lower() for v in vals(p.get("resolution"))}
    cur = []
    for x in c["locations"]:
        cur.append(id2name.get(x, x).lower())
    leaked = [x for x in cur if x not in sit and x in res]
    if leaked:
        bad.append((c["id"], c["dcwPage"], leaked[:3], sorted(sit)[:3], sorted(res)[:3]))

print("cases whose locations contain resolution-only places:", len(bad))
for b in bad[:15]:
    print(" ", b)
