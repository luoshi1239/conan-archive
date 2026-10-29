# 2026-10-28 · 英文标题补全 + EP.585 裁定 + 海外集号纠错

本轮从 DCW 原站另一个入口 `/wiki/Anime`（剧集总表）拿到了逐集原文，
解决三件事：补 1216 集英文标题、裁定悬置的 EP.585、修 EP.1055 脏数据。

---

## 1. 新数据源：DCW 剧集总表

前几轮只用了 793 个案件页，剧集维度的原文（每集标题、播出日期、国际集号、
所属页面）一直没抓。地址：

```
https://www.detectiveconanworld.com/wiki/Anime
```

表结构 8 列，覆盖全部集数：

| Jp# | Int# | Episode title | Original broadcast | English dub broadcast | Plot | Manga source | Next Conan's Hint |
|-----|------|---------------|--------------------|-----------------------|------|--------------|-------------------|

新增 `scripts/parse-dcw-anime-index.py`（约 190 行）解析成
`data/raw/dcw-anime-index.json`（1218 行，含 12 个重播行已剔除）。

### 解析踩到的四个坑

| 坑 | 原文写法 | 处理 |
|---|---|---|
| 国际集号是范围 | `11\-12`、`99\-102` | 展开成 `intNumbers: [11,12]` |
| 警察学校编集号带标记 | `1029 WPS1` | 正则容许 `数字 + WPS序号` |
| 重播行 | `R133 WPS5`、`425 R55` | 认 `R` 前缀，去重时正片优先 |
| 斜体只包住主标题 | `*A* (Part 1)` | 裸 `*` 全部剥离（柯南标题不含 `*`） |

首版只认纯数字，漏了警察学校编 4 集（1029/1038/1042/1061），
`intNumber` 也是 40 个空值——两处都修了，现在 1218/1218 全部解析。

---

## 2. 补 1216 集英文标题

### 为什么做

`title.en` 全库只有 **1 集**有值。日文 1217、简中 1214、繁中 1216，
唯独英文几乎空白——这是国际化检索和对照 DCW 原文的主要缺口。

### 先比对再用，不盲信

`scripts/_probe_index_diff.py` 逐集比对总表与本地库：

| 维度 | 冲突数 |
|---|---|
| 英文标题（库里仅 1 条，无冲突可查） | 0 |
| 国际集号 | 1（EP.1055，见第 3 节） |
| 播出日期 | **0** |
| 页面归属（剧集 caseRefs ↔ 总表 page） | **0** |
| 库有总表无 / 总表有库无 | 0 / 1（EP.1218 于 10-31 播出，今天未上映，不入库） |

三条零冲突说明总表与本地库高度自洽，可以放心搬运。

### 清理规则沿用既有惯例

原标题带 markdown 斜体：`*主标题* (后缀)`。库里 `zhHans` 的既有做法是
**去掉时长标注、保留分段标记**：

| 形态 | 例 | 处理 |
|---|---|---|
| 播出时长 | `(1 Hour Special)`、`(2.5 Hour Special)` | 去掉（与 zhHans 去掉「（2 時間スペシャル）」一致） |
| 分段标记 | `(Part 1)`、`(The Case)`、`(The Resolution)` | 保留（与 zhHans 保留「前篇/后篇」一致） |

原始串完整存 `title.enRaw`，来源记 `title.enSource`，可逐集回溯，不算加工。

首版有个 bug：`*A* (1 Hour Special)` 剥离后剩下 `*A*`，星号残留。
原因是斜体只包住主标题，正则 `^\*.*\*$` 不匹配整串。改成先删全部 `*` 再去后缀，
6 个边界样例全部正确。

### 结果

```
title.en    1 → 1217（100%）
title.enRaw 1217（原文留档）
新增 title.zhHans 缺 3 集、zhHant 缺 1 集，前端按 zhHans → zhHant → ja → en 回落
```

---

## 3. 修 EP.1055 脏数据

`overseasNumber` 存的是 `'11、12'`，而原文两处都写 **1112**：

- 剧集总表：`| 1055 | 1112 | The Ghost's Revenge |`
- 案件页 infobox：`intEpisode: 1112`

`'11、12'` 不知从何误入，已修为 `1112`。

顺带核对全部 36 个「多值」`overseasNumber`（如 EP.96 的 `'99、100、101、102'`），
与总表 `intNumbers` **逐一相同**，都是特别篇对应多个国际集号的正常情况，未动。

首版修正脚本每跑一次都报「修正 36 集」——值没变只是重写，属假幂等。
改成先比较后写入，现在连跑两次都是 `修正 0 集`。

---

## 4. 裁定 EP.585（此前 open）

### 三份原文证据

1. **DCW 剧集总表逐集列明**：
   ```
   585 | 636 | Timeless Sakura's Love                      → Kobayashi-sensei's_Love
   586 | 637 | The Kirin's Horn That Vanished into the Dark → The_Kirin's_Horn_...
   587 | 638 | Kid vs. the Four Divine Detective Boys       → The_Kirin's_Horn_...
   ```
