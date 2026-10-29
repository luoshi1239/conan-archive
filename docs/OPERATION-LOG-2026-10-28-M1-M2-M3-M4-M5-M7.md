# 2026-10-28 · 无人值守批次 M1 / M2 / M3 / M4 / M5 / M6 / M7 / M8

接 `docs/PLAN-UNATTENDED-2026-10-28.md`。方案里 6 个模块全部做完，
执行过程中又发现两个方案外但来源确凿的模块：**M7（案件地点）** 与 **M8（被害者/嫌疑人）**。

**本篇含两次自查回改**，都记在正文里：

- M7 初版误读了 `resolution`（解答段），167 个案件的地点混进泄底地点 → 见 **6bis**
- M8 初版用并行数组按下标配对年龄，40 个案件张冠李戴 → 见 **7.2**

---

## 0. 结论先说

| 模块 | 字段 | 改前 | 改后 |
|---|---|---|---|
| M3 | 角色 `episodeRefs` | 0/147 | **147/147** |
| M4 | 案件 `kind` | 14 条 `动画案件` + 5 条 `None` | **0 脏值** |
| M5 | 案件 `caseType` | 2 别名 + 25 空 + 25 缺来源标签 | **52 条修正，0 遗留** |
| M2 | 案件 `sources` | 773/792 | **792/792** |
| M1 | 案件 `summary` | 45/792 | **472/792** |
| M6 | 剧集 `title.zhHans` / `zhHant` | 1214 / 1216 | **1217 / 1217** |
| M7 | 案件 `locations` | 0/792（键都不存在） | **401/792**（初版 491，剔除解答段地点后下调） |
| M8 | 案件 `victims` / `suspects` | 0 / 0 | **393 案·534 人 / 327 案** |

收尾验证：`VALIDATION_OK`、`APP_JS_OK`、`EN_TITLES_OK`、`P3_OK`、`NAV_KINDS_OK`、`UI_P4_OK`、`M8_OK`。
10 个数据脚本各跑两遍，全部 `IDEMPOTENT_OK（无改动，不写盘）`。

最终 `kind` 分布：`anime-original-case` 469 / `manga-case` 320 / `organization-case` 3。

---

## 1. M3 · 角色 `episodeRefs` 反推

**来源**：`data/entities/episodes.json` 的 `episodes[].characters`，本身 1217/1217 覆盖。

**做法**：倒排成 `{characterId: [集号升序去重]}`，写角色实体的 `episodeRefs`；已有非空的一律跳过。

**结果**：147 个角色全部有值。Conan 跨 1217 集，最多一个角色有 500+ 集引用。

**可验证性**：任一角色详情的「出场剧集」列表都能反查回剧集的 `characters` 字段。

脚本：`scripts/backfill-character-episode-refs.py`
备份：`/tmp/chars_pre_eprefs.json`

---

## 2. M4 · 案件 `kind` 枚举清洗

**问题**：`kind` 混了中文枚举 `动画案件` ×14（历史遗留）+ `None` ×5。

**判定只依据 DCW 原文**，不看标题、不推断：

| 原文特征 | 判定 |
|---|---|
| `mangaSource` 以 `Volume` 开头 | `manga-case` |
| `mangaSource = "TV Original"` | `anime-original-case` |
| `isAnimeExclusive: true` | `anime-original-case` |

**一条踩过的坑**：`case-tsukumo-magician-murder` / `case-yabuuchi-family-murder` 这两个没有 `dcwPage`，
`mangaSource` 取不到。按标题补链时，它们的标题同时出现在两个页面上：

- `The_Cornered_Famous_Detective!_Two_Big_Murder_Cases` — `Volume 14: Files 1-8 (131-138)`，`isAnimeExclusive: False`，`episodeNumbers = [96]` ← **正确**
- `Conan_Cornered_in_the_Darkness` — `TV Original`，845/846 集 ← 错连就会判成动画原创

按「同一剧集号 + 非 TV Original」选前者，两条都定为 `manga-case`。

脚本：`scripts/normalize-case-kind.py`
备份：`/tmp/cases_pre_kind.json`

