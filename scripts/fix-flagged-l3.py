#!/usr/bin/env python3
"""修复 19 条「字段语义错位」的 L3 字段（旧切块脚本把句子分错格）。

两种处置：
    assign  —— 从案件自身原文里截取**逐字原句**，重新指派给正确字段，并译成中文
    absent  —— 原文确实没有该内容，删除该字段（不留空壳、不编造），
               在 case.l3Absent 里留痕

安全约束：
    * new_en 必须是对案件原文的**逐字切片**（start/end 锚点定位），否则整条中止
    * 旧值保留在 field.replacedEn，可回滚
    * 幂等：二次运行零改动

用法：
    python3 scripts/fix-flagged-l3.py [--dry-run]
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "data" / "entities" / "cases.json"
FLAGGED = ROOT / "docs" / "translations" / "flagged.json"
FIELDS = ("culprit", "motive", "method", "evidence", "resolution")
NOTE = "按 DCW 原文原句重新指派（原值系切块错位，旧值存于 replacedEn）"

# 逐字截取区间 + 中文译文
ASSIGN = [
    {
        "caseId": "case-underwater-key-in-the-locked-room-case",
        "source": "resolution",
        "field": "method",
        "start": "After locking the front door",
        "end": "he was able to create a locked room.",
        "zhHans": "锁上大门后，他把钥匙绑在一只甲虫身上——绳子是用纸巾搓成的——从信箱口放了下去。"
                  "他在大门的地砖上铺了一件毛衣，让甲虫走起来更容易。他在模型顶部涂上能吸引雄性甲虫的气味，"
                  "用来给它引路。甲虫走过桥时，钥匙掉进模型的护城河里，纸巾绳也化开了，钥匙就留在那儿。"
                  "之后甲虫被窗外的光吸引，从窗户飞了出去。就这样，他做出了一个密室。",
    },
    {
        "caseId": "case-the-revival-of-the-dying-message",
        "source": "evidence",
        "field": "motive",
        "start": "When confronted with this proof",
        "end": "while cleaning his gun).",
        "zhHans": "面对这个证据，凶手供认：她杀死千寻，是因为千寻与成田交往后又狠心把他甩了，"
                  "逼得他自杀（其他朋友只以为他是在擦枪时出了意外）。",
    },
    {
        "caseId": "case-kaitou-kid-and-the-four-masterpieces",
        "source": "resolution",
        "field": "evidence",
        "start": "Conan reveals that when the police broke into the room",
        "end": "a person jumped out the window.",
        "zhHans": "柯南指出，警方破门进入房间时，那根系着石头的钓鱼线被拉到了窗外，"
                  "制造出有人跳窗而逃的假象。",
    },
    {
        "caseId": "case-cactus-capriccio",
        "source": "motive",
        "field": "motive",
        "start": "When Yashiro found out he was hiring a housekeeper",
        "end": "determined to avenge her father.",
        "zhHans": "Yashiro 得知他要雇女佣后，下定决心为父亲报仇。",
    },
    {
        "caseId": "case-froth-steam-and-smoke",
        "source": "resolution",
        "field": "motive",
        "start": "He killed Daisaku Katsumoto",
        "end": "if the lawsuit wasn't dropped.",
        "zhHans": "他杀死 Daisaku Katsumoto，是因为对方刊登的一篇假报道害得报道中的那位女演员自杀。"
                  "Keisuke 厌恶 Katsumoto 对受害者的漠视，也厌恶社长只是为了销量才这么做、玷污了他全心投入的公司。"
                  "他也无法忍受那位女演员——他的老同学——可能至死都以为是他故意把照片放进那篇假报道。"
                  "当社长威胁说若不撤诉就再写一篇误导性报道时，他在盛怒之下杀了他。",
    },
    {
        "caseId": "case-dancing-demon-at-the-noh-mask-mansion",
        "source": "resolution",
        "field": "motive",
        "start": "Hatsuho annoyingly confesses",
        "end": "as well as the entire museum itself.",
        "zhHans": "Hatsuho 愤愤地供认，她恨 Moyono——她以 Jisaburou 情人的身份过着奢华日子，"
                  "而自己和母亲却要受苦；恨 Akaza——他试图引诱她；也恨 Jisaburou 本人——"
                  "他暗中变卖她父亲的能面，连同整座博物馆一起卖掉。",
    },
    {
        "caseId": "case-bathroom-where-ran-collapsed-as-well",
        "source": "resolution",
        "field": "method",
        "start": "He killed Waka 30 minutes before",
        "end": "which was found by the police.",
        "zhHans": "他在小兰进入房间前 30 分钟就杀了 Waka，用毛巾裹住她的头、给她戴上口罩，"
                  "然后在浴室里散播氯仿。几天前，他还设法让 Rumi 在一只瓶子上留下指纹——"
                  "那只瓶子看上去就是装氯仿的瓶子，后来被警方找到。",
    },
]

# 原文确实没有的内容：删字段，留痕
ABSENT = [
    ("case-the-final-screening-murder-case", "motive", "原文只叙述不在场证明的制造过程，未给出动机"),
    ("case-underwater-key-in-the-locked-room-case", "motive", "原文只叙述甲虫运钥匙的手法，未给出动机"),
    ("case-english-teacher-vs-great-western-detective", "motive", "原文只有 Takai 虐待下属致其自杀的背景，未给出凶手动机"),
    ("case-english-teacher-vs-great-western-detective", "evidence", "原文未给出该案物证"),
    ("case-find-the-buttock-s-mark", "motive", "原文只叙述推理与锁芯证据，未给出动机"),
    ("case-the-hot-chocolate-trap", "method", "原文只给出动机与照片证据，未描述作案手法"),
    ("case-nagasaki-mystery-theatre", "culprit", "原文为误导性陈述（指控 Ran Mouri 后随即否认），沿用 L3-CULPRIT-REJECTED 裁定"),
    ("case-nagasaki-mystery-theatre", "motive", "原文只叙述死亡讯息解读与推理过程，未给出动机"),
    ("case-nagasaki-mystery-theatre", "method", "原文只叙述柯南的固定套路（电击表/变声领结），未给出凶手手法"),
    ("case-cactus-capriccio", "evidence", "原文未给出物证（该字段原句实为动机，已移入 motive）"),
    ("case-the-framed-great-detective", "motive", "原文未给出 Himuro 杀害 Numao 的动机"),
    ("case-jodie-s-memories-and-the-cherry-blossom-viewing-trap", "evidence", "原文未给出该案物证（只揭示角色身份）"),
]


def sha(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def corpus_of(case: dict) -> dict:
    """按字段拆开的原文语料。截取只在单一字段内进行，避免跨字段吞段。"""
    out = {}
    for field in FIELDS:
        value = case.get(field)
        if isinstance(value, dict) and value.get("en"):
            out[field] = value["en"]
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cases = json.loads(CASES.read_text(encoding="utf-8"))
    by_id = {case["id"]: case for case in cases}
    corpus = {case["id"]: corpus_of(case) for case in cases}

    assigned, removed, skipped, errors = [], [], [], []

    for item in ASSIGN:
        case = by_id.get(item["caseId"])
        if case is None:
            errors.append(f"{item['caseId']}: 案件不存在")
            continue
        text = corpus[item["caseId"]].get(item.get("source", item["field"]), "")
        if not text:
            errors.append(f"{item['caseId']}/{item['field']}: 来源字段 {item.get('source')} 无原文")
            continue
        start = text.find(item["start"])
        end = text.find(item["end"], start)
        if start < 0 or end < 0:
            errors.append(f"{item['caseId']}/{item['field']}: 锚点未命中（start={start}, end={end}）")
            continue
        new_en = text[start:end + len(item["end"])].strip()
        if len(new_en) < 30:
            errors.append(f"{item['caseId']}/{item['field']}: 截取过短 {len(new_en)}")
            continue
        if len(new_en) > 900:
            errors.append(f"{item['caseId']}/{item['field']}: 截取过长 {len(new_en)}（锚点跨段，需收窄）")
            continue
        current = case.get(item["field"])
        if not isinstance(current, dict):
            current = {}
        if current.get("en") == new_en and current.get("zhHans") == item["zhHans"]:
            skipped.append(f"{item['caseId']}/{item['field']}")
            continue
        if current.get("en") and current.get("en") != new_en:
            current["replacedEn"] = current["en"]
        current["en"] = new_en
        current["zhHans"] = item["zhHans"]
        current["translationStatus"] = "machine"
        current["translationSourceHash"] = sha(new_en)
        current["translationNote"] = NOTE
        case[item["field"]] = current
        assigned.append(f"{item['caseId']}/{item['field']}")

    for case_id, field, reason in ABSENT:
        case = by_id.get(case_id)
        if case is None:
            errors.append(f"{case_id}: 案件不存在")
            continue
        trail = case.setdefault("l3Absent", [])
        if field not in case:
            if not any(row.get("field") == field for row in trail):
                trail.append({"field": field, "reason": reason})
            skipped.append(f"{case_id}/{field}")
            continue
        case.pop(field)
        if not any(row.get("field") == field for row in trail):
            trail.append({"field": field, "reason": reason})
        removed.append(f"{case_id}/{field}")

    # 顺带修一处译名：Akabeko 是赤べこ（乡土玩具），不是「赤福牛」
    akabeko = 0
    for case in cases:
        for field in FIELDS:
            value = case.get(field)
            if isinstance(value, dict) and "赤福牛" in (value.get("zhHans") or ""):
                value["zhHans"] = value["zhHans"].replace("赤福牛", "Akabeko")
                akabeko += 1

    print(f"重新指派 {len(assigned)} | 删除字段 {len(removed)} | 已是最新 {len(skipped)} | 错误 {len(errors)}")
    print(f"Akabeko 译名修正 {akabeko} 处")
    for row in assigned:
        print("  ASSIGN", row)
    for row in removed:
        print("  REMOVE", row)
    for row in errors:
        print("  ERROR ", row)

    if errors:
        print("有错误，未写入")
        return

    if args.dry_run:
        print("(dry-run，未写入)")
        return

    CASES.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")

    # flagged.json 转为审计台账
    data = json.loads(FLAGGED.read_text(encoding="utf-8"))
    fixed = {(i["caseId"], i["field"]) for i in ASSIGN} | {(c, f) for c, f, _ in ABSENT}
    for row in data.get("items", []):
        if (row["caseId"], row["field"]) in fixed:
            row["status"] = "resolved-2026-10-28"
    data["policy"] = ("以下字段曾因英文原文与字段语义不符而不译；2026-10-28 已逐条处置："
                      "能对上原文的按原句重新指派并翻译（status=resolved），原文没有的已删除字段并留痕于 case.l3Absent")
    FLAGGED.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已写入 cases.json 与 flagged.json")


if __name__ == "__main__":
    main()
