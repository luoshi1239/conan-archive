# Conan Archive · 操作日志（第二批：2026-10-27 续）

> 接手自 `docs/HANDOFF-NEW-SESSION.md`。本批只做**可验证、不编造**的补全与隐患修复。
> 全部脚本幂等（二次运行零改动），结束状态 `VALIDATION_OK`。

---

## 一、本批成果快照

| 维度 | 接手前 | 现在 | 说明 |
|---|---|---|---|
| 剧集 en summary | 598 / 1217 | **1212 / 1217** | +614 集，全部 DCW 原文搬运 |
| 剧集 summary 完全为空 | 546 | **5** | 713/714/882/1061/1187 页面无该集叙述正文 |
| 案件 title 缺失 | 19 | **0** | 其中 2 个是字段名写错（`titles`）导致 |
| 案件 deepSpoilers | 46 | **149** | +103 案（四字段原文 + Resolution 原文） |
| L3 五字段齐全 | 46 | **149** | 同上 |
| 案件有 culprit | 242 | **243** | +1（唯一空位，高置信） |
| 案件↔角色挂接 | 少量 | **2507 条** | 14 个角色的 name/aliases 与 castNames 精确匹配 |
| 剧集有角色 | 73 / 1217（6%） | **1217 / 1217（100%）** | 4398 条，经 案件→角色 关系传递 |
| DCW 正文章节抽取 | 标题文字切块（污染） | **id 锚点切块（干净）** | 793 页全部产出正文 |
| 来源/案件/剧集总数 | 72 / 792 / 1217 | 不变 | 本批未新增实体 |

`python3 scripts/validate-data.py` → `VALIDATION_OK`
`python3 scripts/report-relation-closure.py` → `total=0`（案件/篇章无未闭合）

---

## 二、修复的隐患（重点）

### 1. `dcw-page-blocks.json` 的 Situation 段其实是目录残留

- **现象**：546 集"缺 summary"，接手时判断是"DCW 页面没有 Situation 段"。
- **实测**：536 页的 `Situation` 块内容是 `["3.1.1"]`，`Part 1` 块前 45 行是 BGM 歌曲表。
- **根因**（`extract-dcw-page-blocks.py` 三个缺陷）：
  1. 按标题**文字**切块，页面目录（TOC）里也有 "Situation" 字样，其后的正文是目录编号；
  2. 正文 h3 `Situation` 紧跟 h4 `Part 1`，两标题相邻 → Situation 正文长度 0 被丢弃；
  3. Part 1 块从 TOC 位置起切，混入 BGM 表格。
- **处理**：新增 `scripts/extract-dcw-page-sections.py`，改为**按 HTML 章节锚点**（`id="Situation"` / `id="Part_1"` / 内层 `<span class="mw-headline" id=...>`）切分，正文同时纳入 `<p>/<li>/<dd>/div` 裸文本（spoiler 内容常以裸文本存在于 `<div id="toggledisplay1">`），并按 `Location:/Victim:` 等键把粘连段拆开。
- **结果**：793/793 页产出正文（`noText: 0`）；Situation 460 / Part1 337 / Part2 275 / Resolution 742。
- **旧文件保留**：`dcw-page-blocks.json` 未改动（L3 候选已基于它生成并应用），新脚本作为**唯一正确的抽取入口**，后续 L3 二次挖掘应用新文件。

### 2. 剧集 summary 补齐（不翻译、不总结）

`scripts/backfill-episode-summaries-v2.py`：

- 只填空值，已有内容一律不动；
- 多集一页时按集在页面内的顺序取对应 `Part N`（第 1 集→Part 1，第 2 集→Part 2…），避免两集共用同一段；
- 跳过 `Location:`/`Victim:` 等结构化元数据行，取叙述正文；
- 原文本身只有一句话时（两集一页的第二集常见）如实保留并标记 `shortFromSource`；
- `zhHans`/`zhHant` 留空等人工，**不自行翻译**。

结果：**+614 集**（598 → 1212）；5 集因页面该集段落只有案件信息表或无正文而留空，已列在
`docs/SUMMARY-BACKFILL-REPORT.json` 的 `blocked` 里。

### 3. 案件 title 丢失（字段名 `titles` 写错位置）

- 19 个案件 `title` 全空，其中 2 个（EP.96 拆分案）手写标题一直存在 `titles`（复数）键里，
  与全库其余 773 个实体的 `title`（单数）不一致，前端读不到。
- 处理：
  - `scripts/backfill-case-titles.py` —— 17 个从 DCW 页面 `heading`/`jpTitle` 原文补 en/ja；
  - `scripts/normalize-case-titles.py` —— 把 19 个 `titles` 合并进 `title`（已有值优先，手写中文保留进 zhHans/zhHant/aliases），删除错误键。
- 结果：**0 个案件缺标题**，全库字段统一。

### 4. `normalize-episodes.py` 会把 EP.86/113 的裁定打回去（回退隐患，已修）

- **现象**：重跑 `normalize-episodes.py` 后，EP.86/EP.113 的 `adaptation` 从已裁定的 `manga` 变回 `anime-original`。
- **根因**：`adaptation` 虽在 `KEEP_IF_TRUTHY` 里，但合并逻辑只在"新值为空"时才保留旧值；raw 目录写的是「動畫原創」（truthy），于是 185 行之后 `backfill-dcw-manga-source.py` 的 SV 裁定被覆盖。
- **修复**：在 raw 合并后加"来源佐证优先"判断——当 `raw.dcwMangaKind == manga-special-volume` 且 `dcwMangaSource` 以 `SV` 开头时，保留此前已裁定的 `manga`/`mixed`。
- **验证**：EP.86/113 保持 `manga`；`normalize-episodes.py` 连跑两次零改动；summary 1212 条未被冲掉。