---

## 3. M5 · 案件 `caseType` 规范化

三类脏值，共 52 条：

1. `['manga']` ×2 → 同义归并为 `['manga-adaptation']`
2. 空数组 ×25 → 按 `kind` 推导（`manga-case`→`manga-adaptation`，`anime-original-case`→`anime-original`）；
   `organization-case` 与 `kind` 也为空者保持空，不猜
3. 缺来源标签 ×25 → 补来源串

清完后 `caseType` 是 **792/792 非空**，无遗留。

脚本：`scripts/normalize-case-type.py`
备份：`/tmp/cases_pre_casetype.json`

---

## 4. M2 · 案件 `sources` 补 19 条

**方案假设错了，实际结构完全不同**：

- 原方案以为 `sources` 是 `{page, sourceId}` 对象数组 → **实际是来源 id 字符串数组**
- 原方案以为要新建来源 → **实际 `sources.json` 早就登记了这 19 个案件的专属页面来源**
  （`src-detective-conan-world-*-case`），只是案件没引用

所以这个模块只是「把已有来源 id 引到案件上」，没有新建任何来源。

页名从 `sources[].url` 的 `.../wiki/<PageName>` 反解，**必须 `urllib.parse.unquote`**——
19 个页里有 3 个带撇号被编码成 `%27`（如 `Mariko's_Sorrow`），不 unquote 就匹配不上。

结果：773 → 792/792。

脚本：`scripts/backfill-case-sources.py`
备份：`/tmp/cases_pre_sources.json`

---

## 5. M1 · 案件 `summary`（最大的一个，也改了方案）

### 5.1 改了方案：`resolution` 一律不用

方案原本写「`situation` 空则用 `resolution` 首段」。执行时读了原文才发现这不行——

`dcw-page-sections.json` 的 `resolution` 是**解答段**，首句直接点名凶手：

```
"Satoshi Miyahara is the kidnapper..."
"The killer is Akiko Yonehara..."
```

`summary` 是要在**案件列表页**显示的，写进去等于把「谁是凶手」摆在列表上。**这是泄底，坚决不用。**

### 5.2 只用 `situation`，其余留空

| 情况 | 条数 | 处理 |
|---|---|---|
| 已有 `summary`（历史人工中文） | 45 | 跳过，优先级最高 |
| 有 `situation` 段 | 427 | 搬原文 → **472** |
| 只有 `resolution`、无 `situation` | 320 | **留空** |
| 两段都无 | 13（含在上述 320 内） | **留空** |

320 条留空是**诚实的缺口，不是待办**。它们找不到不泄底的原文可搬。

### 5.3 写入形态

```json
"summary": { "en": "<DCW situation 原文，逐字搬运>" },
"summarySource": "General_Hospital_Murder_Case",
"summaryQuote": true
```

**写成对象不是字符串**，这样前端：
- `textOf()` 能取（已支持多语言对象）
- `langOf()` 返回 `en`
- `labelOf()` 自动加「英文原文·待译」角标 —— 不会伪装成中文

拼接规则：跳过纯标题行（`^[A-Z][A-Za-z' \-]{1,40}$` 且词数 ≤5），累积到 ≥200 字符或最多 3 段，
段间空行，**逐字搬运不改写**。

脚本：`scripts/backfill-case-summaries.py`
备份：`/tmp/cases_pre_summary.json`

---

## 6. M7 · 案件 `locations`（方案外，推翻了「零源」结论）

### 6.1 之前的「零源」判断是错的

`docs/PLAN-UNATTENDED-2026-10-28.md` 原来写着：

> `locations` 0/792 | `dcw-page-facts.json` 793 页**无任何 location/place/setting 字段**；YTV 无。**零源，不列为待办。**

前半句没错，`dcw-page-facts.json` 确实没有这个字段。**错在只探了 facts，没探 sections。**

`dcw-page-sections.json`（页面正文抽取）里，正文有 **853 行** `Location: <地点>`，覆盖 **491 个案件页**。

这是本轮第二个「探测盲区」教训：**判断「零源」之前，两个 raw 文件都要探。**

