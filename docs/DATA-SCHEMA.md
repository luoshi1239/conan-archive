# CONAN INDEX 数据规范

## 目标

将《名侦探柯南》资料拆成可校验、可持续扩展的静态数据。原始资料只读保存，规范化数据由脚本生成。

## 顶层类型

- `episodes`：电视动画集数
- `movies`：剧场版与合作电影
- `ovas`：OVA、Magic File、Bonus File
- `specials`：TV Special、总集篇、重制与特别企划
- `manga`：漫画卷、File、主线篇章
- `characters`：人物档案
- `organizations`：组织与阵营
- `cases`：案件与诡计
- `gadgets`：道具与技术
- `relations`：人物、组织、作品之间的关系

## 电视动画标准字段

```json
{
  "id": "episode-0001",
  "kind": "tv-episode",
  "number": 1,
  "title": {
    "ja": "ジェットコースター殺人事件",
    "zhHans": "云霄飞车杀人事件",
    "zhHant": "雲霄飛車殺人事件",
    "en": null
  },
  "airDate": null,
  "year": 1996,
  "adaptation": "manga|anime-original|mixed|unknown",
  "mangaRefs": ["vol-001"],
  "arc": null,
  "spoiler": 1,
  "status": "catalog|reviewed|complete",
  "summary": null,
  "characters": [],
  "organizations": [],
  "locations": [],
  "gadgets": [],
  "caseTypes": [],
  "sources": ["source-id"]
}
```

## 内容等级

- `catalog`：只有目录字段，不能伪装成完整剧情档案
- `reviewed`：已完成基础事实交叉核对
- `complete`：有剧情摘要、人物、案件类型、关联和剧透信息

## 剧透等级

- `1`：入门，不揭示关键身份、犯人和结局
- `2`：深入，允许主线提示和重要关系
- `3`：全剧透，允许犯人、手法、证据、结局和身份揭示

## 新增字段（2026-10-27 第二批）

### 剧集 `summary`

```json
"summary": {
  "en": "DCW Situation/Part N 原文（不翻译）",
  "ja": "読売テレビ官方日文简介（仅 DCW 无正文的 5 集）",
  "zhHans": "",
  "zhHant": "",
  "sourcePage": "DCW 页面名 或 src-yomiuri-tv-conan",
  "sourceQuote": true
}
```

规则：`en` 只搬 `data/raw/dcw-page-sections.json` 的原文段落；一旦原文本身只有一句话
（两集一页的第二集常见），如实保留并标记短文本来源，不拼接推断。`zhHans`/`zhHant`
留空等人工，禁止机器翻译冒充。

**`ja` 字段（2026-10-28 新增）**：DCW 对 EP.713 / 714 / 882 / 1061 / 1187 只有信息表、
没有正文段落，这 5 集改用読売テレビ（《名侦探柯南》播出电视台）官方站点的
`conan_story` 原文补入，写入 `summary.ja`，`sourcePage` 记 `src-yomiuri-tv-conan`。

- 只补 `summary` 为 `null` 的集，已有 `en` 正文的一律不碰。
- `en` 留空而非填日文——前端回落顺序 `zhHans → zhHant → ja → en` 会命中 `ja`，
  `labelOf()` 对 `ja` 加「（日文原文·待译）」角标。
- YTV **不提供破案者字段**，不得据其剧情叙述反推 `solvedBy`。
- 该站点 1426 条记录中 **101 条 `R##` 前缀是重播/数字重制版**，剧情为改写长文，
  不等于原集，取数时必须跳过（`episode` 以 `R` 开头）。

### 案件 `dcwL3Source`

```json
"dcwL3Source": {
  "motive": {"page": "...", "block": "Resolution", "confidence": "medium",
             "quote": "原文引用", "lang": "en", "reviewedBy": "L3-APPROVED.json"}
}
```

逐字段记录原文出处，便于回滚与人工复核。写入方（`apply-l3-approved.py`、
`backfill-case-resolution.py`）**绝不覆盖**已有非空字段。

### 角色 `caseRefs`

