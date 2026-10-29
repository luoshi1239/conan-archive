#!/usr/bin/env python3
"""从已缓存的 DCW 页面提取结构化事实，输出 data/raw/dcw-page-facts.json。

只提取页面上明确写出的字段，不做任何推断。

infobox 实际排版（已逐行核对）：
    Episode 65                      <- 单集
    (Int. Episode 67)
    Episode 374-375                 <- 多集范围
    (Int. Episode 405-406)
    ...
    Case                            <- 注意：Case / Cast: 分成两行
    Cast:
    Conan Edogawa
    ...
    Case solved by:
    Manga source:
    Volume 45: File 9 (466) ~       <- 可能跨两行
    Volume 46: File 1 (469)
"""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "data" / "raw" / "dcw-pages"
OUT = ROOT / "data" / "raw" / "dcw-page-facts.json"

SKIP_TAGS = {"script", "style", "noscript"}
BLOCK_TAGS = {"p", "li", "tr", "div", "br", "h1", "h2", "h3", "td", "th"}

# 这些标签出现即代表上一个字段结束
STOP_LABELS = (
    "Case solved by", "Next Conan's Hint", "Staff", "Voice cast", "Music",
    "Cast", "Characters", "Gadgets", "Case", "Situation", "People",
    "Resolution", "Trivia", "BGM listing", "Gallery", "In other languages",
    "See also", "Director", "Screenplay", "Storyboard", "Season", "Title",
    "Japanese title", "Original airdate", "Broadcast rating", "Manga case",
    "Manga source", "English version", "Filler case number", "Opening song",
    "Closing song", "Information", "Chronology",
)


