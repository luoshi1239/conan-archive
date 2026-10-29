# Conan Archive · 新会话交接单（HANDOFF）

> 生成时间：2026-10-27 22:15（会话结束前最后状态）
> 状态：`VALIDATION_OK` ✅ + 全链路 `IDEMPOTENT_OK` ✅（9 个脚本重跑零改动）
> 新会话接手必读：本文档 + `docs/OPERATION-LOG-2026-10-27.md`（完整执行记录）

---

## 0. 项目定位

`/Users/ls/Desktop/agent/Hermes/conan-archive` —— 纯静态《名侦探柯南》知识库。
用户目标：**补充完整个知识库，全部完成后一次总审核，不一步一推**。
用户偏好：不编造（犯人/动机/手法/证据/结局必须来自原页）→ 只搬原文；隐患必清除；幂等必须验证；重要变更写 md 日志。

## 0.4 最近一次进展（批 3：前端修复 + L3 双语化 + 翻译流水线）

> 用户授权后已完成 P0/P1/P2 基础建设，详见 `docs/OPERATION-LOG-2026-10-27-BATCH3.md`。

- **前端已修好**：`app.js` 新增 `textOf()/labelOf()`（按 `zhHant→zhHans→ja→en` 取词），1212 集 `[object Object]` 归零；案件详情页新增「深度剧透」五个分区（凶手/动机/手法/证据/结局），英文自动标「原文·待译」。
- **L3 双语化**：新增 `migrate-case-l3-bilingual.py`，848 个字段（618 en + 230 zh）迁入 `{zhHans, en, translationStatus}`；`normalize-case-status.py` 与 `validate-data.py` 已适配新结构。
- **翻译流水线**：`build-translation-queue.py` → `dump-translation-batch.py` → `apply-translations.py`，口径见 `docs/TRANSLATION-GLOSSARY.md`。
  - 进度：**中文 836 槽位（machine 606 + human 230）**，待译 0，已收尾。
  - 每条译文带 `translationSourceHash`，英文改动后旧译文会自动作废重入队。
- **可疑字段**：19 条曾因切块错位不译；2026-10-28 已全部处置（7 条按原句重新指派 + 12 条删除并留痕于 `case.l3Absent`）。
- **cron**：`conan-archive L3 翻译批处理`（`7c83c52219de`，每 30 分钟），但 **Hermes gateway 未启动时不触发**。

## 0.5 最近一次进展（P4：角色实体化，2026-10-28）

> 详见 `docs/OPERATION-LOG-2026-10-28-P4-CHARACTERS.md`。

- **角色 14 → 101**：`create-character-entities.py` 把出现 ≥5 案的人物实体化（新建 87 个，
  `kind:"character"` + `name.en` + `caseRefs` + DCW 来源，中文名留空 `pending`）。
- **化名不重复建实体**：安室透/冲矢昴/伤疤赤井/宫野志保/黑羽快斗 5 个别名并入已有角色的 `aliases`。
- **跳过 14 个**：无名路人、庭审角色、泛称、指代不明、剧中虚构（假面超人/哥美拉）。
- **案件↔角色挂接 2507 → 5334**，792/792 案全覆盖；剧集侧不变。
- **修 3 个前端缺陷**：新角色被误判「主线」（补 `kind`）、琴酒等 6 个被误判「组织」
  （`kind` 优先于 `role`）、详情页打印原始 id（新增 `nameOfRef()/refsText()`，角色详情补「出场案件」）。
- **顺手统一缩进**：`normalize-case-status.py` 由 `indent=1` 改 `indent=2`，全链路 md5 才真正稳定
  （此前是格式打架冒充「不幂等」）。
- 验证脚本：`scripts/verify-ui-p4.js`（抽取 `app.js` 真实函数跑真实数据）→ `UI_P4_OK`。

## 0.6 最近一次进展（P3 / P1 / P2 + 特别篇集号 + 冲突收口，2026-10-28）

> 详见 `docs/OPERATION-LOG-2026-10-28-P3-P1-P2.md`。

**P3 · `spoilerNote` 上页面**
- 上批把 7 条被污染的分析文本从 `spoiler`（须为 1/2/3 整数）迁到 `spoilerNote`，但前端没渲染。
  `detailSections()` 新增「收录备注」分区，`scripts/verify-p3-spoilernote.js` → `P3_OK`（7/7）。

**P1 · 剧集 `solvedBy` 解析 574 → 1157**
- 根因不是缺数据：原文 `Kogoro Mouri (via Conan)[1]` 409 集，括号里是「借助谁」。
  剥脚注/括号/`(x2)`，兼容 `(via Conan}` 半全角不配对变体。