### 5. 已核实的旧结论

- EP.98—101 手工案件的凶手罗马字在缓存原文中**逐字可查**（`Ryuichi Seto` / `Manabu Sawai` ✓），抽查通过。
- 案件 L3 候选三字段（motive/method/evidence）互不雷同（平均 Jaccard 0.14–0.18，无三字段同文），非"整段复制"。

---

## 三、新建脚本

| 脚本 | 作用 | 幂等 |
|---|---|---|
| `extract-dcw-page-sections.py` | 按章节锚点抽取 DCW 正文（793 页） | ✅ |
| `backfill-episode-summaries-v2.py` | 用上述正文补 summary（+614 集） | ✅ |
| `backfill-case-titles.py` | 补 17 个案件标题（DCW 原文） | ✅ |
| `normalize-case-titles.py` | `titles` → `title` 合并（19 个） | ✅ |
| `build-l3-approved.py` | 从审核队列生成 `docs/L3-APPROVED.json` | ✅ |
| `apply-l3-approved.py` | 按批准清单写入案件字段（**绝不覆盖非空**） | ✅ |

新增产物：`data/raw/dcw-page-sections.json`、`docs/SUMMARY-BACKFILL-REPORT.json`、
`docs/CASE-TITLE-BACKFILL.json`、`docs/CASE-TITLE-NORMALIZE.json`、`docs/L3-APPROVED.json`。

备份：`/tmp/ca/episodes_pre_summary_v2.json`、`/tmp/ca/cases_pre_title_backfill.json`、
`/tmp/ca/cases_pre_title_normalize.json`。

---

## 四、L3 深度剧透写入（本批已执行，可一键回滚）

用户偏好是"只搬原文、不编造、全部做完一次总审核"，因此按**最保守口径**执行：

1. `scripts/build-l3-approved.py --only-ready` —— 只批准审核队列里 `readyToApprove=true` 的
   **111 案**（交接单点名的"四字段候选齐全"那批），不是队列全量 763 案。
2. `scripts/apply-l3-approved.py` —— 只写**空字段**，绝不覆盖任何已有中文值；
   实际写入 **319 个字段**（motive 106 / method 106 / evidence 106 / culprit 1）。
3. `scripts/backfill-case-resolution.py` —— L3 第五字段 `resolution` 用 DCW Resolution 原文块
   补 **103 案**（`normalize-case-status.py` 要求五字段齐全才升 deepSpoilers）。
4. `python3 scripts/normalize-case-status.py` → deepSpoilers **46 → 149**。

所有写入字段都带 `dcwL3Source.<field> = {page, block, confidence, quote, lang:"en", reviewedBy}`
可逐字段追溯原文出处。

### ⚠ 已知代价：这些字段目前是**英文原文**

现有 242 条 culprit 与手工 L3 都是中文，这批 319+103 个字段是 DCW 英文长段（中位 ~300 字符）。
全库因此存在"中文正文 + 英文 L3"的混排。若要中文，需人工翻译（本会话不擅自机器翻译）。

### 一键回滚

```bash
cp /tmp/ca/cases_pre_l3_approved.json data/entities/cases.json      # 回到写入前（含 title/角色挂接前状态需叠加下列备份）
python3 scripts/normalize-case-status.py
```

分批备份（按执行顺序叠加）：

| 备份 | 覆盖内容 |
|---|---|
| `/tmp/ca/episodes_pre_summary_v2.json` | summary 补齐前 |
| `/tmp/ca/cases_pre_title_backfill.json` | 标题补全前 |
| `/tmp/ca/cases_pre_title_normalize.json` | `titles`→`title` 合并前 |
| `/tmp/ca/cases_pre_l3_approved.json` | L3 四字段写入前 |
| `/tmp/ca/cases_pre_resolution.json` | resolution 补齐前 |
| `/tmp/ca/cases_pre_char_links.json` / `chars_pre_char_links.json` | 角色挂接前 |

## 五、角色关系挂接（本批已执行）

`scripts/link-character-cases.py`：

- 依据：案件 `castNames`（DCW Case 段 Cast 原文）与角色 `name.*`/`aliases` **精确匹配**（大小写不敏感，
  不做同姓/缩写推断，不新建实体）；
- `case.characters` += characterId（2507 条）；
- `character.caseRefs` = 反向索引（新建字段）；
- 剧集角色由「剧集 → 案件 → 案件角色」关系传递补齐（4398 条，覆盖 1217/1217 集）。

仍未做（等用户决定）：把 388 个 castNames 里的**非现有 14 角色**批量建成实体。
它们只有英文名、无中文译名，会显著改变库的结构与质量分布，不擅自动。

## 六、其他未动项（如实说明）

- 2 条未裁决冲突（`docs/FACT-CONFLICTS.json`）：EP.96 两案一页已确认是本地有意拆分；
  **EP.585 归属（Kirin's Horn vs Kobayashi）仍需人裁**，未改。
- conan-archive 仍未纳入 git（需用户确认后提交）。
- QQ 通知/mimoflash 看门狗：无凭证、无 CLI，维持"未实现"的如实状态。
- 剧集 `structure`/`detailStatus` 仍为 0（120 集结构化动画那项本批未动）。
