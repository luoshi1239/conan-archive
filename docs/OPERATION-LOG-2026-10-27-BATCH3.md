# 作业日志 · 批 3（2026-10-27 夜）

> 承接 `PLAN-RECOMMENDED.md` 的 P0 / P1 / P2 阶段。用户授权："允许，按这个做，无人值守，非必要你拿主意"。

## 一、P0 前端修复（已完成）

**问题 1：全站剧集卡片显示 `[object Object]`（1212/1217 集）**

- 根因：`app.js` 里 `intro: record.summary`，而 `summary` 自上一批起已改为多语言对象，`String()` 后变成 `[object Object]`。
- 修复：新增取词函数 `textOf(value)` / `labelOf(value)`，按 `zhHant → zhHans → ja → en` 顺序取第一个非空字符串；字符串（旧数据）原样返回，对象按语言择优。列表、搜索、详情三处统一走这套函数。
- 验证：`node` 实跑 `app.js` 真实函数 → **0 条** 会渲染成 `[object Object]`。

**问题 2：案件详情页根本不显示剧情字段**

- 根因：`detailSections()` 只输出 档案状态/案件类型/动画范围/关联人物，`culprit / motive / method / evidence / resolution` 一个都没渲染 → 243 条凶手、149 套 L3 全不可见。
- 修复：详情页新增「深度剧透」分区，按 `culprit(凶手) / motive(动机) / method(手法) / evidence(证据) / resolution(结局)` 五项列出；英文原文自动附加「原文·待译」标记；`summary` 对象同样走 `labelOf`。
- 剧集详情同步加「剧情概要」分区。

## 二、P1 L3 字段双语化（已完成）

新增 `scripts/migrate-case-l3-bilingual.py`（幂等）：

- 纯字符串字段统一迁移为 `{ "zhHans": "", "en": "", "translationStatus": "pending|machine|human" }`。
- 语言判定：`dcwL3Source[field].lang == "en"` 的原文归 `en`，其余归 `zhHans` 并标 `human`。
- 结果：**848 个字段**迁移完成（618 英文槽位 + 230 中文槽位）。
- `normalize-case-status.py` 增加 `filled()`：双语对象只有 `zhHans`/`en` 任一非空才算「有内容」，避免空对象被当成已填。
- `validate-data.py` 增加结构校验：L3 字段必须是字符串或 `{zhHans,en,translationStatus}` 之一，非法结构直接 `VALIDATION_FAILED`。

## 三、P2 翻译流水线（已建成 + 前两批已译）

三件工具：

| 脚本 | 作用 |
|---|---|
| `scripts/build-translation-queue.py` | 按「主线相关 + 名案白名单 + 集数靠前」排序，生成 `docs/TRANSLATION-QUEUE.json`（618 字段 → 10 批） |
| `scripts/dump-translation-batch.py` | 取下一批**未译且未登记可疑**的字段，供人读或 JSON 消费 |
| `scripts/apply-translations.py` | 把 `docs/translations/batch-*.json` 写入 `zhHans`，带长度比校验、原文指纹校验、幂等 |

**关键保护（防止译文与原文脱钩）**

- `translationSourceHash`：每条译文记录它翻译时那段英文的 sha1 前 12 位。英文日后被改动时，旧译文自动作废、重入队列，不会静默错配。
- 长度比校验：`zh/en` 长度比必须在 0.15–1.8 之间，超出直接拒收（防漏译、防注水）。
- 绝不覆盖已有 `zhHans`（人工中文优先）。

**翻译口径**：`docs/TRANSLATION-GLOSSARY.md`（忠实原文、专名表内才用中文、表外保留罗马字、不推测不增删）。

**已完成的批次**

| 批次 | 案例数 | 译入字段 | 登记可疑 |
|---|---|---|---|
| 1 | 20 案 | 96 条 | 1 条 |
| 2 | 20 案 | 87 条 | 8 条（累计） |

进度：**中文槽位 409 / 618**，待译 **209**。

## 四、"可疑字段"机制（宁缺勿错）

旧切块脚本对 `motive/method/evidence` 的句子分配经常错位（例如 `motive` 里装的全是调整空调、镜子、甲虫这类手法细节）。这类字段**不翻译**，登记到 `docs/translations/flagged.json`：

```json
{"caseId": "...", "field": "motive", "reason": "装的是手法细节，原文未给出动机", "action": "待重新抽取"}
```

- 宁可页面上暂时只有英文 + 「原文·待译」，也不产出误导性中文。
- 目前已登记 **8 条**，全部待重新抽取（DCW 的 `Resolution` 块内其实有完整句子，只是分配错了）。

## 五、无人值守

已创建 cron 任务 `conan-archive L3 翻译批处理`（`job_id: 7c83c52219de`，每 30 分钟，`continuity: true`）：

- 每跑一批：dump → 翻译 → apply → validate → 报剩余量。
- **注意**：Hermes gateway 当前未启动，任务已保存但不会自动触发；需要在桌面端启动 gateway（或手动 `hermes gateway start`）后才会生效。

## 六、验收

```
python3 scripts/validate-data.py   → VALIDATION_OK
python3 scripts/dump-translation-batch.py → BATCH 3 | 68 字段 | 剩余 431
app.js: node --check               → 通过
```

## 七、后续

1. 继续译批次 3–10（209 字段待译）。
2. 8 条可疑字段按 `Resolution` 块重新抽取后再译（P2.5）。
3. 剧集中文全量翻译仍不建议（180 万字），只按需翻高价值子集。
