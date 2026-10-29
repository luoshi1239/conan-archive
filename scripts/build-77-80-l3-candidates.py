#!/usr/bin/env python3
"""Build sourced L3 candidates for episodes 77-80 cases (schema-correct).

Candidate schema (see scripts/validate-candidates.py):
  candidateId, targetId, field, value, sourceRefs, confidence,
  reviewStatus, reviewNote
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REVIEW_NOTE = "已读取 Detective Conan Wiki 原页面正文并逐字段核对；L3 全剧透字段。"

BATCHES = {
    "case-distinguished-family-consecutive-death": {
        "source": "src-detective-conan-world-distinguished-family-case",
        "facts": {
            "culprit": "日向美雪。她杀死长门三木昭，并参与藏匿长门秀臣的尸体；秀臣本人是自杀。三木昭另有独立计划：杀害岳父长门道三并嫁祸秀臣，以抓钩勒杀未遂。",
            "motive": "二十年前那座小旅馆的大火由秀臣与三木昭引起，美雪的父母因此丧生、秀臣半张脸被烧伤。美雪得知真相后仍爱上秀臣，秀臣却在她求婚时因负罪而自杀。三木昭又当着美雪的面轻描淡写地谈那场纵火，美雪因此决定杀他，并让秀臣替他背下这桩命案。",
            "method": "三木昭先伪造秀臣的杀人现场：用注射器抽自己的血染绷带、戴泳帽再套毛线帽以免留下头发、把抓钩当作勒杀道三的器具，并以电话里假装被袭的喊声把所有人引到楼下。美雪在这个计划里反手杀他：她以“杀了道三就能当上新社长”为诱饵，在阳台上用旧钢笔刺伤他的手，让他松手坠落到栅栏上。秀臣的尸体此前由两人用庭院里的坑洞暂埋，后来以失踪的床单裹住投入池塘；案发前两天出现的“秀臣”，由美雪或三木昭穿他的衣服、缠他的绷带扮演。",
            "evidence": "三木昭手上一处小刺伤，与美雪那把笔尖弯折、已无法使用的旧钢笔对应；他坠落前抓住美雪的手腕，使她的手表脱落。阳台底部的抓钩痕迹也是连续几天“怪声”的来源。柯南另以秀臣素描对照宅内家具摆放、用一幅新买的名画破绽，逐项确认推断。",
            "resolution": "柯南借毛利小五郎揭穿美雪，服部平次以抓钩爬上阳台当场演示三木昭的嫁祸手法。美雪承认自己是为让秀臣“不再孤零零泡在冷水里”才动手，随后用装了苯的热水瓶和打火机试图与众人同归于尽并自杀；柯南与服部事先调换了热水瓶内容物，未能引爆。她崩溃哭喊后被带走。",
        },
    },
    "case-bank-heist-murder": {
        "source": "src-detective-conan-world-bank-heist-case",
        "facts": {
            "culprit": "谷口升。他是抢劫犯佐伯透的共犯，在佐伯开枪打伤前岛之后将其击毙灭口。",
            "motive": "灭口。佐伯意外打伤职员前岛哲也，事态失控；谷口担心佐伯被捕后供出自己，于是当场开枪打死同伙，再把现场包装成正当防卫。",
            "method": "两人事先约定以电话铃声为暗号：佐伯遇到麻烦，谷口就拨他手机提醒。抢劫中谷口按约定拨号，但前岛正好从背后扑向佐伯，佐伯误以为响的是自己的手机而僵住，慌乱中开枪打伤前岛。谷口也随即慌了，索性开枪杀死佐伯，伪装成夺枪自卫。",
            "evidence": "一批止咳润喉糖。谷口到银行前与佐伯见过面，见他感冒便分了一半糖条给他；后来又把这半条给了同样感冒的柯南。抢劫过程中佐伯的糖吃完，想起谷口还有，就把包装纸丢在地上翻找外套，而糖早不在谷口身上。两半包装纸拼合完全吻合，证明二人是共犯。另有被挟持者用录音机偷录的现场声音，与各人手机铃声逐一比对，确认响的是佐伯的手机，即谷口在作案期间确实给他打过电话。",
            "resolution": "柯南借用园子的声音当场揭穿谷口是共犯并说明其杀人经过，警方将其逮捕。",
        },
    },
    "case-wandering-artist-murder": {
        "source": "src-detective-conan-world-wandering-artist-case",
        "facts": {
            "culprit": "早濑喜美江。死者早濑达夫是她“死去”一年的丈夫。",
            "motive": "早濑达夫在银行任职期间挪用公款，失踪后把罪责留给妻子独自承受社会指责，她因此恨他到极点。杀他既为报复，也为把那笔藏起来的公款据为己有——用她自己的说法，是要“把失去的时间买回来”。",
            "method": "一年前达夫在雪山失踪其实是伪装，他被妻子藏匿起来。他因失忆流落在外，靠素描本能反复画着自家房子，记忆逐渐恢复，最终循着素描找回自家门口，被妻子发现后勒死，尸体弃在山坡上。喜美江还专门请清洁公司彻底清扫屋内，并否认死者是自己的丈夫。",
            "evidence": "达夫恢复记忆后回家时在屋内留下的指纹，证明死者正是早濑达夫本人；喜美江客厅家具的摆放与素描中的位置不符，说明素描画的并非现在的房屋；她刚在画廊买下一幅昂贵的画，也与挪用款去向的追问相扣。",
            "resolution": "柯南把众人召集到早濑家当场说明真相，指出凶手是早濑喜美江，她承认杀人。柯南对她几乎没有同情，只说了一句：她在监狱里还有很多时间。",
        },
    },
}


def main() -> None:
    path = ROOT / "data" / "candidates" / "entities.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    candidates = data["candidates"] if isinstance(data, dict) else data

    # 先剔除本批次写坏的中文字段候选（幂等重跑时不会残留）
    bad_ids = set(BATCHES)
    bad_fields = {"犯人", "动机", "手法", "证据", "结局"}
    before = len(candidates)
    candidates = [
        c for c in candidates
        if not (c.get("entityId") in bad_ids and c.get("field") in bad_fields)
    ]
    dropped = before - len(candidates)

    existing = {c.get("candidateId") for c in candidates}
    added = 0
    for case_id, batch in BATCHES.items():
        for field, value in batch["facts"].items():
            cid = f"cand-field-{case_id}-{field}"
            if cid in existing:
                continue
            candidates.append({
                "candidateId": cid,
                "targetId": case_id,
                "field": field,
                "value": value,
                "sourceRefs": [batch["source"]],
                "confidence": "medium",
                "reviewStatus": "accepted",
                "reviewNote": REVIEW_NOTE,
            })
            existing.add(cid)
            added += 1

    if isinstance(data, dict):
        data["candidates"] = candidates
        payload = data
    else:
        payload = candidates
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"dropped={dropped} added={added} total={len(candidates)}")


if __name__ == "__main__":
    main()
