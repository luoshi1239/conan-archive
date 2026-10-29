#!/usr/bin/env python3
"""Build sourced L3 candidates for the Train Trick Murder Case."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'data/candidates/entities.json'; BATCH='p4-deep-case-train-01'; TARGET='case-train-trick'; SOURCE='src-detective-conan-world-train-trick-case'
VALUES={
 'culprit':'伊达隆（Takashi Date）。',
 'motive':'受害者内海掌握伊达收受药企回扣的证据并以此勒索；伊达不想继续被勒索，因此决定杀死内海。',
 'method':'伊达在水之川站下车后戴上假胡子和帽子、翻转外套伪装，再换乘受害者所在的列车；通过电话谎称遗失物品拖延列车，接近内海后用注射器注入诱发心脏病的药物，并抢走硬币伪装成随机抢劫。',
 'evidence':'硬币原本由列车女服务员找零给内海，若硬币上出现女服务员指纹，就能证明硬币曾随内海转移到另一列车并证明伊达在案发列车上；假装借款和抢劫动机也无法解释这一指纹证据。',
 'resolution':'柯南揭示跨线换车、伪装、拖延列车和硬币指纹证据，伊达在证据链面前崩溃并认罪。',
}
rows=json.loads(PATH.read_text(encoding='utf-8')); existing={r.get('candidateId') for r in rows}; added=0
for field,value in VALUES.items():
 cid=f'{BATCH}-{field}'
 if cid in existing: continue
 rows.append({'candidateId':cid,'targetId':TARGET,'field':field,'value':value,'sourceRefs':[SOURCE],'confidence':'medium','reviewStatus':'pending','reviewNote':'已读取TV Original案件页面正文；L3全剧透字段。'}); added+=1
PATH.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'added={added}')