- `scripts/resolve-episode-solvedby.py`；原文留 `solvedByRaw`，`No one`/`N/A` 写 `solvedByNote` 不建引用。
- 剩 4 集如实保留：`Ryohei Onda`×2、`Heihachiro Shiota`×1（库中无此角色）、`Detective Boys`×1（群像）。

**P2 · 剧集 castNames 实体化 101 → 147**
- `scripts/create-character-entities-episodes.py`，口径同 P4 但闸门更严：新增排除
  `Unknown child`/`Forensic member`/`FBI Agent 1`/仅姓氏（`Sasaki`/`Nakamichi`…）。
- 新建 46（Minerva Glass 12 集、Suguru Itakura 11、Tsutomu Akai 11…），跳过 37；中文名全部 `pending`。
- 剧集↔角色挂接 +277。

**B · 21 集集号缺口（真因不是缺页面）**
- 188–193 / 425 / 491–504 三页 HTML 都在，是**多集特别篇 infobox 写法不同**致 `episodeNumbers` 抽成 `[]`。
- 原文写法三种：`Episode 188-193 (Int. Episode 203-208)`、`Episode 491-504 (Int. Episode 538-551)`、
  `Episode 425 (Int. Episode 459-463)`（单集号 + 国际集号范围）。
- `scripts/fix-special-page-episode-numbers.py` 补齐，写 `episodeRange`/`intEpisodes`/`factSource`（含原文串）。
- **结果：命中页面 1196 → 1217，`season`/`castNames`/`coverage.structure` 全部 1217/1217（100%）**，
  `detailStatus` reviewed 1217（原 catalog 21）。
- 特别篇页面的 `solvedBy` 原文即 `null`，**不补**——不编造。

**B · 冲突收口**
- `conflict-ep96-two-cases-one-page` → **resolved / keep-split**：两小时特别篇含两案，
  本地按内容拆两实体、`animeRefs` 都声明 EP.96 是正确粒度，不为对齐 DCW 合并页而合并。
- `conflict-kirin-horn-585-overlap` → **保持 open**：三份原文证据自相矛盾
  （页面集号差 2 但 `intEpisode` 差 3；`jpTitle` 拆分指向 585 属 Kirin，`intEpisode` 指向 Kirin 从 586 起；
  本地库按日文标题把 585 挂 Kobayashi）。不裁定，`dataState` 记录现状未改、
  EP.585 的 cast 只取 Kobayashi 页、Kirin 页重叠只进 `dcwExtraPages` 故无污染。
  `dcw-page-facts.json` 原始抽取结果不改。
- `conflict-ushio-chisato-timeframe` 补上缺失的 `status` 字段（此前只有 `resolution`）。

**修一个真错**：P2 首版把来源写成 `src-detective-conan-world-cases`——该 id 在 `sources.json` **不存在**，
被 `validate-data.py` 拦下 43 条。改为 `-characters` + `-anime` 后通过。新增数据前先确认来源 id 真实存在。

## 0.7 最近一次进展（英文标题 + EP.585 裁定 + 海外集号纠错，2026-10-28）

> 详见 `docs/OPERATION-LOG-2026-10-28-EN-TITLES-EP585.md`。

**新数据源**：DCW 剧集总表 `https://www.detectiveconanworld.com/wiki/Anime`，
`scripts/parse-dcw-anime-index.py` → `data/raw/dcw-anime-index.json`（1218 行，
12 个重播行已剔除）。8 列：Jp# / Int# / Episode title / Original broadcast /
English dub broadcast / Plot / Manga source / Next Conan's Hint。

**英文标题 1 → 1217（100%）**：`backfill-episode-titles-from-index.py`。
比对先行——英文标题、播出日期、页面归属**三条零冲突**才动手。清理规则沿用
`zhHans` 既有惯例：去掉 `(1 Hour Special)` 等时长标注，保留 `(Part 1)` 等分段标记。
原文存 `title.enRaw`，来源 `title.enSource`。

**EP.585 裁定（此前 open → resolved）**：归 `Kobayashi-sensei's_Love`，
Kirin 页 `episodeNumbers` `[585,586,587]` → `[586,587]`。
三份原文证据：① 总表逐集列明 585→Kobayashi、586/587→Kirin；
② `intEpisode` 634 vs 637 差 3，Kobayashi 占满 634-636，Kirin 必从 586 起；
③ Kirin 页自身 airdate 写的是 585 的日期与标题，属 infobox 错位。
**本地 caseRefs 原本就对，未改任何归属。**

**EP.1055 `overseasNumber`** `'11、12'` → `1112`（总表与案件页 infobox 均为 1112）。
其余 35 个多值集号与总表 `intNumbers` 逐一核对**全部一致**。

**另一发现**：总表指向 793 页，其中 22 个（覆盖 29 集）不在
`dcw-page-facts.json` 里，都是多集合集页（Courtroom Confrontation I–IV、
Kid vs. Komei/Amuro/Hakuba 等）。**不是数据缺口**——这 29 集 caseRefs /
solvedByRaw / castNames / 案件实体都齐全，只是案件 `sources` 没记到具体 page。