### 6.2 怎么写的

- 值能**精确命中** `data/entities/locations.json` 已有实体的 `name.en` → 写实体 id（**8 个**，如 `location-tropical-land`）
- 否则写**原文地点名**（**737 个不同值**，如 `Private Mansion`、`Tropical Street`）
- **不为泛称造实体**：`Apartment` / `Street` / `Unknown` 这类 655 个留在原文层，不建 `locations.json` 条目
- 同时写 `locationsSource` = DCW 页名

### 6.3 校验器同步改了

`scripts/validate-data.py` 原来要求 `locations` 必须是实体 id，
写入原文名后直接报 737 条警告。改成双形态：

```python
for ref in row.get("locations", []):
    if ref in location_ids:
        continue
    if ref.startswith("location-"):
        errors.append(f"{row.get('id')}: unknown locations reference {ref}")
    else:
        raw_location_names += 1
```

即：以 `location-` 开头的必须是真实实体（防打错 id），其余按原文地点名收录。

### 6.4 前端同步改了

`app.js` `detailSections()` 第 338 行：

```js
// 旧：refsText(raw.locations)  —— 解析不到的 id 被静默丢弃
if (raw.locations?.length) sections.push(['关联地点', raw.locations.map((x) => nameOfRef(x) || x).join('、')]);
```

`refsText()` 遇到解析不到的 id 会直接扔掉，而 M7 有 737 个原文名本来就解析不到，会被全部吞掉。
改成 `nameOfRef(x) || x`：能解析就显示实体名，解析不到就显示原文。**只影响地点，不动全局行为。**

### 6.5 顺带发现（下一批可做）

同批页面正文里还有：

| 行 | 出现次数（全文） | 落在 situation 段的页数 |
|---|---|---|
| `Victim` | 772 | 474 |
| `Age` | 525 | 358 |
| `Suspects` | 495 | 367 |
| `Cause of death` | 435 | 332 |
| `Culprit` | 274 | 201 |

前四个都是一条原文行，可以照 M7 的搬法补进案件非剧透字段 —— **已在本轮 M8 做完，见第 7 节**。
**`Culprit` 属解答，不能进非剧透字段。**

脚本：`scripts/backfill-case-locations.py`
备份：`/tmp/cases_pre_locations.json`、`/tmp/cases_pre_m7fix.json`

---

## 6bis. M7 口径修正：初版把解答段的地点也搬了

这一节是**自查后回改的**，值得单独记，因为它是本轮最危险的一个错。

### 问题

初版 `collect()` 同时扫 `situation`（案件设定段）和 `resolution`（解答段）：

```python
for key in ("situation", "resolution"):   # ← resolution 不该在这里
    for raw in sec.get(key) or []: ...
```

`resolution` 是解答段。里面的 `Location:` 是「案子查到最后才揭出来的地点」—— 
`Shiki Island`、`hospital`、`party hall`、`Terasawa's fishing tackle shop` 这类，
往往是**凶手藏身地或关键现场**。把它写进案件列表页显示的 `locations`，等于泄底。

### 实测影响

写了个探针逐个案件比对「现存储的地点是否只出现在解答段」：

```
cases whose locations contain resolution-only places: 167
```

**167 个案件**中招（约占当时 491 条的 34%）。

### 修正

- `collect()` 只读 `situation`
- 旧值中被剔除的地点不静默丢弃，记进 `locationsDropped`（数组），可回溯
- 一个案件若全部地点都来自解答段 → 删掉 `locations` 和 `locationsSource`，只留 `locationsDropped`

```python
def collect(page, sections):
    """只读 situation 段。resolution 是解答段，其中的地点属剧透，不取。"""
    ...
    for raw in sec.get("situation") or []:
```

### 结果

| | 修正前 | 修正后 |
|---|---|---|
| 有 `locations` 的案件 | 491 | **401** |
| 其中含解答段独有地点 | 167 | **0** |
| 失去全部地点的案件 | — | 90（原文只在解答段，正确取舍） |
| 记入 `locationsDropped` 的案件 | — | 167 |

