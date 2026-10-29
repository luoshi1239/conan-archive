# 进度存档 — 2026-10-28 无人值守批次（M1–M8，全部完成）

> 目的：上下文过长需开新会话。本文件就是新会话的起点，读完可以直接续跑。
> 项目目录：`/Users/ls/Desktop/agent/Hermes/conan-archive`（未纳入 git，勿擅自 `git init`）

---

## 1. 一句话现状

**方案里 6 个模块（M1–M6）全部完成，另加方案外两个（M7 地点、M8 被害者/嫌疑人）。**
全部脚本幂等（二次运行零改动），收官验证 **七项全绿**：

```
VALIDATION_OK  APP_JS_OK  EN_TITLES_OK  P3_OK  NAV_KINDS_OK  UI_P4_OK  M8_OK
```

**没有遗留的"待补字段"任务了**，剩下的是「无源不补」的诚实缺口（见 §5）。

---

## 2. 完成清单（含实测数字）

| 模块 | 内容 | 改前 | 改后 | 脚本 | 备份 |
|---|---|---|---|---|---|
| M3 | 角色 `episodeRefs` 反向索引 | 0/147 | **147/147** | `backfill-character-episode-refs.py` | `/tmp/chars_pre_eprefs.json` |
| M4 | 案件 `kind` 枚举规范化 | 14 `动画案件` + 5 `None` | **0 脏值** | `normalize-case-kind.py` | `/tmp/cases_pre_kind.json` |
| M5 | 案件 `caseType` 规范化 | 2 别名 + 25 空 + 25 缺来源 | **52 条修正** | `normalize-case-type.py` | `/tmp/cases_pre_casetype.json` |
| M2 | 案件 `sources` 补来源 | 773/792 | **792/792** | `backfill-case-sources.py` | `/tmp/cases_pre_sources.json` |
| M1 | 案件 `summary` 设定段原文 | 45/792 | **472/792** | `backfill-case-summaries.py` | `/tmp/cases_pre_summary.json` |
| M6 | 剧集 `title.zhHans` / `zhHant` | 1214 / 1216 | **1217 / 1217** | `fill-missing-episode-titles-zh.py` | `/tmp/eps_pre_m6.json` |
| M7 | 案件 `locations` 原文地点 | 0/792 | **401/792** | `backfill-case-locations.py` | `/tmp/cases_pre_m7fix.json` |
| M8 | 案件 `victims` / `suspects` | 0 / 0 | **393 案·534 人 / 327 案** | `backfill-case-facts.py` | `/tmp/cases_pre_m8.json` |

最终 `kind` 分布：`anime-original-case` 469 / `manga-case` 320 / `organization-case` 3。

---

## 3. 三个必须知道的关键判断

### 3.1 非剧透字段一律只读 `situation`，绝不读 `resolution`

`dcw-page-sections.json` 每个页面有两个段：

- `situation` — 案件**设定段**（案发、现场、被害人、嫌疑人）
- `resolution` — **解答段**（动机、手法、凶手、案发后追查出的地点）

解答段**直接点名凶手**：

```
"Satoshi Miyahara is the kidnapper..."
"The killer is Akiko Yonehara..."
```

而且解答段里的 `Victim` 是"案发后追加的伤亡"，甚至把 Conan 列为被害人；
两段的 `Victim` 实测 **146 处不一致**。

**教训**：M7 初版图省事两段都读了，结果 **167 个案件**的地点混进解答段独有地点
（`Shiki Island`、`hospital`、`party hall`…），等于在列表页告诉读者凶手藏在哪。
现已全部剔除，被剔除的值记在 `locationsDropped` 里可回溯。

覆盖因此从 491 降到 **401**，90 个案件失去全部地点（原文只在解答段）——
这是**主动放弃，不是能力下降**。

### 3.2 `victims` 必须是对象数组，不能是并行数组

年龄/死因只在**同一原文块内**有效：

```
Victim: Ayaka Tatsuo
Age: 27 years old
Cause of death: Hanging
```

初版写成 `victims[] + victimAges[]` 按下标配对，实测 **40 个案件两者长度不等**
（Furinkazan 5 个被害人只有 2 个年龄），会把 Ayaka 的 27 岁挂到 Yoshiro 头上。
这不是显示 bug，是**数据错误**。已改为 `[{name, age?, causeOfDeath?}]` 块内配对。

### 3.3 判断「零源」之前，两个 raw 文件都要探

`dcw-page-facts.json` 确实没有 location/victim 字段，但 `dcw-page-sections.json` 正文里
有 853 行 `Location:`、772 行 `Victim:`、525 行 `Age:`、495 行 `Suspects:`。
当初只探了 facts 就断言「零源不可补」，漏了一整个模块的量。

---

## 4. 新会话第一件事：跑这套验证

```bash
cd /Users/ls/Desktop/agent/Hermes/conan-archive
python3 scripts/validate-data.py | tail -1          # VALIDATION_OK
node --check app.js && echo APP_JS_OK
node scripts/verify-en-titles.js                     # EN_TITLES_OK
node scripts/verify-p3-spoilernote.js                # P3_OK
node scripts/verify-nav-kinds.js                     # NAV_KINDS_OK
node scripts/verify-ui-p4.js                         # UI_P4_OK
node scripts/verify-m8-case-facts.js                 # M8_OK
```

幂等复核（8 个数据脚本，跑两遍看是否零改动）：

