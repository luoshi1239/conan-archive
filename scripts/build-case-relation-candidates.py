#!/usr/bin/env python3
"""Create case-to-episode relation candidates from reviewed case animeRefs."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CASES=ROOT/'data/entities/cases.json'
CANDIDATES=ROOT/'data/candidates/entities.json'
BATCHES=ROOT/'docs/CONTENT-BATCHES.json'
SOURCE_IDS=['src-detective-conan-world-manga','src-detective-conan-world-anime']
BATCH='p3-case-relations-01'

def expand(ref):
    if not ref.startswith('episode-'): return []
    tail=ref.removeprefix('episode-')
    if '-' not in tail:return [int(tail)]
    a,b=tail.split('-',1);return list(range(int(a),int(b)+1))

cases=json.loads(CASES.read_text())
rows=[]
for case in cases:
    for ref in case.get('animeRefs',[]):
        for n in expand(ref):
            rows.append({'candidateId':f'{BATCH}-{case["id"]}-{n:04d}','targetId':case['id'],'field':'relatedEpisodes','value':[f'episode-{n:04d}'],'sourceRefs':SOURCE_IDS,'confidence':'high' if case.get('status')=='reviewed' else 'medium','reviewStatus':'pending','reviewNote':'由案件 animeRefs 展开为集级候选，用于案件反向关系审计；不新增剧情字段。'})
CANDIDATES.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
bs=json.loads(BATCHES.read_text())
if not any(x.get('batchId')==BATCH for x in bs['batches']): bs['batches'].append({'batchId':BATCH,'scope':'现有案件 animeRefs 的集级候选关系','targetLayer':'structure','episodeNumbers':[],'entityIds':[c['id'] for c in cases],'sourceIds':SOURCE_IDS,'status':'candidate','recordCount':len(rows),'effectiveChanges':0,'validationResult':None,'createdAt':'2026-10-27','appliedAt':None,'notes':'只把已有案件声明展开为候选关系，不推断新的案件或剧情。'})
bs['batches']=[x for x in bs['batches'] if x.get('batchId')!=BATCH or True]
BATCHES.write_text(json.dumps(bs,ensure_ascii=False,indent=2)+'\n')
print('case_relation_candidates',len(rows))
