#!/usr/bin/env python3
"""Register sources + case entities for EP.94-97 (Snow Woman, Kogoro's Date,
Cornered Detective two-case special, Farewell Wine).

EP.96 is a two-hour special containing TWO independent cases; each gets its
own case entity, both pointing at episode-0096.
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
        "id": "src-detective-conan-world-snow-woman-case",
        "title": "Detective Conan Wiki",
        "url": "https://www.detectiveconanworld.com/wiki/Snow_Woman's_Legend_Murder_Case",
        "type": "wiki",
        "language": "en",
        "retrievedAt": TODAY,
        "note": "雪女传说杀人事件（EP.94）：替身演员顶替明星、雪地失温致死的手法与动机原文。",
    },
    {
        "id": "src-detective-conan-world-kogoro-date-case",
        "title": "Detective Conan Wiki",
        "url": "https://www.detectiveconanworld.com/wiki/Kogoro's_Date_Murder_Case",
        "type": "wiki",
        "language": "en",
        "retrievedAt": TODAY,
        "note": "小五郎约会杀人事件（EP.95）：签收快递留下的笔迹时间差、勒索动机原文。",
    },
    {
        "id": "src-detective-conan-world-cornered-detective-case",
        "title": "Detective Conan Wiki",
        "url": "https://www.detectiveconanworld.com/wiki/The_Cornered_Famous_Detective!_Two_Big_Murder_Cases",
        "type": "wiki",
        "language": "en",
        "retrievedAt": TODAY,
        "note": "走投无路的名侦探！连续两大杀人事件（EP.96，2 小时特别篇）：Case 1 九十九元康魔术师案与 Case 2 薮内家案两案原文；漫画源 File.131-138。",
    },
    {
        "id": "src-detective-conan-world-farewell-wine-case",
        "title": "Detective Conan Wiki",
        "url": "https://www.detectiveconanworld.com/wiki/The_Farewell_Wine_Murder_Case",
        "type": "wiki",
        "language": "en",
        "retrievedAt": TODAY,
        "note": "离别美酒杀人事件（EP.97）：自导绑架、私人医生以「测试」为名实施毒杀的原文。",
    },
]

NEW_CASES = [
    {
        "id": "case-snow-woman-legend-murder",
        "titles": {
            "zhHans": "雪女传说杀人事件",
            "zhHant": "雪女傳說殺人事件",
            "ja": "雪女伝説殺人事件",
            "en": "Snow Woman's Legend Murder Case",
        },
        "kind": "动画案件",
        "caseType": "murder",
        "episodeRange": {"start": 94, "end": 94},
        "animeRefs": ["episode-0094"],
        "mangaRefs": [],
        "origin": {"type": "tv-original", "note": "TV 原创（Filler），无漫画对应 File。"},
        "characters": ["character-conan-edogawa", "character-kogoro-mouri", "character-ran-mouri"],
        "sourceRefs": ["src-detective-conan-world-snow-woman-case"],
        "status": "reviewed",
        "detailStatus": "deepSpoilers",
        "createdAt": TODAY,
        "updatedAt": TODAY,
        "summary": "被害人：绢田亚希子（Akiko Kinoshita），26 岁，以「雪女」一角走红的电影女星，死于低温失温（hypothermia），遗体被埋在雪中。",
        "culprit": "被害人的专属替身演员、同岁同伴浅沼洋子（Yoko Asanuma）。",
        "motive": "嫉妒。亚希子始终拿到关注与名声，而洋子作为替身最多只能做她的影子，永远站在二线。",
        "method": "洋子先伪造一封亚希子自称生病、想自杀的信，再预订自己多年前打工过的山形温泉旅馆房间，安排两人同住。次日滑雪途中给亚希子下药使其昏睡，脱下她的滑雪服换上一身白色和服，把人埋进雪里造成失温死亡；随后自己穿上亚希子含全脸面罩的滑雪装返回旅馆，此后一人分饰两角。因熟悉旅馆地形，众人一直以为亚希子只是「生病」待在房间。",
        "evidence": "众人先因那封伪造信认定亚希子是想自杀出走，直到雪中挖出遗体也以「自杀」收场。柯南从一人分饰两角时无法同时出现在两处、以及旅馆动线与入住安排上的破绽反推出真相，把「雪女」的传说外观还原成一场人为的低温杀人。",
        "resolution": "柯南揭穿洋子的替身身份与分饰两角的手法，说明那封「自杀信」是她伪造的、白色的和服与雪地是故意制造的雪女意象。真相在旅馆众人面前公开，洋子的嫉妒动机与其长期作为影子的处境一并被点明。",
    },
    {
        "id": "case-kogoro-date-murder",
        "titles": {
            "zhHans": "小五郎约会杀人事件",
            "zhHant": "小五郎約會殺人事件",
            "ja": "小五郎のデート殺人事件",
            "en": "Kogoro's Date Murder Case",
        },
        "kind": "动画案件",
        "caseType": "murder",
        "episodeRange": {"start": 95, "end": 95},
        "animeRefs": ["episode-0095"],
        "mangaRefs": [],
        "origin": {"type": "tv-original", "note": "TV 原创（Filler），无漫画对应 File。"},
        "characters": ["character-conan-edogawa", "character-kogoro-mouri"],
        "sourceRefs": ["src-detective-conan-world-kogoro-date-case"],
        "status": "reviewed",
        "detailStatus": "deepSpoilers",
        "createdAt": TODAY,
        "updatedAt": TODAY,
        "summary": "被害人：竹中一美（Kazumi Takenaka），29 岁，公司职员，胸口中刀死于自宅公寓。",
        "culprit": "被害人的室友、进口商品销售总监岛村幸子（Sachiko Shimamura）。",
        "motive": "灭口。一美掌握幸子在日本销售违禁商品的把柄，并以此勒索，威胁向警方举报。",
        "method": "命案发生前二十分钟，幸子刻意让快递员把邮件交给一美签收，并当场确认圆珠笔还留有墨水——这封签收单就此成为她「不久后一美还活着」的时间证据。二十分钟后她持刀刺死一美，尸体倒地时圆珠笔滚落，她慌乱间抓起笔，随后把笔放进自己车里。",
        "evidence": "关键物证是那支圆珠笔：签收单上的笔迹证明一美当时还活着并能正常签字，而包裹签收与死亡之间只有二十分钟，期间出入公寓的只有幸子。柯南据此戳破幸子的不在场说法。",
        "resolution": "小五郎本已抓着圆珠笔要质问幸子，却因手从桌面滑开、头部撞到桌子当场昏倒；柯南改用变声领结以小五郎的声音完成推理，指认幸子为凶手。幸子认罪并交代一美以违禁商品之事勒索她。被带走时柯南问她为何不在那个观景点对小五郎下手，她答自己对小五郎并无怨恨。",
    },
    {
        "id": "case-tsukumo-magician-murder",
        "titles": {
            "zhHans": "走投无路的名侦探！连续两大杀人事件（九十九元康案）",
            "zhHant": "走投無路的名偵探！連續兩大殺人事件（九十九元康案）",
            "ja": "追いつめられた名探偵! 連続2大殺人事件（九十九元康殺人事件）",
            "en": "The Cornered Famous Detective! Two Big Murder Cases (Tsukumo Case)",
        },
        "kind": "动画案件",
        "caseType": "murder",
        "episodeRange": {"start": 96, "end": 96},
        "animeRefs": ["episode-0096"],
        "mangaRefs": ["file-131-133"],
        "origin": {"type": "manga", "note": "漫画改编，Volume 14，File.131-138（漫画案件 #37、#38 两个案件合为 2 小时特别篇）。"},
        "characters": ["character-conan-edogawa", "character-ran-mouri", "character-kogoro-mouri"],
        "sourceRefs": ["src-detective-conan-world-cornered-detective-case"],
        "status": "reviewed",
        "detailStatus": "deepSpoilers",
        "createdAt": TODAY,
        "updatedAt": TODAY,
        "summary": "EP.96 特别篇的第一案。被害人：九十九元康（Motoyasu Tsukumo），知名魔术师，死于氰化钾中毒；另有十四年前的旧案死者吉野（Yoshirou Kinoshita，20 岁），在水遁魔术中溺亡。",
        "culprit": "凶手是元康的弟子三代目（Mako Miyoshi），本名三代木下真湖（Mako Kinoshita）。旧案的真凶则是元康本人。",
        "motive": "为兄复仇。十四年前，才华出众的吉野在水遁逃脱魔术中溺亡，表面是意外，实为师父元康嫉妒其天赋、担心被超越而暗中动了手脚——元康在后台对手铐做了处理，使吉野表演时无法自行脱身而溺死。当时年仅七岁的真湖在后台目睹了元康动手，却因年纪太小无法作证，此案最终按意外结案。真湖此后苦学魔术，只为成为元康的入室弟子并伺机复仇。",
        "method": "真湖以弟子的身份接近元康，把元康绑起后以氰化钾将其毒杀，使元康死于氰酸钾中毒。元康知道她的真实身份与杀意，被绑后始终神态平静。",
        "evidence": "旧案的关键在于当年幼小的目击者所见与手铐被动手脚的事实；本案则以元康中毒的死因、以及弟子三人各自的动机与在场关系层层收束到真湖身上。",
        "resolution": "柯南在不弄晕小五郎的情况下协助破案，揭出真湖本名木下真湖、是被元康害死的吉野之妹，十四年前的事故实为谋杀。因元康被绑后毫无惧色，真湖一度威胁要杀掉元康的女儿绫乃（Ayano，6 岁），想看见他真正恐惧的表情；但绫乃终究无辜，真湖最后无法下手，也承认自己不止一次起过杀念。",
    },
    {
        "id": "case-yabuuchi-family-murder",
        "titles": {
            "zhHans": "走投无路的名侦探！连续两大杀人事件（薮内家案）",
            "zhHant": "走投無路的名偵探！連續兩大殺人事件（藪內家案）",
            "ja": "追いつめられた名探偵! 連続2大殺人事件（藪内家殺人事件）",
            "en": "The Cornered Famous Detective! Two Big Murder Cases (Yabuuchi Case)",
        },
        "kind": "动画案件",
        "caseType": "murder",
        "episodeRange": {"start": 96, "end": 96},
        "animeRefs": ["episode-0096"],
        "mangaRefs": ["file-131-138"],
        "origin": {"type": "manga", "note": "漫画改编，与九十九元康案同属 Volume 14 File.131-138 的 2 小时特别篇。"},
        "characters": ["character-conan-edogawa", "character-ran-mouri"],
        "sourceRefs": ["src-detective-conan-world-cornered-detective-case"],
        "status": "reviewed",
        "detailStatus": "deepSpoilers",
        "createdAt": TODAY,
        "updatedAt": TODAY,
        "summary": "EP.96 特别篇的第二案，发生在群马县薮内家。被害人：薮内真知子（Machiko Yabuuchi），39 岁，薮内吉近的第二任妻子，胸腹受刀伤死亡，遗体被投入庭院水井——与第一任薮内夫人的死亡是同一口井；胸口插着一朵山茶花。另有以十字弓射向薮内芳房（Yoshifusa，64 岁）的未遂袭击。",
        "culprit": "「薮内芳房」是冒名顶替者。真芳房多年前已死在巴西，顶替者是田中秋彦（Hickson Tanaka），巴西出生的日裔，是卡洛斯（Carlos）的保镖兼监护人。真知子之死是他正当防卫中刺中对方所致；设置十字弓的是薮内圭子（Keiko Yabuuchi）。",
        "motive": "田中冒名的动机是保护卡洛斯：卡洛斯才是真芳房与巴西女子所生的儿子、遗产继承人之一。假冒芳房可让所有威胁指向自己，同时让外界以为卡洛斯只是保镖、不会对他动手。真知子之死源于她自己意图谋夺「芳房」的那份遗产：她不知道真芳房早已死亡，也不知道眼前的人是假的。圭子设十字弓是想逼「芳房」回巴西，她欠着债，指望没有这个人遗产份额就能覆盖。",
        "method": "真知子在都市酒会上打了一通电话制造不在场证明，然后坐车返回、等待下手时机；她事先告诉薮内裕美（Hiromi）去把加热露天浴池的火重新烧旺，借此让「芳房」被单独留在浴池。她带着那朵山茶花，打算把嫌疑引向一直指控薮内家害死自己姐姐的姐夫。但田中身手极好，她持刀刺去时被格挡、刀被反送回来，反而刺死了自己。",
        "evidence": "真知子胸口的山茶花与第一任薮内夫人溺亡的那口井构成刻意布置的误导；关键在「芳房」这个人的身份链——巴西的死亡记录、卡洛斯的真实身世，以及他收到的两封威胁信（一封来自真知子、一封来自圭子）。柯南的父亲优作随有希子回到日本并潜入薮内家，部分内容由他揭示，其余由柯南麻醉山村刑警后说出。",
        "resolution": "田中秋彦承认自己在真知子之死中的角色，说明自己是卡洛斯的家教兼保镖，随后平静地向警方投案。优作正式现身并去见有希子。另需注意：本集的表层主线是兰因看到柯南摘下眼镜的脸而怀疑他就是新一，有希子以一套复杂但说得通的解释替柯南脱身；这一层与命案本身相互独立。",
    },
    {
        "id": "case-farewell-wine-murder",
        "titles": {
            "zhHans": "离别美酒杀人事件",
            "zhHant": "離別美酒殺人事件",
            "ja": "別れのワイン殺人事件",
            "en": "The Farewell Wine Murder Case",
        },
        "kind": "动画案件",
        "caseType": "murder",
        "episodeRange": {"start": 97, "end": 97},
        "animeRefs": ["episode-0097"],
        "mangaRefs": [],
        "origin": {"type": "tv-original", "note": "TV 原创（Filler），无漫画对应 File。"},
        "characters": ["character-conan-edogawa", "character-kogoro-mouri"],
        "sourceRefs": ["src-detective-conan-world-farewell-wine-case"],
        "status": "reviewed",
        "detailStatus": "deepSpoilers",
        "createdAt": TODAY,
        "updatedAt": TODAY,
        "summary": "被害人：市川小太郎（Kotaro Ichikawa），65 岁，市川产业社长，死于毒物引发的心脏病发作。另有柯南被绑架囚禁于市川家酒窖地下室的插曲，被绑架者实为社长本人所安排。",
        "culprit": "社长的私人医生冈野仁（Hitoshi Okano）。",
        "motive": "复仇。市川当年把作为生意伙伴的冈野之父逼到破产，老人此后酗酒、抑郁，在久病的妻子去世几年后自杀，那时冈野正要上大学。身为私人医生，冈野随时都可以下手，但他一直忍着；直到市川向他吐露，打算装作心脏病发作来「测试」两个女儿和泉（Kazue）与瑞江（Mizue）到底有多爱自己，他才决定动手。",
        "method": "冈野没有按社长的剧本演戏，而是利用这场「测试」给市川注射了致命剂量的药物，让心脏病发作成为真实的死亡。绑架并囚禁柯南的人其实是市川本人——他事先安排，好让这场测试显得像真的。",
        "evidence": "柯南曾在洗手间看到和泉带着疑似装有药物的注射器走向酒窖，这条线索与后来绑匪身份的反转互相印证：真正动手的另有其人，且早有预谋地把别人的计划当成掩护。此外长女和泉确实起过杀父之心，也备有可用来下手的毒酒，但最终不是她下的手。",
        "resolution": "柯南与毛利小五郎逐一辨明视频证据与线索，把真凶指向私人医生冈野仁。冈野的动机由此被揭开：父亲的破产、酗酒与自杀，以及市川亲口说出的「测试」。",
    },
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    # sources
    sdata = load(SOURCES)
    slist = sdata["sources"] if isinstance(sdata, dict) else sdata
    have = {s["id"] for s in slist}
    added_s = 0
    for s in NEW_SOURCES:
        if s["id"] not in have:
            slist.append(s)
            added_s += 1

    # cases
    cdata = load(CASES)
    clist = cdata["cases"] if isinstance(cdata, dict) else cdata
    chave = {c["id"] for c in clist}
    added_c = 0
    for c in NEW_CASES:
        if c["id"] not in chave:
            clist.append(c)
            added_c += 1

    dump(SOURCES, sdata)
    dump(CASES, cdata)
    print(f"sources_added={added_s} cases_added={added_c} total_cases={len(clist)} total_sources={len(slist)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
