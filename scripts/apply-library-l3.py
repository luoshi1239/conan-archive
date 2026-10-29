#!/usr/bin/env python3
"""Apply the reviewed Library Murder Case L3 batch idempotently."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CAND=ROOT/'data/candidates/entities.json'; CASES=ROOT/'data/entities/cases.json'; EPS=ROOT/'data/episodes/episodes.json'; BATCHES=ROOT/'docs/CONTENT-BATCHES.json'
BATCH='p4-deep-case-library-01'; TARGET='case-library-murder'; SOURCE='src-detective-conan-world-library-case'; FIELDS={'culprit','motive','method','evidence','resolution'}
rows=json.loads(CAND.read_text(encoding='utf-8')); selected=[r for r in rows if r.get('candidateId','').startswith(BATCH+'-')]
if {r.get('field') for r in selected} != FIELDS: raise SystemExit('图书馆L3候选字段不完整')
for r in selected:
 if r.get('sourceRefs') != [SOURCE]: raise SystemExit('图书馆L3来源不一致')
 r['reviewStatus']='accepted'; r['confidence']='medium'; r['reviewNote']='已读取案件页面正文并逐字段核对；L3全剧透字段。'
CAND.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
cases=json.loads(CASES.read_text(encoding='utf-8')); case=next(r for r in cases if r.get('id')==TARGET); changes=0
for r in selected:
 if case.get(r['field']) != r['value']: case[r['field']]=r['value']; changes+=1
for k,v in {'spoiler':3,'status':'reviewed','deepSpoilers':True}.items():
 if case.get(k)!=v: case[k]=v; changes+=1
if SOURCE not in case.setdefault('sources',[]): case['sources'].append(SOURCE); changes+=1
CASES.write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
eps=json.loads(EPS.read_text(encoding='utf-8')); episode_changes=0
for e in eps:
 if e.get('number')==50:
  if e.get('spoiler')!=3: e['spoiler']=3; episode_changes+=1
  if e.get('status')!='reviewed': e['status']='reviewed'; episode_changes+=1
  cov=e.setdefault('coverage',{})
  if cov.get('deepSpoilers') is not True: cov['deepSpoilers']=True; episode_changes+=1
  if SOURCE not in e.setdefault('sources',[]): e['sources'].append(SOURCE); episode_changes+=1
EPISODES=EPS; EPISODES.write_text(json.dumps(eps,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
batches=json.loads(BATCHES.read_text(encoding='utf-8'))
if not any(r.get('batchId')==BATCH for r in batches.get('batches',[])):
 batches.setdefault('batches',[]).append({'batchId':BATCH,'scope':'图书馆杀人事件 L3 深度剧透字段','targetLayer':'deepSpoilers','episodeNumbers':[50],'entityIds':[TARGET],'sourceIds':[SOURCE],'status':'applied','recordCount':len(selected),'effectiveChanges':changes+episode_changes,'validationResult':'pending-post-apply-validation','createdAt':'2026-10-27','appliedAt':'2026-10-27','notes':'第三个深度剧透试点；新增案件实体并应用EP.51。'})
BATCHES.write_text(json.dumps(batches,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'case_changes={changes}'); print(f'episode_changes={episode_changes}')
