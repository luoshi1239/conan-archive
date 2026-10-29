#!/usr/bin/env python3
"""Apply the reviewed L3 batches for episodes 53 and 54."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CAND=ROOT/'data/candidates/entities.json'; CASES=ROOT/'data/entities/cases.json'; EPS=ROOT/'data/episodes/episodes.json'; BATCHES=ROOT/'docs/CONTENT-BATCHES.json'
BATCHES_INFO=[
 ('p4-deep-case-weapon-01','case-mystery-weapon',53,'src-detective-conan-world-weapon-case'),
 ('p4-deep-case-game-01','case-game-company-murder',54,'src-detective-conan-world-game-company-case'),
]
FIELDS={'culprit','motive','method','evidence','resolution'}
rows=json.loads(CAND.read_text(encoding='utf-8'))
cases=json.loads(CASES.read_text(encoding='utf-8')); episodes=json.loads(EPS.read_text(encoding='utf-8'))
all_changes=0
for batch,target,number,source in BATCHES_INFO:
 selected=[r for r in rows if r.get('candidateId','').startswith(batch+'-')]
 if {r.get('field') for r in selected} != FIELDS: raise SystemExit(f'{batch}:字段不完整')
 for r in selected:
  if r.get('sourceRefs') != [source]: raise SystemExit(f'{batch}:来源不一致')
  r['reviewStatus']='accepted'; r['confidence']='medium'; r['reviewNote']='已读取案件页面正文并逐字段核对；L3全剧透字段。'
 case=next(c for c in cases if c.get('id')==target); changes=0
 for r in selected:
  if case.get(r['field']) != r['value']: case[r['field']]=r['value']; changes+=1
 for key,value in {'spoiler':3,'status':'reviewed','deepSpoilers':True}.items():
  if case.get(key)!=value: case[key]=value; changes+=1
 if source not in case.setdefault('sources',[]): case['sources'].append(source); changes+=1
 episode=next(e for e in episodes if e.get('number')==number)
 if target not in episode.setdefault('caseRefs',[]): episode['caseRefs']=sorted(set(episode['caseRefs'])|{target}); changes+=1
 if episode.get('spoiler')!=3: episode['spoiler']=3; changes+=1
 if episode.get('status')!='reviewed': episode['status']='reviewed'; changes+=1
 if episode.get('detailStatus')!='reviewed': episode['detailStatus']='reviewed'; changes+=1
 episode.setdefault('coverage',{})['deepSpoilers']=True
 if source not in episode.setdefault('sources',[]): episode['sources'].append(source); changes+=1
 if target=='case-game-company-murder':
  if 'organization-black' not in episode.setdefault('organizations',[]): episode['organizations'].append('organization-black'); changes+=1
 all_changes+=changes
batches=json.loads(BATCHES.read_text(encoding='utf-8'))
for batch,target,number,source in BATCHES_INFO:
 if not any(x.get('batchId')==batch for x in batches.get('batches',[])):
  batches.setdefault('batches',[]).append({'batchId':batch,'scope':f'{target} L3深度剧透字段','targetLayer':'deepSpoilers','episodeNumbers':[number],'entityIds':[target],'sourceIds':[source],'status':'applied','recordCount':5,'effectiveChanges':'pending-post-apply-report','validationResult':'pending-post-apply-validation','createdAt':'2026-10-27','appliedAt':'2026-10-27','notes':'逐字段读取案件正文；EP.54另保留黑衣组织爆炸作为结局上下文。'})
CAND.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); CASES.write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); EPS.write_text(json.dumps(episodes,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); BATCHES.write_text(json.dumps(batches,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'effective_changes={all_changes}')