角色实体的反向索引（`["case-..."]`），由 `link-character-cases.py` 依据案件 `castNames`
与角色 `name.*`/`aliases` 精确匹配生成，只增不删。

### 角色实体结构（2026-10-28 P4 起）

```json
{
  "id": "character-wataru-takagi",
  "kind": "character",
  "name": { "en": "Wataru Takagi" },
  "translationStatus": "pending",
  "status": "skeleton",
  "aliases": ["Tooru Amuro"],
  "caseRefs": ["case-...", "..."],
  "sources": ["src-detective-conan-world-characters", "src-detective-conan-world-anime"],
  "note": "由案件页 cast 列表自动实体化；中文名待补"
}
```

约定：

1. `kind` 必须是 `"character"`——前端 `entityToCard()` 靠它判「人物」，
   缺失会被误判成「主线」，有 `role` 时还会被 `role.includes('组织')` 误判成「组织」。
2. **中文名留空**：`name` 只有 `en`，`translationStatus: "pending"`。
   `TRANSLATION-GLOSSARY.md` 规定专名未收录者保留罗马字，不得自行拼汉字。
3. **化名不新建实体**：同一人物的其他名字进 `aliases`（如 `Tooru Amuro` → `character-rei-furuya`），
   否则人物索引会出现重复人物。
4. `status: "skeleton"` 表示只有骨架（名/出场案件/来源），没有 `role`/`summary`——
   原文没给的不写。
5. 无名路人（`Policeman`）、庭审角色（`Presiding judge`）、剧中虚构（`Kamen Yaiba`）
   一律不建实体。

前端显示：所有实体 id 引用字段（`characters`/`caseRefs`/`members`/`userRefs`/`relations`…）
必须经 `nameOfRef()` / `refsText()` 解析成展示名再渲染，禁止 `.join('、')` 直出 id。

### 剧集结构化字段（2026-10-28 P4-C 起）

来源：`data/raw/dcw-page-facts.json`（793 页原文事实），由
`fix-special-page-episode-numbers.py` → `resolve-episode-solvedby.py` →
`create-character-entities-episodes.py` → `backfill-episode-structure.py` 依次回填。

```json
{
  "season": 15,
  "solvedBy": "character-conan-edogawa",
  "solvedByRaw": "Kogoro Mouri (via Conan)[1]",
  "solvedByParsedFrom": "via-contractor",
  "solvedByNote": "原文记为 No one，本集无破案者",
  "castNames": ["Conan Edogawa", "Ai Haibara", "Detective Boys"],
  "characters": ["character-conan-edogawa", "character-ai-haibara"],
  "dcwExtraPages": ["The_Kirin's_Horn_That_Vanished_into_the_Dark"],
  "dcwL3Source": { "season": "Kobayashi-sensei's_Love" },
  "coverage": {
    "directory": true,
    "basicFacts": true,
    "structure": true,
    "deepSpoilers": true
  }
}
```

约定：

1. **`season` 是整数**，由页面 `season` 字符串（`"15"`）转换；非纯数字不写。
2. **`solvedByRaw` 保留原文一字不改**，`solvedBy` 是解析出的角色 id。
   二者并存，任何解析错误都可回溯。
   原文括号内是「借助谁破案」（`Kogoro Mouri (via Conan)`）而非第二个人，
   解析时剥括号、剥 `[n]` 脚注、剥 `(x2)` 倍数，并兼容 `(via Conan}` 半全角不配对变体。
3. **`solvedByNote`**：原文为 `No one`/`N/A`/`None` 等无数值答案时写入，
   此时**不设** `solvedBy`——不虚构破案者。
4. **`castNames` 同样是原文**（DCW `caseCast`），`characters` 是解析后的角色 id 列表。
   解析不出的名字只保留在 `castNames` 里，不会凭空造实体。