## 0.8 最近一次进展（YTV 官方日文补 5 集 summary，2026-10-28）

> 详见 `docs/OPERATION-LOG-2026-10-28-YTV-SUMMARIES.md`。

**结论先说：YTV 没有 `solvedBy` 字段。** 想补那 60 集破案者的设想落空——
不能靠它补，也不能从剧情叙述反推，那是编造。YTV 真正的价值是
**1217 集的官方日文剧情简介**，正好补 DCW 正文缺失的 5 集。

**新数据源**：読売テレビ（《名侦探柯南》播出电视台）`https://www.ytv.co.jp/conan/`。
站点是 Vue 3 + axios SPA，历史各话不在 HTML 里，走静态 JSON：

```
GET https://www.ytv.co.jp/conan/data/case.json  → 4,347,732 字节，1426 条
```

路径线索来自 `js/vue/top.js` 的 `jsonPaths.next_stories`。
试过 `cases.json` / `caseList.json` / `story.json` / `archive.json` /
`backnumber.json` / `library.json` / `episode.json` —— 全部 404，只有 `case.json` 是全集。

`data` 下关键字段：`conan_story`（日文简介，1217 集）、`title`（1217）、
`episode`（含 `R##` 重播形态）、`onair_date`（仅 73 集）。

**踩到的坑：`R##` 重播记录会冒充正片。** 1426 条里 **101 条 `R##` 前缀**是
重播/数字重制版，按字符串排序排在正片前（`R` > 数字），且剧情是**改写过的长文**：

| 集 | 正片 | `R##` 重播 |
|---|---|---|
| EP.2 | 150 字符 | 1789 字符 |
| EP.71 | 148 字符 | 1199 字符 |
| EP.345 | 910 字符 | 0 字符 |

按「同集号取第一条」会读到重制版内容。**取数必须跳过 `episode` 以 `R` 开头的记录。**
这个错误在写盘前抓到，未污染数据。

**补 summary**：`scripts/backfill-episode-summaries-from-ytv.py`

| 集 | 标题 | 字符 |
|---|---|---|
| EP.713 | 服部平次と吸血鬼館（二） | 1058 |
| EP.714 | 服部平次と吸血鬼館（三） | 973 |
| EP.882 | さざ波の魔法使い（後編） | 1057 |
| EP.1061 | 警察学校編 Wild Police Story CASE. 諸伏景光 | 490 |
| EP.1187 | エピソード“ZERO”工藤新一水族館事件 | 220 |

只写 `summary.ja`，`en`/`zhHans`/`zhHant` 留空——因为 `textOf()` 回落顺序是
`zhHans → zhHant → ja → en`，`ja` 自然命中，不需要 `en` 兜底；也避免让人误以为是中文正文。
`sourcePage` 记 `src-yomiuri-tv-conan`，`sourceQuote: true`。

**来源登记**：`scripts/add-ytv-source.py` → `data/sources.json` 72 → **73 条**。

**前端**：`app.js` 的 `labelOf()` 原本只给 `en` 加「（英文原文·待译）」，
日文会以裸文本出现、用户不知其来源。新增 `ja` 分支加「（日文原文·待译）」。
渲染实测：`ja 5 集 / en 1076 集 / 中文 136 集 / 空 0`。

**顺手修掉链上的格式撕裂**：`link-character-cases.py` 用 `indent=1` 重写
`episodes.json`/`cases.json`/`characters.json`，与链上前面 `backfill-episode-structure.py`
的 `indent=2` 打架，谁后跑谁说了算 → 每次快照比对都 DIFF（语义其实相同）。
统一改为 `indent=2`（3 处数据写入 + 1 处报告写入）。修复后四文件全 `SAME`。

**没有做的事**：

- **60 集 `solvedBy` 仍空**。DCW 总表无破案者字段，YTV `case.json` 也无。
  YTV 简介虽写「コナンと平次は…見破る」，读成 `solvedBy = Conan Edogawa` 属推断，不是搬原文。
  构成：52 集原文 null / 4 集原文 `No one`·`N/A` / 4 集有名字但库里无实体。
- **`title.ja` 未改**。YTV 标题与库内比 118 条「实质不同」，看下来全是排版差异
  （半角/全角数字、多了读音如 `(ﾅｲﾄﾊﾞﾛﾝ)`、少了 `（1 時間スペシャル）` 时长标注）。
  库内半角数字加空格是既有规范化风格，不是错误。

## 0.9 最近一次进展（M1/M2/M3/M4/M5/M7 无人值守批次，2026-10-28 夜）

