#!/usr/bin/env python3
"""Build sourced L3 candidates for EP.90-93 cases.

Cases:
  case-flower-scent-murder          (EP.90)
  case-bank-robber-hospitalization  (EP.91)
  case-fearful-traversing-murder    (EP.92-93)

All facts are taken from the detectiveconanworld.com wiki article body.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAND = ROOT / "data" / "candidates" / "entities.json"

SRC_FLOWER = "src-detective-conan-world-flower-scent-case"
SRC_BANK = "src-detective-conan-world-bank-robber-hospital-case"
SRC_TRAV = "src-detective-conan-world-fearful-traverse-case"

CASES = [
    "case-flower-scent-murder",
    "case-bank-robber-hospitalization",
    "case-fearful-traversing-murder",
]

FIELDS = {
    "case-flower-scent-murder": {
        "summary": "被害人：白木大辅（Daisuke Shiraki），58 岁，Bay Front 酒店老板；先被氯仿麻醉，再用领带勒死。",
        "culprit": "尾崎翠（Midori Ozaki），33 岁，理香的经纪人。",
        "motive": (
            "理香对外宣称的花道绝技实为其姐春香所创。理香与白木合谋窃取春香技艺并买通花道界赞助人，"
            "令春香被整个花道圈封杀、名声尽毁，春香最终在卧室用数十束花同时绽放释放毒物自杀。"
            "尾崎翠发现姐姐陈尸花丛后查出真相，遂以经纪人身份潜入理香身边，策划一并杀死理香与白木。"
        ),
        "method": (
            "把氯仿与氰化钾各冻成小球，分别塞进经低温处理、退回花苞状态的鲜花里。"
            "赠送给宾客的花中放氯仿球，随时间推移花朵绽放、氯仿挥发令目标昏睡；"
            "舞台上的花中放氰化钾球，同理在表演时释放，企图杀死理香并在其中一并自尽。"
            "只有同时负责宾客用花与舞台用花的人才能完成这套布置。"
        ),
        "evidence": (
            "柯南在被褥箱中发现氯仿（CHCl₃）与氰化钾（KCN）两瓶化学品，并从受害者的花上闻到氯仿气味；"
            "搜查理香随身物品时找到一瓶氯仿，确认为同一来源。"
            "因宾客收到的花本应已盛开、而舞台上的花仍是花苞，柯南据此判定第二批毒花针对的是理香本人；"
            "又因花由经纪人尾崎翠一人经手，锁定凶手。"
        ),
        "resolution": (
            "柯南揭穿冰镇毒花球的机关，指出尾崎翠是把姐姐的绝技变成杀人手段。"
            "尾崎翠的计划是先杀白木、再在舞台上与理香同归于尽；理香获救，幕后旧案一并被揭开。"
        ),
    },
    "case-bank-robber-hospitalization": {
        "summary": "被害人：关口由美子（Yumiko Sekiguchi），被劫匪团伙挟持；住院的烧伤病人为团伙成员，是灭口对象。",
        "culprit": (
            "劫匪团伙：首领山本、赤羽右卫门、英子、高垣，另有伪装成警察与护士的两人参与。"
            "直接胁迫者为该团伙，动手者被逼为银行职员关口义男。"
        ),
        "motive": (
            "团伙为撇清银行抢劫案，打算杀掉烧伤住院的同伙灭口，"
            "并把银行职员关口义男伪造成策划整起抢劫的主谋；"
            "为此挟持他的女儿关口由美子，逼他动手。"
        ),
        "method": (
            "把枪藏在糖果盒里交给义男，让他用里面的武器杀死烧伤病人；"
            "同时用手机在院内多处监视义男的行动，"
            "由同伙在商场楼顶露台用望远镜远程观察，一旦他迟疑就威胁对其女儿下手。"
        ),
        "evidence": (
            "柯南注意到义男声称很忙却一直提着糖果盒在院内走动，而糖果盒本不该是给父亲的礼物"
            "（其父为糖尿病人，不能吃糖）；院内禁止使用手机，却有数人一直打电话并注视义男。"
            "他又屡次望向商场方向并低声念女儿名字——柯南据此判断女儿被挟持在商场楼顶露台，"
            "因为从那里可以用望远镜清楚观察他们的动静。"
        ),
        "resolution": (
            "柯南当面拦下义男并道破胁迫结构。义男承认被设局。"
            "柯南从糖果盒里取出枪，引起伪装警察与持报男子注意，随即用增强踢力鞋踢出足球制服二人；"
            "又用麻醉手表放倒伪装护士及看守女儿的woman，其余少年侦探团成员配合行动。"
            "父女团聚，劫匪团伙全部被捕。"
        ),
    },
    "case-fearful-traversing-murder": {
        "summary": "被害人：平井健一（Kenichi Hirai），22 岁，登山向导；被飞刀擦伤脸颊后失去平衡坠崖，头部撞石致死。",
        "culprit": "代号「狐狸」的职业杀手，本作中冒充山间小屋管理员岩田重吉（Juukichi Iwata）。",
        "motive": (
            "平井长期往返该山道，认识真正的岩田重吉，是「狐狸」冒名顶替计划中的变数，"
            "因此在计划推进前被灭口。"
            "「狐狸」本身是受雇杀手，与牛尾文三之间另有因果：半年前他在刺杀某企业社长时令对方车辆失控撞上校车，"
            "造成牛尾年仅 5 岁的女儿千纱死亡，「狐狸」由此隐姓埋名避风头。"
        ),
        "method": (
            "在登山途中向平井投掷小刀；平井仓促躲闪只被划伤脸颊，但失去平衡坠下高崖。"
            "「狐狸」事前已将真正的管理员岩田重吉绑架并囚禁在附近洞穴，"
            "自己以管理员身份在小屋接待一行人，掌握所有人的动向。"
        ),
        "evidence": (
            "柯南与毛利小五郎下崖验尸，发现平井后脑撞在岩石上，"
            "但脸颊另有一道刀割伤，且近处有一把带血的小刀——说明有人先向他掷刀，"
            "他勉强避开却被划伤、失衡坠亡，并非单纯失足。"
            "其后文三目睹「老人」岩田在滑坡中把川边推下悬崖后健步逃走，"
            "才判断这个「管理员」就是「狐狸」本人。"
        ),
        "resolution": (
            "文三坦承整趟登山都是他设的局：他从未生病、也不想寻死，"
            "一切只为亲手杀掉害死女儿千纱的「狐狸」。"
            "他一度举枪，柯南拿出他钱包里千纱的照片请他不要弄脏自己的手，文三放下枪；"
            "「狐狸」抢枪欲杀众人，被柯南踢飞，逃跑时被小五郎以柔道摔倒，伪装脱落、真面目远比外表年轻。"
            "「狐狸」、文三与川边肇三人被捕；离开前文三向柯南道谢并含笑告别。"
        ),
    },
}

# 同一页面中与本案件无关、但必须如实记录为独立事件的事实
NOTES = {
    "case-fearful-traversing-murder": {
        "relatedIncidents": [
            "凉子（Kyoko Saegusa）之死与「狐狸」无关：川边肇（Akira Kawabe）为灭口而杀害她，"
            "二人此前共同犯下抢劫杀人案。",
            "牛尾文三雇凶杀自己的委托与本次登山均为其复仇布局的一部分，文三本人不构成杀人既遂。",
            "在毛利侦探事务所遭狙击、以及小五郎在睡梦中被刺，原文均记为未遂事件。",
        ],
    },
}


def main() -> None:
    data = json.loads(CAND.read_text(encoding="utf-8"))
    cands = data["candidates"] if isinstance(data, dict) else data

    bad = {"targetId", "entityId"}
    dropped = 0
    kept = []
    for c in cands:
        tid = c.get("targetId") or c.get("entityId")
        if tid in CASES:
            dropped += 1
            continue
        kept.append(c)

    added = 0
    for cid, fields in FIELDS.items():
        for name, value in fields.items():
            kept.append(
                {
                    "candidateId": f"cand-l3-{cid}-{name}",
                    "targetId": cid,
                    "field": name,
                    "value": value,
                    "sourceRefs": [
                        {
                            "case-flower-scent-murder": SRC_FLOWER,
                            "case-bank-robber-hospitalization": SRC_BANK,
                            "case-fearful-traversing-murder": SRC_TRAV,
                        }[cid]
                    ],
                    "confidence": "high",
                    "reviewStatus": "accepted",
                    "reviewNote": "字段取自 detectiveconanworld.com wiki 页面正文，逐条核对。",
                }
            )
            added += 1

    for cid, extra in NOTES.items():
        for i, text in enumerate(extra["relatedIncidents"], start=1):
            kept.append(
                {
                    "candidateId": f"cand-l3-{cid}-relatedIncident-{i}",
                    "targetId": cid,
                    "field": "relatedCases",
                    "value": text,
                    "sourceRefs": [SRC_TRAV],
                    "confidence": "high",
                    "reviewStatus": "accepted",
                    "reviewNote": "原文将此事记为独立事件，不可并入主案。",
                }
            )
            added += 1

    if isinstance(data, dict):
        data["candidates"] = kept
        payload = data
    else:
        payload = kept
    CAND.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"dropped={dropped} added={added} total={len(kept)}")


if __name__ == "__main__":
    main()
