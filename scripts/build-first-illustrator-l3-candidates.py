#!/usr/bin/env python3
"""Build sourced L3 candidates for episodes 59 and 60 cases."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; PATH=ROOT/'data/candidates/entities.json'
BATCHES={
 'p4-deep-case-first-errand-01':('case-first-errand-murder','src-detective-conan-world-first-errand-case',{
  'culprit':'村濑（Murase）。',
  'motive':'村濑经营的商店即将被拆除，负责拆除的掮客要把店址推平；村濑因不愿失去商店而杀死了对方。',
  'method':'村濑在废弃商店处杀害负责拆迁的掮客，并在孩子经过时误以为孩子看见了自己，从而试图灭口。',
  'evidence':'村濑对孩子在废弃商店出现表现出异常恐惧；孩子只是去旧商店购买物品，并未真正看见杀人过程，村濑的反应反而暴露了其心理。',
  'resolution':'柯南和少年侦探团救下孩子并揭示商店拆迁背景，村濑因意识到自己误判孩子目击情况而崩溃认罪。',
 }),
 'p4-deep-case-illustrator-01':('case-illustrator-murder','src-detective-conan-world-illustrator-case',{
  'culprit':'花冈健仁（Kenjin Hanaoka）。',
  'motive':'长野泉是花冈的幽灵画师和秘密情人，花冈的大部分作品实际由她创作；泉要求他离婚并以揭露关系和代笔事实施压，花冈因此失控杀人。',
  'method':'花冈用水晶烟灰缸击打泉致死，把尸体倚在阳台并用鱼线、花盆和门上的钉子组成机关；开门后花盆脱落，鱼线和尸体被拉向排水口，制造自杀假象。',
  'evidence':'泉作品中的蝴蝶标记、花冈脚趾甲上被指甲油留下的蝴蝶标记，以及阳台鱼线机关共同指向花冈；花冈声称从未到过现场也与机关矛盾。',
  'resolution':'柯南通过蝴蝶标记和阳台机关揭穿花冈伪造自杀的计划，花冈最终承认因泉要求他面对婚姻和代笔事实而杀人。',
 }),
}
rows=json.loads(PATH.read_text(encoding='utf-8')); existing={r.get('candidateId') for r in rows}; added=0
for batch,(target,source,values) in BATCHES.items():
 for field,value in values.items():
  cid=f'{batch}-{field}'
  if cid in existing: continue
  rows.append({'candidateId':cid,'targetId':target,'field':field,'value':value,'sourceRefs':[source],'confidence':'medium','reviewStatus':'pending','reviewNote':'已读取案件页面正文；L3全剧透字段。'}); added+=1
PATH.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'added={added}')
