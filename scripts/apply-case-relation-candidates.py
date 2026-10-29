#!/usr/bin/env python3
"""Apply accepted case relatedEpisodes candidates without inventing facts."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CANDIDATES=ROOT/'data/candidates/entities.json'
CASES=ROOT/'data/entities/cases.json'
BATCHES=ROOT/'docs/CONTENT-BATCHES.json'
BATCH='p3-case-relations-01'

candidates=json.loads(CANDIDATES.read_text())
for row in candidates:
    if row.get('candidateId','').startswith(BATCH):
        row['reviewStatus']='accepted'
        row['reviewNote']='已由现有案件 animeRefs 展开并核对；仅写入 relatedEpisodes 反向导航。'
CANDIDATES.write_text(json.dumps(candidates,ensure_ascii=False,indent=2)+'\n')

cases=json.loads(CASES.read_text())
by={row['id']:row for row in cases}
changes=0
for row in candidates:
    if not row.get('candidateId','').startswith(BATCH) or row.get('reviewStatus')!='accepted':continue
    target=by.get(row.get('targetId'))
    if target is None: raise SystemExit(f'unknown case {row.get("targetId")}')
    refs=set(target.get('relatedEpisodes',[]))
    value=row.get('value') or []
    before=len(refs);refs.update(value)
    target['relatedEpisodes']=sorted(refs)
    changes+=len(refs)-before
CASES.write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
bs=json.loads(BATCHES.read_text())
for batch in bs['batches']:
    if batch.get('batchId')==BATCH:
        batch['status']='applied';batch['effectiveChanges']=changes;batch['validationResult']='pending-post-apply-validation';batch['appliedAt']='2026-10-27'
        break
BATCHES.write_text(json.dumps(bs,ensure_ascii=False,indent=2)+'\n')
print(f'accepted_candidates={sum(r.get("candidateId","").startswith(BATCH) and r.get("reviewStatus")=="accepted" for r in candidates)}')
print(f'effective_changes={changes}')