覆盖从 491 降到 401 是**主动放弃**，不是能力下降。宁可少 90 条地点，也不在列表页告诉读者凶手藏在哪。

同一口径随后贯穿 M8（见下节）：**非剧透字段一律只读 `situation`**。

---

## 7. M8 · 案件 `victims` / `suspects`

### 7.1 来源与字段

`situation` 段里 DCW 用「案件事件块」逐条登记事实，一个案件页可能有多块
（`Furinkazan` 一个页面含 5 起死亡）：

```
Location: Forest, Nagano
Victim: Ayaka Tatsuo
Age: 27 years old
Cause of death: Hanging
Suspects: Naonobu Torada, Tatsue Torada, ...
```

写入三个字段：

```json
"victims":   [{ "name": "...", "age": "...", "causeOfDeath": "..." }],
"suspects":  ["原文整串"],
"caseFactsSource": "<DCW 页名>"
```

### 7.2 踩到的坑：并行数组按下标配对会张冠李戴

**第一版**写成两个平行数组：

```json
"victims":    ["Yoshiro Torada", "Koji Tatsuo", ...],
"victimAges": ["27 years old", "31 years old"]
```

靠下标配 `victims[i] ↔ victimAges[i]`。写完抽查发现 Furinkazan 直接错了：

| | 5 个被害人 | 2 个年龄 |
|---|---|---|
| 按下标配 | `Yoshiro Torada` → 27 岁 | ← **27 岁其实是 Ayaka 的** |

探针统计：**40 个案件**的 `victims` 与 `victimAges` 长度不等。原因很简单——
原文只给部分被害人写了年龄，压平成数组后位置信息就丢了。

**这不是显示 bug，是数据错误**，会把 A 的年龄挂到 B 头上。已回滚（`/tmp/cases_pre_m8.json`）重写。

### 7.3 改成块内配对

`victims` 改为对象数组，年龄/死因在**解析时**就按块归属给当前被害人：

```python
cur = None  # 当前被害人
for line in situation:
    if FORBIDDEN.match(line):      # Culprit/Resolution/Trick/Motive → 断开配对
        cur = None; continue
    if 是 Victim 行: cur = 取或建被害人对象
    if 是 Age 行   : 只有 cur 存在且还没有 age 才写   # 不借别人的
    if 是 Cause 行 : 同上
```

结果（`case-furinkazan` 实测）：

```
Yoshiro Torada     （Swept away by a tornado）
Koji Tatsuo        （Blunt force trauma）
Kuroto Kai         （Dehydration after being unable to move...）
Ayaka Tatsuo       （27 years old、Hanging）      ← 配对正确
Shigetsugu Torada  （31 years old、Electrocution）
```

前三人原文没写年龄，就**没有**年龄字段。

### 7.4 三条防污染规则

1. **`Culprit` 行一律不搬**。`situation` 段里也有 97 次 `Culprit:`，属解答。
2. **占位值不搬**：`Unknown` / `Unknown culprit(s)` / `N/A` / `None`。
   探针查出 8 条 `Suspects: Unknown culprit`（原文如此），过滤后 suspects 覆盖 362 → 327。
3. **`suspects` 不拆名**。`Naonobu Torada, Tatsue Torada, and Akira Tatsuo` 原样保留——
   拆名是推断，且 `Tatsuo family` 这种集合名根本拆不开。

### 7.5 覆盖

| 字段 | 覆盖 |
|---|---|
| `victims` | **393 / 792 案，534 人** |
| 其中带原文年龄 | 383 人 |
| 其中带原文死因 | 347 人 |
| `suspects` | **327 / 792 案** |

### 7.6 校验与渲染

- `validate-data.py` 新增：`victims` 每项只能是 `{name, age?, causeOfDeath?}`（未知键报错）；
  `suspects`/`locationsDropped` 必须是非空字符串数组，且不得含 `culprit/killer/murderer` 字样
- `app.js` 新增 `formatVictim()`，渲染成 `姓名（年龄、死因）`，缺项省略
- `detailSections()` 的 section 支持第三项 `pre=true`，配合 `.detail-sections p.pre-line{white-space:pre-line}`
  保留换行（否则 `\n` 被 `<p>` 折叠成空格）
