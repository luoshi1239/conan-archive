#!/usr/bin/env python3
"""按 HTML 章节锚点抽取 DCW 页面正文段落（替代标题文字切块的做法）。

## 为什么需要这个脚本（已修复的隐患）

`extract-dcw-page-blocks.py` 用「标题文字出现位置之间的内容」切块，有三个缺陷：

1. **TOC 污染**：页面目录里也有 "Situation" 字样，其后紧跟目录编号 `3.1`/`3.1.1`，
   于是 `blocks["Situation"] = ["3.1.1"]` —— 全库 536 页是这样。
2. **正文被吞**：正文 h3 `Situation` 后面紧跟 h4 `Part 1`，两标题相邻 → Situation 正文
   长度 0 被丢弃；真正的剧情在 Part 1/2/3 里，而这些块又从 TOC 起切，混进了 BGM 歌曲表。
3. **老版页面漏抓**：老版 MediaWiki 把锚点放在标题内层 `<span class="mw-headline" id="X">`，
   只看 `<hN id=...>` 会整段漏掉；而正文常在 `<div id="toggledisplay1">` 里以裸文本存在
   （不是 `<p>`），只取 `<p>` 同样漏。

## 做法

- 以 `<h1>~<h6>`（含内层带 id 的 span）为章节边界，按锚点 id 或标题文字匹配章节；
- 章节内的正文按块级标签切行（p/li/dd/dt/div/br/tr），裸文本也能取到；
- 丢弃目录残留（纯编号行）、`[edit]`、`Show spoilers »`、纯图片 alt 等噪声行；
- 只搬原文，不总结、不翻译、不推断（铁律）。

输出 `data/raw/dcw-page-sections.json`：
    {"stats": {...}, "pages": {page: {"situation": [para...], "part1": [...], "resolution": [...]}}}
"""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "data" / "raw" / "dcw-pages"
OUT = ROOT / "data" / "raw" / "dcw-page-sections.json"

MIN_HTML = 20_000
HEAD_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
SKIP_TAGS = {"script", "style", "noscript", "table", "figure", "sup"}
VOID_TAGS = {"img", "br", "hr", "input", "meta", "link", "source", "wbr", "area", "col", "embed"}
# 块级标签：遇到就切行（裸文本 div 也能成段）
BREAK_TAGS = {"p", "li", "dd", "dt", "div", "br", "tr", "td", "th", "ul", "ol", "dl"}

SECTION_IDS = {
    "Situation": "situation",
    "Part_1": "part1",
    "Part_2": "part2",
    "Part_3": "part3",
    "Part_4": "part4",
    "Resolution": "resolution",
    "People": "people",
    "Story": "story",
}
SECTION_TITLES = {
    "Situation": "situation",
    "Part 1": "part1",
    "Part 2": "part2",
    "Part 3": "part3",
    "Part 4": "part4",
    "Resolution": "resolution",
    "People": "people",
    "Story": "story",
}
# 任何标题都会结束当前章节（避免把 Trivia/Gallery 混进 Resolution）
ANY_HEADING = set(SECTION_TITLES) | {
    "Case", "Trivia", "Gallery", "Music", "Staff", "Voice cast", "Notes",
    "References", "See also", "In other languages", "BGM listing", "Quotes",
    "Anime", "Manga", "Plot", "Summary", "Characters", "Gadgets", "Episodes",
}

TOC_LINE = re.compile(r"^\d+(\.\d+)*$")
# 短行多半是噪声（"8"、"#"），但 DCW 的 Resolution 块会用 Evidence / Conclusion / Motive
# 这类小标题给段落分组——它们是**结构信息**，丢了就无法按字段精确切分。
LABEL_LINE = re.compile(r"^[A-Z][A-Za-z]{2,24}(?: [A-Z][A-Za-z]{1,24})?$")

# DCW 有些页面把结构化元数据与正文粘在同一段裸文本里，例如：
#   "Location: 100 Series Shinkansen Victim: Everyone on the train Culprits: Ueda and Shimoda Conan and Ran ..."
# 按 "Key:" 把这类粘连段拆开，让元数据行与正文各自成段（后续可按需过滤）。
META_KEYS = (
    "Location", "Victim", "Victims", "Age", "Time", "Cause of death", "Suspects",
    "Suspect", "Culprit", "Culprits", "Criminal", "Criminals", "Weapon", "Hostage",
    "Stolen", "Robber", "Robbers", "Police", "Detective", "Motive", "Method",
    "Evidence", "Result", "Death", "Injured", "Case Type", "See also",
)
SPLIT_META = re.compile(
    r"(?<=[\.\!\?\)\]0-9])\s+(?=(?:" + "|".join(re.escape(k) for k in META_KEYS) + r")\s*:)"
)
NOISE = re.compile(
    r"^(Show spoilers »|Hide spoilers|« Hide spoilers|Show spoilers)\s*$"
    r"|^\[\s*(edit|source)\s*\]$"
    r"|^#+$|^Toggle .*subsection$",
    re.I,
)


class SectionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cur: str | None = None
        self.out: dict[str, list[str]] = {}
        self.skip_depth = 0
        self.heading_depth = 0
        self.heading_id: str | None = None
        self.heading_text: list[str] = []
        self.buf: list[str] = []
        self.heading_level = 0
        self.situation_level = 0
        self.situation_parts = 0
        self.in_situation = False

    # ---------- 内部工具 ----------
    def flush(self) -> None:
        text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
        self.buf = []
        if not text or not self.cur:
            return
        keep_short = bool(LABEL_LINE.match(text))   # Evidence / Conclusion / Motive 等分组小标题
        if len(text) < 15 and not keep_short:
            return
        if TOC_LINE.match(text) or NOISE.search(text):
            return
        paras = self.out.setdefault(self.cur, [])
        for part in SPLIT_META.split(text):
            part = part.strip()
            if not part or len(part) < 2:
                continue
            if TOC_LINE.match(part) or NOISE.search(part):
                continue
            if paras and paras[-1].lower() == part.lower():
                continue
            paras.append(part)

    def close_heading(self) -> None:
        text = re.sub(r"\s+", " ", "".join(self.heading_text)).strip()
        self.heading_depth = 0
        key = SECTION_IDS.get(self.heading_id or "") or SECTION_TITLES.get(text)

        # Situation 之下的子章节（如 "Negotiation Chapter"/"Pursuit Chapter"/"Desperation Chapter"，
        # 或没有 id 的 "Part 1"）按出现顺序映射成 part1/part2/part3，供多集一页的剧集各取一段。
        if key == "situation":
            self.in_situation = True
            self.situation_level = self.heading_level
            self.situation_parts = 0
        elif key is None and self.in_situation and self.heading_level > self.situation_level:
            self.situation_parts += 1
            if self.situation_parts <= 4:
                key = f"part{self.situation_parts}"
        else:
            self.in_situation = False

        self.cur = key
        if key:
            self.out.setdefault(key, [])
        self.heading_text = []
        self.heading_id = None

    # ---------- 事件 ----------
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in VOID_TAGS:
            if tag == "br":
                self.flush()
            return
        if tag in SKIP_TAGS:
            self.skip_depth += 1
            return
        if tag in HEAD_TAGS:
            if self.heading_depth:
                self.close_heading()
            self.heading_depth = 1
            self.heading_level = int(tag[1])
            self.heading_id = a.get("id")
            self.heading_text = []
            self.flush()
            return
        if self.heading_depth:
            # 老版页面：<h3><span class="mw-headline" id="Situation">
            if a.get("id") and not self.heading_id:
                self.heading_id = a.get("id")
            return
        if tag in BREAK_TAGS:
            self.flush()

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS:
            if self.skip_depth:
                self.skip_depth -= 1
            return
        if tag in HEAD_TAGS and self.heading_depth:
            self.close_heading()
            return
        if tag in BREAK_TAGS:
            self.flush()

    def handle_data(self, data):
        if self.skip_depth:
            return
        if self.heading_depth:
            self.heading_text.append(data)
            return
        if self.cur:
            self.buf.append(data)


def extract(html: str) -> dict[str, list[str]]:
    p = SectionParser()
    p.feed(html)
    p.flush()
    return {k: v for k, v in p.out.items() if v}


def main() -> None:
    pages: dict[str, dict[str, list[str]]] = {}
    stats = {
        "scanned": 0,
        "skippedSmall": 0,
        "withSituation": 0,
        "withPart1": 0,
        "withPart2": 0,
        "withResolution": 0,
        "storyText": 0,
        "noText": 0,
    }
    for f in sorted(PAGES.glob("*.html")):
        html = f.read_text(encoding="utf-8", errors="replace")
        if len(html) < MIN_HTML:
            stats["skippedSmall"] += 1
            continue
        stats["scanned"] += 1
        secs = extract(html)
        pages[f.stem] = secs
        for key, stat in (
            ("situation", "withSituation"),
            ("part1", "withPart1"),
            ("part2", "withPart2"),
            ("resolution", "withResolution"),
        ):
            if secs.get(key):
                stats[stat] += 1
        if secs.get("situation") or secs.get("part1"):
            stats["storyText"] += 1
        if not secs:
            stats["noText"] += 1

    OUT.write_text(
        json.dumps({"stats": stats, "pages": pages}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(stats, ensure_ascii=False))
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