> 详见 `docs/OPERATION-LOG-2026-10-28-M1-M2-M3-M4-M5-M7.md`、`docs/PLAN-UNATTENDED-2026-10-28.md`。
> 6 个模块 5 个落地（M3/M4/M5/M2/M1）+ 方案外 M7，脚本全部幂等，收官 `VALIDATION_OK`。

| 模块 | 字段 | 改前 → 改后 | 脚本 |
|---|---|---|---|
| M3 | 角色 `episodeRefs` | 0/147 → **147/147** | `backfill-character-episode-refs.py` |
| M4 | 案件 `kind` | 14 条 `动画案件` + 5 条 `None` → **0 脏值** | `normalize-case-kind.py` |
| M5 | 案件 `caseType` | 52 条修正（2 别名 / 25 空 / 25 缺来源标签） | `normalize-case-type.py` |
| M2 | 案件 `sources` | 773 → **792/792** | `backfill-case-sources.py` |
| M1 | 案件 `summary` | 45 → **472/792**（427 条搬 situation 段） | `backfill-case-summaries.py` |
| M7 | 案件 `locations` | 0（键都不存在）→ **401/792**（只取设定段） | `backfill-case-locations.py` |
| M8 | 案件 `victims` / `suspects` | 0 / 0 → **393 案·534 人 / 327 案** | `backfill-case-facts.py` |
| M6 | 剧集 `title.zhHans` / `zhHant` | 1214/1216 → **1217/1217** | `fill-missing-episode-titles-zh.py` |

**必须知道的三个判断**：

1. **M1 不用 `resolution`**。解答段首句直接点名凶手（`"The killer is Akiko Yonehara…"`），
   搬进 `summary` = 列表页泄底。只用 `situation`；320 条只有解答、或两段都无 → **故意留空**，不是待办。
2. **M7 推翻「locations 零源」**。`dcw-page-facts.json` 确实无 location 字段，
   但 `dcw-page-sections.json` 正文有 853 行 `Location:`，覆盖 491 页 —— 当初只探了 facts 没探 sections。
   值命中 `locations.json` 实体名就写实体 id（8 个），否则写原文地点名（737 个），不为泛称造实体。
   `validate-data.py` 已改为双形态判定。
3. **M2 的 `sources` 是 id 字符串数组**，不是 `{page, sourceId}` 对象；19 个案件的专属页面来源
   早在 `sources.json` 里登记好了，只是没被引用。页名反解必须 `urllib.parse.unquote`（3 个页带 `%27`）。

**M7 口径修正（同日二次修订）**：初版 M7 同时读了 `situation`（设定段）和 `resolution`（解答段），
导致 **167 个案件**的地点里混进只出现在解答段的地点（`Shiki Island`、`hospital`、`party hall`…）——
那是「案子后来才揭出来的地点」，放非剧透字段就是泄底。现已改为**只取 `situation`**：
覆盖 491 → **401**，90 个案件因此失去全部地点（原文只在解答段），这是正确取舍。
被剔除的旧值记入 `locationsDropped` 可回溯。

**M8 新增（同日）**：案件 `victims` / `suspects` 从 `situation` 段的 `Victim:/Age:/Cause of death:/Suspects:` 行搬原文。
`victims` 是对象数组 `[{name, age?, causeOfDeath?}]`——年龄和死因**在同一条原文块内配对**，块里没写就是没有。
（初版做成 `victims[]+victimAges[]` 并行数组按下标配对，会有 40 个案件张冠李戴，已废弃。）
`Culprit` 行一律不搬。覆盖：被害者 **393 案 / 534 人**（383 人带年龄、347 人带死因）、嫌疑人 **327 案**。

**M6 剧集中文标题：已补全（同日）。** EP.1077 / EP.1203 由本集已有 `zhHant` 逐字转简（可回验）；
EP.1217 无任何中文源，按日文「背中を押す手」人工自译「推背的手」，**标了 `translationStatus: machine`**。
现在 `zhHans` / `zhHant` 均 **1217/1217**。全库只有这一条是自译。

**前端改动**：`app.js` `detailSections()` 第 338 行，地点渲染由 `refsText()` 改为
`raw.locations.map((x) => nameOfRef(x) || x).join('、')` —— 解析不到的 id 不再被静默丢弃。

## 1. 当前数据快照（2026-10-28 M1-M7 批次后实测）

