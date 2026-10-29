# 2026-10-28 · P3 / P1 / P2 + 特别篇集号修复 + 冲突收口

本轮按 P3 → P1 → P2 顺序推进，并完成 A（文档）与 B（缺口 / 冲突）两部分。

---

## 1. P3 · `spoilerNote` 上页面

### 问题

前一批把 7 个案件被污染的 `spoiler` 字段（本应是 1/2/3 整数，却被旧脚本写进 94–159 字中文分析）
迁到了新字段 `spoilerNote`，但**前端从未渲染该字段** —— 等于换个地方继续看不见。

### 处置

`app.js` 的 `detailSections()` 案件分支新增「收录备注」分区：

```js
if (raw.spoilerNote) sections.push(['收录备注', raw.spoilerNote]);
```

### 验证

新增 `scripts/verify-p3-spoilernote.js`，从 `app.js` 抽取真实 `detailSections` 执行：

```
✓ 7/7 全部渲染（94–159 字）
✓ 无备注的案件不出现该分区
✓ spoiler 类型非数字 0
P3_OK
```

---

## 2. P1 · 剧集 `solvedBy` 解析

### 根因

`solvedBy` 挂接率只有 574/1217（47%），但**不是数据缺失** —— DCW 原文写法带大量补充说明：

| 原文写法 | 集数 | 说明 |
|---|---|---|
| `Kogoro Mouri (via Conan)` | 409 | 括号内是「借助谁破案」，不是第二个人 |
| `Conan Edogawa` | 299 | 直书 |
| `Hiroshi Agasa (via Conan)` | 若干 | 同上 |
| `Sonoko Suzuki (via Conan}` | 1 | **原文括号半角开、全角闭** |
| `Conan Edogawa (x2)` | 若干 | 倍数说明 |
| `No one` / `N/A` | 4 | 本就没有破案者 |

### 处置

新增 `scripts/resolve-episode-solvedby.py`：

1. 剥脚注 `[1]`；
2. 剥括号补充（含不配对的 `(via Conan}` 变体）；
3. 剥 `(x2)` 倍数；
4. 取人名 → 查角色实体（含别名表）；
5. 原文保留在 `solvedByRaw`，解析来源写入 `solvedByParsedFrom`；
6. `No one`/`N/A` 写 `solvedByNote`，**不建角色引用**。

### 结果

```
574 → 1157 集（新增 583）
```

剩 4 条如实保留（3 种写法）：

| 写法 | 集数 | 不解析理由 |
|---|---|---|
| `Ryohei Onda` | 2 | 库中无此角色，不建实体 |
| `Heihachiro Shiota` | 1 | 同上 |
| `Detective Boys` | 1 | 群像，不是个人 |

---

## 3. P2 · 剧集 `castNames` 实体化

### 口径

与 P4（按**案件** castNames）同口径，本次按**剧集** castNames，阈值 ≥5 集。
闸门比 P4 更严，新增三类排除：

| 写法 | 判定 |
|---|---|
| `Unknown child` / `Unnamed officer` / `Anonymous…` | 身份不明 |
| `Forensic member` / `FBI Agent 1` / `Police Officer 2` | 岗位或编号（正则含 member/agent/officer/guard/staff… + 结尾数字） |
| `Sasaki` / `Nakamichi` / `Tashiro` / `Hidaka` / `Oda` / `Shiota` | 仅姓氏 |
| `Detective Boys` / `Kamen Yaiba` / `Gomera` / `Night Baron` | 非个人 |

### 结果

```
新建 46 个（Minerva Glass 12 集、Suguru Itakura 11、Tsutomu Akai 11、Kazumi Sanada 10、Pisco 9 …）
角色实体 101 → 147
跳过 37 个（非个人 12 / 岗位编号 / 仅姓氏 / 身份不明）
中文名一律留空 translationStatus: "pending"，未猜一个字
```

> 注：首跑为 43 个；随后第 4 节补上 21 集特别篇集号，新暴露 3 个达门槛人物
> （如 `Ethan Hondou`，出现在 491–504「红与黑的碰撞」全部 16 集），再跑一次级联到 **46**。
> 这是正常级联，不是重复建实体——脚本以 `name.en` 去重，二次运行零改动。

新增剧集↔角色挂接 **+277**（46 个角色共被剧集引用 **335** 次），
再由 `link-character-cases.py` 补案件侧挂接 **+125** 条（角色详情「出场案件」不再空白）。

### 事故：来源 id 写错

