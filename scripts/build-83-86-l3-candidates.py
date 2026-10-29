#!/usr/bin/env python3
"""Build sourced L3 candidates for EP.83-86 cases.

Cases: case-general-hospital-murder (83), case-ski-lodge-murder (84-85),
case-kidnapping-location (86). Facts come from wiki article bodies only.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data" / "candidates" / "entities.json"
BATCH = "ep-83-86-l3"

SPECS = {
    "case-general-hospital-murder": {
        "src": "src-detective-conan-world-general-hospital-case",
        "fields": [
            ("culprit", "外科医生白井光雄（Mitsuo Shirai）", "Wiki Resolution：The culprit who murdered Eto is Mitsuo Shirai。"),
            ("motive", "被害人江藤胜敏长期嘲讽他，还以揭发手段逼他退出两人争抢的晋升名额，他遂起杀意。", "Wiki Resolution：was always mocked by his rival Eto…Eto tried to blackmail him into backing off the promotion。"),
            ("method", "先用 CPR 假人做前三夜的「幻影刺杀」：借对面房间的灯光把人影投到小五郎房的窗上，让人以为小五郎出现幻觉、精神失常，便于把罪栽给他；第四夜在对面房间真实刺杀江藤，再以钝器打昏小五郎并把刀塞进他手里。", "Wiki Resolution：light was reflecting the silhouettes…first three murders were in reality a CPR dummy…fourth and real murder occurred in the room opposite。"),
            ("evidence", "咖啡杯上没有他的指纹：他戴乳胶手套捏住杯把冲洗，护士的指纹却仍留在杯上；他称自己清洗过杯子，无法解释为何只洗掉自己的指纹。另查到他根本不在办公室，是用免提电话与护士通话制造在场假象。", "Wiki Resolution：指纹缺失、手套冲洗、免持电话制造不在场。"),
            ("resolution", "白井当面对质后认罪，交代动机与被打压的晋升竞争；小五郎洗清嫌疑。", "Wiki Resolution 末段认罪。"),
        ],
    },
    "case-ski-lodge-murder": {
        "src": "src-detective-conan-world-ski-lodge-case",
        "fields": [
            ("culprit", "米原晃子（Akiko Yonehara），帝丹小学前教师，被害者们的同事", "Wiki Resolution：The killer is Akiko Yonehara。"),
            ("motive", "三年前十二岁的持田美奈子在排球社教室被吊死，校方以考试压力自杀结案；晃子判断她是被杉山与另一名教师（岛田）灭口，遂以「合宿」名义把相关教师聚到山庄复仇。", "Wiki Resolution：inspired by the death of the little Minako Mochizuki…deduced that she had been killed。"),
            ("method", "先杀音乐教师杉山并藏尸屋外让其冻僵，扰乱死亡时间；再袭园子制造不在场证明，随即假扮成被害人（园子看到的「晃子」其实是杉山尸体）；最后以假发编成的发辫勒杀，用完可收回头上、不留凶器。各处留下口红写的「美奈子」。", "Wiki Resolution：藏尸冻僵、袭击园子做不在场证明、假发勒杀、口红留言。"),
            ("evidence", "死者岛田颈部有细小的血痕抓伤，假发上检出他的血迹；凶器始终搜不到，因为就是她头上的长假发。", "Wiki Resolution：Ran says there were small bloody scratches on the dead Shimoda's neck…droplets of his blood in the wig。"),
            ("resolution", "晃子摘下假发认罪，说无法原谅背叛甚至杀害学生的教师，也承认自己伤及园子同样有罪；兰情绪崩溃跪抱柯南。暴风雪停后警方抵达。", "Wiki Resolution 末段。"),
        ],
    },
    "case-kidnapping-location": {
        "src": "src-detective-conan-world-kidnapping-location-case",
        "fields": [
            ("culprit", "Tomidokoro（富所），被绑架女孩准子的父亲所租住大楼的受害者家属", "Wiki People：Tomidokoro — Junko's kidnapper。"),
            ("motive", "他被租户（准子之父）的疏忽害死了幼女：大楼施工期间屋顶门锁损坏达一周无人修理，孩子从屋顶坠落身亡，而对方获判无罪，他无法接受遂行报复。", "Wiki Resolution：caused by his negligence…Since Junko's father was acquitted, he couldn't stand it and decided to take revenge。"),
            ("method", "绑架并捆绑准子，把她带到附近大楼的露台；用对讲机遥控指示准子之父行动，最后要求他自刎，否则杀死准子。", "Wiki Resolution：forced Junko's dad to do his bidding via walkie-talkie…wanted the other man to stab himself。"),
            ("evidence", "光彦的新无线电收音机截获了犯人与被害者家属的通话，据此锁定位置。", "Wiki Case Situation：radio transceiver intercepts a kidnap case；Resolution 由柯南与少年侦探团破局。"),
            ("resolution", "柯南把对讲机踢到犯人脸上将其击昏，救出准子并用对讲机告知其父，阻止了自杀；柯南因此错过兰的空手道比赛，还因谎称看到背踢取胜被兰识破。", "Wiki Resolution 末段。"),
        ],
    },
}


def main() -> None:
    raw = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    candidates = raw["candidates"] if isinstance(raw, dict) else raw
    existing = {c.get("candidateId") for c in candidates}

    added = 0
    for case_id, spec in SPECS.items():
        for field, value, note in spec["fields"]:
            cid = f"cand-{BATCH}-{case_id}-{field}"
            if cid in existing:
                continue
            candidates.append(
                {
                    "candidateId": cid,
                    "targetId": case_id,
                    "field": field,
                    "value": value,
                    "sourceRefs": [spec["src"]],
                    "confidence": "high",
                    "reviewStatus": "accepted",
                    "reviewNote": note,
                }
            )
            added += 1

    if isinstance(raw, dict):
        raw["candidates"] = candidates
        payload = raw
    else:
        payload = candidates
    CANDIDATES.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"added={added} total={len(candidates)}")


if __name__ == "__main__":
    main()