| 维度 | 数值 |
|---|---|
| 剧集 | **1217**（1216 + EP.1217「背后的手」） |
| 案件实体 | **792** |
| 案件 `kind` 分布 | **anime-original-case 469 / manga-case 320 / organization-case 3**（0 脏值，2026-10-28 M4） |
| 案件 `caseType` | **792/792 非空**，0 脏值（2026-10-28 M5） |
| 案件 `summary` | **472/792**：对象 `{en}` 427（DCW situation 原文）+ 字符串 45（历史人工中文）；320 条原文只有解答段，故意留空 |
| 案件 `locations` | **401/792**（只取 situation 段；实体 id + 原文地点名；被剔除的解答段地点记 `locationsDropped`） |
| 案件 `victims` | **393/792 案，534 人**（383 人带原文年龄、347 人带原文死因，块内配对） |
| 案件 `suspects` | **327/792**（原文整串，不拆名） |
| 案件 `sources` | **792/792**（2026-10-28 M2） |
| 来源 | **73** |
| 剧集→案件覆盖 | **1217/1217**，`RELATION-CLOSURE` total=0 |
| 漫画↔剧集双向 | 0 缺失 / 0 不匹配 |
| 案件 detailStatus | catalog 549 / partial 103 / **deepSpoilers 140** |
| 有 culprit | **242**（nagasaki 误导性陈述已删） |
| L3 五字段齐全 | **140** |
| 剧集 summary | **1217 / 1217（100%）**：en 1212（DCW 原文）+ ja 5（YTV 官方原文，见 §0.8） |
| 剧集 `season` | **1217 / 1217（100%）** |
| 剧集 `castNames` | **1217 / 1217（100%）** |
| 剧集 `coverage.structure` | **1217（100%）** |
| 剧集 `solvedBy` 挂角色 | **1157**（剩 60 集无：52 原文 null / 4 原文 No one/N-A / 4 库中无该角色） |
| 剧集 `title.en` | **1217 / 1217（100%）**（2026-10-28 由 DCW 剧集总表补全） |
| 剧集 `title.ja` | 1217 / 1217 |
| 剧集 `title.zhHans` | **1217 / 1217（100%）**（EP.1077/1203 由繁中转简，EP.1217 自译标 machine） |
| 剧集 `title.zhHant` | **1217 / 1217（100%）**（EP.1217 自译标 machine） |
| 剧集 `airDate` | 1217 / 1217 |
| 剧集 `overseasNumber` | 1217 / 1217（EP.1055 已由 `'11、12'` 纠为 `1112`） |
| 剧集 detailStatus | **reviewed 1217**（原 reviewed 1196 / catalog 21） |
| 剧集有角色 | **1217 / 1217（4398+ 条关系）** |
| 角色实体 | **147**（P4 建 101 + P2 建 43） |
| 案件↔角色挂接 | **5334 条**，792/792 案全覆盖 |
| 实体合计 | **957**（人物 147 / 案件 792 / 组织 4 / 道具 8 / 地点 6） |
| 案件 title 缺失 | **0**（792/792 有 en） |
| DCW 页面缓存 | 793 页（0 失败） |
| DCW 正文抽取 | `data/raw/dcw-page-sections.json`（id 锚点，793/793 有正文） |
| L3 候选 | `data/candidates/dcw-l3.json` 1933 条 |

> ⚠ 已知质量取舍：新增的 319 个 L3 字段（motive/method/evidence/culprit）+ 103 个 resolution
> 是 **DCW 英文原文**，与库内中文正文混排。逐字段出处见案件 `dcwL3Source`。
> 如需中文，需人工翻译；回滚见 `docs/OPERATION-LOG-2026-10-27-BATCH2.md` 第四节。

## 2. 新会话接手步骤（照做即可）

```bash
cd /Users/ls/Desktop/agent/Hermes/conan-archive
python3 scripts/validate-data.py          # 应输出 VALIDATION_OK
python3 scripts/report-relation-closure.py # 应输出 total=0
```

然后按下面优先级继续（详见 `docs/OPERATION-LOG-2026-10-27-BATCH2.md`）。

## 3. 剩余任务（按优先级）

1. **L3 中文化：已完成（2026-10-28 收尾）**。618 个英文槽位全部处置：`machine 606` + `human 230`，
   待译 **0**。19 条语义错位字段已按 DCW 原句重新指派（7 条）或删除并留痕（12 条，
   `case.l3Absent`），详见 `docs/OPERATION-LOG-2026-10-28-L3-B4-B10.md` 第 8 节。
   英文原文日后更新时 `translationSourceHash` 会让旧译文自动作废重入队列。
   453 案非 ready 的四字段候选仍未批。
2. **角色实体化：已完成（2026-10-28，P4）**。角色 14 → **101**（新建 87 个 ≥5 案角色），
   案件↔角色挂接 5334 条、792/792 案覆盖。5 个化名并入已有角色，14 个无名/虚构条目跳过。
   详见 `docs/OPERATION-LOG-2026-10-28-P4-CHARACTERS.md`。
   - 遗留：87 个角色**中文名仍空**（`pending`），需官方译名来源，不自行拼汉字。
   - 遗留：`Detective Boys`（291 案）应建 organization 实体，成员关系需来源。
   - 遗留：<5 案的一次性路人 269 个未实体化（P4 口径有意为之）。