- 新增 `scripts/verify-m8-case-facts.js`：逐个案件核验渲染无 `[object Object]`、
  每个被害人名字都在、**所有年龄死因都能在该案原文里找到**（防串人），并硬校验 Furinkazan 的配对

脚本：`scripts/backfill-case-facts.py`
备份：`/tmp/cases_pre_m8.json`

---

## 8. M6 · 剧集中文标题（分了两种来源）

原先判断「无中文源、不做」。后来按要求补全，但要**分清哪些是转换、哪些是翻译**：

| 集 | 缺什么 | 做法 | 标记 |
|---|---|---|---|
| EP.1077 | `zhHans` | 本集已有 `zhHant`「黑衣組織的謀略（狩獵）」→ **逐字繁转简** | `zhHansFrom: "zhHant-transliteration"` |
| EP.1203 | `zhHans` | 本集已有 `zhHant`「園子與柯南的怪談之夜」→ **逐字繁转简** | 同上 |
| EP.1217 | `zhHans` + `zhHant` | 无任何中文稿，按日文「背中を押す手」**人工自译**「推背的手」 | `translationStatus: "machine"` + `translationNote` |

**为什么必须分开记**：前两条不是翻译，同一记录里就有繁中稿可逐字回验；
1217 是自译，**不能冒充官方译名**，必须让前端和读者都知道。

繁转简用**显式字表**而不是整库转换（只收本批实际出现的 10 个字），转换后校验长度一致，
防止漏字或一个繁体字被换成两个字。

结果：`title.zhHans` / `title.zhHant` 均 **1217/1217**。全库仅 EP.1217 一条是自译。

来源复核：DCW 英文/日文、YTV 日文均无中文译名；zh.wikipedia API curl 返回空、百度百科不可达。

脚本：`scripts/fill-missing-episode-titles-zh.py`
备份：`/tmp/eps_pre_m6.json`

---

## 9. 验证与幂等

```bash
cd /Users/ls/Desktop/agent/Hermes/conan-archive
python3 scripts/validate-data.py | tail -1          # VALIDATION_OK
node --check app.js                                 # APP_JS_OK
node scripts/verify-en-titles.js                    # EN_TITLES_OK
node scripts/verify-p3-spoilernote.js               # P3_OK
node scripts/verify-nav-kinds.js                    # NAV_KINDS_OK
node scripts/verify-ui-p4.js                        # UI_P4_OK
node scripts/verify-m8-case-facts.js                # M8_OK
```

10 个数据脚本连跑两遍，各自尾部输出 `IDEMPOTENT_OK（无改动，不写盘）`——二次运行零改动。

数据写入统一 `json.dumps(..., ensure_ascii=False, indent=2)` + 末尾换行。

本会话最终实测输出：

```
VALIDATION_OK / APP_JS_OK / EN_TITLES_OK / P3_OK / NAV_KINDS_OK / UI_P4_OK / M8_OK
渲染核验案件 393 个
```

---

## 10. 回滚

```bash
cd /Users/ls/Desktop/agent/Hermes/conan-archive

# 剧集
cp /tmp/eps_pre_m6.json          data/episodes/episodes.json       # 回滚 M6 中文标题

# 案件（同一文件，按需选择）
cp /tmp/cases_pre_m8.json        data/entities/cases.json          # 回滚 M8 victims/suspects
cp /tmp/cases_pre_m7fix.json     data/entities/cases.json          # 回滚 M7 口径修正（回到 491 的旧口径）
cp /tmp/cases_pre_locations.json data/entities/cases.json          # 回滚 M7 初版（含解答段地点）
cp /tmp/cases_pre_summary.json   data/entities/cases.json          # 回滚 M1
cp /tmp/cases_pre_sources.json   data/entities/cases.json          # 回滚 M2
cp /tmp/cases_pre_casetype.json  data/entities/cases.json          # 回滚 M5
cp /tmp/cases_pre_kind.json      data/entities/cases.json          # 回滚 M4

# 角色
cp /tmp/chars_pre_eprefs.json    data/entities/characters.json     # 回滚 M3
```

