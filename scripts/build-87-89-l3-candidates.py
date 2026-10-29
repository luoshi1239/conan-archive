#!/usr/bin/env python3
"""Build sourced L3 candidates for EP.87-89 cases (crane 87, dracula 88-89)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data" / "candidates" / "entities.json"
BATCH = "ep-87-89-l3"

SPECS = {
    "case-crane-return-murder": {
        "src": "src-detective-conan-world-crane-return-case",
        "fields": [
            ("culprit", "町田保（Tamotsu Machida），死者之弟，画家", "Wiki Resolution：revealed the real culprit who is Tamotsu Machida。"),
            ("motive", "他长期靠兄长接济，得知兄长要把全部财产捐给濒危鸟类保护后，为继承遗产而杀兄并嫁祸侄子博。", "Wiki Resolution：mooching off Shuzo for money…decided to kill him and frame Hiroshi to inherit his wealth。"),
            ("method", "在壁炉烟囱内架好弩，用橡皮筋固定一块木片卡住扳机，木片与钓鱼线相连；等博朝标本鸟发射十字弓的同时拉动钓鱼线触发弩箭射死秀三，再用钓鱼线把弩从烟囱里拉出。", "Wiki Resolution：bowgun in the chimney…wood behind trigger…rubberband…fishing wire…pulled the bowgun out。"),
            ("evidence", "准备替换破窗的玻璃上有一道划痕，来自博射出的十字弓；碎玻璃整齐排列说明被超弹性镜面挡住；烟囱内有钓鱼线留下的直线状空隙；他后裤袋里有一根来自烟囱顶鸟巢的羽毛。", "Wiki Resolution：scratch on replacement glass…Super elastic mirror…void in chimney…bird feather in his back pocket。"),
            ("resolution", "柯南借小五郎之口推翻博的误杀自白，指认真凶町田保；秀三的两名子女最终决定按其遗愿把遗产捐给濒危鸟类。", "Wiki Resolution 末段。"),
        ],
    },
    "case-dracula-villa-murder": {
        "src": "src-detective-conan-world-dracula-villa-case",
        "fields": [
            ("culprit", "田所俊哉（Toshiya Tadokoro），死者弟子兼实际代笔人", "Wiki Resolution：the actual culprit: Toshiya Tadokoro。"),
            ("motive", "妹妹香织患肾衰竭，寅仓以负担医疗费为条件让他做「影子写手」；寅仓却买通医生只维持不治愈以延长合作，最终香织一年前病亡，且长期谎称她仍在美洲住院。护士愧疚告知真相后他崩溃报仇。", "Wiki Resolution：bribed the Tokyo doctor…keep her merely stable…caused young Kaori's death。"),
            ("method", "屋顶雪面未留脚印，因为他把梯子架在相邻屋顶之间跨过去；留声机胶片卷轴既营造恐怖气氛，又靠胶片一端系门实现离开后自动关门、且不留下指纹；事先在酒窖藏一支同样的木桩，解决无法从密室取走凶器的问题。", "Wiki Resolution：ladder from one roof to the other…film strip tied to the door…duplicate stake in the cellar。"),
            ("evidence", "他声称在房内听到胶片卷轴的转动声，但该房间做了隔音处理，这一点只有真凶才说得出来；此外密室的门是靠胶片自动关上。", "Wiki Resolution：impossible as the door was soundproofed。"),
            ("resolution", "柯南识破胶片与屋顶梯子的机关，指出只有田所能说出「听到卷轴声」这一点，田所认罪。", "Wiki Resolution 末段。"),
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
            candidates.append({
                "candidateId": cid, "targetId": case_id, "field": field, "value": value,
                "sourceRefs": [spec["src"]], "confidence": "high",
                "reviewStatus": "accepted", "reviewNote": note,
            })
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