3. ~~**5 集 summary 仍空**：713/714/882/1061/1187~~ → **已补（2026-10-28，见 §0.8）**：
   改用読売テレビ官方 `conan_story` 写入 `summary.ja`，1217/1217 全覆盖。
4. **冲突**（`docs/FACT-CONFLICTS.json`，5 条：**resolved 5 / open 0**）。
   - EP.585 归属：**已裁定 resolved（2026-10-28）**——归 `Kobayashi-sensei's_Love`。
     依据三份原文：① DCW `/wiki/Anime` 剧集总表逐集列明 585→Kobayashi、586/587→Kirin；
     ② `intEpisode` Kobayashi=634 / Kirin=637 差 3 集，583-585 占满 634-636，Kirin 必从 586 起；
     ③ Kirin 页自身 `airdate` 写的是 `August 28, 2010 (Timeless Sakura's Love)`——即 585 的日期与标题，
     证明该页 infobox 从 585 起算属页面自身错位。
     动作：Kirin 页 `episodeNumbers` `[585,586,587]`→`[586,587]`（原值存 `episodeNumbersRaw`），
     清 EP.585 的 `dcwExtraPages`；**本地 caseRefs 原本即正确，未改任何归属**。
     脚本：`scripts/resolve-ep585-attribution.py`。
   - EP.96：**已收口 resolved / keep-split**（2026-10-28）。两小时特别篇含两案，本地拆两实体是正确粒度，
     不为对齐 DCW 合并页而合并。
5. **剧集结构化：已完成（2026-10-28，P4-C）**。`season` / `castNames` / `coverage.structure`
   全部 **1217/1217（100%）**，`solvedBy` 挂角色 **1157**，`detailStatus` reviewed **1217**。
   21 集集号缺口真因是多集特别篇 infobox 写法不同，已由 `fix-special-page-episode-numbers.py` 从原文补齐。
   - 遗留：60 集无 `solvedBy`——其中 **56 集原文即 `null`**（含 21 集特别篇页面），**4 集原文 `No one`/`N/A`**（EP.12/43/795/1089，写 `solvedByNote` 不虚构破案者），**4 集有原文但库中无该角色**（EP.67 `Heihachiro Shiota`、EP.225 `Detective Boys`、EP.661/662 `Ryohei Onda`）。均不补。
   - 遗留：226 个 `castNames` 未收录（最高 `Nakamichi` 21 集），多为仅姓氏/岗位，按口径不建实体。
6. **看门狗**：mimo-flash 无法固定（patch 拒写 config.yaml、hermes CLI 不存在）→ 只能本地进程。
7. **QQ 通知**：无凭证，未实现，不得伪称。
8. **git**：conan-archive 仍未纳入版本控制（需用户确认后提交）。
9. **~~案件正文可补字段~~ → 已完成（2026-10-28 M8）**：`victims`（393 案 / 534 人）+ `suspects`（327 案）
   已从 `situation` 段搬入。`Culprit` 行按口径不搬。
   - 遗留：`Weapon` 行仅 3 处（`Pipe bomb` 等），量太小未单独建字段，原文仍在 raw 里可取。
   - 遗留：`Time` / `Time of death` 行零散出现，未建字段。
10. **~~M6 剧集中文标题 4 处~~ → 已完成（2026-10-28）**：`zhHans`/`zhHant` 均 1217/1217。
    EP.1077/1203 繁中转简；EP.1217「推背的手」为人工自译，标 `translationStatus: machine`。
    日后拿到官方译名应覆盖并把状态改 `human`。

## 4. 已排除的隐患（勿回退）

- `normalize-episodes.py` 曾全量覆盖回填数据（caseRefs 1215→186）→ 已改为 `KEEP_IF_TRUTHY` 逐字段保留 + raw 合并 + 保留 RAW 外记录。
- **`normalize-episodes.py` 曾把 EP.86/113 的 `adaptation` 打回 `anime-original`**（2026-10-27 第二批发现并修复）→ 现加"来源佐证优先"：`dcwMangaKind == manga-special-volume` 且 `dcwMangaSource` 以 `SV` 开头时保留已裁定的 `manga`/`mixed`。
- **`dcw-page-blocks.json` 的 Situation 块是目录残留**（`["3.1.1"]`），Part 块混入 BGM 表 → 新增 `extract-dcw-page-sections.py` 按 id 锚点重抽；勿再用旧块做"页面无正文"的判断。
- **案件字段名 `titles`（复数）**：19 个手写标题写错键名被静默丢弃 → `normalize-case-titles.py` 已合并为 `title`，勿再引入 `titles`。
- `validate-data.py` 曾只查 `sources`，16 实体用 `sourceRefs` 逃检 → 已并查两字段且要求至少一个非空。
- `caseType` 类型分裂（32 list / 16 str）→ 统一 list（792/792）。
- 案件状态不一致（561 None / 5 None / deepSpoilers 标志矛盾）→ normalize-case-status.py 统一三态。
- EP.1217 越界引用 → 已补入剧集库。
- 「Ran Mouri 是 Nagasaki 案凶手」→ **误导性陈述**（原文随即否认），已拒绝写入 `docs/L3-CULPRIT-REJECTED.json`。

