#!/usr/bin/env python3
"""Build sourced L3 candidates for episodes 67 and 68-70 cases."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; PATH=ROOT/'data/candidates/entities.json'
BATCHES={
 'p4-deep-case-stage-actress-01':('case-stage-actress-murder','src-detective-conan-world-stage-actress-case',{
  'culprit':'佐々木瞳（Hitomi Sasaki），大出祥子的经纪人。',
  'motive':'宇田雄一原本是佐々木的恋人，后来为大出祥子与她分手；佐々木已经接受了这个结果。但祥子随即又甩掉宇田，说他无趣又迟钝，扬言要把他还给佐々木，还傲慢地笑着。佐々木无法原谅祥子根本没有认真对待这段感情、只是存心把宇田从她身边夺走。',
  'method':'佐々木利用舞台布景上方悬挂的星星道具作为定位点，用钓鱼线把毒液滴入祥子的杯子；杯子按剧本规定的位置预先摆好，滴毒因此能精准命中。',
  'evidence':'佐々木手上留有强行把钓鱼线从星星道具上扯下时的划痕，说明她当时慌了神；案发后毛利小五郎让所有人留在原地，那根用于作案的钓鱼线应该还在她的口袋里。',
  'resolution':'柯南揭穿钓鱼线滴毒手法，佐々木承认杀人；案件结束后盐田平八郎打算接手侦探事务所，却被妻子接回家。',
 }),
 'p4-deep-case-night-baron-01':('case-night-baron-murder','src-detective-conan-world-night-baron-case',{
  'culprit':'狭山明子（Akiko Sayama），软件公司职员、前田聪的未婚妻。',
  'motive':'三年前她敬爱的兄长因江原时男入侵其公司系统、盗走他投入全部资金的程序而跳楼自杀；狭山为复仇策划了这场暗夜男爵谜题活动，并假称掌握传说中的暗夜男爵病毒，引江原参赛。',
  'method':'晚餐后狭山以交付病毒为由把江原叫到自己的1901室，将他迷昏，再潜入江原房间放置手套、制造从内部反锁的密室；她给昏迷的江原换上男爵装束（省去假发），把尸体从背风的窗户抛下，让尸体恰好落在江原房间阳台正下方，看起来像是江原反锁房间、扮成男爵试图翻进下层房间时失足坠楼。',
  'evidence':'当时唯一能使尸体落在江原阳台下方的方法，是从背风区域抛下，而该区域只有20层以下的房间能够进入，最终只能指向1901室；柯南让警方从各嫌疑人房间抛下绑有配重、系着被单冒充披风的卷起被褥，结果全部被“公主风”吹离各自阳台下方，反证江原不可能从自己阳台坠落；狭山从房间打到前台的电话记录也证明抛尸时她在案发现场。',
  'resolution':'柯南借沉睡的小五郎揭穿密室与风向诡计，狭山被认定为凶手；未婚夫前田聪为替她制造不在场证明，偷走男爵装束假扮男爵，最终因妨碍调查被起诉，兰查证其不在场证明为他洗脱杀人嫌疑；狭山被带走时哭着让前田忘了她，前田承诺等她出狱。',
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
