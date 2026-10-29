#!/usr/bin/env python3
"""Build sourced L3 candidates for episodes 63 and 64 cases."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; PATH=ROOT/'data/candidates/entities.json'
BATCHES={
 'p4-deep-case-gomera-01':('case-gomera-murder','src-detective-conan-world-gomera-case',{
  'culprit':'松井秀豪（Shugo Matsui），即哥美拉皮套演员。',
  'motive':'龟井散布“松井厌倦演哥美拉、想转向其他角色”的流言，松井得知后不愿最后一部哥美拉电影完成，于是杀害龟井。',
  'method':'松井事先用哥美拉皮套脚部印出脚印并涂上颜料，让人以为足立留下痕迹；行凶后在楼梯处脱下皮套，跑进楼下储物间把皮套从窗户丢出并点火，制造怪兽行凶的假象；他先用影视道具血伪装腿伤，事后又用另一把刀刺伤自己的腿并把刀藏进道具箱，还换掉衬衫以掩盖出汗痕迹。',
  'evidence':'地面只有哥美拉的脚印而没有尾痕；松井换过衬衫，而早前步美把果汁洒在他衣服上；腿伤前后矛盾、道具箱里的另一把刀，以及他与足立、智美的串供一起指向他。',
  'resolution':'柯南借助阿笠博士揭穿脚印与皮套调包手法，松井承认因流言而杀人；足立和智美此前是在替他隐瞒。',
 }),
 'p4-deep-case-third-fingerprint-01':('case-third-fingerprint-murder','src-detective-conan-world-third-fingerprint-case',{
  'culprit':'寺冈警部（Inspector Teraoka），警视厅搜查四课管理官，毛利小五郎的前上司。',
  'motive':'松山以揭发寺冈收受贿赂、泄露警方行动情报为把柄勒索他，并索要资金以便从自己犯下的另一起杀人案中脱身、逃往国外，寺冈因此杀死松山。',
  'method':'寺冈在码头枪杀松山，试图把案件引向抢劫或意外方向；他随身携带的配枪藏在裤下枪套里，因此进入车内时发出金属碰撞声。',
  'evidence':'枪上出现的第三枚指纹属于寺冈的妻子美沙子，她无意中碰到寺冈藏起来的枪；柯南从寺冈上车时听到的异常金属声判断他使用的是自己的枪。',
  'resolution':'柯南查明第三枚指纹来自误触配枪的美沙子，也确认寺冈为灭口而杀人；寺冈在毛利面前承认受贿被勒索的事实。',
 }),
}
rows=json.loads(PATH.read_text(encoding='utf-8')); existing={r.get('candidateId') for r in rows}; added=0
for batch,(target,source,values) in BATCHES.items():
    for field,value in values.items():
        cid=f'{batch}-{field}'
        if cid in existing: continue
        rows.append({'candidateId':cid,'targetId':target,'field':field,'value':value,'sourceRefs':[source],'confidence':'medium','reviewStatus':'pending','reviewNote':'已读取案件页面 Situation/Resolution 正文；L3全剧透字段。'})
        added+=1
PATH.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(f'added={added}')
