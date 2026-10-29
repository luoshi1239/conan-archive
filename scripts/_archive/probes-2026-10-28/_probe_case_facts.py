"""探针：统计 dcw-page-sections.json 正文里的条目行（Victim/Age/...）覆盖情况。"""
import json
import re
import collections

SRC = "data/raw/dcw-page-sections.json"
FIELDS = ["Victim", "Age", "Cause of death", "Suspects", "Culprit", "Location",
          "Murder weapon", "Time of death", "Weapon"]

data = json.load(open(SRC, encoding="utf-8"))
pages = data["pages"] if "pages" in data else data

pat = {f: re.compile(r"^\**%s\**\s*:\s*(.+)$" % re.escape(f), re.I) for f in FIELDS}
cnt = collections.Counter()
per = collections.Counter()
samples = collections.defaultdict(list)
pagehit = collections.Counter()

for name, p in pages.items():
    for f in FIELDS:
        hit = False
        for sec in ("situation", "resolution"):
            for line in (p.get(sec) or []):
                m = pat[f].match((line or "").strip())
                if m:
                    cnt[f] += 1
                    per[(f, sec)] += 1
                    hit = True
                    if len(samples[f]) < 8:
                        samples[f].append((name, sec, m.group(1)[:110]))
        if hit:
            pagehit[f] += 1

print("pages:", len(pages))
print("\n== page-level coverage (unique pages) ==")
for f in FIELDS:
    print("  %-16s pages=%d lines=%d  %s" % (f, pagehit[f], cnt[f],
          dict((s, per[(f, s)]) for s in ("situation", "resolution") if per[(f, s)])))

print("\n== samples ==")
for f in FIELDS:
    if not samples[f]:
        continue
    print("--", f)
    for x in samples[f][:5]:
        print("   ", x)
