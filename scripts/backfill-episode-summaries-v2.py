#!/usr/bin/env python3
"""用 DCW 页面正文（按章节锚点抽取的原文段落）补齐空缺的剧集 summary。

背景（隐患修复）：
    546 集 summary 为空，原判断是"页面无 Situation 段"。实测是
    `extract-dcw-page-blocks.py` 的标题切块缺陷导致 Situation/Part N 段落被丢弃或污染。
    `extract-dcw-page-sections.py` 按 id 锚点重新抽取后，681 页有可用正文。

规则（铁律）：
    - 只搬英文原文，**不翻译、不总结、不推断**；zhHans/zhHant 保持空字符串等人工。
    - 只填空值：已有 summary 的剧集一律不动（幂等，重跑零改动）。
    - 多集同页时按集在页面内的顺序取对应 Part N（第 1 集→Part 1，第 2 集→Part 2…），
      缺该 Part 时回退 Situation → Part 1。
    - 段落不足 80 字符或缺失 → 记入 blocked 清单，不硬填。

输出：
    data/episodes/episodes.json（就地补 summary）
    docs/SUMMARY-BACKFILL-REPORT.json（统计 + 每集来源 + blocked 清单）
"""
from __future__ import annotations

import json
import re
import shutil
import collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPISODES = ROOT / "data" / "episodes" / "episodes.json"
SECTIONS = ROOT / "data" / "raw" / "dcw-page-sections.json"
FACTS = ROOT / "data" / "raw" / "dcw-page-facts.json"
REPORT = ROOT / "docs" / "SUMMARY-BACKFILL-REPORT.json"
BACKUP = Path("/tmp/ca/episodes_pre_summary_v2.json")

MAX_CHARS = 1500
MIN_CHARS = 80
MIN_SHORT_CHARS = 25   # 原文本身就短（如两集一页的第二集结论）时接受的下限
SOURCE_ID = "src-detective-conan-world-anime"

# Situation 段首常是结构化元数据行（Location: / Victim: / Age: ...），不能当 summary 开头
META_LINE = re.compile(
    r"^(Location|Victim|Age|Time|Cause of death|Suspects?|Suspect|Weapon|Culprit|Criminals?"
    r"|Police|Detective|People|Case|Case Type|Death|Motive|Method|Evidence|Result|Injured"
    r"|Hostage|Stolen|Robbers?|Characters|Note|Notes)\s*:",
    re.I,
)
NEEDS_REPAIR = re.compile(
    r"^(?:Location|Victim|Victims|Age|Time|Cause of death|Suspects?|Culprits?|Criminals?"
    r"|Weapon|Hostage|Stolen|Robbers?|Police|Detective|Motive|Method|Evidence|Result"
    r"|Death|Injured|Case Type)\s*:"
)
ONE_WORD = re.compile(r"^[A-Z][a-z]*( ?[A-Z][a-z]*)?$")


def is_content(para: str) -> bool:
    """判断是否叙述性正文（排除页面结构化元数据行/单词标签）。

    注意：这里**不**做长度限制——原文本身可能只有一句话（两集一页的第二集常见），
    长度门槛由 MIN_CHARS / MIN_SHORT_CHARS 在汇总后统一把关。
    """
    if META_LINE.match(para):
        return False
    if ONE_WORD.match(para.strip()):
        return False
    return True


def pick_section(secs: dict, page_index: int, ep_count: int) -> tuple[str | None, list[str]]:
    """按集在页面内的序号挑章节。"""
    if ep_count > 1:
        key = f"part{page_index + 1}"
        if secs.get(key):
            return key, secs[key]
    for key in ("situation", "story", "part1", "part2", "part3", "part4"):
        if secs.get(key):
            return key, secs[key]
    return None, []


def join_paragraphs(paras: list[str]) -> str:
    """跳过元数据行，取叙述段落，累计到 MAX_CHARS 附近为止。"""
    out: list[str] = []
    total = 0
    for p in paras:
        if not is_content(p):
            continue
        if total and total + len(p) > MAX_CHARS:
            break
        out.append(p)
        total += len(p) + 1
        if total >= MAX_CHARS:
            break
    return " ".join(out).strip()