```bash
cd /Users/ls/Desktop/agent/Hermes/conan-archive
python3 scripts/backfill-character-episode-refs.py
python3 scripts/normalize-case-kind.py
python3 scripts/normalize-case-type.py
python3 scripts/backfill-case-sources.py
python3 scripts/backfill-case-summaries.py
python3 scripts/backfill-case-locations.py
python3 scripts/backfill-case-facts.py
python3 scripts/fill-missing-episode-titles-zh.py
```

每个都应打印 `IDEMPOTENT_OK（无改动，不写盘）`。

---

## 5. 剩余任务

### 5.1 无源，按口径不补（不要再试）

| 缺口 | 为什么 |
|---|---|
| 133 个角色中文名 | 需官方译名源；库内只有罗马字 |
| 60 集 `solvedBy` | DCW 总表与 YTV 都无此字段；从剧情反推＝编造 |
| 741 案件中文标题 | 需人工译名源 |
| 320 条案件 `summary` | 原文只有解答段，搬了就是泄底 |
| `locations` 剩 391 条 | 原文 `Location:` 行只出现在解答段 |
| 角色 `role` / `summary` / `name.ja` | 793 页全是案件/剧集页，没有角色页 |

### 5.2 可做但价值有限

1. **`Weapon` 行只有 3 处**（`Pipe bomb` / `Falling flower pot` / `Presumably a gun`）——量太小没建字段。
2. **`Time` / `Time of death` 行**零散出现，未建字段。
3. **269 个低频 `castNames` 未实体化**、`Detective Boys`（456 集）应建组织。
4. **38 处重复译文**待清。
5. **22 个总表页面**对应案件的 `sources[].page` 缺精确页名。

### 5.3 需要人工复核的一条

**EP.1217「推背的手」是自译**，标了 `translationStatus: "machine"`。
日文原题「背中を押す手」、DCW 英文 `The Hands Pushing Their Back`，可及来源均无中文译名。
拿到官方译名后应覆盖，并把状态改 `human`、清掉 `translationNote`。

---

## 6. 唯一一条自译 vs 两条繁转简（别混）

| 集 | 来源 | 标记 |
|---|---|---|
| EP.1077「黑衣组织的谋略（狩猎）」 | 本集 `zhHant` 逐字繁转简 | `zhHansFrom: "zhHant-transliteration"` |
| EP.1203「园子与柯南的怪谈之夜」 | 同上 | 同上 |
| EP.1217「推背的手」 | 无中文源，人工自译 | `translationStatus: "machine"` + `translationNote` |

前两条**不是翻译**，同一记录里就有繁中稿可逐字回验。

---

## 7. 回滚命令

```bash
cd /Users/ls/Desktop/agent/Hermes/conan-archive

cp /tmp/eps_pre_m6.json          data/episodes/episodes.json     # M6
cp /tmp/cases_pre_m8.json        data/entities/cases.json        # M8
cp /tmp/cases_pre_m7fix.json     data/entities/cases.json        # M7（保留 401 口径）
cp /tmp/cases_pre_summary.json   data/entities/cases.json        # M1
cp /tmp/cases_pre_sources.json   data/entities/cases.json        # M2
cp /tmp/cases_pre_casetype.json  data/entities/cases.json        # M5
cp /tmp/cases_pre_kind.json      data/entities/cases.json        # M4
cp /tmp/chars_pre_eprefs.json    data/entities/characters.json   # M3
```

`cases.json` 七个模块共享同一文件，回滚任意一项会连带丢掉其余；
按 **M4 → M5 → M2 → M1 → M7 → M8** 顺序重跑脚本即可补回（都幂等）。

⚠ `/tmp/cases_pre_locations.json` 是 **491 的旧口径**（含解答段泄底地点），仅追溯用，正常别回滚到它。

前端回滚：`cp /tmp/app.js.bak app.js` —— 慎用，会连地点回落、M8 被害者渲染一起丢掉。

---

## 8. 铁律（新会话沿用）

- 只搬原文、不编造、不覆盖非空字段；语义不符宁可留空。
- **非剧透字段只读 `situation`**，`Culprit` 一律不搬。
- 每批做完再统一总审核，不要一步一推请示。
- 脚本必须幂等，结束状态必须 `VALIDATION_OK`。
- JSON 一律 `json.dumps(..., ensure_ascii=False, indent=2)` + 末尾换行，**禁止 `indent=1`**。
- Python 3.9：**不能用 `str | None`**，用 `typing.Optional`。
- 长脚本用 `write_file` 落盘再跑，**不用 heredoc**。
- 不擅自 `git init`、不擅自启动 gateway。
- 绝不返回空响应。
- 探针脚本不要留在 `scripts/` 根目录，用完移入 `scripts/_archive/probes-2026-10-28/`。

---

## 9. 相关文档

| 文件 | 内容 |
|---|---|
| `docs/OPERATION-LOG-2026-10-28-M1-M2-M3-M4-M5-M7.md` | 本轮完整操作日志（11 节，含两次回改记录） |
| `docs/PLAN-UNATTENDED-2026-10-28.md` | 执行方案（已同步为最终状态） |
| `docs/DATA-SCHEMA.md` | 数据结构规范（含 M1/M3/M4/M5/M6/M7/M8 七节新字段） |
| `docs/HANDOFF-NEW-SESSION.md` | 项目总交接单（§0.9 为本轮，快照表已更新） |
