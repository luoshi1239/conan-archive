#!/usr/bin/env python3
"""Build sourced L3 candidates for the Holmes Freak Murder Case."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'data/candidates/entities.json'; BATCH='p4-deep-case-holmes-freak-01'; TARGET='case-holmes-freak-murder'; SOURCE='src-detective-conan-world-holmes-freak-case'
VALUES={
 'culprit':'户野健人（Kento Togano）。',
 'motive':'户野健人憎恨小说《Irene Adler Sneer》对艾琳·艾德勒的侮辱；该作品由广之和俊明创作，书中让福尔摩斯遭到艾琳嘲笑。',
 'method':'户野先杀害广之，将尸体放入汽车并踩住刹车，开暖气、挂挡后打开车库使汽车驶入海中；将尸体抛下悬崖掩盖死亡时间。随后以漏油、断电和打火机制造车库火灾，并利用断电机会刺杀俊明。',
 'evidence':'绫子试图抄写众人填写的问卷，却发现户野的问卷一题未答，说明他预先知道主人会死亡；汽车机关、车库火灾和断电时机共同指向户野。',
 'resolution':'柯南揭示户野的多段伪装事故和问卷证据，户野在证据面前承认犯案；案件后柯南向服部平次说明自己缩小前后的真实身份。',
}
rows=json.loads(PATH.read_text(encoding='utf-8')); existing={r.get('candidateId') for r in rows}; added=0
for field,value in VALUES.items():
 cid=f'{BATCH}-{field}'
 if cid in existing: continue
 rows.append({'candidateId':cid,'targetId':TARGET,'field':field,'value':value,'sourceRefs':[SOURCE],'confidence':'medium','reviewStatus':'pending','reviewNote':'已读取漫画改编案件页面正文；L3全剧透字段。'}) ; added+=1
PATH.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'added={added}')
