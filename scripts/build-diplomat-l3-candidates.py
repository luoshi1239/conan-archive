#!/usr/bin/env python3
"""Append sourced L3 candidates for the Diplomat Murder Case."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'data/candidates/entities.json'
BATCH='p4-deep-case-diplomat-01'; TARGET='case-diplomat-murder'; SOURCE='src-detective-conan-world-diplomat-case'
VALUES={
 'culprit':'津村公江（Kimie Tsujimura）。',
 'motive':'为女儿雪子及山城家遭受的旧案复仇；她认为丈夫津村功曾参与毁掉山城家的人生。',
 'method':'先用安眠药使丈夫昏睡，再用藏在钥匙扣吊坠中的毒针刺杀；随后利用钥匙扣和鱼线布置假密室，制造受害者死于封闭房间的假象。',
 'evidence':'毒针与钥匙扣、安眠药、鱼线布置、假密室机关以及案件现场的时间和物证相互印证。',
 'resolution':'公江在推理揭示后认罪并向警方投案；她请求高志照顾雪子，高志答应，案件结束。',
}
rows=json.loads(PATH.read_text(encoding='utf-8')); existing={r.get('candidateId') for r in rows}; added=0
for field,value in VALUES.items():
 cid=f'{BATCH}-{field}'
 if cid in existing: continue
 rows.append({'candidateId':cid,'targetId':TARGET,'field':field,'value':value,'sourceRefs':[SOURCE],'confidence':'medium','reviewStatus':'pending','reviewNote':'基于外交官案件原页面正文；L3全剧透字段，应用后前端必须默认隐藏。'}); added+=1
PATH.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
print(f'added={added}')
