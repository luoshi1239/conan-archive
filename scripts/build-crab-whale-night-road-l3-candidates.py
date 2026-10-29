#!/usr/bin/env python3
"""Build sourced L3 candidates for episodes 65 and 66 cases."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; PATH=ROOT/'data/candidates/entities.json'
BATCHES={
 'p4-deep-case-crab-whale-01':('case-crab-whale-kidnapping','src-detective-conan-world-crab-whale-case',{
  'culprit':'两名绑架者：一名男子与一名女子（页面人物表列为 Keita 的绑架者，未给出正式姓名）。',
  'motive':'两名绑架者以远藤圭太为人质向远藤圭吾勒索大笔日元，准备得手后携款潜逃。',
  'method':'二人从远藤家前院绑走5岁的圭太，留下“孩子在我们手上，报警就杀了他，等我们联系”的字条，随后用电话遥控赎金交付流程，并在酒店准备逃跑。',
  'evidence':'字条内容与赎金指示、绑匪对交付地点的选择，以及南水族馆相关线索帮助柯南锁定赎金交接与藏匿位置；两名绑架者在酒店准备出逃时被柯南当场击中制服。',
  'resolution':'柯南在酒店制服两名绑架者，圭太被安全送回父亲身边，二人被逮捕。',
 }),
 'p4-deep-case-night-road-01':('case-night-road-murder','src-detective-conan-world-night-road-case',{
  'culprit':'竹野浩二（Kouji Takeno），米花大学二年级学生，常盘圭子的男友。',
  'motive':'竹野与池田都爱慕常盘圭子；圭子在雪山事故中因脚伤被留在山上冻死。竹野后来得知池田是故意扰乱队伍、让圭子得不到及时救援，还曾在酒桌上向同样醉酒的日下炫耀此事，于是决定复仇。',
  'method':'竹野把水族馆的小溪石装进自己登山用的耐磨运动袜，装满石头后做成沉重钝器，用钓鱼绳绑好后从远处向站在街上抽烟的池田投掷，将其一击打死。',
  'evidence':'血液之所以溅到废弃大楼墙面、屋顶栏杆和上层公寓玻璃上，是因为装满石头的袜子在高强度撞击后反弹所致；水族馆石堆中残留的羊毛纤维，以及竹野没有换下的、沾有池田血迹的袜子成为决定性证据。',
  'resolution':'柯南揭穿“袜装溪石”的投掷手法和羊毛纤维来源，竹野承认是为圭子复仇而杀人；池田当年故意拖延救援的事实也随之曝光。',
 }),
}
rows=json.loads(PATH.read_text(encoding='utf-8')); existing={r.get('candidateId') for r in rows}; added=0
for batch,(target,source,values) in BATCHES.items():
    for field,value in values.items():
        cid=f'{batch}-{field}'
        if cid in existing: continue
        rows.append({'candidateId':cid,'targetId':target,'field':field,'value':value,'sourceRefs':[source],'confidence':'medium','reviewStatus':'pending','reviewNote':'已读取案件页面 Case Situation/Resolution 正文；L3全剧透字段。'})
        added+=1
PATH.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'added={added}')
