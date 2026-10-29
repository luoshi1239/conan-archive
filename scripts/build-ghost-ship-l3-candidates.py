#!/usr/bin/env python3
"""Build sourced L3 candidates for A Ghost Ship Murder Case."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; PATH=ROOT/'data/candidates/entities.json'; BATCH='p4-deep-case-ghost-ship-01'; TARGET='case-ghost-ship-murder'; SOURCE='src-detective-conan-world-ghost-ship-case'
VALUES={
 'culprit':'木下五郎（Goro Kinoshita）。',
 'motive':'木下为寻找志木岛幽灵船失踪的黄金而追杀掌握线索的人，目标是独占被埋藏的巨额黄金。',
 'method':'木下为逼问滨田浩二而绑架并折磨他，随后杀害知情者；他伪造上原的枪击自杀，并试图把杀人罪嫁祸给毛利小五郎；之后又杀死上原并袭击柯南和三上铃。',
 'evidence':'上原的枪伤位于错误的一侧，枪被放在错误的手中；伤口附近有火药灼痕，说明枪击距离和方向与自杀不符；黄金砖块被苔藓覆盖，揭示其长期藏在洞穴废墟中。',
 'resolution':'柯南揭露伪造枪击、黄金藏匿和嫁祸计划，木下被制服；黄金原本埋在废墟中，岛民因此一直以为诅咒和债务已经结束。',
}
rows=json.loads(PATH.read_text(encoding='utf-8')); existing={r.get('candidateId') for r in rows}; added=0
for field,value in VALUES.items():
 cid=f'{BATCH}-{field}'
 if cid in existing: continue
 rows.append({'candidateId':cid,'targetId':TARGET,'field':field,'value':value,'sourceRefs':[SOURCE],'confidence':'medium','reviewStatus':'pending','reviewNote':'已读取首个两集TV Original案件页面正文；L3全剧透字段。'}); added+=1
PATH.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'added={added}')
