#!/usr/bin/env python3
"""Apply the reviewed Moonlight Sonata L3 case batch."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CAND=ROOT/'data/candidates/entities.json'; CASES=ROOT/'data/entities/cases.json'; EPS=ROOT/'data/episodes/episodes.json'; BATCHES=ROOT/'docs/CONTENT-BATCHES.json'
BATCH='p4-deep-case-moonlight-01'; TARGET='case-moon-shadow-island'
FIELDS={'culprit','motive','method','evidence','resolution'}
rows=json.loads(CAND.read_text())
for row in rows:
    if row.get('candidateId','').startswith(BATCH):
        row['reviewStatus']='accepted'; row['confidence']='medium'; row['reviewNote']='已读取案件正文并逐字段核对；L3全剧透字段。'
CAND.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
cases=json.loads(CASES.read_text()); case=next(x for x in cases if x['id']==TARGET); changes=0
for row in rows:
    if row.get('candidateId','').startswith(BATCH) and row.get('reviewStatus')=='accepted':
        field=row['field']; old=case.get(field)
        if old != row['value']: case[field]=row['value']; changes+=1
case['spoiler']=3; case['status']='reviewed'; case['deepSpoilers']=True
CASES.write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
episodes=json.loads(EPS.read_text()); episode_changes=0
for ep in episodes:
    if ep.get('number') in (11,12):
        cov=ep.setdefault('coverage',{})
        if cov.get('deepSpoilers') is not True: episode_changes+=1
        cov['deepSpoilers']=True; ep['spoiler']=3
        ep['detailStatus']='reviewed'; ep['status']='reviewed'
EPS.write_text(json.dumps(episodes,ensure_ascii=False,indent=2)+'\n')
batches=json.loads(BATCHES.read_text())
if not any(x.get('batchId')==BATCH for x in batches['batches']): batches['batches'].append({'batchId':BATCH,'scope':'月影岛案件 L3 深度剧透字段','targetLayer':'deepSpoilers','episodeNumbers':[11,12],'entityIds':[TARGET],'sourceIds':['src-detective-conan-world-moonlight-sonata'],'status':'applied','recordCount':5,'effectiveChanges':changes+episode_changes,'validationResult':'pending-post-apply-validation','createdAt':'2026-10-27','appliedAt':'2026-10-27','notes':'首个深度剧透试点；仅应用月影岛案件及EP.11—12。'})
BATCHES.write_text(json.dumps(batches,ensure_ascii=False,indent=2)+'\n')
print('case_field_changes',changes); print('episode_deep_changes',episode_changes)
