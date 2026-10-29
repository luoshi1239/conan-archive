#!/usr/bin/env python3
"""Apply the reviewed Ghost Ship Murder Case L3 batch idempotently."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; CAND=ROOT/'data/candidates/entities.json'; CASES=ROOT/'data/entities/cases.json'; EPS=ROOT/'data/episodes/episodes.json'; BATCHES=ROOT/'docs/CONTENT-BATCHES.json'
BATCH='p4-deep-case-ghost-ship-01'; TARGET='case-ghost-ship-murder'; NUMBERS={61,62}; SOURCE='src-detective-conan-world-ghost-ship-case'; FIELDS={'culprit','motive','method','evidence','resolution'}
rows=json.loads(CAND.read_text(encoding='utf-8')); selected=[r for r in rows if r.get('candidateId','').startswith(BATCH+'-')]
if {r.get('field') for r in selected}!=FIELDS: raise SystemExit('幽灵船L3候选字段不完整')
for r in selected:
 if r.get('sourceRefs') != [SOURCE]: raise SystemExit('幽灵船L3来源不一致')
 r['reviewStatus']='accepted'; r['confidence']='medium'; r['reviewNote']='已读取首个两集TV Original案件页面正文并逐字段核对；L3全剧透字段。'
cases=json.loads(CASES.read_text(encoding='utf-8')); case=next(c for c in cases if c.get('id')==TARGET); changes=0
for r in selected:
 if case.get(r['field'])!=r['value']: case[r['field']]=r['value']; changes+=1
for key,val in {'spoiler':3,'status':'reviewed','deepSpoilers':True}.items():
 if case.get(key)!=val: case[key]=val; changes+=1
if SOURCE not in case.setdefault('sources',[]): case['sources'].append(SOURCE); changes+=1
eps=json.loads(EPS.read_text(encoding='utf-8'))
for ep in eps:
 if ep.get('number') not in NUMBERS: continue
 if TARGET not in ep.setdefault('caseRefs',[]): ep['caseRefs']=sorted(set(ep['caseRefs'])|{TARGET}); changes+=1
 for key,val in {'spoiler':3,'status':'reviewed','detailStatus':'reviewed'}.items():
  if ep.get(key)!=val: ep[key]=val; changes+=1
 if ep.setdefault('coverage',{}).get('deepSpoilers') is not True: ep['coverage']['deepSpoilers']=True; changes+=1
 if SOURCE not in ep.setdefault('sources',[]): ep['sources'].append(SOURCE); changes+=1
batches=json.loads(BATCHES.read_text(encoding='utf-8'))
if not any(b.get('batchId')==BATCH for b in batches.get('batches',[])):
 batches.setdefault('batches',[]).append({'batchId':BATCH,'scope':'幽灵船杀人事件 L3深度剧透字段','targetLayer':'deepSpoilers','episodeNumbers':[61,62],'entityIds':[TARGET],'sourceIds':[SOURCE],'status':'applied','recordCount':5,'effectiveChanges':changes,'validationResult':'pending-post-apply-validation','createdAt':'2026-10-27','appliedAt':'2026-10-27','notes':'首个两集TV Original案件；不建立漫画File关系。'})
CAND.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); CASES.write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); EPS.write_text(json.dumps(eps,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); BATCHES.write_text(json.dumps(batches,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'effective_changes={changes}')
