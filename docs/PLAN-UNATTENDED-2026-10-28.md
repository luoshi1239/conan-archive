# conan-archive 无人值守执行方案（2026-10-28 夜）

> 依据：`scripts/audit-progress.py` 全库实测 + `scripts/_probe_gap_sources.py` / `_probe_final_plan.py` 源能力探测。
> 原则不变：**只搬原文、不编造、绝不覆盖已有非空字段、脚本幂等、全程 `indent=2`**。

---

## 一、探测结论：什么能做，什么不能做

### 能做（有原文可搬）

| 模块 | 来源 | 现状 → 目标 |
|---|---|---|
| **M1 案件 `summary`** | `data/raw/dcw-page-sections.json` 的 `situation`（案件设定段）英文原文段落（`withSituation` **427**、`withResolution` 742、`storyText` 787） | 45 → **472**（实测 427，原估 460 偏高） |
| **M7 案件 `locations`**（方案外新增） | `dcw-page-sections.json` 正文里的 `Location: <地点>` 行，覆盖 **491** 个案件页 | 0（键都不存在）→ **491** |
| **M2 案件 `sources`** | DCW 页标题与案件 `title.en` 精确匹配 | 773 → **约 790**（17/19 命中） |
| **M3 角色 `episodeRefs`** | 本地反推：`episodes[].characters` → 角色维度倒排（当前 147/147 角色可从剧集侧反推，Conan 跨 1217 集） | 0 → **147** |
| **M4 案件 `kind` 规范化** | 本地枚举清洗：`动画案件`×14 → `anime-original-case`；`None`×5 逐条查原文定 | 792 条 100% 合法枚举 |
| **M5 案件 `caseType` 规范化** | 本地：`['manga']`×2 → `['manga-adaptation']`；空数组 ×25 → 按 `kind` 推导或留空并登记 | 收敛 |
| **M6 剧集 `title.zhHans`/`zhHant` 补 4 处** | 同名案件的既有中文标题（1077/1203/1217） | 1214→1217 / 1216→1217 |

### 不能做（无源，已探测排除）

| 模块 | 为什么 |
|---|---|
| **~~`locations` 0/792~~** | **已推翻，见 M7**。`dcw-page-facts.json` 793 页确实**无任何 location/place/setting 字段**，但 `dcw-page-sections.json` 正文有 853 行 `Location:`，覆盖 491 个案件页 —— 当时只探了 facts 没探 sections，是探测漏项，不是真零源。 |
| **角色 `role`/`summary`/`name.ja`（133 空）** | 793 页全是**案件/剧集页**，无角色页（抽查 Takagi/Megure/Chiba 命中 0）；`caseCast` 只有人名。**零源。** |
| **60 集 `solvedBy`** | DCW 总表与 YTV 均无破案者字段；从剧情反推＝编造。**已登记为「已知缺口」。** |
| **741 案件中文标题 / 38 处重复译文** | 中文需人工译名源，机器翻译冒充被明令禁止。 |

---

## 二、执行顺序

按「风险从低到高、依赖从内到外」排：

```
M3（纯本地反推，零外部依赖）
 → M4（本地枚举清洗）
 → M5（本地枚举清洗）
 → M2（标题精确匹配，只补空 sources）
 → M1（唯一"搬正文"模块，量最大）
 → M7（同为搬正文，只取设定段）
 → M8（同源，victims/suspects）
 → M6（4 条中文标题，繁转简 + 一条自译标 machine）
```

每个模块独立成脚本，单独可回滚；每个脚本必须 `--dry-run` 先行。

---

## 三、逐模块规格

### M3 · 角色 `episodeRefs` 反推

- 来源：`episodes[].characters`（100% 覆盖）
- 逻辑：`{characterId: sorted([episodeNumber, ...])}`
- 写 `episodeRefs`，**只补空的**；已有非空一律跳过
- 预期：147 个角色全部有值
- 回滚：`cp /tmp/chars_pre_eprefs.json data/entities/characters.json`
- 脚本：`scripts/backfill-character-episode-refs.py`

