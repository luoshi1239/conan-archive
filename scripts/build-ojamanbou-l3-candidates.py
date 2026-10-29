#!/usr/bin/env python3
"""Build sourced L3 candidates for the Ojamanbou Murder Case."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'data/candidates/entities.json'; BATCH='p4-deep-case-ojamanbou-01'; TARGET='case-ojamanbou-murder'; SOURCE='src-detective-conan-world-ojamanbou-case'
VALUES={
 'culprit':'中山英之（Hideyuki Nakayama）。',
 'motive':'被害人藤井常久与中山的妹妹分手，导致妹妹退出小じゃマンボウ清洁公司，并在横滨工地工作时遭遇致命事故；中山从妹妹日记得知此事后决定复仇。',
 'method':'中山把口琴放在地面诱使藤井弯腰，再把清洁公司卡车停在对面利用反光观察藤井的位置；他将屋顶钢梁与监控摄像机用钢丝连接，通过监控画面掌握时机远程放下钢梁。',
 'evidence':'屋顶由中山公司安装的监控摄像机拍到了中山自己的倒影；口琴上没有藤井或犯人的指纹；摄像机与钢梁之间的钢丝机关说明中山具备并利用了作案条件。',
 'resolution':'柯南根据监控画面中的倒影、口琴指纹缺失和钢梁远程机关揭露中山为犯人。',
}
rows=json.loads(PATH.read_text(encoding='utf-8')); existing={r.get('candidateId') for r in rows}; added=0
for field,value in VALUES.items():
 cid=f'{BATCH}-{field}'
 if cid in existing: continue
 rows.append({'candidateId':cid,'targetId':TARGET,'field':field,'value':value,'sourceRefs':[SOURCE],'confidence':'medium','reviewStatus':'pending','reviewNote':'已读取TV Original案件页面正文；L3全剧透字段。'}); added+=1
PATH.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'added={added}')