首版脚本 `SOURCES = ["src-detective-conan-world-cases", …]`，但
`src-detective-conan-world-cases` **在 `data/sources.json` 中根本不存在**，
`validate-data.py` 拦下 43 条 `unknown sources`。

正确 id 是 `src-detective-conan-world-characters` + `src-detective-conan-world-anime`。
已改脚本并回填 43 条数据。**教训**：新增数据前先 grep 来源 id 是否真实存在。

---

## 4. B · 21 集集号缺口（真因不是缺页面）

### 现象

`backfill-episode-structure.py` 首跑后 21 集仍 `catalog`：
`188–193`（危命的复活 6 集）、`425`（黑色冲击）、`491–504`（红与黑的碰撞 14 集）。

### 误判与纠正

最初判断「DCW 没有这些页面」。实际三个页面都在 `data/raw/dcw-pages/` 里：

- `The_Desperate_Revival.html`（278 KB）
- `Clash_of_Red_and_Black.html`（469 KB）
- `Black_Impact!_The_Moment_the_Black_Organization_Reaches_Out.html`（226 KB）

真因是：**多集特别篇的 infobox 写法与单集页不同**，`episodeNumbers` 被抽成空数组 `[]`。

### 原文里的真实写法

```
The_Desperate_Revival    → "Episode 188-193 (Int. Episode 203-208)"
Clash_of_Red_and_Black   → "Episode 491-504 (Int. Episode 538-551)"
Black_Impact!            → "Episode 425 (Int. Episode 459-463)"
```

注意第三种：**单集号 + 国际集号范围**，与另两种都不同。

### 处置

新增 `scripts/fix-special-page-episode-numbers.py`，从原始 HTML 按上述三种模式抽取：

- 只处理 `episodeNumbers` 为空的页面（已有集号绝不动）；
- 写入 `episodeNumbers` / `episodeRange` / `intEpisodes` / `intEpisode` / `factSource`；
- `factSource` 记录命中的原文串，便于追溯。

```
补集号 3 页（共 793 页）
    425        （ 1 集）  Black_Impact!_The_Moment_the_Black_Organization_Reaches_Out
    491-504    （14 集）  Clash_of_Red_and_Black
    188-193    （ 6 集）  The_Desperate_Revival
```

### 结果

```
命中页面 1217 集（此前 1196）
season 补 21 → 1217/1217
castNames 补 21，角色挂接 +308
detailStatus 升 reviewed 21
无对应页面 0 集
```

`coverage.structure` **1217/1217（100%）**。

特别篇页面的 `solvedBy` 原文即 `null`（DCW 未提供），因此不补 —— 不编造。

---

## 5. B · 冲突收口

`docs/FACT-CONFLICTS.json` 原有 5 条冲突，本轮处置后状态：

| id | 状态 | 说明 |
|---|---|---|
| `conflict-ushio-chisato-timeframe` | resolved | 补上缺失的 `status` 字段（原有 resolution 但无 status） |
| `conflict-ep0086-sv-special-adaptation` | resolved | 原有 |
| `conflict-ep0113-sv-special-adaptation` | resolved | 原有 |
| `conflict-ep96-two-cases-one-page` | **resolved** | 本轮收口，裁定 `keep-split` |
| `conflict-kirin-horn-585-overlap` | **open（保留）** | 补全三份证据，但证据自相矛盾，不裁定 |

### EP.96（已裁定）

两小时特别篇含两个独立案件，本地按内容拆为两个实体，二者 `animeRefs` 均声明 EP.96 —— 这是正确粒度。
DCW 只提供合并页面是来源侧问题，不应据此合并实体（合并会丢失两案各自的 victim/culprit/motive 等）。
裁定：`keep-split`，DCW 合并页的 castNames/caseType 不自动挂接。

### EP.585（不裁定）

收集到三份互相矛盾的原文证据：

| 证据 | 内容 | 指向 |
|---|---|---|
| ① Kobayashi 页 | `episodeNumbers=[583,584,585]`，`intEpisode=634` | 差 2 集 |
| ② Kirin 页 | `episodeNumbers=[585,586,587]`，`intEpisode=637` | 差 3 集 |
| ③ 本地逐集日文标题 | 583=小林先生の恋、584=白鳥警部の失恋、585=時を超える桜の恋、586=闇に消えた麒麟の角、587=キッドVS四神探偵団 | — |

