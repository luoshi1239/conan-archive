#!/usr/bin/env python3
"""登记 EP.102-106 的案件实体与来源。

覆盖：
  EP.102-103  The Historical Actor Murder Case        File.170-172  Volume 18  漫画改编
  EP.104-105  The Mysterious Mansion of a Band of Thieves Case
                                                      File.167-169  Volume 17  漫画改编（绑架+寻宝，非命案）
  EP.106      Scoop Picture Murder Case               动画原创（DCW Category:Anime_Exclusive）

事实全部来自 detectiveconanworld.com 对应页面正文；EP.106 的动画原创属性由页面
Category:Anime_Exclusive 判定，而非「files.json 查不到映射」这种反向推断。

幂等：重复执行只补缺失项，不覆盖已有内容。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "sources.json"
CASES = ROOT / "data" / "entities" / "cases.json"
TODAY = "2026-10-27"

NEW_SOURCES = [
    {
        "id": "src-detective-conan-world-historical-actor",
        "type": "wiki",
        "title": "The Historical Actor Murder Case — Detective Conan Wiki",
        "url": "https://www.detectiveconanworld.com/wiki/The_Historical_Actor_Murder_Case",
        "language": "en",
        "publisher": "detectiveconanworld.com",
        "accessedAt": TODAY,
        "notes": "EP.102-103（File.170-172，Volume 18）。Case/People/Resolution 段为事实来源。",
    },
    {
        "id": "src-detective-conan-world-thieves-mansion",
        "type": "wiki",
        "title": "The Mysterious Mansion of a Band of Thieves Case — Detective Conan Wiki",
        "url": "https://www.detectiveconanworld.com/wiki/The_Mysterious_Mansion_of_a_Band_of_Thieves_Case",
        "language": "en",
        "publisher": "detectiveconanworld.com",
        "accessedAt": TODAY,
        "notes": "EP.104-105（File.167-169，Volume 17）。案件性质为绑架+寻宝，无命案既遂。",
    },
    {
        "id": "src-detective-conan-world-scoop-picture",
        "type": "wiki",
        "title": "Scoop Picture Murder Case — Detective Conan Wiki",
        "url": "https://www.detectiveconanworld.com/wiki/Scoop_Picture_Murder_Case",
        "language": "en",
        "publisher": "detectiveconanworld.com",
        "accessedAt": TODAY,
        "notes": "EP.106，动画原创（页面 Category:Anime_Exclusive）。Case/Resolution 段为事实来源。",
    },
]


NEW_CASES = [
    {
        "id": "case-historical-actor-murder",
        "type": "case",
        "titles": {
            "zhHans": "时代剧演员杀人事件",
            "zhHant": "時代劇演員殺人事件",
            "ja": "時代劇俳優殺人事件",
            "en": "The Historical Actor Murder Case",
        },
        "aliases": ["历史剧演员杀人事件"],
        "summary": (
            "小五郎带柯南、小兰去探班时代剧演员土方幸三郎，同栋公寓另一层住着"
            "特技演员冲田一。土方之妻、女演员永仓严在冲田房间隔壁的阳台上被发现"
            "吊死，尸体随后坠落。冲田有充分动机——永仓曾当面羞辱他，且他当晚的行踪"
            "说不清楚，警方几乎要定他的罪。"
        ),
        "caseType": ["murder", "locked-room", "trick-floor"],
        "mangaRefs": ["file-170-172"],
        "animeRefs": ["episode-0102-0103"],
        "sourceRefs": ["src-detective-conan-world-historical-actor"],
        "detailStatus": "deepSpoilers",
        "confidence": "high",
        "reviewStatus": "reviewed",
        "victimDescription": "永仓严（38 岁），女演员，土方幸三郎之妻。被钢丝勒死，尸体先被吊起，后坠落到楼下阳台。",
        "culprit": "土方幸三郎（51 岁），时代剧演员，被害人丈夫。",
        "motive": (
            "两个动机叠加：妻子永仓严有外遇，同时他即将破产，需要她的保险金。"
            "他由此起了杀意。"
        ),
        "method": (
            "他事先租下同栋楼里三间格局完全相同的公寓，在其中一间杀人后把尸体运到"
            "冲田房间隔壁的阳台。为了让人误判楼层，他涂黑了电梯楼层显示数字六左下角"
            "的那一笔，使「6」看起来像「5」；又刻意站在数字显示板前递名片，"
            "让同行的人都低头看名片而错过实际楼层。尸体先用钢丝吊在阳台上，"
            "再定时让钢丝断裂坠落，制造出刚被发现的时点。"
        ),
        "evidence": (
            "决定性物证是小五郎在土方房里弄坏、随手塞进沙发坐垫下的一把道具枪。"
            "那把枪后来出现在众人被带往的房间里——而按土方的说法他们都待在五楼，"
            "道具枪却在六楼。柯南由此反推出电梯数字被动手脚，楼层判断整个错了。"
        ),
        "resolution": (
            "柯南借小五郎之口拆穿：电梯「6」被刮改成「5」，递名片是让人低头的掩护，"
            "三间同装修公寓解释了尸体怎么能「凭空」出现在隔壁房间。"
            "土方承认杀人，动机是外遇加保险金。"
        ),
        "spoiler": (
            "本案三名主要角色的姓名取自新选组：土方岁三、冲田总司、永仓新八，"
            "与被害人丈夫的职业（时代剧演员）呼应。另有一处小五郎式的收尾——"
            "他被柯南麻醉推理完，醒来后的第一件事是去掀女性更衣室，被小兰扇了一巴掌。"
            "（同一段落结构在 EP.106 亦有，属该时期固定笑点。）"
        ),
        "relatedCharacters": [],
        "relatedOrganizations": [],
        "relatedLocations": [],
        "relatedCases": [],
        "createdAt": TODAY,
        "updatedAt": TODAY,
    },
    {
        "id": "case-goblin-gang-mansion",
        "type": "case",
        "titles": {
            "zhHans": "盗贼团谜之洋馆事件",
            "zhHant": "盜賊團謎之洋館事件",
            "ja": "盗賊団謎の洋館事件",
            "en": "The Mysterious Mansion of a Band of Thieves Case",
        },
        "aliases": ["妖怪团谜之洋馆事件", "哥布林盗贼团洋馆事件"],
        "summary": (
            "小五郎收到署名「中村操」的委托信，误以为是女性便兴冲冲赶去洋馆，"
            "到场却见两个自称是委托人亲属的男人，屋里几十座钟同时敲响，"
            "还有一座报时鸟被换成妖怪像的钟。真正的委托人中村操被绑架藏了起来。"
        ),
        "caseType": ["kidnapping", "treasure", "cipher", "anime-manga-adaptation"],
        "mangaRefs": ["file-167-169"],
        "animeRefs": ["episode-0104-0105"],
        "sourceRefs": ["src-detective-conan-world-thieves-mansion"],
        "detailStatus": "deepSpoilers",
        "confidence": "high",
        "reviewStatus": "reviewed",
        "victimDescription": (
            "本案无命案被害人。真中村操（推理作家、饭渊茂次郎的外孙女）被绑架后关在阁楼，"
            "获救时存活。饭渊茂次郎本人已病故，死因与本案无关。"
            "另有两起未遂：小五郎与柯南在书房险遭枪击，小兰被勒颈挟持后自行反制。"
        ),
        "culprit": (
            "两名假冒「中村操」及其兄长的男子，实为妖怪团（盗贼团）前成员。"
            "页面未给出二人姓名。"
        ),
        "motive": (
            "不是为钱而杀人，而是为了宝石。两人想找出当年首领私吞、"
            "没有分给手下的赃物宝石。饭渊茂次郎生前把藏匿点的线索设计成钟表机关谜题，"
            "他们解不开，于是绑架真中村操、冒名写信把小五郎（实际是柯南）骗来借用推理能力。"
        ),
        "method": (
            "绑架加冒充：把真中村操关进阁楼，由一人缠绷带伪装成她本人（绷带手里藏枪），"
            "另一人扮作她的兄长，用委托信引来名侦探。为逼迫解谜，"
            "他们在书房对柯南与小五郎开枪（未击中），又勒住循声赶来的小兰做人质。"
            "解谜线索本身是饭渊留下的两道：一座数字钟显示 11:00，"
            "最后两个零之间有一道划痕，读作 110|0，"
            "日语谐音「百獣の王」（ひゃくじゅうのおう）即百兽之王、指向狮子；"
            "第二道线索是字母 L N R，取 light / night / right 的首字母。"
            "柯南还用打火机照出妖怪像与钟表之间的对应关系，才看穿两人冒充者的身份。"
        ),
        "evidence": (
            "绷带手中藏枪暴露两人并非委托人亲属；妖怪团的齿轮式手法与那座妖怪报时钟勾连，"
            "使柯南确认对方身份；阁楼里找到被绑的真中村操，绑架事实当场成立。"
        ),
        "resolution": (
            "柯南解出 110|0 → 百獣の王 → 狮子，配合 L N R（光、夜、右）确定报时鸟的取法，"
            "找到藏在钟里的宝石。假中村操被小五郎打倒，其同伙被小兰制服，"
            "真中村操从阁楼获救。两名妖怪团前成员落网。"
        ),
        "spoiler": (
            "本案是「名侦探被反向利用」的结构：委托人本身就是局，"
            "写信请侦探来的人正是要借侦探的脑子。小五郎因为信上写着女性化的名字"
            "（中村操）而一口认定对方是美女，这个误判贯穿全集笑点，"
            "也让他完全没有察觉两个男人在场有什么不对。"
        ),
        "relatedCharacters": [],
        "relatedOrganizations": [],
        "relatedLocations": [],
        "relatedCases": [],
        "createdAt": TODAY,
        "updatedAt": TODAY,
    },
    {
        "id": "case-scoop-picture-murder",
        "type": "case",
        "titles": {
            "zhHans": "独家照片杀人事件",
            "zhHant": "獨家照片殺人事件",
            "ja": "スクープ写真殺人事件",
            "en": "Scoop Picture Murder Case",
        },
        "aliases": ["独家拍摄杀人事件", "特讯照片杀人事件"],
        "summary": (
            "摄影师柳濑龙一在天使城饭店获颁第 35 届读切摄影奖，并当场得到一只新手表。"
            "记者中井晃突然现身，往他脸上吹了一把白色粉末。当夜中井打电话向小五郎求助，"
            "称有人要杀他；柯南赶到时，中井砸破窗户、浑身着火从公寓坠楼身亡。"
            "柳濑恰好在高架桥上拍下了全过程，声称纯属运气。"
        ),
        "caseType": ["murder", "anime-original", "staged-accident", "time-delay-device"],
        "mangaRefs": [],
        "animeRefs": ["episode-0106"],
        "sourceRefs": ["src-detective-conan-world-scoop-picture"],
        "detailStatus": "deepSpoilers",
        "confidence": "high",
        "reviewStatus": "reviewed",
        "victimDescription": "中井晃（Atsushi Nakai），报社记者。头部遭钝器击打后被烧，砸破窗户坠楼身亡。",
        "culprit": "柳濑龙一（Ryuuichi Yanase），「犯罪摄影」摄影师，第 35 届读切摄影奖得主。",
        "motive": (
            "灭口。柳濑那些获奖的「恰好拍到」的犯罪照片，"
            "全是他在现场动手布置后自己拍下的；中井看穿了这个把戏，"
            "当众往他脸上吹生石灰来摊牌——生石灰正是他用来纵火的手段。"
            "中井打电话给小五郎求助，等于要把事情捅出去，柳濑于是先下手。"
        ),
        "method": (
            "生石灰（caustic lime）加水放热的延时纵火装置。生石灰遇水会产生高达约 300 度的"
            "放热反应，与运动场划线用的消石灰不同。他把生石灰和报纸一起布置在厨房水槽，"
            "并将水龙头扳手压到 1/4 开——水慢慢流出、渗进石灰，"
            "延迟一段时间后自燃。这段延迟正好够他离开公寓、赶到高架桥上"
            "「恰巧」拍到坠楼的瞬间。高架巴士乘客楼梯让他只需三分钟就能往返现场，"
            "所以他有办法先布置、再出现在远处的拍摄点。"
        ),
        "evidence": (
            "决定性物证是他颁奖礼上刚拿到的那只手表，被发现烧毁在中井家厨房台面上；"
            "而他自己的手腕上表不见了。他辩称是中井偷的，柯南便请阿笠博士处理"
            "他获奖照片里车身反射的影像——放大后能看到案发前他手腕上还戴着那只表，"
            "而这只表出现在中井家厨房，证明他当时人在现场。"
            "另一旁证：他因看到烟雾而下意识加速，被监控拍到超速，"
            "粉色违章通知从他口袋掉了出来。"
        ),
        "resolution": (
            "柯南借上电视节目与小五郎同台的机会麻醉小五郎，用变声领结以「名侦探」身份"
            "当面指认：纵火装置是生石灰，时间差由水龙头开度控制，"
            "获奖照片是自导自演，手表被烧毁在现场而照片证明他戴着表。"
            "柳濑无从辩解。"
        ),
        "spoiler": (
            "本案把「摄影师的运气」这一职业神话整个掀翻：他每一次「恰好在场」，"
            "都是先制造现场再去拍。真凶伏法后，柯南才想起小五郎还被他麻醉着丢在休息室，"
            "跑去一看——小五郎已经醒了，正在偷看女更衣室，随即被扇。"
            "阿笠博士用来处理照片的软件在片中名为「Agasa Photoshob」，是对 Photoshop 的戏仿。"
        ),
        "relatedCharacters": [],
        "relatedOrganizations": [],
        "relatedLocations": [],
        "relatedCases": [],
        "createdAt": TODAY,
        "updatedAt": TODAY,
    },
]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    src_doc = load_json(SOURCES)
    existing_source_ids = {row["id"] for row in src_doc["sources"]}
    sources_added = 0
    for row in NEW_SOURCES:
        if row["id"] in existing_source_ids:
            continue
        src_doc["sources"].append(row)
        existing_source_ids.add(row["id"])
        sources_added += 1
    if sources_added:
        save_json(SOURCES, src_doc)

    case_rows = load_json(CASES)
    if isinstance(case_rows, dict):
        case_rows = case_rows.get("cases", [])
    existing_case_ids = {row.get("id") for row in case_rows}
    cases_added = 0
    for row in NEW_CASES:
        if row["id"] in existing_case_ids:
            continue
        case_rows.append(row)
        existing_case_ids.add(row["id"])
        cases_added += 1
    if cases_added:
        save_json(CASES, case_rows)

    print(f"sources_added={sources_added} cases_added={cases_added}")
    print(f"sources_total={len(existing_source_ids)} cases_total={len(case_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