5. **重叠页面不合并 cast**：一集被多个 DCW 页面覆盖时（如历史上的 EP.585 同时被
   `Kobayashi-sensei's_Love` 与 `The_Kirin's_Horn…` 覆盖），
   首个页面写入 `castNames`/`characters`，其余页面只记入 `dcwExtraPages`。
   > 2026-10-28 已裁定 EP.585 归 `Kobayashi-sensei's_Love`（依据 DCW `/wiki/Anime`
   > 总表逐集归属 + `intEpisode` 自洽 + Kirin 页自身 airdate 错位），
   > Kirin 页 `episodeNumbers` 由 `[585,586,587]` 修正为 `[586,587]`，原值存
   > `episodeNumbersRaw`。该页不再覆盖 585，EP.585 的 `dcwExtraPages` 已清空。
   > 见 `docs/FACT-CONFLICTS.json` → `conflict-kirin-horn-585-overlap`。

   这样避免把另一案件的人物混进本集。
6. **`title.en` 来自 DCW `/wiki/Anime` 剧集总表**（`data/raw/dcw-anime-index.json`），
   不是案件页。写入时：
   - `title.en`：清理后的英文标题——剥离 markdown 斜体 `*`，
     去掉 `(1 Hour Special)` / `(2.5 Hour Special)` 等播出时长标注，
     **保留** `(Part 1)` / `(The Case)` 等分段标记（与 `zhHans` 的既有惯例一致）
   - `title.enRaw`：总表原始串，一字不改，用于回溯
   - `title.enSource`：来源 URL
   只填空不覆盖已有值；日文 1217 / 简中 1214 / 繁中 1216，前端按
   `zhHans → zhHant → ja → en` 回落。
7. **`overseasNumber` 是国际集号**，源自总表 `Int#`。特别篇对应多个集号时
   用 `、` 连接（`"99、100、101、102"`），36 集如此，已与总表 `intNumbers` 逐一核对。
8. **`dcwL3Source`** 记录每个字段来自哪个页面，供审计。
9. **`coverage.*` 必须是布尔值**，`detailStatus` 只允许
   `catalog` / `reviewed` / `complete`（见 `validate-data.py`）。
   `structure` 为真且原状态是 `catalog` 时升为 `reviewed`。

### 特别篇页面的集号（2026-10-28 起）

多集特别篇的 DCW 页面 infobox 写法与单集页不同，`episodeNumbers` 容易抽成空数组。
`dcw-page-facts.json` 现补充以下字段（只补空的，已有集号绝不动）：

```json
{
  "episodeNumbers": [188, 189, 190, 191, 192, 193],
  "episodeRange": "188-193",
  "intEpisodes": [203, 204, 205, 206, 207, 208],
  "intEpisode": 203,
  "factSource": "html:Episode 188-193 (Int. Episode 203-208)"
}
```

原文三种写法（均由 `fix-special-page-episode-numbers.py` 支持）：

```
Episode 188-193 (Int. Episode 203-208)     多集 + 国际集号范围
Episode 491-504 (Int. Episode 538-551)     同上
Episode 425 (Int. Episode 459-463)         单集 + 国际集号范围
```

`factSource` 记录命中的原文串——集号来自页面原文，不是推算。

### 案件 `spoilerNote`（2026-10-28 起）

`spoiler` 必须是 **1/2/3 整数**（见「剧透等级」）。
历史上有脚本把中文分析文本误写进该字段（94–159 字），
导致前端 `(record.spoiler || 1) <= activeLevel` 变成 `NaN`、整条案件被永久过滤。

`fix-spoiler-type-pollution.py` 把这类文本**原文迁入 `spoilerNote`**（一字不改），
`spoiler` 恢复默认等级 2。前端 `detailSections()` 以「收录备注」分区渲染 `spoilerNote`。

### 案件 `summary` 的对象结构（2026-10-28 M1 起）

案件 `summary` 从此前写法不一的字符串/`null`，统一为**多语言对象**（与 L3 字段同构）：

```json
{
  "summary": { "en": "DCW situation 段英文原文（逐字搬运）" },
  "summarySource": "General_Hospital_Murder_Case",
  "summaryQuote": true
}
```

约定：

