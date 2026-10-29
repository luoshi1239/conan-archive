#!/usr/bin/env python3
"""Audit case coverage, field completeness, and episode reverse links."""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def expand(ref):
    if not ref.startswith("episode-"): return []
    tail=ref.removeprefix("episode-")
    if "-" not in tail: return [int(tail)]
    a,b=tail.split("-",1); return list(range(int(a),int(b)+1))

def main():
    episodes=load("data/episodes/episodes.json")
    cases=load("data/entities/cases.json")
    by={r["number"]:r for r in episodes}
    rows=[]
    for case in cases:
        nums=sorted({n for ref in case.get("animeRefs",[]) for n in expand(ref)})
        linked=[by[n] for n in nums if n in by]
        fields={
            "title": bool(case.get("title")),
            "summary": bool(case.get("summary")),
            "mangaRefs": bool(case.get("mangaRefs")),
            "animeRefs": bool(case.get("animeRefs")),
            "characters": bool(case.get("characters")),
            "locations": bool(case.get("locationRefs") or case.get("locations")),
            "sources": bool(case.get("sources")),
            "deepSpoilers": all(case.get(k) is not None for k in ("culprit","motive","method","evidence","resolution")),
        }
        rows.append({
            "id":case["id"], "title":case.get("title",{}).get("zhHans") if isinstance(case.get("title"),dict) else case.get("title"),
            "status":case.get("status"), "episodeCount":len(nums),
            "reviewedEpisodes":sum(r.get("detailStatus")=="reviewed" for r in linked),
            "structureEpisodes":sum((r.get("coverage") or {}).get("structure") is True for r in linked),
            "fields":fields,
            "missingFields":[k for k,v in fields.items() if not v],
        })
    report={
        "generatedFrom":["data/entities/cases.json","data/episodes/episodes.json"],
        "caseCount":len(rows),
        "status":dict(Counter(r["status"] for r in rows)),
        "totalReferencedEpisodes":sum(r["episodeCount"] for r in rows),
        "totalStructureEpisodes":sum(r["structureEpisodes"] for r in rows),
        "deepSpoilerCases":sum(r["fields"]["deepSpoilers"] for r in rows),
        "cases":rows,
    }
    out=ROOT/"docs"/"CASE-COVERAGE.json"
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="cases"},ensure_ascii=False,indent=2))
    print(f"WROTE {out.relative_to(ROOT)}")

if __name__=="__main__": main()
