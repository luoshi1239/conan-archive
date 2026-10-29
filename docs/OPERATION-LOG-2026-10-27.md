# Conan Archive 知识库补全 · 操作日志

> 记录区间：2026-10-26 ~ 2026-10-27（无人值守批次，主会话 + 抓取后台进程）
> 全部数据已通过 `validate-data.py`（VALIDATION_OK）与全链路幂等验证（IDEMPOTENT_OK）
> **新会话接手请看 `docs/HANDOFF-NEW-SESSION.md`（交接单）**

---

## 一、最终状态快照（2026-10-27）

| 维度 | 数值 | 说明 |
|---|---|---|
| 剧集 | **1217** | 1216 + 新增 EP.1217（2026-10-17 播出，DCW 收录） |
| 案件实体 | **792** | 原 51 → 792（DCW 页面生成 741 + 手工 51） |
| 来源 | **72** | 原 69 → 72 |
| 剧集→案件覆盖 | **1217/1217（0 空）** | 关系闭合报告 total=0 |
| 漫画↔剧集双向 | **0 缺失 / 0 不匹配** | files.json 与 episodes.json 完全闭合 |
| 案件 detailStatus | catalog 550 / partial 196 / deepSpoilers 46 | 无 None |
| 有 culprit 的案件 | **242** | 原 46 → 242（185 high + 11 cleaned + 原 46） |
| L3 五字段齐全 | 46 | 需人工审核后由队列批准扩充（111 案四字段候选齐全） |
| 剧集 summary | 缺 **546**（en 598 / zhHans 136 人工 / 全空 546） | 英文从 DCW Situation 原文搬运（不翻译不编造），中文需人工 |
| DCW 页面缓存 | 793 页（0 失败） | `data/raw/dcw-pages/` |

---

## 二、本轮完成的工作

### 1. 底座补全（规模化主链条）

1. **DCW 全集索引抓取与解析**：`/wiki/Anime`（1.8MB）→ 1214 集表格，含 Jp#/Int#/标题/播出日期/漫画来源/下一集提示。落盘 `data/raw/dcw-anime-index.json`，差异报告 `docs/DCW-IMPORT-DIFF.json`。
2. **漫画来源回填**：`backfill-dcw-manga-source.py` 把 DCW Manga source 原文写入每集 `raw.dcwMangaSource/dcwMangaKind/dcwAirDate`，共 4776 条编辑，幂等验证通过。
3. **动画原创判定修正**：EP.86/EP.113 被原库误标 `anime-original`，实为特别篇漫画改编（SVFile.2 / SVFile.6）。本地 files.json rawLabel 与 DCW `SV1 - F2/F6` 双向印证，已改为 `manga` 并记入 FACT-CONFLICTS（两来源佐证）。
4. **793 个 DCW 页面批量抓取**：`fetch-dcw-pages.py`（线程池 6 并发、幂等、20KB 阈值）。唯一失败 = EP.1218 红链页（403，DCW 尚无页面）。
5. **页面事实提取**：`extract-dcw-page-facts.py` —— 集号（含 `Episode 374-375` 范围展开、`830-832` 中间集补齐、`Int.` 海外集号隔离）、`Case`+`Cast:` 两行识别、多行 Manga source 合并、Category 提取。最终 793 页 0 不一致（与全集表逐集比对）。
6. **案件实体生成**：`generate-case-entities-from-dcw.py` —— 741 个案件骨架，`caseType` 仅来自 Category 白名单映射（锁闭密室/连环杀人/不可能犯罪/暴风雪山庄/神秘旅行等），**绝不靠标题关键词猜测**；主线多集页（Desperate Revival、Black Impact）回退用全集表链接映射。
7. **旧实体合并**：`merge-dcw-facts-into-cases.py` 按集号重叠合并 DCW 元数据进原 51 实体（44 条），不留重复。
8. **警察学校篇补抓**：EP.1029/1038/1042/1061（+1134）五个 Wild Police 页面，位于全集表之外，单独抓取。
9. **EP.586-587 部分认领**：Kirin's Horn 页面声明 [585,586,587] 与 Kobayashi 案重叠，按"只认领空闲集号"处理，EP.585 归属冲突记入 FACT-CONFLICTS 待人工。
10. **EP.1217 补充**：`append-dcw-new-episodes.py` 将已播出的 1217 集补进剧集库（覆盖结构 `{directory,basicFacts}`）。

### 2. 隐患排除（用户重点要求）

| 隐患 | 处理 |
|---|---|
| **normalize-episodes.py 全量覆盖回填数据**（重跑即摧毁 caseRefs 1215→186、dcwRaw 4776→0） | 重写为 `KEEP_IF_TRUTHY` 逐字段保留 + raw 合并 + 保留 RAW 外的记录；从备份恢复后验证 `IDEMPOTENT_OK` |
| **validate-data.py 只查 `sources`，16 条实体用 `sourceRefs` 逃检** | 改为并查 `sources`+`sourceRefs`，且要求至少一个非空 |
| **caseType 类型分裂**（32 list / 16 str） | 全部统一为 list（792/792） |
| **案件状态字段不一致**（561 个 detailStatus=None、5 个 status=None、deepSpoilers 标志矛盾） | `normalize-case-status.py` 统一三态：catalog/partial/deepSpoilers |
| **la 集号越界**（某实体声明 EP.1217 但库只到 1216） | 补入 1217 集，消除悬空引用 |
| **误导性凶手陈述**（Nagasaki 案原文 "That culprit is Ran Mouri... Ran is not the true culprit"） | 拒绝写入，理由入档 `docs/L3-CULPRIT-REJECTED.json` |
| **三集特别篇丢中间集**（`Episode 830-832` 解析成 [830,832]） | 范围展开修复（29 页受影响） |
| **海外集号污染日文编号**（`(Int. Episode 198-199)`）（13 页） | 先定位第一个 Episode 修复 |
| **候选质量**（`man and woman`、`arrested` 等非人名） | `looks_like_name()` 过滤，medium 从 67 降至 12 |

