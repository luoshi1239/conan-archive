"""探针：检查 situation 与 resolution 里的 Victim/Age/Cause 是否一致，能否安全只取 situation。"""
import json
import re
import collections

SRC = "data/raw/dcw-page-sections.json"
data = json.load(open(SRC, encoding="utf-8"))
pages = data["pages"] if "pages" in data else data


def lines(sec, f):
    return [re.match(r"^%s\s*:\s*(.+)$" % re.escape(f), (l or "").strip()).group(1).strip()
            for l in (sec or [])
            if re.match(r"^%s\s*:\s*(.+)$" % re.escape(f), (l or "").strip())]


same = 0
diff = 0
only_sit = 0
only_res = 0
examples = []

for name, p in pages.items():
    sit, res = p.get("situation") or [], p.get("resolution") or []
    for f in ("Victim", "Age", "Cause of death"):
        vs, vr = lines(sit, f), lines(res, f)
        if vs and vr:
            if [x.lower() for x in vs] == [x.lower() for x in vr]:
                same += 1
            else:
                diff += 1
                if len(examples) < 12:
                    examples.append((name, f, vs[:3], vr[:3]))
        elif vs:
            only_sit += 1
        elif vr:
            only_res += 1

print("both-sections same:", same, " diff:", diff)
print("only situation:", only_sit, " only resolution:", only_res)
for e in examples:
    print("DIFF", e)

# 多值情况（一个页面同一字段出现多次）
multi = collections.Counter()
for name, p in pages.items():
    for sec in ("situation", "resolution"):
        for f in ("Victim", "Age", "Cause of death", "Suspects"):
            n = len(lines(p.get(sec) or [], f))
            if n > 1:
                multi[(f, sec, n)] += 1
print("\nmulti-value per page:", dict(multi))