### M4 · 案件 `kind` 规范化

- `动画案件` ×14 → `anime-original-case`（中文枚举值混入英文枚举，是历史遗留）
- `None` ×5 → 逐条打印标题+原文，按 DCW `mangaSource` 定（`TV Original`→`anime-original-case`，漫画→`manga-case`），定不了的**保持 None 并登记**，不猜
- 不改任何 `detailStatus`
- 脚本：`scripts/normalize-case-kind.py`

### M5 · 案件 `caseType` 规范化

- `['manga']` ×2 → `['manga-adaptation']`（同义归并）
- 空数组 ×25 → 若 `kind` 有值则按 `kind` 推（`manga-case`→`['manga-adaptation']`，`anime-original-case`→`['anime-original']`）；`kind` 也空则留空
- 脚本：`scripts/normalize-case-type.py`

### M2 · 案件 `sources` 补 19 个

- 匹配键：案件 `title.en` 与 `dcw-page-facts.json` 的 `heading` 精确匹配（小写去空格）
- 命中 17/19；`case-tsukumo-magician-murder` / `case-yabuuchi-family-murder` 同源于 `The_Cornered_Famous_Detective` 页（标题带括号后缀），需按 `dcwPage` 字段兜底匹配
- 写入格式沿用既有 `sources` 结构：`{page: <DCW 页名>, sourceId: "src-detective-conan-world-anime"}`
- **只补空 `sources`**，已有的一律不动
- 脚本：`scripts/backfill-case-sources.py`

### M1 · 案件 `summary`（最大模块）

- 来源：`data/raw/dcw-page-sections.json` 的 `pages[<pageName>].situation`（列表，英文段落）
- 写入 `summary.en`（**不写中文**），同时写 `summarySource` + `summaryQuote: true`
- **只补空**：已有 `summary` 的 45 条一律跳过（那是人工中文，优先级最高）
- ~~若 `situation` 为空但 `resolution` 有内容 → 用 `resolution` 首段~~
  **已否决（执行时纠正）**：`resolution` 是解答段，首句直接点名凶手（`"The killer is Akiko Yonehara…"`），
  写进 `summary` 等于在列表页泄底。**只用 `situation`**；有 `situation` 的 427 页 + 已有 45 条 = **472**，
  其余 320 条**故意留空**（只有解答、或两边都无），这是诚实缺口不是待办。
- 每页多段用空行连接，不裁剪不改写；跳过纯标题行（`^[A-Z][A-Za-z' \-]{1,40}$` 且 ≤5 词），
  累积到 ≥200 字符或最多 3 段
- 实测 45 → 472（原估「约 460」把 13 条两边都无的算进了分子，实际 472）
- 脚本：`scripts/backfill-case-summaries.py`

### M7 · 案件 `locations`（方案外新增，推翻「零源」结论）

- 来源：`data/raw/dcw-page-sections.json` 正文中的 `Location: <地点>` 行
- **只取 `situation`（案件设定段）**。`resolution`（解答段）里的地点属「案发后才揭出来」的信息，
  放进非剧透字段即泄底——初版误取两段，167 个案件混入解答段地点，已修正并记 `locationsDropped`
- 值能精确命中 `locations.json` 已有实体 `name.en` → 写实体 id，否则写**原文地点名**；
  不为 `Apartment`/`Street`/`Unknown` 这类泛称造实体
- 同时写 `locationsSource` = DCW 页名
- `validate-data.py` 已改为双形态：以 `location-` 开头的必须是真实实体，其余按原文地点名收录
- 实测 401/792（初版 491，修正后下调），脚本 `scripts/backfill-case-locations.py`

### M8 · 案件 `victims` / `suspects`（同日新增）

- 来源：同一 `situation` 段的 `Victim:` / `Age:` / `Cause of death:` / `Suspects:` 行
- `victims` 为对象数组 `[{name, age?, causeOfDeath?}]`，年龄/死因**按原文块配对**；
  块里没写就是没有，绝不按平铺下标去配（会张冠李戴）
