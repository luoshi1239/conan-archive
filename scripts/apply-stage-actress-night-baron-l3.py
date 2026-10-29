#!/usr/bin/env python3
"""Apply reviewed L3 batches for Stage Actress and Night Baron cases."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; CAND=ROOT/'data/candidates/entities.json'; CASES=ROOT/'data/entities/cases.json'; EPS=ROOT/'data/episodes/episodes.json'; BATCHES=ROOT/'docs/CONTENT-BATCHES.json'
INFO=[('p4-deep-case-stage-actress-01','case-stage-actress-murder',[67],'src-detective-conan-world-stage-actress-case','舞台女演员杀人事件 L3深度剧透字段','TV Original；不建立漫画File关系。'),('p4-deep-case-night-baron-01','case-night-baron-murder',[68,69,70],'src-detective-conan-world-night-baron-case','暗夜男爵杀人事件 L3深度剧透字段','漫画改编三集案件（File 72-77）。')]
FIELDS={'culprit','motive','method','evidence','resolution'}
rows=json.loads(CAND.read_text(encoding='utf-8')); cases=json.loads(CASES.read_text(encoding='utf-8')); eps=json.loads(EPS.read_text(encoding='utf-8')); total=0
for batch,target,nums,source,scope,note in INFO:
    selected=[r for r in rows if r.get('candidateId','').startswith(batch+'-')]
    if {r.get('field') for r in selected}!=FIELDS: raise SystemExit(f'{batch}:字段不完整')
    for r in selected:
        if r.get('sourceRefs')!=[source]: raise SystemExit(f'{batch}:来源不一致')
        r['reviewStatus']='accepted'; r['confidence']='medium'; r['reviewNote']='已读取案件页面 Situation/Resolution 正文并逐字段核对；L3全剧透字段。'
    case=next(c for c in cases if c.get('id')==target); changes=0
    for r in selected:
        if case.get(r['field'])!=r['value']: case[r['field']]=r['value']; changes+=1
    for key,val in {'spoiler':3,'status':'reviewed','deepSpoilers':True}.items():
        if case.get(key)!=val: case[key]=val; changes+=1
    if source not in case.setdefault('sources',[]): case['sources'].append(source); changes+=1
    for num in nums:
        ep=next(e for e in eps if e.get('number')==num)
        if target not in ep.setdefault('caseRefs',[]): ep['caseRefs']=sorted(set(ep['caseRefs'])|{target}); changes+=1
        for key,val in {'spoiler':3,'status':'reviewed','detailStatus':'reviewed'}.items():
            if ep.get(key)!=val: ep[key]=val; changes+=1
        if ep.setdefault('coverage',{}).get('deepSpoilers') is not True: ep['coverage']['deepSpoilers']=True; changes+=1
        if source not in ep.setdefault('sources',[]): ep['sources'].append(source); changes+=1
    total+=changes
    batches=json.loads(BATCHES.read_text(encoding='utf-8'))
    if not any(b.get('batchId')==batch for b in batches.get('batches',[])):
        batches.setdefault('batches',[]).append({'batchId':batch,'scope':scope,'targetLayer':'deepSpoilers','episodeNumbers':nums,'entityIds':[target],'sourceIds':[source],'status':'applied','recordCount':5,'effectiveChanges':changes,'validationResult':'pending-post-apply-validation','createdAt':'2026-10-27','appliedAt':'2026-10-27','notes':note})
        BATCHES.write_text(json.dumps(batches,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
CAND.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); CASES.write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); EPS.write_text(json.dumps(eps,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'effective_changes={total}')