def main() -> None:
    eps = json.loads(EPISODES.read_text(encoding="utf-8"))
    secs_all = json.loads(SECTIONS.read_text(encoding="utf-8"))["pages"]
    facts = json.loads(FACTS.read_text(encoding="utf-8"))["pages"]

    ep2page: dict[int, list[str]] = collections.defaultdict(list)
    page2eps: dict[str, list[int]] = collections.defaultdict(list)
    for p in facts:
        for n in p["episodeNumbers"] or []:
            ep2page[n].append(p["page"])
            page2eps[p["page"]].append(n)
    for v in page2eps.values():
        v.sort()

    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    if not BACKUP.exists():
        shutil.copy2(EPISODES, BACKUP)

    filled: list[dict] = []
    blocked: list[dict] = []
    repair: list[dict] = []

    for e in eps:
        existing = e.get("summary")
        if isinstance(existing, dict):
            en_now = existing.get("en") or ""
            if en_now and not NEEDS_REPAIR.match(en_now):
                continue          # 已有干净英文原文 → 不动
            if en_now:
                repair.append({"episode": e["id"], "number": e.get("number")})
            target = existing     # 旧人工中文字段保留，只补 en
        elif existing:
            continue              # 非预期结构（字符串旧值），保守跳过
        else:
            target = None

        if target is None:
            target = {"en": "", "zhHans": "", "zhHant": ""}
        num = e.get("number")
        pages = ep2page.get(num) or []
        if not pages:
            blocked.append({"episode": e["id"], "number": num, "reason": "no_dcw_page"})
            continue

        chosen = None
        fallback = None
        for pg in pages:
            secs = secs_all.get(pg) or {}
            page_eps = page2eps.get(pg) or [num]
            idx = page_eps.index(num) if num in page_eps else 0
            key, paras = pick_section(secs, idx, len(page_eps))
            text = join_paragraphs(paras)
            if not key or not text:
                continue
            if len(text) >= MIN_CHARS:
                chosen = (pg, key, text, False)
                break
            # 原文本身就这么短（常见于两集一页的第二集）——保留为兜底，不丢弃
            if len(text) >= MIN_SHORT_CHARS and fallback is None:
                fallback = (pg, key, text, True)
        if chosen is None:
            chosen = fallback

        if not chosen:
            if target.get("en"):
                continue  # 修复失败但原有英文还在 —— 保留，不丢数据
            blocked.append(
                {
                    "episode": e["id"],
                    "number": num,
                    "pages": pages,
                    "reason": "no_story_text_or_too_short",
                }
            )
            continue

        pg, key, text, is_short = chosen
        target["en"] = text
        target.setdefault("zhHans", "")
        target.setdefault("zhHant", "")
        target["sourcePage"] = pg
        target["sourceQuote"] = True
        e["summary"] = target
        srcs = e.get("sources") or []
        if SOURCE_ID not in srcs:
            srcs.append(SOURCE_ID)
            e["sources"] = srcs
        filled.append(
            {
                "episode": e["id"],
                "number": num,
                "page": pg,
                "section": key,
                "chars": len(text),
                "shortFromSource": is_short,
                "hadZhOnly": "legacy" in target or bool(target.get("zhHans")),
            }
        )

    EPISODES.write_text(json.dumps(eps, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    total = len(eps)
    with_en = sum(1 for e in eps if isinstance(e.get("summary"), dict) and e["summary"].get("en"))
    cumulative = [
        {
            "episode": e["id"],
            "number": e.get("number"),
            "page": e["summary"].get("sourcePage"),
            "chars": len(e["summary"].get("en") or ""),
        }
        for e in eps
        if isinstance(e.get("summary"), dict)
        and e["summary"].get("sourcePage")
    ]
    report = {
        "generatedBy": "scripts/backfill-episode-summaries-v2.py",
        "source": "data/raw/dcw-page-sections.json (id-anchored <p>/<li>/<dd>/div text from cached DCW pages)",
        "policy": "英文原文搬运，不翻译不总结；只填空值；zhHans/zhHant 留空等人工",
        "totalEpisodes": total,
        "filledThisRun": len(filled),
        "repairedMetadataPrefix": len(repair),
        "filledCumulative": len(cumulative),
        "blockedThisRun": len(blocked),
        "withEnSummaryAfter": with_en,
        "withoutEnSummaryAfter": total - with_en,
        "filled": filled,
        "cumulativeFilled": cumulative,
        "blocked": blocked,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if not isinstance(v, list)}, ensure_ascii=False))
    print(f"wrote {EPISODES.relative_to(ROOT)} / {REPORT.relative_to(ROOT)}")
    if blocked:
        sample = collections.Counter(b["reason"] for b in blocked)
        print("blocked reasons:", dict(sample))


if __name__ == "__main__":
    main()
