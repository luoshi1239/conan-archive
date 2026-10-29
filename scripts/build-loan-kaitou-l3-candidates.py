#!/usr/bin/env python3
"""Build sourced L3 candidates for episodes 75 and 76 cases."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; PATH=ROOT/'data/candidates/entities.json'
BATCHES={
 'p4-deep-case-loan-company-01':('case-loan-company-president-murder','src-detective-conan-world-loan-company-case',{
  'culprit':'藤井贵子（Takako Fujii），Hida金融职员。',
  'motive':'贵子从大学毕业后三年一直因心脏病住院，父母已故、脾气不好又没朋友，只有男友来探望她。男友为她借了日田的钱，无力偿还后上吊自杀；贵子事后才知道男友是为她借钱，而合约就压在男友脚下。她进入公司从底层做起，只为等复仇的时机。',
  'method':'贵子事先在厨房煤气灶旋钮的左侧涂上氰化钾，然后在离开办公室前把鸣笛水壶坐上火。水壶鸣笛时，多疑的日田慌着去关火，绝大多数灶具按右手习惯设计，他很自然会用右手拇指去拧旋钮左侧，毒物就这样沾在拇指上；他回办公室舔手指，随即中毒身亡。她原本打算第二天早上再擦掉毒物，尸体却被提前发现。',
  'evidence':'毒物只出现在办公室门的内侧把手上，外侧没有，符合日田匆忙开门、沾毒、返回锁门的过程，也解释了房间反锁。案发后只有藤井贵子靠近过灶台，她借“泡茶”之机用手帕擦掉毒物；手帕是湿的但不是水，目暮在上面滴碘液后颜色消失，说明上面是漂白剂。漂白剂能中和氰化物，也能漂白痕迹，且不常在药店出售，却出现在女厕的柜子里。此外她惯用右手，取烟、点烟、拿东西都用右手，唯独那天用左手去拧旋钮，因为她抽烟时手指会碰嘴唇，怕残留毒物。',
  'resolution':'柯南借沉睡的小五郎揭穿旋钮涂毒与漂白剂灭证，藤井贵子承认杀人。她把毒涂在左侧、用左手拧旋钮这两个细节，连同漂白剂手帕，一起构成了无法辩驳的证据链。',
 }),
 'p4-deep-case-conan-vs-kaitou-kid-01':('case-conan-vs-kaitou-kid','src-detective-conan-world-conan-vs-kaitou-kid',{
  'culprit':'怪盗基德（黑羽快斗）；本集没有杀人凶手，作案目标为黑珍珠“漆黑之星”。',
  'motive':'基德盯上铃木财团收藏的世界最大黑珍珠“漆黑之星”，按预告函在愚人节动手；这一次既是为盗宝，也是他与柯南的第一次正式交锋。',
  'method':'基德先用暗号预告函“四月一日，当月亮分成两半时，我将前来拜访漆黑之星之名起源之地，随海浪的呼唤”给出线索，在酒店天台与柯南初次见面时冒充中森警部的声音把警员都调上天台，再用闪光弹脱身；博物馆那次只是预演，他在船上伪装成铃木史郎混入，把真正的黑珍珠留在铃木朋子身上，让全员戴的复制品接连爆炸制造混乱，趁乱得手。',
  'evidence':'柯南识破船上“铃木史郎”是基德假扮，因为园子打电话发现真正的父亲与姐姐还在家里；他又从朋子对珍珠“孔雀色”的描述、握持方式与因年代而黯淡的光泽，判断博物馆那颗太亮是赝品，从而锁定基德真正偷走的是朋子身上那颗。',
  'resolution':'柯南在船上揭穿基德假扮成小兰，基德认输交还黑珍珠；柯南踩碎他的手机，防止他再用同样手法。基德临走谎称已剥走小兰的衣服，把柯南支开，实际只是在交给小兰前把礼服复制了一份，还留卡片向小兰道歉、夸她可爱。次日柯南被媒体捧为“守护黑珍珠的英雄”，他本人并不高兴；基德则因跳进冷海逃走而感冒，被青子笑骂。',
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