1. **只有 `en`**，`zhHans`/`zhHant` 一律不写——中文摘要须人工撰写，禁止机器翻译冒充。
   前端 `textOf()` 取到 `en`、`langOf()` 返回 `en`、`labelOf()` 自动加「英文原文·待译」角标。
2. `summary` 为字符串的 45 条是**历史人工中文**，优先级最高，任何脚本都不得覆盖。
3. **`resolution`（解答段）绝不进 `summary`**——它首句即点名凶手，写进去等于在列表页泄底。
   只有 `situation` 的 427 条被填充；`summary` 为空（`null`）的 320 条是**有意留空**，
   因为原文只有解答段、或两段都没有，不是待补事项。
4. `summarySource` 记录 DCW 页名，`summaryQuote: true` 表示逐字引用而非改写。
5. `validate-data.py` 允许字符串或 `{en: ...}` 对象两种形态（向后兼容旧数据）。

### 案件 `locations` 的双形态（2026-10-28 M7 起，含口径修正）

`locations` 是**混合数组**，元素两种形态：

- **实体 id**：以 `location-` 开头，必须在 `data/entities/locations.json` 中存在（如 `location-tropical-land`）
- **DCW 原文地点名**：直接存原文串（如 `Private Mansion`、`Tropical Street`）

```json
{
  "locations": ["Private Mansion", "location-tropical-land"],
  "locationsSource": "Roller_Coaster_Murder_Case"
}
```

约定：

1. **只取 `situation` 段**（案件设定段）。**`resolution`（解答段）的地点一律不取**——
   那是「案发后才揭出来的地点」，放进非剧透字段等于泄底。
   初版误取了两段，导致 167 个案件混入解答段地点（如 `Shiki Island`、`hospital`），已修正。
2. 被剔除的旧值记入 `locationsDropped`（数组），可回溯；90 个案件因此失去全部地点
   （它们的地点原文只在解答段），**这是正确取舍，不是待补**。
3. **不为泛称造实体**：`Apartment` / `Street` / `Unknown` 这类保持原文串，不新建 `locations.json` 条目。
4. `locationsSource` 记录来源 DCW 页名。
5. `validate-data.py` 的双形态判定：以 `location-` 开头的**必须**是真实实体，否则报错；
   其余按原文地点名计数（`raw_location_names`），不报错。
6. 前端 `detailSections()` 用 `nameOfRef(x) || x` 渲染——解析不到就显示原文，
   不再像旧的 `refsText()` 那样把未知 id 静默丢弃。

### 案件被害人 / 嫌疑人（2026-10-28 M8 起）

```json
{
  "victims": [
    { "name": "Ayaka Tatsuo", "age": "27 years old", "causeOfDeath": "Hanging" },
    { "name": "Shigetsugu Torada", "age": "31 years old", "causeOfDeath": "Electrocution" },
    { "name": "Yoshiro Torada", "causeOfDeath": "Swept away by a tornado" }
  ],
  "suspects": [
    "Naonobu Torada, Tatsue Torada, Yui Torada, Tamefumi Tatsuo, and Akira Tatsuo"
  ],
  "caseFactsSource": "Furinkazan"
}
```

约定：

1. **`victims` 是对象数组，不是并行数组。** `age` / `causeOfDeath` 属于**同一原文块**内的配对结果——
   块里没写 Age 就是没有，**绝不借用其他被害人的**。
   > 初版写成 `victims[] + victimAges[]` 两个并行数组靠下标配对，实测 40 个案件两者长度不等
   > （Furinkazan 5 个被害人只有 2 个年龄），要显示「Yoshiro Torada 27 岁」——张冠李戴，已废弃。
2. `name` / `age` / `causeOfDeath` **逐字保留 DCW 原文**，不做单位换算、不做中译。
3. `suspects` 存**原文整串**，保留 `and`、逗号、`families` 等原貌，**不拆成一堆名字**——
   拆名属推断，且 `Tatsuo family` 这类集合无法拆。
