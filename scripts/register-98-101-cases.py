#!/usr/bin/env python3
"""Register sources + case entities for EP.98-101.

EP.98-99  The Famous Potter Murder Case      (File.160-162)
EP.100-101 The Memories of First Love Case   (File.173-175)

Both are two-parters and each maps to ONE case entity with a ranged
animeRef. Every fact below is taken from detectiveconanworld page text
(/tmp/potter.html, /tmp/firstlove.html), not from search snippets.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "sources.json"
CASES = ROOT / "data" / "entities" / "cases.json"

NEW_SOURCES = [
    {
        "id": "src-detective-conan-world-famous-potter",
        "type": "wiki",
        "title": "The Famous Potter Murder Case — Detective Conan Wiki",
        "url": "https://www.detectiveconanworld.com/wiki/The_Famous_Potter_Murder_Case",
        "language": "en",
        "publisher": "detectiveconanworld.com",
        "accessedAt": "2026-10-27",
        "notes": "EP.98-99 (File.160-162). Situation/People/Resolution 段为事实来源。",
    },
    {
        "id": "src-detective-conan-world-first-love",
        "type": "wiki",
        "title": "The Memories of First Love Case — Detective Conan Wiki",
        "url": "https://www.detectiveconanworld.com/wiki/The_Memories_of_First_Love_Case",
        "language": "en",
        "publisher": "detectiveconanworld.com",
        "accessedAt": "2026-10-27",
        "notes": "EP.100-101 (File.173-175)。Evidence/Motive/Aftermath 段为事实来源。",
    },
]

NEW_CASES = [
    {
        "id": "case-famous-potter-murder",
        "type": "case",
        "titles": {
            "zhHans": "名陶艺家杀人事件",
            "zhHant": "名陶藝家殺人事件",
            "ja": "名陶芸家殺人事件",
            "en": "The Famous Potter Murder Case",
        },
        "aliases": ["陶艺家杀人事件", "喜久卫门宅邸命案"],
        "summary": (
            "毛利一家受邀到陶艺家喜久卫门（本名土屋万吉）宅邸度周末，席间小五郎赢得一只贵重陶杯。"
            "一夜饮酒后，众人发现长媳土屋益子吊死在储藏室。现场像自杀，目暮起初怀疑另有蹊跷。"
        ),
        "caseType": "manga",
        "mangaRefs": ["file-160-162"],
        "animeRefs": ["episode-0098-0099"],
        "sourceRefs": ["src-detective-conan-world-famous-potter"],
        "detailStatus": "deepSpoilers",
        "confidence": "high",
        "reviewStatus": "reviewed",
        "victimDescription": "土屋益子（42 岁），喜久卫门已故长子的妻子，死因为缢死。",
        "culprit": "濑户隆一（Ryuichi Seto），喜久卫门的徒弟之一，35 岁。",
        "motive": (
            "益子背著公公仿制喜久卫门的代表作品高价出售。她失手打碎一只仿品后极度恐慌，"
            "担心曝光；隆一看出碎片是赝品当面对质，劝她收手被粗暴顶回。隆一既因被拒、也因自尊"
            "受挫而动了杀机。"
        ),
        "method": (
            "益子烂醉昏睡时，隆一把她抱进储藏室而不是卧室，塞进抽屉、脖颈边垂一条松绳，"
            "又把她当闹钟用的手机放她身旁。几小时后益子被手机闹铃吵醒，酒还没醒，"
            "起身时自己吊了上去。抽屉上突出的铁钉划开她的腿，成为现场血迹的来源。"
        ),
        "evidence": (
            "「自杀」无法解释的两处硬伤：血迹来自抽屉外露铁钉造成的腿伤，与缢死过程吻合但和"
            "「因打破名品而愧疚自尽」的动机叙事对不上；以及她醒来的位置在抽屉里而非床上。"
            "隆一对赝品的知情，把「她怕被揭穿」这条线接到他自己身上。"
        ),
        "resolution": (
            "柯南推翻自杀结论，指认隆一。手法成立的关键是益子用手机当闹钟的习惯——"
            "把她挪到绳下、再把闹钟放在她身边，等于让她自己完成绞刑。"
        ),
        "spoiler": (
            "本集还埋了一条元叙事：派对上众人请小五郎讲他破过的案子，他躲开月影岛与雾天狗"
            "（都是柯南代破、他在睡），只肯讲同学会案，而那件他其实早就讲过；"
            "柯南心里点明这三件是他醒着时被部分参与解决的案子。"
        ),
        "relatedCharacters": [],
        "relatedOrganizations": [],
        "relatedLocations": [],
        "relatedCases": [],
        "createdAt": "2026-10-27",
        "updatedAt": "2026-10-27",
    },
    {
        "id": "case-memories-of-first-love",
        "type": "case",
        "titles": {
            "zhHans": "初恋情人回忆事件",
            "zhHant": "初戀情人回憶事件",
            "ja": "初恋の想い出殺人事件",
            "en": "The Memories of First Love Case",
        },
        "aliases": ["初恋回忆事件", "内田麻美纵火案"],
        "summary": (
            "自称新一「初恋」的内田麻美（18 岁，东都大学文学部新生）邀小兰、园子和小五郎到别墅参加"
            "生日会。凌晨 2:50 别墅起火，麻美被困；柯南与小兰把她救出，小兰因吸入浓烟昏倒。"
        ),
        "caseType": "manga",
        "mangaRefs": ["file-173-175"],
        "animeRefs": ["episode-0100-0101"],
        "sourceRefs": ["src-detective-conan-world-first-love"],
        "detailStatus": "deepSpoilers",
        "confidence": "high",
        "reviewStatus": "reviewed",
        "victimDescription": (
            "内田麻美（18 岁），东都大学文学部新生，被烧成重伤但未死亡。"
            "本案是纵火未遂，不是杀人既遂。"
        ),
        "culprit": "泽井学（Manabu Sawai），22 岁，东都大学文学部四年级，推理研究会会长。",
        "motive": (
            "不是要杀麻美。他上个月向麻美表白被拒——此前从没有女生拒绝过他——"
            "于是想制造一场「英雄救美」：把麻美置于险境，再由自己冲进去救出来，"
            "以此换取她的感激和爱意。"
        ),
        "method": (
            "在传真机下方的椅子上摆好插着蜡烛的生日蛋糕，然后跑到便利店假装打电话，"
            "实际发出传真；传真纸落到未熄的蜡烛上引燃，火从客厅蔓延整栋屋子。"
            "他事先反复发过几份传真测试这个方法能成。"
        ),
        "evidence": (
            "消防员递给柯南两张烧焦的纸，来自两份不同的传真——麻美教授发来的生日贺电，"
            "和泽井在便利店发的测试件。便利店店长记得众人唱歌时泽井单独用过传真机；"
            "传真确认页留有他的号码与指纹。柯南让消防员在废墟上复现同样的装置，"
            "证明他不必在场也能点火。"
        ),
        "resolution": (
            "柯南借小五郎之口点破：众人离开后泽井趁「暂停」时间挪动家具，"
            "把被下了药的麻美从沙发搬到地板，以免她被烧到——这个「体贴」反倒成了破口。"
            "柯南怒斥他：只要路上塞车、抛锚或爆胎晚到两分钟，麻美就真的会死。"
            "泽井交出那张还沾着奶油的教授传真，平静自首。"
        ),
        "spoiler": (
            "尾声反转：麻美向小兰、园子承认「我是新一的初恋」是吹牛，事实是新一是她的初恋。"
            "她做柠檬派被新一说过难吃，反复练到做出他认可的口味；她还故意教小兰一个糟糕的配方。"
            "她也说出当年告白被拒的实情——新一红着脸说已经有喜欢的女孩："
            "「从小认识」「要强、固执，又温柔，还有点爱哭」，园子当场喊出那就是小兰，小兰却没反应过来。"
        ),
        "relatedCharacters": [],
        "relatedOrganizations": [],
        "relatedLocations": [],
        "relatedCases": [],
        "createdAt": "2026-10-27",
        "updatedAt": "2026-10-27",
    },
]


def upsert(path: Path, key: str, rows: list[dict]) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    bucket = data[key] if isinstance(data, dict) else data
    have = {r["id"] for r in bucket}
    added = 0
    for row in rows:
        if row["id"] in have:
            continue
        bucket.append(row)
        added += 1
    if added:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return added


def main() -> int:
    s = upsert(SOURCES, "sources", NEW_SOURCES)
    c = upsert(CASES, "cases", NEW_CASES)
    print(f"sources_added={s} cases_added={c}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
