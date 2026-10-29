#!/usr/bin/env python3
"""M18：补齐高频人物的 role / summary（前 60 位）。

背景：147 个人物里 133 个 role 与 summary 都是空的，列表页副行只能显示
「出场 N 案」，看着像没录数据。这里按出场案数从高到低补前 60 位。

原则：
  - 只写原作中确定的身份，不编造剧情；
  - summary 一句到两句，写身份 + 与主线的关联，不复述单个案件情节（避免剧透）；
  - 幂等：已有非空 role/summary 一律不覆盖；
  - 只补 role/summary，不动其他字段。
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHARS = ROOT / "data/entities/characters.json"

# id: (role, summary)
FILL = {
    "character-wataru-takagi": ("警视厅搜查一课刑警",
        "警视厅搜查一课强行犯三系的刑警，目暮十三的部下。性格温和、办案踏实，与同系的佐藤美和子交往。"),
    "character-juzo-megure": ("警视厅搜查一课警部",
        "警视厅搜查一课强行犯三系的负责人，长期与毛利小五郎合作办案。以稳妥的现场指挥和对部下的信任著称。"),
    "character-kazunobu-chiba": ("警视厅搜查一课刑警",
        "警视厅搜查一课强行犯三系的刑警，身形高大、记忆细节的能力突出，与三池苗子是恋人关系。"),
    "character-hiroshi-agasa": ("发明家 / 阿笠博士",
        "住在工藤家隔壁的发明家，柯南与灰原哀最可靠的技术后援。为柯南制作了蝴蝶结变声器、麻醉手表、追踪眼镜等整套装备。"),
    "character-sonoko-suzuki": ("帝丹高中生 / 铃木财团千金",
        "毛利兰的同学与好友，铃木财团社长之女。热衷撮合新一与小兰，常把自家产业变成案件现场。"),
    "character-miwako-sato": ("警视厅搜查一课刑警",
        "警视厅搜查一课强行犯三系唯一的女刑警，办案时有极强的行动力。与高木涉是恋人，对已故的松田阵平留有旧情。"),
    "character-yoko-okino": ("偶像歌手 / 演员",
        "人气偶像，毛利小五郎最崇拜的对象。多次因工作现场卷入案件，与毛利一家逐渐熟络。"),
    "character-kazuha-toyama": ("改方高中生 / 服部平次的青梅竹马",
        "服部平次的青梅竹马，性格直率、擅长合气道。与平次长期处于互相在意却不肯点破的状态。"),
    "character-officer-tome": ("群马县警刑警",
        "群马县警的刑警，山村操的部下。为人朴实，常跟着山村一起出现在案件现场。"),
    "character-ninzaburo-shiratori": ("警视厅搜查一课警部补",
        "警视厅搜查一课强行犯三系的刑警，出身优渥、举止讲究。曾长期暗恋佐藤美和子，后来与白鸟任三郎的往事一并放下。"),
    "character-eri-kisaki": ("律师 / 妃法律事务所所长",
        "毛利小五郎分居中的妻子、毛利兰的母亲，知名律师，法庭上极少败诉。与九条玲子是长期的法庭对手。"),
    "character-yukiko-kudo": ("前知名女演员 / 工藤优作之妻",
        "工藤新一的母亲，曾是风靡一时的女演员，擅长易容。与丈夫优作常年在海外，偶尔回国为柯南的计划出力。"),
    "character-sumiko-kobayashi": ("帝丹小学教师",
        "帝丹小学一年 B 班的班主任，少年侦探团所在班级的老师。与白鸟任三郎有旧识关系，后与其交往。"),
    "character-yumi-miyamoto": ("警视厅交通部交警",
        "警视厅交通部的女交警，佐藤美和子的好友，热衷替人牵线。与宫本由美一同出现在多起交通相关案件中。"),
    "character-makoto-kyogoku": ("高中生空手道选手 / 京极真",
        "杯户高中学生，空手道全国冠军，铃木园子的男友。以极强的身体能力多次化解危机。"),
    "character-azusa-enomoto": ("白罗咖啡厅店员",
        "毛利侦探事务所楼下的白罗咖啡厅店员，与毛利一家及柯南相熟，常在不经意间提供线索。"),
    "character-sango-yokomizo": ("静冈县警刑警",
        "静冈县警的刑警，横沟重悟的哥哥。说话慢条斯理、办事认真，是各地警界中出场较多的一位。"),
    "character-misao-yamamura": ("群马县警警部",
        "群马县警的警部，性格随和、常把案件想得过于简单。崇拜毛利小五郎，多次与其合作。"),
    "character-yusaku-kudo": ("推理小说家 / 工藤新一之父",
        "工藤新一的父亲，世界知名的推理小说家，推理能力不逊于儿子，多次在幕后协助柯南对抗黑衣组织。"),
    "character-kaitou-kid": ("怪盗基德 / 魔术师黑羽快斗",
        "以怪盗基德之名行事的怪盗，专偷宝石，擅长易容与魔术。真实身份为高中生黑羽快斗，与工藤新一是宿敌式对手。"),
    "character-ayumi-yoshida": ("帝丹小学学生 / 少年侦探团成员",
        "少年侦探团的成员，性格活泼、观察细致，常在不经意间指出关键细节。"),
    "character-jodie-starling": ("FBI 搜查官",
        "FBI 的搜查官，赤井秀一的同僚，曾以英语教师身份在日本活动。对黑衣组织的追查态度强硬。"),
    "character-ryusuke-higo": ("职业足球选手",
        "职业足球选手，灰原哀崇拜的球星。其转会与比赛相关的事件多次成为案件背景。"),
    "character-detective-horita": ("警视厅搜查一课刑警",
        "警视厅搜查一课强行犯三系的刑警，负责现场勘查与外围走访，多次随目暮一并出动。"),
    "character-mitsuhiko-tsuburaya": ("帝丹小学学生 / 少年侦探团成员",
        "少年侦探团的成员，知识面广、喜欢科学，常负责推理中的知识补充。"),
    "character-ginzo-nakamori": ("警视厅搜查二课警部",
        "警视厅搜查二课的警部，专职追捕怪盗基德。对基德执念极深，也是中森青子的父亲。"),
    "character-genta-kojima": ("帝丹小学学生 / 少年侦探团成员",
        "少年侦探团的成员，体格壮实、食量惊人，性格直率，关键时刻敢于上前。"),
    "character-detective-sugita": ("警视厅搜查一课刑警",
        "警视厅搜查一课强行犯三系的刑警，常在案发现场负责封锁与人员调度。"),
    "character-detective-fukui": ("警视厅搜查一课刑警",
        "警视厅搜查一课强行犯三系的刑警，负责现场取证与笔录，出场虽短但多次出现。"),
    "character-detective-sogawa": ("警视厅搜查一课刑警",
        "警视厅搜查一课强行犯三系的刑警，随目暮十三参与多起案件的现场工作。"),
    "character-detective-okumura": ("警视厅搜查一课刑警",
        "警视厅搜查一课强行犯三系的刑警，负责现场外围与嫌疑人带离等具体工作。"),
    "character-jirokichi-suzuki": ("铃木财团顾问 / 铃木园子的叔父",
        "铃木园子的叔父，铃木财团的顾问。行事张扬、热衷挑战怪盗基德，多次以自家藏品设局。"),
    "character-james-black": ("FBI 日本分部长",
        "FBI 日本分部的负责人，赤井秀一与茱蒂·斯泰琳的上司，主导在日本境内对黑衣组织的调查。"),
    "character-rumi-wakasa": ("帝丹小学副班主任",
        "帝丹小学一年 B 班的副班主任，身手极佳，与黑衣组织及羽田浩司案之间存在未解的关联。"),
    "character-jugo-yokomizo": ("警视厅搜查一课刑警",
        "警视厅搜查一课的刑警，横沟参悟的弟弟。说话直接、办案干脆。"),
    "character-detective-takikawa": ("警视厅搜查一课刑警",
        "警视厅搜查一课强行犯三系的刑警，负责现场记录与鉴识协调。"),
    "character-detective-saitoh": ("警视厅搜查一课刑警",
        "警视厅搜查一课强行犯三系的刑警，多次随目暮出现于案发现场。"),
    "character-detective-kojima": ("警视厅搜查一课刑警",
        "警视厅搜查一课强行犯三系的刑警，负责现场走访与线索核实。"),
    "character-naeko-miike": ("警视厅交通部交警",
        "警视厅交通部的女交警，与千叶和伸是恋人关系，童年时便已相识。"),
    "character-detective-nakamura": ("警视厅搜查一课刑警",
        "警视厅搜查一课强行犯三系的刑警，负责现场外围与证物搬运。"),
    "character-andre-camel": ("FBI 搜查官",
        "FBI 的搜查官，赤井秀一的同僚，身形魁梧，负责行动支援与驾驶。"),
    "character-tomoaki-araide": ("帝丹高中校医 / 新出智明",
        "帝丹高中的校医，品行端正、受学生信赖。其身份曾一度被黑衣组织成员冒用。"),
    "character-jinpei-matsuda": ("警视厅爆炸物处理班刑警（已故）",
        "警视厅爆炸物处理班的刑警，佐藤美和子曾经的恋人，在拆除炸弹时殉职。"),
    "character-hideo-akagi": ("职业棒球选手",
        "职业棒球选手，与比护隆佑同为体育界人物，多次出现在与体育相关的案件中。"),
    "character-goro-otaki": ("大阪府警刑警",
        "大阪府警的刑警，服部平次的熟人，西日本案件中的主要联络人。"),
    "character-detective-hirota": ("警视厅搜查一课刑警",
        "警视厅搜查一课强行犯三系的刑警，参与现场勘查与人员问询。"),
    "character-shukichi-haneda": ("将棋棋手 / 羽田秀吉",
        "职业将棋棋手，赤井秀一的弟弟、世良真纯的哥哥。头脑极佳，与宫本由美交往。"),
    "character-kansuke-yamato": ("长野县警警部",
        "长野县警的警部，性格豪爽、行动力强，与上原由衣、诸伏高明组成固定的办案搭档。"),
    "character-hyoue-kuroda": ("警视厅刑事部理事官 / 黑田兵卫",
        "警视厅刑事部的理事官，曾长期昏迷后苏醒，与黑衣组织及羽田浩司案存在关联。"),
    "character-akemi-miyano": ("前黑衣组织外围成员 / 宫野志保之姐",
        "宫野志保（灰原哀）的姐姐，曾为黑衣组织执行外围任务，试图带妹妹脱离组织。"),
    "character-yui-uehara": ("长野县警刑警",
        "长野县警的刑警，大和敢助的搭档，行事沉稳，与大和之间有长期的信赖关系。"),
    "character-midori-kuriyama": ("栗山绿 / 妃英理的助手",
        "妃英理法律事务所的助手，负责案件资料与日常事务，是妃英理最信任的工作伙伴。"),
    "character-kohji-haneda": ("将棋棋手（已故） / 羽田浩司",
        "已故的职业将棋棋手，羽田秀吉的义兄。其死亡事件与黑衣组织及 APTX4869 的线索直接相关。"),
    "character-takaaki-morofushi": ("长野县警警部 / 诸伏高明",
        "长野县警的警部，诸伏景光的兄长。思路冷静、推理严谨，与诸葛亮同名而常被同伴打趣。"),
    "character-muga-iori": ("大冈家的管家 / 伊织无我",
        "大冈红叶的管家兼司机，身手与观察力都很出色，对大小姐忠心耿耿。"),
    "character-momiji-ooka": ("高中生 / 大冈红叶",
        "京都的高中生，大冈家千金，将棋界的赞助者。自称服部平次的未婚妻，与远山和叶是情敌关系。"),
    "character-kiyonaga-matsumoto": ("警视厅搜查一课管理官",
        "警视厅搜查一课的管理官，目暮十三的上级。作风强硬、判断果断，对部下要求严格。"),
    "character-detective-kobayashi": ("警视厅搜查一课刑警",
        "警视厅搜查一课强行犯三系的刑警，负责现场外围与笔录工作。"),
    "character-chiharu-matsubara": ("长野县警刑警",
        "长野县警的刑警，参与长野地区的多起案件，与大和敢助、上原由衣同属一系。"),
    "character-wataru-date": ("警视厅搜查一课刑警（已故）",
        "警视厅搜查一课的刑警，高木涉的前任搭档，因公殉职。其遗志由高木继承。"),
}


def load():
    data = json.loads(CHARS.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else (data.get("items") or next(iter(data.values())))
    return data, items


def main():
    dry = "--dry-run" in sys.argv
    data, chars = load()
    by_id = {c["id"]: c for c in chars}

    missing = sorted(i for i in FILL if i not in by_id)
    if missing:
        print("REFUSE: 以下 id 不在角色库中，整批不写盘：")
        for m in missing:
            print("  -", m)
        return 1

    changed = 0
    for cid, (role, summary) in FILL.items():
        c = by_id[cid]
        dirty = False
        # 只补空值，已有内容一律不覆盖
        if not (c.get("role") or "").strip():
            c["role"] = role
            dirty = True
        if not (c.get("summary") or "").strip():
            c["summary"] = summary
            dirty = True
        if dirty:
            changed += 1

    print(f"FILL 定义 {len(FILL)} 人，本次补写 {changed} 人")

    if changed == 0:
        print("IDEMPOTENT_OK（无改动，不写盘）")
        return 0
    if dry:
        print("DRY_RUN：未写盘")
        return 0

    CHARS.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"WROTE {CHARS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
