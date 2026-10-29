#!/usr/bin/env python3
"""从 DCW 页面 Resolution 段抽取 L3 候选（culprit / motive / method / evidence / resolution）。

只做两件事：
  1) 用严格句式匹配识别 culprit（'The culprit is X.' / 'The culprits are X and Y.'）
  2) 把 Resolution 原文按语义子标题切块（Evidence / Translation changes / ...）

不生成任何原文没有的句子。所有产出写入候选层 data/candidates/dcw-l3.json，
不直接改案件实体——需人工/审核脚本确认后才 apply。

confidence 规则：
  high   —— 'The culprit is X.' 句式明确，且 X 能在 People 段找到同名
  medium —— 句式明确但 People 段没匹配到
  low    —— 只有 'culprit' 关键词，无明确句式（不产出 culprit 值）
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOCKS = ROOT / "data" / "raw" / "dcw-page-blocks.json"
OUT = ROOT / "data" / "candidates" / "dcw-l3.json"

TODAY = "2026-10-27"
SRC = "src-detective-conan-world-anime"

CULPRIT_PATTERNS = [
    # "The culprit is X." / "The culprits are X and Y."
    re.compile(r"^\s*The culprits?\s+(?:is|are|was|were)\s+(.+?)(?:\.\s|\.$|$)", re.I),
    # "it is revealed the culprit (X) took ..." / "revealed that the culprit was X"
    re.compile(r"culprit\s*\(([^()]{2,60})\)", re.I),
    re.compile(r"culprits?\s+(?:is|was|are|were)\s+(?:revealed to be\s+)?([A-Z][^.,;]{1,55})", re.I),
    # "The culprit's face revealed, Yasuo Murakami."
    re.compile(r"culprit'?s?\s+(?:face|identity)\s+(?:is\s+)?revealed[^,]*,\s*([A-Z][^.,;]{1,55})", re.I),
    # "X is the culprit" / "X was the culprit behind"
    re.compile(r"^([A-Z][^.,;]{1,55}?)\s+(?:is|was)\s+the\s+culprit", re.I),
    # "revealed to be X" 但没有 culprit 词时不可靠，不用
]

# 这些措辞说明页面没有给出唯一凶手，必须放弃，绝不猜
NO_UNIQUE_CULPRIT = re.compile(
    r"many (?:people|of them) had a motive|several suspects|"
    r"each (?:had|has) a motive|the culprit is unknown|no single culprit",
    re.I,
)


def looks_like_name(raw: str) -> bool:
    """只有明显是人名的值才接受。

    拒绝：man and woman / arrested / due to the fact that / not Sako /
          one that bought the potted flower
    """
    if not raw or len(raw) < 3 or len(raw) > 45:
        return False
    low = raw.lower()
    if low.startswith(("that", "this", "it ", "not ", "one ", "none", "due ", "able ", "trying ")):
        if low.startswith("none other than "):
            return True
        return False
    # 抽象/动作词直接毙
    if re.match(r"^(man|woman|men|women|person|people|police|arrested|body|none)\b", low):
        return False
    words = raw.split()
    if len(words) > 5:
        return False
    caps = sum(1 for w in words if w[:1].isupper())
    # 至少 2 个首字母大写的词，或单词但长度 >=4 且首字母大写
    if len(words) == 1:
        return caps == 1 and len(words[0]) >= 4 and words[0].isalpha()
    return caps >= max(2, len(words) - 1)


def find_culprit(body: list[str]) -> tuple[str | None, str | None]:
    """返回 (名字, 命中的原句)。找不到唯一凶手时返回 (None, None)。"""
    for ln in body:
        if NO_UNIQUE_CULPRIT.search(ln):
            return None, None
    for pat in CULPRIT_PATTERNS:
        for ln in body:
            m = pat.search(ln)
            if not m:
                continue
            raw = m.group(1).strip().strip(".").strip()
            raw = re.sub(r"^(?:the|a|an|none other than)\s+", "", raw, flags=re.I)
            raw = re.split(r",\s*(?:who|whose|and)\b|\s+who\b|\s+whose\b", raw)[0].strip()
            raw = re.sub(r"\s*\(.*?\)", "", raw).strip()
            if looks_like_name(raw):
                return raw, ln
    return None, None
STOP_SUB = {
    "Evidence", "Translation changes", "Anime", "Manga", "Trivia", "Notes",
    "References", "Gallery", "Music", "Staff", "Voice cast", "BGM listing",
    "In other languages", "See also",
}


def norm(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())


NOISE = {"Show spoilers »", "Show spoilers", "Contents"}

EVIDENCE_RE = re.compile(
    r"\b(proof|prove[sd]?|evidence|fingerprints?|footprints?|traces?|"
    r"found|discovered|revealed|left behind|weapon)\b",
    re.I,
)

MOTIVE_RE = re.compile(
    r"\b(because|since|in order to|so that|revenge|avenge|insurance|inheritance|"
    r"blackmail|jealous|cheated|affair|debt|money|inherit|hatred|grudge|"
    r"cover up|silence|protect)\b",
    re.I,
)

METHOD_RE = re.compile(
    r"\b(trick|tricked|using|used|switched|set up|disguise[ds]?|fake[ds]?|"
    r"staged|made it (?:look|appear|seem)|pretend\w*|poison\w*|strangl\w*|"
    r"stab\w*|hung|hanged|locked|rigged|planted|tamper\w*|swapp?ed|"
    r"alibi|time ?delay|remote|device)\b",
    re.I,
)


def split_sentences(text: str) -> list[str]:
    """按句号/问号/叹号切句，保留完整句子（只切分，不改写任何词）。"""
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(])", text)
    out = []
    for p in parts:
        p = p.strip()
        if len(p) < 25:
            continue
        if p in NOISE:
            continue
        out.append(p)
    return out


def split_subheads(lines: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    cur = "body"
    out[cur] = []
    for ln in lines:
        if ln in STOP_SUB:
            cur = ln
            out.setdefault(cur, [])
            continue
        out[cur].append(ln)
    return out


def main() -> None:
    data = json.loads(BLOCKS.read_text(encoding="utf-8"))
    pages = data["pages"]

    candidates = []
    stats = {"pages": 0, "withResolution": 0, "culpritHigh": 0, "culpritMedium": 0,
             "withEvidence": 0, "withMethod": 0, "withMotive": 0}

    for page, blocks in sorted(pages.items()):
        stats["pages"] += 1
        res = blocks.get("Resolution") or []
        if not res:
            continue
        stats["withResolution"] += 1
        people = blocks.get("People") or []
        people_norm = {norm(p) for p in people}
        sub = split_subheads(res)
        body = [x for x in sub.get("body", []) if x != "Show spoilers »"]

        # ---- culprit ----
        culprit_name, culprit_src = find_culprit(body)

        if culprit_name:
            hit = norm(culprit_name) in people_norm
            conf = "high" if hit else "medium"
            stats["culpritHigh" if hit else "culpritMedium"] += 1
            candidates.append({
                "candidateId": f"dcw-l3-{page}-culprit",
                "targetId": None,
                "dcwPage": page,
                "field": "culprit",
                "value": culprit_name,
                "sourceRefs": [SRC],
                "sourceBlock": "Resolution",
                "quote": (culprit_src or "")[:600],
                "confidence": conf,
                "reviewStatus": "pending",
                "reviewNote": "自动抽取自 DCW Resolution 段 'The culprit is X.' 句式",
                "extractedAt": TODAY,
            })

        # ---- evidence ----
        ev = [x for x in sub.get("Evidence", []) if len(x) > 40]
        ev_source = "Resolution/Evidence"
        if not ev:
            # 多数页面没有独立 Evidence 子标题，证据句散落在 Resolution 正文里。
            # 只取含明确证据词汇的原句，不改写。
            ev_sents = [s for s in split_sentences(" ".join(body)) if EVIDENCE_RE.search(s)]
            ev = ev_sents[:4]
            ev_source = "Resolution/evidence-sentence"
        if ev:
            stats["withEvidence"] += 1
            candidates.append({
                "candidateId": f"dcw-l3-{page}-evidence",
                "targetId": None,
                "dcwPage": page,
                "field": "evidence",
                "value": " ".join(ev)[:2000],
                "sourceRefs": [SRC],
                "sourceBlock": ev_source,
                "quote": ev[0][:600],
                "confidence": "medium",
                "reviewStatus": "pending",
                "reviewNote": "原文证据句/证据段，未改写，需人工确认",
                "extractedAt": TODAY,
            })

        # ---- method / motive：按句切分，只保留命中关键词的原句（不改写）----
        if body:
            joined = " ".join(body)
            sents = split_sentences(joined)

            motive_sents = [s for s in sents if MOTIVE_RE.search(s)]
            if motive_sents:
                stats["withMotive"] += 1
                candidates.append({
                    "candidateId": f"dcw-l3-{page}-motive",
                    "targetId": None,
                    "dcwPage": page,
                    "field": "motive",
                    "value": " ".join(motive_sents)[:2000],
                    "sourceRefs": [SRC],
                    "sourceBlock": "Resolution",
                    "quote": motive_sents[0][:600],
                    "sentenceCount": len(motive_sents),
                    "confidence": "medium",
                    "reviewStatus": "pending",
                    "reviewNote": "原文含动机连词的原句集合，未改写，需人工确认是否即动机全貌",
                    "extractedAt": TODAY,
                })

            method_sents = [s for s in sents if METHOD_RE.search(s)]
            if method_sents:
                stats["withMethod"] += 1
                candidates.append({
                    "candidateId": f"dcw-l3-{page}-method",
                    "targetId": None,
                    "dcwPage": page,
                    "field": "method",
                    "value": " ".join(method_sents)[:2000],
                    "sourceRefs": [SRC],
                    "sourceBlock": "Resolution",
                    "quote": method_sents[0][:600],
                    "sentenceCount": len(method_sents),
                    "confidence": "medium",
                    "reviewStatus": "pending",
                    "reviewNote": "原文含手动词汇的原句集合，未改写，需人工确认完整性",
                    "extractedAt": TODAY,
                })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {"version": 1, "stats": stats, "candidateCount": len(candidates),
             "candidates": candidates},
            ensure_ascii=False, indent=1,
        ) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(stats, ensure_ascii=False))
    print(f"candidates={len(candidates)} -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