**注意**：`cases.json` 的 7 个模块共享同一文件，回滚任意一项都会连带丢掉其他模块。
只回滚一项后，按 **M4 → M5 → M2 → M1 → M7 → M8** 顺序重跑对应脚本即可恢复其余（都是幂等脚本，会补回）。

**`/tmp/cases_pre_m7fix.json` 是 491 那条旧口径**（含解答段地点，有泄底风险），
仅用于追溯，正常不要回滚到它。

前端回滚：`cp /tmp/app.js.bak app.js` —— **慎用**，那是更早的版本，会连地点回落、M8 被害者渲染一起丢掉。

`/tmp` 重启会丢，需要长期保留请复制出去。

---

## 11. 本轮新增/改动的文件清单

**新增脚本（10）**

```
scripts/backfill-character-episode-refs.py     M3
scripts/normalize-case-kind.py                 M4
scripts/normalize-case-type.py                 M5
scripts/backfill-case-sources.py               M2
scripts/backfill-case-summaries.py             M1
scripts/backfill-case-locations.py             M7（含口径修正）
scripts/backfill-case-facts.py                 M8
scripts/fill-missing-episode-titles-zh.py      M6
scripts/verify-m8-case-facts.js                M8 渲染验证
scripts/verify-*.js 里的 formatVictim 抽取修复   （改，非新增）
```

**改动**

| 文件 | 改动 |
|---|---|
| `scripts/validate-data.py` | `locations` 双形态判定；新增 `victims` 结构校验、`suspects`/`locationsDropped` 串数组校验、`summary` 字符串/对象两态校验；新增 `SPOILER_LABEL` 剧透字样检查 |
| `app.js` | `detailSections()` 地点渲染改 `nameOfRef(x) \|\| x`；新增 `formatVictim()`；section 支持 `pre` 标记；被害者/嫌疑人段渲染 |
| `styles.css` | 新增 `.detail-sections p.pre-line{white-space:pre-line}` |
| `scripts/verify-p3-spoilernote.js` | 抽取函数列表加 `formatVictim`（否则 eval 时报未定义） |
| `scripts/verify-ui-p4.js` | 同上 |
| `docs/PLAN-UNATTENDED-2026-10-28.md` | 修正 `locations` 「零源」结论；补 M7 口径、M8 规格；M1 460→472；M6 改为已完成；产出表与验证命令同步 |
| `docs/DATA-SCHEMA.md` | 新增六节：case `summary` 对象 / `locations` 双形态（含只取 situation 的强制口径）/ `victims`+`suspects` / `kind` 枚举 / `caseType` / 剧集标题补法 / 角色 `episodeRefs` |
| `docs/HANDOFF-NEW-SESSION.md` | 新增 §0.9、快照表 +6 行、脚本索引 +9、备份点 +9、剩余任务 9/10 改为已完成 |
| `docs/CHECKPOINT-2026-10-28-UNATTENDED.md` | 本轮进度存档 + 收尾复核记录 |
| `docs/OPERATION-LOG-2026-10-28-M1-M2-M3-M4-M5-M7.md` | 本篇，含 6bis 口径修正记录 |

**数据文件**

```
data/entities/cases.json        （kind / caseType / sources / summary / locations / locationsDropped / victims / suspects / caseFactsSource）
data/entities/characters.json   （episodeRefs）
data/episodes/episodes.json     （title.zhHans / zhHant / zhHansFrom / translationStatus）
```

**清理**

`scripts/_probe_*.py` 11 个已移入 `scripts/_archive/probes-2026-10-28/`；
本轮新写的探针（`_probe_case_facts.py`、`_probe_fact_diff.py`、`_probe_loc_spoiler.py`、
`_probe_plan_m8.py`、`_probe_multi.py`、`_probe_m8_check.py`、`_probe_culprit_sus.py`、`_probe_align.py`）
同样归档到同一目录，`scripts/` 根目录不留探针。