## 5. 关键脚本索引（全部幂等，二次运行零改动）

| 脚本 | 作用 |
|---|---|
| `normalize-episodes.py` | 剧集库重建（保留增强字段） |
| `backfill-dcw-manga-source.py` | 漫画来源原文回填 + SV 裁定（EP.86/113） |
| `generate-case-entities-from-dcw.py` | 案件骨架生成（caseType 仅用 Category 白名单） |
| `merge-dcw-facts-into-cases.py` | 旧实体 DCW 元数据合并 |
| `apply-dcw-l3-high.py` / `apply-dcw-l3-cleaned.py` | culprit 写入（high 句式 / medium 人工核对） |
| `normalize-case-status.py` | 案件状态三态统一 |
| `backfill-episode-summaries.py` | summary 搬运（旧字符串→dict，en 598 条） |
| `build-dcw-l3-candidates.py` | L3 候选生成（1933 条，原文引用） |
| `build-l3-review-queue.py` | 审核队列（763 案） |
| **`extract-dcw-page-sections.py`** | **按 id 锚点抽取页面正文（793/793，替代旧切块）** |
| **`backfill-episode-summaries-v2.py`** | **summary 补齐（598→1212，DCW 原文）** |
| **`backfill-case-titles.py`** | **补 17 个案件标题（DCW heading/jpTitle）** |
| **`normalize-case-titles.py`** | **`titles`→`title` 合并（19 个）** |
| **`build-l3-approved.py`** | **生成待批准清单（`--only-ready` 只挑四字段齐全的 111 案）** |
| **`apply-l3-approved.py`** | **按清单写入 L3 字段（绝不覆盖非空）** |
| **`backfill-case-resolution.py`** | **L3 第五字段 resolution（DCW Resolution 原文块）** |
| **`link-character-cases.py`** | **案件↔角色↔剧集关系挂接（精确匹配，只增不删）** |
| **`create-character-entities.py`** | **P4：≥5 案人物实体化（化名并入、无名/虚构跳过，幂等）** |
| **`create-character-entities-episodes.py`** | **P2：≥5 集人物实体化（闸门更严：排除岗位/编号/仅姓氏/身份不明）** |
| **`backfill-episode-structure.py`** | **P4-C：剧集 `season`/`solvedBy`/`solvedByRaw`/`castNames`/角色挂接回填** |
| **`resolve-episode-solvedby.py`** | **P1：`solvedByRaw` 剥括号/脚注/倍数 → 角色实体（574→1157）** |
| **`fix-special-page-episode-numbers.py`** | **B：多集特别篇页面集号补齐（三种原文写法，只补空的）** |
| **`parse-dcw-anime-index.py`** | **解析 DCW `/wiki/Anime` 剧集总表 → `data/raw/dcw-anime-index.json`（1218 行）** |
| **`backfill-episode-titles-from-index.py`** | **英文标题补全（1→1217，写 `title.en`/`enRaw`/`enSource`，只填空）** |
| **`resolve-ep585-attribution.py`** | **EP.585 裁定：Kirin 页集号→[586,587]，清 EP.585 的 `dcwExtraPages`** |
| **`add-ytv-source.py`** | **幂等登记 `src-yomiuri-tv-conan`（YTV 官方站点）到 `sources.json`** |
| **`backfill-episode-summaries-from-ytv.py`** | **YTV 官方日文补 5 集 `summary.ja`（1212→1217）；跳过 `R##` 重播；`--dry-run`** |
| **`verify-en-titles.js`** | **剧集标题验证：每集可取、`title.en` 全覆盖、无 markdown 残留、分段标记保留** |
| **`verify-ui-p4.js`** | **抽取 `app.js` 真实函数 + 真实数据验证前端（类型/脏文本/裸 id）** |
| **`verify-p3-spoilernote.js`** | **验证 `spoilerNote` 在案件详情渲染（7/7）** |
| **`verify-nav-kinds.js`** | **验证 5 个分区入口计数（147/792/4/8/6/957）** |
| **`backfill-character-episode-refs.py`** | **M3：角色 `episodeRefs` 反推（0→147，只补空）** |
| **`normalize-case-kind.py`** | **M4：案件 `kind` 枚举清洗（`动画案件`/`None` → 三值，依据 DCW `mangaSource`）** |
| **`normalize-case-type.py`** | **M5：案件 `caseType` 规范化（同义归并 + 空值按 kind 推导 + 来源标签）** |
| **`backfill-case-sources.py`** | **M2：案件 `sources` 补引已登记的专属页来源（773→792，页名 `unquote`）** |
| **`backfill-case-summaries.py`** | **M1：案件 `summary.en` 搬 DCW `situation` 段（45→472，绝不用 `resolution`）** |
| **`backfill-case-locations.py`** | **M7：案件 `locations` 从 `situation` 的 `Location:` 行提取（只取设定段，避开解答段泄底）** |
| **`backfill-case-facts.py`** | **M8：案件 `victims`/`suspects` 从 `situation` 块内配对搬原文（`Culprit` 不搬）** |
| **`fill-missing-episode-titles-zh.py`** | **M6：剧集中文标题补全（繁中转简可回验；无源者自译标 `machine`）** |
| **`verify-m8-case-facts.js`** | **M8 渲染验证：被害者/嫌疑人是否渲染、年龄死因是否在原文、有无串人** |
| `fetch-dcw-pages.py` | 793 页抓取（幂等，20KB 阈值） |
| `extract-dcw-page-facts.py` / `extract-dcw-page-blocks.py` | 页面事实 / 正文块提取 |