4. 原文占位值 `Unknown` / `Unknown culprit(s)` / `N/A` / `None` **不搬**：它们不含任何信息。
5. 字段来源只到 `caseFactsSource`（DCW 页名）一级——同页多块共用同一来源。
6. **`Culprit` 行一律不搬。** `resolution` 整段不读；`situation` 段里的 `Culprit:`
   也会断开块配对并跳过。
7. 自定义字段校验：`validate-data.py` 要求 `victims` 每项只能是
   `{name, age?, causeOfDeath?}`，未知键报错；`suspects` 每项必须是非空字符串且不得含
   `culprit/killer/murderer` 字样（防剧透字段串入）。
8. 前端渲染：被害者逐行显示为 `姓名（年龄、死因）`，缺项自动省略；两段均带
   `pre-line` 类以保留换行。渲染验证见 `scripts/verify-m8-case-facts.js`。

### 案件 `kind` 枚举（2026-10-28 M4 起）

全库 792 条已收敛为三个值，无脏值：

| 值 | 数量 | 判定依据（只看 DCW 原文） |
|---|---|---|
| `anime-original-case` | 469 | `mangaSource = "TV Original"` 或 `isAnimeExclusive: true` |
| `manga-case` | 320 | `mangaSource = "Volume …"` |
| `organization-case` | 3 | 组织相关案件 |

历史脏值 `动画案件`×14（中文混入英文枚举）与 `None`×5 已清除；`None` 的靠 `mangaSource` 定，
两条无 `dcwPage` 的（`case-tsukumo-magician-murder`、`case-yabuuchi-family-murder`）靠标题补链到
`The_Cornered_Famous_Detective!_Two_Big_Murder_Cases`（`Volume 14: Files 1-8 (131-138)`）定为 `manga-case`，
**不可**错连到 `Conan_Cornered_in_the_Darkness`（那是 TV Original）。

### 案件 `caseType` 规范化（2026-10-28 M5 起）

- `['manga']` → `['manga-adaptation']`（同义归并）
- 空数组按 `kind` 推导：`manga-case` → `['manga-adaptation']`，`anime-original-case` → `['anime-original']`；
  `organization-case` 与 `kind` 也为空者保持空数组，不猜
- 每条题材值必须有来源标签，共 52 条修正，0 遗留

### 剧集中文标题的补法（2026-10-28 M6 起）

`title.zhHans` / `title.zhHant` 均已 **1217/1217 全覆盖**。补法分两类，**必须区分**：

| 类型 | 场景 | 写法 | 可否回验 |
|---|---|---|---|
| 简繁转换 | 本集已有 `zhHant`、缺 `zhHans` | `title.zhHans` + `title.zhHansFrom: "zhHant-transliteration"` | 可，同一记录里就有繁中稿 |
| 人工自译 | 日文/英文有标题但无任何中文稿 | `title.zhHans`/`zhHant` + `title.translationStatus: "machine"` + `title.translationNote` | 否，须人工复核 |

约定：

1. **简繁转换不是翻译**，走显式字表逐字替换，转换后校验长度一致（防漏字/多吃字）。
   目前本批只涉及 EP.1077、EP.1203 两条，字表仅收录实际出现的字。
2. **人工自译必须标 `translationStatus: machine`**，让前端和读者都知道这不是官方译名。
   目前全库只有 **EP.1217「推背的手」** 一条属于此类（日文原题「背中を押す手」，
   DCW 英文 `The Hands Pushing Their Back`）。
3. DCW 英文/日文、YTV 日文均无中文译名；zh.wikipedia / 百度百科目前不可达。
   若日后拿到官方译名，直接覆盖并把 `translationStatus` 改 `human`、清掉 `translationNote`。
4. 脚本 `scripts/fill-missing-episode-titles-zh.py`：只补空，任何已有值不动，幂等。

### 角色 `episodeRefs`（2026-10-28 M3 起）

角色实体的剧集反向索引（`[1, 2, 3, …]` 集号升序去重），由 `episodes[].characters` 倒排生成，
覆盖 147/147 角色。只补空，已有值不动。与 `caseRefs`（案件反向索引）并列。

