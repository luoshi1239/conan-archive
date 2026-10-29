#!/usr/bin/env python3
"""用読売テレビ官方日文剧情简介，补 DCW 正文缺失的 5 集 summary。

背景
----
DCW 的案件页对 EP.713 / 714 / 882 / 1061 / 1187 只有信息表、没有正文段落，
因此这 5 集的 `summary` 一直是 null。其他 1212 集都有英文正文。

読売テレビ是《名侦探柯南》的播出电视台，其官网 `data/case.json` 提供
1217 集的官方日文剧情简介（字段 `conan_story`）。这是 DCW 之外的第二个
官方来源，用来补齐这 5 集。

写入规则
--------
- 只处理 `summary` 为 null 的集，已有正文的一律不动（不覆盖原则）。
- 日文原文写入 `summary.ja`；`en` / `zhHans` / `zhHant` 一律不动，
  留作后续翻译，不伪造英文或中文。
- `summary.sourcePage` 记来源 id，`summary.sourceQuote` 标记为原文直引。
- 跳过 `R` 前缀的重播记录（101 条，剧情是重制版改写，不等于原集）。

幂等：目标集 summary 非 null 即跳过。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPS = ROOT / "data/episodes/episodes.json"
YTV = Path("/tmp/ytv_case.json")

SOURCE_ID = "src-yomiuri-tv-conan"
DRY = "--dry-run" in sys.argv

TARGET = [713, 714, 882, 1061, 1187]


def load_ytv() -> dict:
    """读 YTV 记录，只保留正片（跳过 R 前缀重播）。"""
    rows = json.loads(YTV.read_text(encoding="utf-8"))
    out = {}
    for r in rows:
        raw = str((r.get("data") or {}).get("episode") or "").strip()
        if not raw or raw.upper().startswith("R"):
            continue
        m = re.match(r"^(\d+)", raw)
        if not m:
            continue
        n = int(m.group(1))
        if n in out:
            print(f"  警告：EP.{n} 正片记录重复，保留首条")
            continue
        out[n] = r["data"]
    return out


def main() -> int:
    eps = json.loads(EPS.read_text(encoding="utf-8"))
    index = {e["number"]: e for e in eps}
    ytv = load_ytv()

    filled, skipped, missing = [], [], []
    for n in TARGET:
        e = index.get(n)
        if e is None:
            missing.append((n, "库中无此集"))
            continue
        if e.get("summary"):
            skipped.append((n, "已有 summary"))
            continue
        d = ytv.get(n)
        if not d:
            missing.append((n, "YTV 无正片记录"))
            continue
        story = (d.get("conan_story") or "").strip()
        if not story:
            missing.append((n, "YTV conan_story 为空"))
            continue

        # 内部换行统一成空格（原文用全角空格分段，保留全角空格）
        story = re.sub(r"[\r\n]+", "", story)

        e["summary"] = {
            "ja": story,
            "en": "",
            "zhHans": "",
            "zhHant": "",
            "sourcePage": SOURCE_ID,
            "sourceQuote": True,
        }
        filled.append((n, len(story), d.get("title")))

    if filled and not DRY:
        EPS.write_text(json.dumps(eps, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    tag = "（dry-run，未写盘）" if DRY else ""
    print(f"补 summary.ja：{len(filled)} 集{tag}")
    for n, ln, t in filled:
        print(f"  EP.{n}  {ln:4d} 字符  {t}")
    if skipped:
        print(f"跳过 {len(skipped)} 集：")
        for n, why in skipped:
            print(f"  EP.{n}  {why}")
    if missing:
        print(f"无法处理 {len(missing)} 集：")
        for n, why in missing:
            print(f"  EP.{n}  {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
