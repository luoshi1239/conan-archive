"""探针：估算只取 situation 后 locations 的覆盖，以及 victim/age/cause/suspects 的覆盖。"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
cases = json.loads((ROOT / "data/entities/cases.json").read_text(encoding="utf-8"))
pages = json.loads((ROOT / "data/raw/dcw-page-sections.json").read_text(encoding="utf-8"))["pages"]
locs = json.loads((ROOT / "data/entities/locations.json").read_text(encoding="utf-8"))
id2name = {e["id"]: ((e.get("name") or {}).get("en") or "").lower() for e in locs}
by_name = {((e.get("name") or {}).get("en") or "").strip().lower(): e["id"] for e in locs}


def lines(sec, field):
    rx = re.compile(r"^%s\s*:\s*(.+)$" % re.escape(field))
    out = []
    for raw in sec or []:
        m = rx.match(str(raw).strip())
        if m:
            v = m.group(1).strip()
            if v:
                out.append(v)
    return out


now = 0
new = 0
shrink = 0
grow = 0
same = 0
lose_all = []
for c in cases:
    if not c.get("dcwPage"):
        continue
    p = pages.get(c["dcwPage"]) or {}
    sit = lines(p.get("situation"), "Location")
    cur = [id2name.get(x, x) for x in (c.get("locations") or [])]
    if c.get("locations"):
        now += 1
    if sit:
        new += 1
    if len(sit) < len(set(cur)):
        shrink += 1
    elif len(sit) > len(set(cur)):
        grow += 1
    else:
        same += 1
    if cur and not sit:
        lose_all.append(c["id"])

print("locations now:", now, " with situation-only:", new)
print("would shrink:", shrink, " grow:", grow, " same len:", same)
print("cases that would lose ALL locations:", len(lose_all))
print(lose_all[:10])

print("\n== new fields coverage (situation only) ==")
for f in ("Victim", "Age", "Cause of death", "Suspects"):
    n = sum(1 for c in cases if c.get("dcwPage") and lines((pages.get(c["dcwPage"]) or {}).get("situation"), f))
    print("  %-16s %d" % (f, n))

print("\n== examples ==")
for c in cases[:400]:
    p = pages.get(c.get("dcwPage") or "") or {}
    v = lines(p.get("situation"), "Victim")
    if v:
        print(c["id"], "|", v, "|", lines(p.get("situation"), "Age"), "|", lines(p.get("situation"), "Cause of death"))
        if len([1]) > 0 and c is not None:
            pass
        if cases.index(c) > 6:
            break