- 按 `intEpisode`（634→637 差 3）：Kobayashi 若占 583–585，Kirin 必须从 **586** 起。
- 按 `jpTitle` 拆标题：Kirin 页列出「時を超える桜の恋」，则 585 属 **Kirin** —— 与上一条相反。
- 本地库把 585「時を超える桜の恋」挂在 Kobayashi 案件下 —— 与 intEpisode 一致、与 jpTitle 相反。

**不裁定**。`dataState` 已记录：本地数据保持现状未改；EP.585 的 `castNames` 只取 Kobayashi 页（10 人），
Kirin 页因重叠只记入 `dcwExtraPages`，**未合并其 6 个独有人物**（Ginzo Nakamori / Jirokichi Suzuki /
Kaitou Kid / Kogoro Mouri / Ran Mouri / Sonoko Suzuki），因此不存在 cast 污染。

`dcw-page-facts.json` 的原始抽取结果**不改**（原始证据，改动即污染）。

待查来源：读卖电视台官方第 583–587 话各话简介、原作漫画第 67–68 卷 File 归属、日文维基各话リスト。

---

## 6. 最终状态

| 项 | 数值 |
|---|---|
| 剧集总数 | 1217 |
| `season` 有值 | **1217 / 1217（100%）** |
| `castNames` 有值 | **1217 / 1217（100%）** |
| `coverage.structure` | **1217（100%）** |
| `solvedBy` 挂到角色实体 | **1157**（剩 4 集原文无对应个人） |
| `detailStatus` | reviewed 1217（此前 reviewed 1196 / catalog 21） |
| 角色实体 | **147**（101 + 43） |
| 案件实体 | 792 |
| 实体合计 | **957**（人物 147 / 案件 792 / 组织 4 / 道具 8 / 地点 6） |

校验链全绿：

```
VALIDATION_OK
CHAIN_IDEMPOTENT_OK
APP_JS_OK
UI_P4_OK
P3_OK
NAV_KINDS_OK（characters 147 / cases 792 / organizations 4 / gadgets 8 / places 6 / entities 957）
```

---

## 7. 新增/修改文件

| 文件 | 说明 |
|---|---|
| `scripts/resolve-episode-solvedby.py` | P1：`solvedByRaw` → 角色实体；`--dry-run`；幂等 |
| `scripts/create-character-entities-episodes.py` | P2：剧集 castNames 实体化；`--min`；`--dry-run`；幂等 |
| `scripts/fix-special-page-episode-numbers.py` | B：补特别篇页面集号（三种原文写法）；幂等 |
| `scripts/verify-p3-spoilernote.js` | P3 前端验证 |
| `scripts/verify-nav-kinds.js` | 期望值 101/911 → 147/957 |
| `app.js` | `detailSections()` 新增「收录备注」分区 |
| `data/raw/dcw-page-facts.json` | 3 页补 `episodeNumbers` / `episodeRange` / `intEpisodes` / `intEpisode` / `factSource` |
| `data/episodes/episodes.json` | `season` / `solvedBy` / `solvedByRaw` / `castNames` / `characters` / `dcwExtraPages` / `coverage` |
| `data/entities/characters.json` | +46 角色 |
| `docs/FACT-CONFLICTS.json` | EP.96 收口；EP.585 补证据；补 status 字段 |

---

## 8. 回滚

```bash
cp /tmp/eps_pre_solvedby.json data/episodes/episodes.json      # P1 前
cp /tmp/chars_pre_p2.json data/entities/characters.json        # P2 前
cp /tmp/facts_pre_special.json data/raw/dcw-page-facts.json    # 特别篇集号前
cp /tmp/eps_pre_structure.json data/episodes/episodes.json     # P4-C 前
cp /tmp/conflicts_pre.json docs/FACT-CONFLICTS.json            # 冲突改动前
```

前端 `app.js` 改动只有一处 `if (raw.spoilerNote) sections.push(...)`，删除该行即可回退。

---

## 9. 遗留

| 项 | 状态 |
|---|---|
| 226 个未收录 castNames（最高 `Nakamichi` 21 集） | 多为仅姓氏/岗位，按口径不建实体 |
| 147 个角色中 133 个中文名空白 | 待官方来源，不猜 |
| 741 个案件标题只有日文 | 待译 |
| `Detective Boys`（435 集）应建 organization | 需成员名单，不编造 |
| EP.585 归属 | 冲突保留 open，见第 5 节 |
| 5 集 summary 为空（713/714/882/1061/1187） | DCW 页面无叙述正文 |
| 38 处重复译文 | cron 重叠触发，两版均忠实，未清理 |
| git 未初始化 | 需用户明确确认 |
