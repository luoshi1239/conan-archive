# 2026-10-28 · YTV 官方日文简介补 5 集 summary

接上一轮的英文标题补全，继续处理 `docs/HANDOFF-NEW-SESSION.md` §3 的第 3 条：
「5 集 summary 仍空：713/714/882/1061/1187 —— 页面该集段落只有案件信息表或无正文，
需其他来源，不得按相邻集推断。」

---

## 0. 结论先说

**YTV 没有 `solvedBy` 字段。** 那一轮想顺手补 60 集 `solvedBy` 的设想落空了，
不能靠它补，也不能从剧情文字反推——那就是编造。YTV 真正的价值是
**1217 集的官方日文剧情简介**，正好补这 5 集。

结果：**summary 从 1212/1217 → 1217/1217，零空缺。**

---

## 1. 数据源：読売テレビ（YTV）官方站点

《名侦探柯南》的播出电视台。站点 `https://www.ytv.co.jp/conan/` 是 Vue 3 + axios
单页应用，历史各话不在 HTML 里，走静态 JSON：

```
GET https://www.ytv.co.jp/conan/data/case.json   → 4,347,732 字节，1426 条记录
```

接口线索来自 `js/vue/top.js`：

```js
jsonPaths: {
  news_tops: "data/news.json",
  news_pickups: "data/news_pickups.json",
  next_stories: "data/caseTop.json"
}
```

试过 `cases.json` / `caseList.json` / `story.json` / `archive.json` / `backnumber.json`
/ `library.json` / `episode.json` —— 全部 404。只有 `case.json` 是全集。

单条记录的关键字段（挂在 `data` 下）：

| 字段 | 含义 | 覆盖 |
|---|---|---|
| `conan_story` | 官方日文剧情简介 | 1217 集 |
| `title` | 日文标题 | 1217 集 |
| `episode` | 集号（含 `R##` 重播形态） | 1218 个集号 |
| `onair_date` | 播出日期 | 仅 73 集 |
| `conan_next_hint_text` | 下集提示 | 少量 |

登记为来源 `src-yomiuri-tv-conan`（`scripts/add-ytv-source.py`，幂等）。
`data/sources.json` 由 72 → **73 条**。

---

## 2. 踩到的坑：`R##` 重播记录会冒充正片

第一次统计时按「同集号取第一条」，结果 EP.2 的剧情读出来 1789 字符，
而正片实际只有 150 字符。

原因：1426 条记录里有 **101 条 `R##` 前缀的重播/数字重制版**，
`R02`、`R71`、`R72` 等按字符串排序都排在正片前面（`R` ASCII 大于数字），
而且重制版的剧情是**改写过的长文**，不是原集内容。

抽样对照：

| 集 | 正片 | `R##` 重播 |
|---|---|---|
| EP.2 | 150 字符 | 1789 字符 |
| EP.71 | 148 字符 | 1199 字符 |
| EP.345 | 910 字符 | 0 字符 |

修正：凡 `episode` 以 `R` 开头一律跳过。修正后 **正片 1218 个集号 / 重播 101 条**，
剧情长度中位 667、最短 100、最长 2792 —— 分布正常。

这个错误在写盘之前就抓到了，没有污染数据。

---

## 3. 补 summary

### 为什么不覆盖 en / zhHans

5 集的 `summary` 原本是 `null`（不是空对象），所以写入不涉及覆盖。
但为了不让人误以为是中文正文，日文原文只写进 `summary.ja`：

```json
{
  "ja": "原因不明の爆発でトンネルが崩れ…",
  "en": "",
  "zhHans": "",
  "zhHant": "",
  "sourcePage": "src-yomiuri-tv-conan",
  "sourceQuote": true
}
```

`en` 留空而不是填日文——`textOf()` 的回落顺序是
`zhHans → zhHant → ja → en`，`ja` 自然会命中，不需要 `en` 兜底。

### 写入结果

`scripts/backfill-episode-summaries-from-ytv.py`

| 集 | 标题 | 字符 |
|---|---|---|
| EP.713 | 服部平次と吸血鬼館（二） | 1058 |
| EP.714 | 服部平次と吸血鬼館（三） | 973 |
| EP.882 | さざ波の魔法使い（後編） | 1057 |
| EP.1061 | 警察学校編 Wild Police Story CASE. 諸伏景光 | 490 |
| EP.1187 | エピソード“ZERO”工藤新一水族館事件 | 220 |

原文段落间的全角空格保留，只把换行去掉（`re.sub(r"[\r\n]+", "", story)`），
避免前端渲染时出现无谓的段落断裂。