## 原始数据规则

1. `data/raw/` 只保存来源原文，不直接修改。
2. 所有规范化记录必须保留 `sources`。
3. 不确定字段使用 `null` 或 `unknown`，禁止猜测填充。
4. 特别篇、合并篇、重制篇不能强行转换为普通集数。
5. 中文译名冲突时保留 `zhHans`、`zhHant` 和 `aliases`。
6. 作品事实与剧情摘要分开记录，避免把剧场版内容误当漫画主线。

## 候选资料层

尚未完成字段级审核的内容保存在 `data/candidates/`，不直接供前端加载，也不覆盖 `data/raw/`。

每条候选记录必须包含：

- `candidateId`：候选记录唯一 ID；
- `targetId`：现有规范化记录 ID；
- `field`：待补充或待修正字段；
- `value`：候选值，允许显式为 `null`；
- `sourceRefs`：至少一个已登记来源；
- `confidence`：`high`、`medium` 或 `low`；
- `reviewStatus`：`pending`、`accepted` 或 `rejected`；
- `reviewNote`：字段级审核说明。

候选记录只有在审核映射明确应用后，才可以进入规范化数据。候选校验命令为：

```bash
python3 scripts/validate-candidates.py
```

内容批次登记在 `docs/CONTENT-BATCHES.json`，批次和字段可信度报告由以下命令生成：

```bash
python3 scripts/report-batch-progress.py
python3 scripts/report-field-confidence.py
```

## 案件 L3 字段的双语结构（2026-10-27 批 3 起）

案件实体的 `culprit` / `motive` / `method` / `evidence` / `resolution` 统一为多语言对象：

```json
"method": {
  "zhHans": "柯南解开了密室杀人的手法……",
  "en": "Conan figures out the trick to the locked room murder was……",
  "translationStatus": "machine",
  "translationSourceHash": "a1b2c3d4e5f6",
  "translationStale": false
}
```

| 字段 | 说明 |
|---|---|
| `zhHans` | 简体中文。人工撰写为 `human`，AI 翻译为 `machine`，空字符串表示待译 |
| `en` | DCW 页面英文原文。**只搬原文，不改写**，是译文的唯一依据 |
| `translationStatus` | `human`（人工）/ `machine`（AI 翻译，未经人工复核）/ `pending`（待译） |
| `translationSourceHash` | 译文对应英文的 sha1 前 12 位。英文改动后旧译文自动作废重入队列 |
| `translationStale` | 曾因原文变更被作废的标记 |

兼容规则：

- 旧数据里该字段可能是**纯字符串**，读取方必须先做类型判断（前端 `textOf()` 已处理）。
- 「字段有内容」的判定：`zhHans` 或 `en` **任一非空**（`normalize-case-status.py` 的 `filled()`）。
- `validate-data.py` 会拒绝既不是字符串、也不是 `{zhHans,en,translationStatus}` 的结构。

翻译工具链与口径：

```bash
python3 scripts/build-translation-queue.py    # 生成排序队列
python3 scripts/dump-translation-batch.py     # 取下一批待译字段
python3 scripts/apply-translations.py         # 写入 docs/translations/batch-*.json
```

口径见 `docs/TRANSLATION-GLOSSARY.md`；语义错位字段登记在 `docs/translations/flagged.json`（不译）。

### L3 字段的审计字段（2026-10-28 起）

| 字段 | 用途 |
|---|---|
| `translationNote` | 译文处置说明，如「按 DCW 原文原句重新指派（原值系切块错位）」 |
| `replacedEn` | 被纠正前的旧英文原文，便于回滚与追溯 |
| `case.l3Absent` | 数组，记录**原文确实没有、因而删除**的字段：`[{field, reason}]` |

**「原文没有」的表示法**：删掉该字段（值为 `None`），**不要**留 `{zhHans:"", en:""}` 空壳——
`validate-data.py` 会拒绝两语全空的字段，`normalize-case-status.py` 的 `filled()` 也不会
把空壳算作「有内容」。