class TextOf(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self.skip += 1
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS:
            if self.skip:
                self.skip -= 1
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def to_lines(html: str) -> list[str]:
    p = TextOf()
    p.feed(html)
    out = []
    for ln in "".join(p.parts).splitlines():
        ln = re.sub(r"[ \t\u00a0]+", " ", ln).strip()
        if ln:
            out.append(ln)
    return out


def _label_match(ln: str, label: str) -> str | None:
    """'Manga source: xxx' -> 'xxx'；不含该标签 -> None。"""
    if ln == label or ln == label + ":":
        return ""
    if ln.startswith(label + ":"):
        return ln[len(label) + 1:].strip()
    return None


def field(lines: list[str], label: str, max_follow: int = 3) -> str | None:
    """取标签后的值；值为空则向后取最多 max_follow 行（用于跨行字段）。"""
    for i, ln in enumerate(lines):
        v = _label_match(ln, label)
        if v is None:
            continue
        if v:
            return v
        chunks: list[str] = []
        for j in range(i + 1, min(i + 1 + max_follow, len(lines))):
            nxt = lines[j]
            if any(_label_match(nxt, s) is not None for s in STOP_LABELS):
                break
            chunks.append(nxt)
        return " ".join(chunks) if chunks else None
    return None


def field_block(lines: list[str], label: str, max_lines: int = 12) -> list[str]:
    """取标签后连续多行（用于 Manga source / Cast 这种列表）。"""
    for i, ln in enumerate(lines):
        v = _label_match(ln, label)
        if v is None:
            continue
        out: list[str] = []
        if v:
            out.append(v)
        for j in range(i + 1, min(i + 1 + max_lines, len(lines))):
            nxt = lines[j]
            if any(_label_match(nxt, s) is not None for s in STOP_LABELS):
                break
            if re.match(r"^\d{1,4}$", nxt) or nxt.endswith(":"):
                break
            out.append(nxt)
        return out
    return []


def parse_episode_no(lines: list[str]) -> tuple[list[int], int | None]:
    """解析 infobox 声明的集号。

    实测排版三种：
        Episode 65                          -> [65]
        Episode 374-375                     -> [374, 375]
        Episode 830-832                     -> [830, 831, 832]
        Episode 184
        (Int. Episode 198-199)              -> 日文 [184] / 海外 198
    关键：必须先定位「第一个 Episode」，不能在全文中泛搜范围，否则会把
    (Int. Episode 198-199) 误当成日文集号。
    """
    window = lines[:160]
    text = "\n".join(window)

    jp: list[int] = []
    ints: int | None = None

    # 先切掉 Int. 段，避免海外集号污染日文集号判定
    m_int = re.search(r"Int\.?\s*Episode\s*(\d{1,4})", text)
    if m_int:
        ints = int(m_int.group(1))

    first = re.search(r"Episode\s*(\d{1,4})(?:\s*-\s*(\d{1,4}))?", text)
    if first:
        a = int(first.group(1))
        b = first.group(2)
        if b is not None:
            bb = int(b)
            if a <= bb and bb - a < 20:
                jp = list(range(a, bb + 1))
            else:
                jp = [a]
        else:
            jp = [a]
    return jp[:20], ints


def parse_manga_files(raw: str | None) -> list[int]:
    """'Volume 45: File 9 (466) ~ Volume 46: File 1 (469)' -> [466,469]"""
    if not raw:
        return []
    out: list[int] = []
    for a, b in re.findall(r"\((\d{1,4})\s*-\s*(\d{1,4})\)", raw):
        a, b = int(a), int(b)
        if a <= b and b - a < 40:
            out.extend(range(a, b + 1))
    for one in re.findall(r"\((\d{1,4})\)", raw):
        out.append(int(one))
    seen, uniq = set(), []
    for n in out:
        if n not in seen:
            seen.add(n)
            uniq.append(n)
    return sorted(uniq)


def parse_cast(lines: list[str]) -> list[str]:
    """'Case' 下一行 'Cast:'，再往下每行一个名字，直到 'Case solved by:'。"""
    for i, ln in enumerate(lines):
        if ln not in ("Case", "Case:"):
            continue
        if i + 1 >= len(lines):
            continue
        nxt = lines[i + 1]
        if _label_match(nxt, "Cast") is None:
            continue
        # 同行内联值
        cast: list[str] = []
        inline = _label_match(nxt, "Cast") or ""
        if inline:
            cast.extend(x.strip() for x in inline.split("/") if x.strip())
        for j in range(i + 2, min(i + 40, len(lines))):
            v = lines[j]
            if v.startswith("Case solved by") or v.startswith("Next Conan"):
                break
            if v.endswith(":"):
                break
            if re.match(r"^\d{1,4}$", v):
                break
            cast.append(v)
        return cast
    return []


def extract(path: Path) -> dict:
    html = path.read_text(encoding="utf-8", errors="replace")
    lines = to_lines(html)
    cats = sorted(
        {c.replace("_", " ") for c in re.findall(r'href="/wiki/Category:([^"#]+)"', html)}
    )
    m = re.search(r'<h1[^>]*id="firstHeading"[^>]*>(.*?)</h1>', html, re.S)
    heading = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else None

    ep_numbers, int_from_infobox = parse_episode_no(lines)

    jp_raw = field(lines, "Japanese title")
    japanese_ep = None
    jp = jp_raw
    if jp_raw:
        mj = re.search(r"Episode\s*(\d{1,4})", jp_raw)
        if mj:
            japanese_ep = int(mj.group(1))
        jp = re.split(r"\s*\(\s*Episode", jp_raw)[0].strip() or None

    int_ep = int_from_infobox
    if int_ep is None:
        for ln in lines[:160]:
            m3 = re.search(r"Int\.?\s*Episode\s*(\d{1,4})", ln)
            if m3:
                int_ep = int(m3.group(1))
                break

    manga_lines = field_block(lines, "Manga source", max_lines=6)
    manga_raw = " ".join(manga_lines) if manga_lines else None

    return {
        "page": path.stem,
        "heading": heading,
        "jpTitle": jp,
        "japaneseEpNo": japanese_ep,
        "episodeNumbers": ep_numbers,
        "intEpisode": int_ep,
        "airdate": field(lines, "Original airdate", max_follow=1),
        "mangaSource": manga_raw,
        "mangaFiles": parse_manga_files(manga_raw),
        "isAnimeExclusive": any(c.lower() == "anime exclusive" for c in cats),
        "caseCast": parse_cast(lines),
        "solvedBy": field(lines, "Case solved by", max_follow=1),
        "mangaCaseNumber": field(lines, "Manga case", max_follow=1),
        "fillerCaseNumber": field(lines, "Filler case number", max_follow=1),
        "season": field(lines, "Season", max_follow=1),
        "categories": cats,
        "hasInfobox": "infobox" in html,
    }


def main() -> None:
    facts = [extract(f) for f in sorted(PAGES.glob("*.html"))]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "version": 3,
                "generatedFrom": "data/raw/dcw-pages",
                "pageCount": len(facts),
                "missingInfobox": sum(1 for f in facts if not f["hasInfobox"]),
                "pages": facts,
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"pages={len(facts)} "
        f"withEpisodeNo={sum(1 for f in facts if f['episodeNumbers'])} "
        f"withCast={sum(1 for f in facts if f['caseCast'])} "
        f"withMangaFiles={sum(1 for f in facts if f['mangaFiles'])} "
        f"noMangaSource={sum(1 for f in facts if not f['mangaSource'])}"
    )
    print(f"animeExclusive={sum(1 for f in facts if f['isAnimeExclusive'])}")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
