#!/usr/bin/env python3
"""Apply the reviewed Train Trick Murder Case L3 batch idempotently."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CAND=ROOT/'data/candidates/entities.json'; CASES=ROOT/'data/entities/cases.json'; EPS=ROOT/'data/episodes/episodes.json'; BATCHES=ROOT/'docs/CONTENT-BATCHES.json'
BATCH='p4-deep-case-train-01'; TARGET='case-train-trick'; NUMBER=55; SOURCE='src-detective-conan-world-train-trick-case'; FIELDS={'culprit','motive','method','evidence','resolution'}
rows=json.loads(CAND.read_text(encoding='utf-8')); selected=[r for r in rows if r.get('candidateId','').startswith(BATCH+'-')]
if {r.get('field') for r in selected} != FIELDS: raise SystemExit('列车L3候选字段不完整')
for r in selected:
 if r.get('sourceRefs') != [SOURCE]: raise SystemExit('列车L3来源不一致')
 r['reviewStatus']='accepted'; r['confidence']='medium'; r['reviewNote']='已读取TV Original案件页面正文并逐字段核对；L3全剧透字段。'
cases=json.loads(CASES.read_text(encoding='utf-8')); case=next(c for c in cases if c.get('id')==TARGET); changes=0
for r in selected:
 if case.get(r['field']) != r['value']: case[r['field']]=r['value']; changes+=1
for key,value in {'spoiler':3,'status':'reviewed','deepSpoilers':True}.items():
 if case.get(key)!=value: case[key]=value; changes+=1
if SOURCE not in case.setdefault('sources',[]): case['sources'].append(SOURCE); changes+=1
episodes=json.loads(EPS.read_text(encoding='utf-8')); episode=next(e for e in episodes if e.get('number')==NUMBER)
refs=set(episode.get('caseRefs',[]))
if TARGET not in refs: episode['caseRefs']=sorted(refs|{TARGET}); changes+=1
for key,value in {'spoiler':3,'status':'reviewed','detailStatus':'reviewed'}.items():
 if episode.get(key)!=value: episode[key]=value; changes+=1
coverage=episode.setdefault('coverage',{})
if coverage.get('deepSpoilers') is not True: coverage['deepSpoilers']=True; changes+=1
if SOURCE not in episode.setdefault('sources',[]): episode['sources'].append(SOURCE); changes+=1
batches=json.loads(BATCHES.read_text(encoding='utf-8'))
if not any(b.get('batchId')==BATCH for b in batches.get('batches',[])):
 batches.setdefault('batches',[]).append({'batchId':BATCH,'scope':'列车诡计杀人事件 L3深度剧透字段','targetLayer':'deepSpoilers','episodeNumbers':[NUMBER],'entityIds':[TARGET],'sourceIds':[SOURCE],'status':'applied','recordCount':5,'effectiveChanges':changes,'validationResult':'pending-post-apply-validation','createdAt':'2026-10-27','appliedAt':'2026-10-27','notes':'TV Original；不建立漫画File关系。'})
CAND.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); CASES.write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); EPS.write_text(json.dumps(episodes,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); BATCHES.write_text(json.dumps(batches,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'effective_changes={changes}')
