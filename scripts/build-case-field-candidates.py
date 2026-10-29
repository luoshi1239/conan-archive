#!/usr/bin/env python3
"""Create candidates for already-declared case character/location/File links."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CASES=ROOT/'data/entities/cases.json'; CAND=ROOT/'data/candidates/entities.json'; BATCHES=ROOT/'docs/CONTENT-BATCHES.json'
BATCH='p3-case-relations-02'
SOURCE=['src-detective-conan-world-manga','src-detective-conan-world-anime']
fields=[]
for case in json.loads(CASES.read_text()):
    cid=case['id']
    for field in ('characters','locationRefs','mangaRefs'):
        value=case.get(field)
        if value:
            fields.append((cid,field,value))
rows=[]
for cid,field,value in fields:
    rows.append({'candidateId':f'{BATCH}-{cid}-{field}','targetId':cid,'field':field,'value':value,'sourceRefs':SOURCE,'confidence':'high' if field in ('characters','mangaRefs') else 'medium','reviewStatus':'pending','reviewNote':'由现有案件字段和已登记来源生成候选，用于实体/漫画/地点关系覆盖审计。'})
CAND.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
bs=json.loads(BATCHES.read_text())
if not any(x.get('batchId')==BATCH for x in bs['batches']):bs['batches'].append({'batchId':BATCH,'scope':'案件已有角色、地点、漫画 File 关系覆盖审计','targetLayer':'structure','episodeNumbers':[],'entityIds':[x['id'] for x in json.loads(CASES.read_text())],'sourceIds':SOURCE,'status':'candidate','recordCount':len(rows),'effectiveChanges':0,'validationResult':None,'createdAt':'2026-10-27','appliedAt':None,'notes':'只审计已有关系，不新增实体或推断剧情。'})
BATCHES.write_text(json.dumps(bs,ensure_ascii=False,indent=2)+'\n')
print('case_relation_field_candidates',len(rows))