### 3. L3 深度剧透（规模化候选）

- `extract-dcw-page-blocks.py`：按标题切分页面 → Situation/People/Resolution 原文块（791/793 有 Resolution）。
- `build-dcw-l3-candidates.py`：从 Resolution 原文抽 candidate，**全是原文引用不改写翻译**。产出 **1933 条候选**：culprit 204（192 high + 12 medium）、motive 594、method 546、evidence 589。
- `apply-dcw-l3-high.py`：192 条 high culprit 里 185 条写入（7 条已有不覆盖）。
- `apply-dcw-l3-cleaned.py`：12 条 medium 逐句人工核对 → 11 条清洗写入（去职衔/从句/副词，双凶手保留），1 条拒绝（Ran Mouri 误导陈述）。
- `build-l3-review-queue.py`：生成 `docs/L3-REVIEW-QUEUE.md`（483KB）+ `.json` —— **763 案待审，111 案四字段齐全可直接批准**。所有 value 为原文未翻译。

### 4. 审计与验证基础设施

- `docs/CASE-GENERATION-REPORT.json`、`CASE-MERGE-REPORT.json`、`DCW-IMPORT-DIFF.json`、`DCW-FETCH-STATE.json`、`EPISODE-APPEND-REPORT.json`、`L3-APPLY-REPORT.json`、`L3-CULPRIT-REJECTED.json`、`L3-REVIEW-QUEUE.{md,json}` 全部落盘。
- 全链路 7 脚本二次运行 md5 一致 = `IDEMPOTENT_OK`；`VALIDATION_OK`。

---

## 三、遗留问题 / 待办（按优先级）

1. **L3 审核批准**：111 案四字段候选齐全，用户审核 `docs/L3-REVIEW-QUEUE.md` 后经 `docs/L3-APPROVED.json` 写入 → deepSpoilers 46 → ~157。**method/motive/evidence 是英文原文，需人工翻译或确认接受英文态。**
2. **剧集 summary 缺 1081 条**：英文可从 DCW Situation 段搬运（783 页已有缓存），中文需人工。
3. **角色实体仅 14 个**：案件有 `castNames`（英文名）但未挂接角色实体，角色层是大缺口。
4. **2 条未裁决冲突**（`docs/FACT-CONFLICTS.json`）：EP.585 归属（Kirin/Kobayashi），EP.96 两案一页。
5. **EP.98—101 尚未跑 `extract-verdicts.py` 逐句比对**。
6. **看门狗未建**：mimo-flash 无法固定（patch 拒写 config.yaml、"hermes" CLI 不存在），5 分钟监督只能本地进程实现；QQ 通知无凭证未实现。

---

## 四、关键文件索引

| 文件 | 说明 |
|---|---|
| `scripts/register-102-106-cases.py` | 手工批（EP.102—106 三案，51→54 时代的注册器） |
| `scripts/import-dcw-anime-index.py` | DCW 全集表 → raw 索引 |
| `scripts/backfill-dcw-manga-source.py` | 漫画来源回填 + SV 裁定 |
| `scripts/fetch-dcw-pages.py` | 793 页抓取（幂等） |
| `scripts/extract-dcw-page-facts.py` | 页面→结构化事实（集号/cast/漫画/类别） |
| `scripts/generate-case-entities-from-dcw.py` | 741 案件骨架生成 |
| `scripts/merge-dcw-facts-into-cases.py` | 旧实体 DCW 元数据合并 |
| `scripts/record-alignment-conflicts.py` | 无法裁定冲突入档 |
| `scripts/append-dcw-new-episodes.py` | EP.1217 补充 |
| `scripts/extract-dcw-page-blocks.py` | 正文块切分（Situation/Resolution） |
| `scripts/build-dcw-l3-candidates.py` | L3 候选生成（1933 条） |
| `scripts/apply-dcw-l3-high.py` / `apply-dcw-l3-cleaned.py` | culprit 写入（high/cleaned） |
| `scripts/backfill-episode-summaries.py` | summary 搬运（旧字符串统一为 dict，en 598 条） |
| `scripts/build-l3-review-queue.py` | 审核队列生成 |
| `scripts/normalize-case-status.py` | 状态统一 |
| `data/raw/dcw-pages/` | 793 页缓存（L3 二次挖掘素材） |
| `data/raw/dcw-page-facts.json` / `dcw-page-blocks.json` | 页面事实 / 正文块 |
| `data/raw/dcw-anime-index.json` | 全集表结构化 |
| `data/candidates/dcw-l3.json` | 1933 条 L3 候选 |
| `docs/L3-REVIEW-QUEUE.md` | 人工审核入口（763 案） |
| `docs/FACT-CONFLICTS.json` | 5 条冲突（3 已裁定 + 2 待裁） |

---

## 五、明文限制（如实陈述）

- **mimoflash 监督子 agent 未启用**：`patch` 拒写 `config.yaml`（安全策略），`hermes` CLI 不存在（exit 127）。子 agent 若派生继承的是父模型（deepseek-v4-flash）。
- **QQ 通知未实现**：无可用凭证/接口，未伪称发送。
- **后台抓取进程被工具中断杀过 4 次**（proc_3b7ce3664bab/9fc6f3375d3b/4f8dd3aecca0/56bd02bc9e98），均幂等续跑完成。
- **本批次未创建 git 提交**：conan-archive 目录未纳入版本控制（工作区快照显示 `?? ./`），如需入库请用户确认后再提交。