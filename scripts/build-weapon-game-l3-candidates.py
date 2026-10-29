#!/usr/bin/env python3
"""Build sourced L3 candidates for episodes 53 and 54 cases."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'data/candidates/entities.json'
SOURCE_WEAPON='src-detective-conan-world-weapon-case'
SOURCE_GAME='src-detective-conan-world-game-company-case'
BATCHES={
 'p4-deep-case-weapon-01': ('case-mystery-weapon', SOURCE_WEAPON, {
  'culprit':'寺泽典夫（Norio Terasawa）。',
  'motive':'被害人井本龙介关闭了寺泽经营的钓具店，并准备将店址改作公司财产；在拒绝寺泽请求、又折断其珍贵鱼竿后，寺泽决定杀人。',
  'method':'寺泽用钓鱼竿发射铅坠击中井本头部，并利用破碎的向日葵花盆制造被钝器直接击打的假象。',
  'evidence':'邻室废弃公寓留下的深刻印记符合甩竿姿势；阳台栏杆有铅坠撞击痕迹，飞鸟也曾被误击；现场找到带有寺泽指纹的鱼竿握柄。',
  'resolution':'柯南通过甩竿痕迹、栏杆撞击痕迹和带指纹的鱼竿握柄揭露寺泽为犯人。',
 }),
 'p4-deep-case-game-01': ('case-game-company-murder', SOURCE_GAME, {
  'culprit':'竹下宏信（Hironobu Takeshita）。',
  'motive':'竹下认为中岛秀明抛弃曾与两人交往的大学拳击部经理吉美，导致吉美自杀，因此杀害中岛并试图嫁祸。',
  'method':'竹下事先调换手提箱编号，使装有炸弹的箱子在中岛与 Tequila 交换时误交给 Tequila，利用爆炸杀死目标但实际造成 Tequila 误中。',
  'evidence':'中岛手提箱的钥匙能打开竹下手中的箱子；竹下在得知中岛箱内只有 Tequila 给的钱时表现出异常；酒店号码、调换编号和爆炸箱形成完整证据链。',
  'resolution':'柯南揭示手提箱调换和炸弹机关，竹下认罪；随后柯南前往 Tequila 的联络地点，发现琴酒和伏特加为灭口而引发爆炸。',
 }),
}
rows=json.loads(PATH.read_text(encoding='utf-8')); existing={r.get('candidateId') for r in rows}; added=0
for batch,(target,source,values) in BATCHES.items():
 for field,value in values.items():
  cid=f'{batch}-{field}'
  if cid in existing: continue
  rows.append({'candidateId':cid,'targetId':target,'field':field,'value':value,'sourceRefs':[source],'confidence':'medium','reviewStatus':'pending','reviewNote':'已读取案件页面正文；L3全剧透字段。EP.54的黑衣组织爆炸作为结局上下文，不与案件犯人混同。'}); added+=1
PATH.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'added={added}')