- `suspects` 存原文整串，不拆名；`Unknown` / `Unknown culprit` 等占位值不搬
- **`Culprit` 行一律不搬**（属解答）
- 实测：被害者 393 案 / 534 人（383 带年龄、347 带死因）、嫌疑人 327 案
- 脚本 `scripts/backfill-case-facts.py`，渲染验证 `scripts/verify-m8-case-facts.js`

### M6 · 剧集中文标题补 4 处（**已完成**）

- EP.1077 / 1203 缺 `zhHans`、EP.1217 缺 `zhHans` + `zhHant`
- 实际做法分两类：
  - EP.1077「黑衣组织的谋略（狩猎）」、EP.1203「园子与柯南的怪谈之夜」——本集已有 `zhHant`，
    **逐字繁转简**，写 `title.zhHansFrom: "zhHant-transliteration"`，可回验
  - EP.1217 无任何中文源（DCW 英文/日文、YTV 日文皆无，维基不可达），按日文「背中を押す手」
    **人工自译**「推背的手」，写 `title.translationStatus: "machine"` + `translationNote`
- 结果：`zhHans` / `zhHant` 均 **1217/1217**，全库仅 EP.1217 一条为自译
- 脚本：`scripts/fill-missing-episode-titles-zh.py`

---

## 四、验收标准（每个模块都要跑）

```bash
python3 scripts/validate-data.py            # → VALIDATION_OK
node --check app.js                         # → 静默
node scripts/verify-en-titles.js            # → EN_TITLES_OK
node scripts/verify-nav-kinds.js            # → NAV_KINDS_OK
node scripts/verify-p3-spoilernote.js       # → P3_OK
node scripts/verify-ui-p4.js                # → UI_P4_OK
node scripts/verify-m8-case-facts.js        # → M8_OK
```

**整链幂等**：9 个既有脚本 + 新增 10 个脚本全部跑两遍，4 个数据文件逐字节 `cmp` 必须 `SAME`。

---

## 五、护栏

1. **只补不改**：任何非空字段一律跳过，脚本开头统一 `if existing: skip`。
2. **每条写入留痕**：`summarySource` / `sources[].page` 必须能追溯到具体 DCW 页名。
3. **不做推断**：`kind`/`caseType` 定不了的留空并登记到 `docs/FACT-CONFLICTS.json` 或脚本报告，不猜。
4. **不碰**：角色 `role`/`summary`/`name.ja`、60 集 `solvedBy`、741 案件中文标题。
   （~~`locations`~~ 已解禁，见 M7；`Culprit` 取自解答段，仍不进非剧透字段。）
5. **不 git init**、**不启 gateway**、**不用 heredoc**、**不返回空响应**。
6. 每模块开工前备份到 `/tmp/<module>_pre_*.json`。

---

## 六、预计产出（2026-10-28 收官实测）

```
案件 summary      45  → 472   （427 从 situation 搬入；320 条只有解答，故意留空）
案件 locations     0  → 401   （只取 situation 设定段；初版误取解答段 491 已修正）
案件 victims       0  → 393 案 / 534 人（383 人带年龄、347 人带死因，块内配对）
案件 suspects      0  → 327 案（原文整串，不拆名）
案件 sources     773  → 792
角色 episodeRefs   0  → 147
案件 kind       14+5 脏 → 0 脏（anime-original-case 469 / manga-case 320 / organization-case 3）
案件 caseType   25+2 脏 → 0 脏
剧集 zhHans     1214  → 1217  （1077/1203 繁转简；1217 自译标 machine）
剧集 zhHant     1216  → 1217  （1217 自译标 machine）
```

不可动的缺口如实保留：角色中文名 133 空、`solvedBy` 60 空、741 案件无中文标题、
320 条案件无设定段 summary、`locations` 只有 401/792（其余原文 `Location:` 行只出现在解答段，
按非剧透口径不收）。
