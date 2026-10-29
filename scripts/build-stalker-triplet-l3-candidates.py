#!/usr/bin/env python3
"""Build sourced L3 candidates for episodes 71 and 72 cases."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; PATH=ROOT/'data/candidates/entities.json'
BATCHES={
 'p4-deep-case-stalker-01':('case-stalker-murder','src-detective-conan-world-stalker-case',{
  'culprit':'西谷美穂（Miho Nishitani），家庭餐厅店员、永井达也的跟踪受害对象。',
  'motive':'永井长期跟踪西谷，在她报警后当众把她推下车站楼梯；西谷判断警察保护不了自己，认为永井迟早会杀了她，于是决定先下手。',
  'method':'西谷事先买好一瓶“Guts-man”运动饮料，投入磷酸毒物，再从自动贩卖机另买一瓶做样子，假装取出机器多给的那一瓶喝下，实际取出的是毒瓶；她把毒瓶留在栏杆上等永井喝，永井误以为是机器多送的而喝下毒发。',
  'evidence':'毒瓶上的贴纸宣传的是早已结束的抽奖活动，而且贩卖机里不太可能还留着旧货；毛利小五郎又在机器里发现了她真正付钱买的那一瓶，证明她事先准备了毒瓶。更关键的是，永井把隐藏摄像机装在自己的打火机里，拍下了西谷按柯南所述方式投毒的全过程。',
  'resolution':'柯南揭穿毒瓶与贴纸破绽，西谷承认杀人。由于是预谋投毒，正当防卫不成立；但柯南在她家门外灌木丛中发现装有多种危险工具的袋子，上面有永井的指纹，证明永井原本打算折磨她，西谷因此很可能获得从轻判决。事后毛利感叹，如果她没有杀人，本可以有别的路。',
 }),
 'p4-deep-case-triplet-01':('case-triplet-country-home-murder','src-detective-conan-world-triplet-case',{
  'culprit':'富泽太一（Taichi Tomizawa），富泽家长子、小说家。',
  'motive':'太一靠写作维生，但工作量减少、收入下滑，向父亲要钱时才发现父亲一直在向编辑施压，让对方拒绝给他约稿；他误以为父亲要逼自己放弃写作、回公司接班。听说父亲这天要去看三子佑造未婚妻，他认为这是行凶的好机会。',
  'method':'太一提前把父亲答录机上的时钟调早，跟踪父亲回家后行凶，用石头砸死父亲，随后播放事先录好的留言，再把时钟调回；他还打坏了卫星天线，逼迫父亲到屋外，制造电话留言与作案时间吻合的假象。作案时他戴着假发伪装，并把窃听麦克风藏进父亲的手表，用来掌握比赛结束、父亲回家等一切动向，行凶后取走手表销毁证据。',
  'evidence':'案发时11:30有长达十分钟的停电，停电时答录机无法录音，只靠电池维持时钟与通话；太一那条“11:30打来”的留言与作案时刻恰好吻合，这需要不可能的运气，反证只有能改动答录机时钟的人才能做到。他自称11:30在弹珠店，但法律要求弹珠店11点前必须关门，不在场证明不成立。',
  'resolution':'柯南借铃木园子之口揭穿答录机时钟与停电诡计，指认太一为凶手。园子姐姐绫子的婚事因此告吹，但案件结束后康纳与兰仍为园子假装推理的表现感到好笑。',
 }),
}
rows=json.loads(PATH.read_text(encoding='utf-8')); existing={r.get('candidateId') for r in rows}; added=0
for batch,(target,source,values) in BATCHES.items():
    for field,value in values.items():
        cid=f'{batch}-{field}'
        if cid in existing: continue
        rows.append({'candidateId':cid,'targetId':target,'field':field,'value':value,'sourceRefs':[source],'confidence':'medium','reviewStatus':'pending','reviewNote':'已读取案件页面 Case Situation / Resolution 正文；L3全剧透字段。'})
        added+=1
PATH.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'added={added}')