二次运行：`补 summary.ja：0 集 / 跳过 5 集（已有 summary）` —— 幂等。

---

## 4. 前端：日文也要标注

`app.js` 的 `labelOf()` 原本只给 `en` 加「（英文原文·待译）」角标，
日文回落到界面上会是一段没有任何说明的日文，用户不知道它是什么。

```js
function labelOf(value) {
  const text = textOf(value);
  if (!text) return '';
  const lang = langOf(value);
  if (lang === 'en') return `${text}（英文原文·待译）`;
  if (lang === 'ja') return `${text}（日文原文·待译）`;   // ← 新增
  return text;
}
```

渲染实测：

```
ja 原文 5 集 / en 原文 1076 集 / 中文 136 集 / 空 0
EP.713 → …た…。（日文原文·待译）
```

---

## 5. 顺手修掉一个链上的格式撕裂

跑幂等检查时 `episodes.json` 出现 DIFF，但 JSON 语义完全相同 —— 是**字节层面**的差异。

查出来是 `scripts/link-character-cases.py` 用 `indent=1` 重写
`episodes.json` / `cases.json` / `characters.json`，而链上前面的
`backfill-episode-structure.py` 用的是 `indent=2`。两个脚本互相打架，
谁后跑谁说了算，导致每次快照比对都 DIFF。

全库约定是 `indent=2`，把 `link-character-cases.py` 的 3 处数据写入
+ 1 处报告写入统一改成 2。

修复后：

```
SAME  episodes/episodes.json
SAME  entities/characters.json
SAME  entities/cases.json
SAME  raw/dcw-page-facts.json
```

---

## 6. 没有做的事，以及为什么

**没有补 `solvedBy`（60 集仍空）。**

| 缺口类型 | 集数 | 说明 |
|---|---|---|
| 原文就是 `null` | 52 | 多集特别篇合并页没有这个字段 |
| 原文写 `No one` / `N/A` | 4 | 原文本就说没有个人破案者 |
| 有名字但库里无角色实体 | 4 | `Ryohei Onda`×2、`Heihachiro Shiota`、`Detective Boys` |

DCW 的 Anime 总表**不含破案者字段**，YTV 的 `case.json` **也不含**。
YTV 的剧情简介里虽然写了「コナンと平次は…見破る」，但那是叙述，
把它读成 `solvedBy = Conan Edogawa` 属于推断，不是搬原文。

按「不编造」的铁律，这 60 集保持原样。

**没有改 `title.ja`。**

拿 YTV 的 `title` 与库内逐一比对，118 条「实质不同」，但看下来全是排版差异：

```
库: 6 月の花嫁殺人事件      YTV: ６月の花嫁殺人事件     （半角/全角数字）
库: 闇の男爵殺人事件        YTV: 闇の男爵(ﾅｲﾄﾊﾞﾛﾝ)殺人事件  （多了读音）
库: 空飛ぶ密室 工藤新一最初の事件（1 時間スペシャル）  YTV: 同左，无时长标注
```

库内的半角数字加空格是既有的规范化风格（人工翻译也遵循），不是错误。不动。

---

## 7. 最终状态

```
剧集 1217
  summary 有值   1217  ← 本轮 1212 → 1217
    .en          1212
    .ja             5  （新增，全部带 YTV 来源标注）
    zhHans/zhHant 136 / 0
  title.en       1217
  title.ja       1217
  solvedBy       1157  （60 集仍空，见 §6）

来源 73（新增 src-yomiuri-tv-conan）
冲突 5 条：resolved 5 / open 0
```

验证：

```
VALIDATION_OK
CHAIN_IDEMPOTENT_OK（episodes / characters / cases / page-facts 四文件逐字节一致）
APP_JS_OK / EN_TITLES_OK / P3_OK / NAV_KINDS_OK / UI_P4_OK
```

---

## 8. 回滚

```bash
# 撤销 summary.ja 回填
cp /tmp/eps_pre_ytv_summary.json data/episodes/episodes.json

# 撤销来源登记
cp /tmp/sources_pre_ytv.json data/sources.json

# 撤销前端日文标注（app.js 中删除 labelOf 的 ja 分支即可）

# 撤销 indent 修复（不推荐，会重新引入链上 DIFF）
```

---

## 9. 脚本索引（新增）

| 脚本 | 用途 |
|---|---|
| **`add-ytv-source.py`** | 幂等登记 `src-yomiuri-tv-conan` 来源 |
| **`backfill-episode-summaries-from-ytv.py`** | 用 YTV 官方日文补 5 集 `summary.ja`；跳过 `R##` 重播；`--dry-run` |
