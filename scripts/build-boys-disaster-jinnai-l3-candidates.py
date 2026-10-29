#!/usr/bin/env python3
"""Build sourced L3 candidates for episodes 73 and 74 cases."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; PATH=ROOT/'data/candidates/entities.json'
BATCHES={
 'p4-deep-case-boys-disaster-01':('case-detective-boys-disaster','src-detective-conan-world-boys-disaster-case',{
  'culprit':'春日辉彦（Teruhiko Kasuga），春日集团继承人。',
  'motive':'春日完全是奉父亲之命才与富家女忍订婚的，父亲要求他要娶富家女，否则就断绝经济援助。他想回到从前那种花心的日子，于是决定杀掉未婚妻，并伪装成意外事故。',
  'method':'春日把忍带到海边一处可以望见海的洞穴，让她喝下掺有安眠药的果汁，趁她昏睡时把她丢在洞里，打算让上涨的潮水把她淹死；随后他谎称洞中留下的SOS只是玩笑，试图拖住救援。',
  'evidence':'洞中留下的求救信号与忍的失踪直接矛盾，春日“只是玩笑”的说法站不住脚；柯南与少年侦探团在洞中找到了昏迷的忍。',
  'resolution':'柯南一行带着昏睡的忍往洞穴深处走，被潮水从另一处洞口冲到潮池，正好撞上在那里偷偷钓鱼的小五郎与春日。春日狗急跳墙，把步美当人质，威胁要杀掉在场所有人，被一位老人扔罐头打中，随后兰与管理员赶到将其制服逮捕。小五郎则因为在禁钓潮池钓鱼，被管理员训了整整一小时。',
 }),
 'p4-deep-case-jinnai-01':('case-death-god-jinnai-murder','src-detective-conan-world-jinnai-case',{
  'culprit':'吉野里美（Satomi Yoshino），南条隼人的经纪人、前演员。',
  'motive':'三年前北野弘之拿到了《死神阵内》的主演位置，嫉妒的南条诱骗他不带替身完成特技，并拆掉他车上的螺栓，导致车辆失控爆炸，北野身亡。某个夜晚吉野开车送醉酒的南条回家，他把这件事全部说了出来，吉野由此决定复仇。',
  'method':'吉野用乙烯胶带和钓鱼线在窗户上做出人体剪影，把线连到电灯开关与电梯上；电梯下行时先点亮房间的灯，再把胶带从窗户上扯掉，从楼下与外面看去就像房里有人走过。她以此制造“死神阵内现身”的假象，同时在七楼射杀南条。',
  'evidence':'柯南在电梯处被胶带绊倒，发现胶带与钓鱼线连动机关的痕迹；现场所谓“走动的人影”随电梯运行才出现，与真人行动不符。',
  'resolution':'柯南揭穿电梯联动的人体剪影诡计，指认吉野为凶手；吉野承认是为北野复仇，并说出南条醉酒后亲口承认三年前动手的经过。这话也说明三年前北野之死是南条所为，北野的旧案随之真相大白。',
 }),
}
rows=json.loads(PATH.read_text(encoding='utf-8')); existing={r.get('candidateId') for r in rows}; added=0
for batch,(target,source,values) in BATCHES.items():
    for field,value in values.items():
        cid=f'{batch}-{field}'
        if cid in existing: continue
        rows.append({'candidateId':cid,'targetId':target,'field':field,'value':value,'sourceRefs':[source],'confidence':'medium','reviewStatus':'pending','reviewNote':'已读取案件页面 Case Situation / Resolution / Motive 正文；L3全剧透字段。'})
        added+=1
PATH.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'added={added}')