## 6. 明文限制（如实告知用户）

- **mimoflash 监督未启用**：`patch` 拒写 `config.yaml`（安全策略），`hermes` CLI 不存在（exit 127）。子 agent 派生继承父模型（deepseek-v4-flash）。
- **QQ 通知未实现**：无凭证/接口。
- **conan-archive 未纳入 git**：工作区快照 `?? ./`，本批次无提交。入库需用户确认。
- 抓取后台进程运行中被工具中断过 4 次（均幂等续跑完成，无数据损失）。
- **维基百科 ja/zh/en 全线不可达**（curl 连接重置；`conan.fandom.com` 超时）。
  `web_extract` 只回 503 字符、`browser_exec` 权限异常、`lightpanda` 返回空。
  故外文原文只能取 DCW + YTV 两个通得上的源。
- **60 集 `solvedBy` 空且不可补**：DCW 总表与 YTV `case.json` 均无破案者字段。
  从剧情叙述反推＝编造，不做。这 60 集是**已知且接受的缺口**，不是待办。
- **预览窗格的 `read`/`elements` 一直超时**，无法 GUI 逐字核对页面；
  前端验证靠 `verify-*.js` 抽取 `app.js` 真实函数跑真实数据。

## 7. 备份点

近期回滚点（`/tmp`，重启会丢，需要长期保留请自行复制）：

| 文件 | 用途 |
|---|---|
| `/tmp/cases_pre_m8.json` | 撤销 M8 案件 victims/suspects |
| `/tmp/cases_pre_m7fix.json` | 撤销 M7 口径修正（locations 491→401，含 locationsDropped） |
| `/tmp/eps_pre_m6.json` | 撤销 M6 剧集中文标题补全 |
| `/tmp/cases_pre_locations.json` | 撤销 M7 初版案件 locations（491） |
| `/tmp/cases_pre_summary.json` | 撤销 M1 案件 summary（本轮） |
| `/tmp/cases_pre_sources.json` | 撤销 M2 案件 sources（本轮） |
| `/tmp/cases_pre_casetype.json` | 撤销 M5 案件 caseType（本轮） |
| `/tmp/cases_pre_kind.json` | 撤销 M4 案件 kind（本轮） |
| `/tmp/chars_pre_eprefs.json` | 撤销 M3 角色 episodeRefs（本轮） |
| `/tmp/eps_pre_ytv_summary.json` | 撤销 YTV 补 summary.ja |
| `/tmp/sources_pre_ytv.json` | 撤销 `src-yomiuri-tv-conan` 登记（本轮） |
| `/tmp/eps_pre_titles.json` | 撤销英文标题回填（1→1217） |
| `/tmp/facts_pre_585.json` | 撤销 EP.585 裁定 |
| `/tmp/conflicts_pre.json` | 撤销冲突文件改动 |
| `/tmp/eps_pre_structure.json` | 撤销剧集结构化回填 |
| `/tmp/facts_pre_special.json` | 撤销特别篇集号补齐 |
| `/tmp/chars_pre_p4.json` + `/tmp/cases_pre_p4.json` | 撤销 P4 角色实体化 |
| `/tmp/app.js.bak` + `/tmp/index_pre_nav.html` | 撤销前端分区入口 |
| `/tmp/ca/ep_before_append.json` | 1216 集历史基准 |
| `/tmp/ca/cases_pre_l3.json` | L3 写入前案件状态 |
| `/tmp/ca/dcw-episodes.json`、`dcw-page-map.json` | 全集表解析中间产物 |