2. **intEpisode 自洽**：Kobayashi 页 634、Kirin 页 637，相差 3。
   若 Kobayashi 占 583-585（int 634/635/636），Kirin 必从 586 起。
3. **Kirin 页自身 airdate** 写的是 `August 28, 2010 (Timeless Sakura's Love)`
   ——那是 585 的日期与标题，证明该页 infobox 从 585 起算，而实际内容是 586-587。

上一轮之所以判不了，是因为只有前两条中的 intEpisode，加上 jpTitle 反向证据，
两条打架。拿到总表的逐集归属后三条贯通。

### 裁定与动作

**EP.585 归 Kobayashi's Love；Kirin's Horn 覆盖 586-587。**

`scripts/resolve-ep585-attribution.py`：

- `dcw-page-facts.json`：Kirin 页 `episodeNumbers` `[585,586,587]` → `[586,587]`
  - 原值留档 `episodeNumbersRaw`
  - 修正依据写 `episodeNumbersNote`
- `episodes.json`：清 EP.585 的 `dcwExtraPages`（该页不再覆盖 585）
- `FACT-CONFLICTS.json`：`conflict-kirin-horn-585-overlap` open → **resolved**

**本地剧集归属原本就是对的**（585 归 Kobayashi、586/587 归 Kirin，与总表一致），
这轮没有改动任何 caseRefs，只修正了页面元数据。

### 验证

```
EP.583  cast=10  Conan / Sumiko Kobayashi / Ninzaburo Shiratori / Detective Boys …
EP.584  cast=10  同上
EP.585  cast=10  同上 —— 小林-白鸟线三集一致
EP.586  cast=9   Conan / Kaitou Kid / Ai Haibara / Jirokichi Suzuki / Ginzo Nakamori
EP.587  cast=9   同上 —— 基德线两集一致
```

重跑 `backfill-episode-structure.py` 后 cast 未变，`VALIDATION_OK`。

---

## 5. 另一发现：22 个页面不在本地抽取值里

总表链接指向 793 个页面，其中 22 个（覆盖 29 集）不在
`dcw-page-facts.json` 里，都是多集合集页：

```
Courtroom Confrontation I–IV（264-265 / 297-298 / 489 / 606-607）
Kid vs. Komei / Kid vs. Amuro / Kid VS Hakuba（983-984 / 1105-1106 / 1193-1194）
Metropolitan Police Detective Love Story 8（487）
Head-to-Head Match with the Black Organization（345）
Heiji Hattori vs. Shinichi Kudo（490）
… 共 22 个
```

**这不是数据缺口**：这 29 集的 caseRefs、solvedByRaw、castNames、案件实体都齐全，
只是案件实体的 `sources` 只记到来源 id（`src-detective-conan-world-anime`）
没记到具体 page。属可追溯性的小瑕疵，不影响功能。已记入遗留。

---

## 6. 最终状态

```
剧集 1217
  title.en        1217  （本轮 1 → 1217）
  title.ja        1217
  title.zhHans    1214
  title.zhHant    1216
  airDate         1217
  overseasNumber  1217  （EP.1055 已纠错）
  season          1217
  castNames       1217
  solvedBy 挂实体  1157

冲突 5 条：resolved 5 / open 0
```

验证全绿：

```
VALIDATION_OK
CHAIN_IDEMPOTENT_OK（9 脚本连跑，4 个数据文件逐字节 SAME）
APP_JS_OK
P3_OK / NAV_KINDS_OK(147/792/4/8/6/957) / UI_P4_OK
```

---

## 7. 回滚

```bash
# 英文标题
cp /tmp/eps_pre_titles.json data/episodes/episodes.json

# EP.585 裁定（facts + EP.585 dcwExtraPages）
cp /tmp/facts_pre_585.json data/raw/dcw-page-facts.json
python3 scripts/backfill-episode-structure.py

# 冲突文件
cp /tmp/conflicts_pre.json docs/FACT-CONFLICTS.json
```

---

## 8. 遗留

1. **`sources` 未记具体 page**（22 个合集页 / 29 集）——只有来源 id，无页面级追溯。
2. **60 集 `solvedBy` 空**，三类：
   - **52 集原文即 `null`**（其中 21 集来自多集特别篇页，页面无该字段）
   - **4 集原文 `No one`/`N/A`**（EP.12/43/795/1089，写 `solvedByNote`，不虚构破案者）
   - **4 集有原文但库中无该角色**（EP.67 `Heihachiro Shiota`、EP.225 `Detective Boys`、
     EP.661/662 `Ryohei Onda`）

   总表**不含** solvedBy 字段，本轮无法补；日文维基等外部源在本机全部不可达
   （`ja/zh/en.wikipedia.org` 连接重置，`conan.fandom.com` 超时），故仍不伪造。
3. `title.zhHans` 缺 3 集、`zhHant` 缺 1 集——前端回落 ja/en，不影响显示。
4. 147 个角色中 133 个中文名空白；`Detective Boys`（435 集）应建 organization
   但缺成员名单；5 集 summary 空；38 处重复译文；cron 缺锁；git 未初始化。
