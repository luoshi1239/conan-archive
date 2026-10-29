# 操作日志 2026-10-28 · L3 翻译收尾（批 4–10）

## 一、本轮结论

**L3 五字段中文翻译已完成 599 / 618 = 96.9%**，剩余 19 条全部是**主动不译**的
可疑字段（已登记 `docs/translations/flagged.json`），**无漏网**。

```
validate-data.py       → VALIDATION_OK（连跑两次同结果，幂等）
dump-translation-batch → ALL_TRANSLATED
```

## 二、cron 连续失败 6 次的真正原因（两个独立 bug）

之前的 cron 任务 `conan-archive L3 翻译批处理`（`7c83c52219de`）报
`provider timeout`，表面看是模型超时，实际是两个叠加的缺陷：

### bug 1：系统 python3 的 SSL 库太旧，API 根本连不上

```
/usr/bin/python3  → Python 3.9.6 + LibreSSL 2.8.3
调用 api.ls1223.cn 直接抛：
  URLError [SSL: TLSV1_ALERT_PROTOCOL_VERSION] tlsv1 alert protocol version
```

LibreSSL 2.8.3 不支持该端点要求的 TLS 版本，握手阶段就被拒（0.4 秒返回）。
用 curl 测同一个 key、同一个端点：**HTTP 200，2–5 秒返回**——所以不是 key、
不是额度、不是中转站故障。

**可用解释器**：`/opt/homebrew/bin/python3.14`（OpenSSL 3.6.4），实测 4.7 秒调通。

### bug 2：失败分支不递增计数 → 死循环空转

`auto-translate.py` 的 `while done < args.max_chunks` 里，块失败时只
`continue`，`done` 不增加。于是一次 `--max-chunks 1` 变成**无限重试同一块**，
外部看就是"跑 400 秒没输出"。

已修：加 `consecutive_failures`，连续 3 块失败即 `[STOP]` 退出。

### bug 3（顺带修）：模型名从 config.yaml 抓错

原代码 `grab("default")` 用正则抓 config.yaml 里第一个 `default:`，
本机抓到的是 `mimo-v2.6-flash`（某个 provider 的默认模型），不是翻译想用的。
现改为固定 `deepseek-v4.1-flash`，可用环境变量 `TRANSLATE_MODEL` 覆盖。

## 三、翻译执行环境（重要，勿用系统 python3）

```bash
cd ~/Desktop/agent/Hermes/conan-archive
/opt/homebrew/bin/python3.14 scripts/auto-translate.py        # 跑到底
/opt/homebrew/bin/python3.14 scripts/auto-translate.py --max-chunks 3
```

单块 3–6 秒，全库 351 字段约 6 分钟跑完。脚本直连中转站，**不经过 Hermes 会话**，
不产生聊天记录，因此也不受 Hermes cron 的 90 秒调用上限约束。

## 四、质量抽查（实测，非抽样估计）

| 检查项 | 结果 |
|---|---|
| `译文 == 原文` 的字段 | 194 条，**全部是 `culprit`**（人名保留罗马字，符合术语表） |
| 译文含英文问答腔（"What would you like…"等） | **0** |
| 非 culprit 字段译文无汉字残留 | **0** |
| 待译 19 条是否都在 flagged.json | **19/19，无漏网** |

术语表口径执行到位：表内角色用中文名，表外人名保留罗马字（如 Chiharu Shirakawa
不译成汉字），`culprit` 原文只有人名时译文也只有人名。

## 五、前端联动

`app.js` 取词顺序 `zhHans → zhHant → ja → en`，`labelOf()` 仅在落到 `en` 时
追加「（英文原文·待译）」。所以 599 条中文现在**直接显示中文**，不再挂待译角标；
19 条 flagged 字段仍显示英文+待译，属预期行为。

## 六、cron 任务现状

`7c83c52219de` 已不在 `cron/jobs.json`（当前仅剩 2 个任务），不会再产生失败通知。
翻译既已收尾，**不建议重建**；将来若英文原文更新（`translationSourceHash` 会让
旧译文自动作废并重入队列），再手动跑一次上面的命令即可。

## 七、遗留（非本轮范围）

- 19 条 flagged 字段需按 DCW `Resolution` 块重新抽取原文后再译。
- 741 案 `title` 只有日文原题（无 `zhHans`），是数据源如此，非本轮遗漏。

---

## 八、19 条 flagged 字段已处置（2026-10-28 补记）

本节由后续会话执行，脚本 `scripts/fix-flagged-l3.py`（幂等，可复算）。

**处置原则**：能对上原文的，按**逐字原句**重新指派给正确字段并翻译；原文确实没有的，
**删除该字段**并在 `case.l3Absent` 留痕。不猜、不补、不留空壳。

### 重新指派（7 条，均从同案原文逐字截取）

| 案件 / 字段 | 原错内容 | 改为（来源字段） |
|---|---|---|
| underwater-key / method | 只有一句「In this manner…」 | 甲虫运钥匙全过程（resolution） |
| revival-of-dying-message / motive | KIX→泉佐野的推理过程 | 凶手供认的动机（evidence 内 "Motive" 段） |
| kaitou-kid-four-masterpieces / evidence | 基德冒充高木的支线 | 钓鱼线+石头的物证（resolution） |
| cactus-capriccio / motive | 高尔夫球印等不在场证明细节 | Yashiro 为父报仇（evidence） |
| froth-steam-and-smoke / motive | 混入「漫画与动画差异」导航残片 | 完整动机四句（resolution） |
| dancing-demon-noh / motive | 铁签刺杀的手法细节 | Hatsuho 恨三人的供述（resolution） |
| bathroom-where-ran-collapsed / method | 世良指认 Rumi 的推理链 | 氯仿+毛巾+指纹嫁祸（resolution） |

**踩到的坑**：首版截取用「整案英文拼接」做语料，`start`/`end` 锚点落在不同字段时会把
中间整段吞进来（froth 的 motive 一度被截成 1642 字符，还带进了 wiki 导航残片）。
已改为**限定在单一来源字段内截取**，并加 900 字符上限兜底；修正后该字段 578 字符。

### 删除字段（12 条，原文确实没有）

`final-screening/motive`、`underwater-key/motive`、`english-teacher/motive`、
`english-teacher/evidence`、`find-the-buttock-s-mark/motive`、`hot-chocolate-trap/method`、
`nagasaki/culprit`（沿用 `L3-CULPRIT-REJECTED` 裁定：原文指控 Ran Mouri 后随即否认）、
`nagasaki/motive`、`nagasaki/method`、`cactus-capriccio/evidence`、
`framed-great-detective/motive`、`jodie-memories/evidence`

每条的删除理由都写在 `case.l3Absent[].reason` 里，可逐条追溯。

### 连带结果

- L3 字段：`machine 606` + `human 230`，**待译 0**，`flagged` 19/19 全部 resolved。
- `deepSpoilers` 由 149 降到 **140**：9 案因为删掉了那个"本来就不该存在"的字段，
  五字段不再齐全。这是**如实反映**，不是数据退化。
- 顺手修一处译名：`赤福牛` → `Akabeko`（赤べこ 是福岛乡土玩具，不是赤福）。
- 校验：`VALIDATION_OK`；`fix-flagged-l3.py` 二次运行零改动（幂等）；
  `audit-translations.py` 长度异常 0、数字丢失 0、空壳 0。

**回滚**：`cp /tmp/cases_pre_fixflagged.json data/entities/cases.json && python3 scripts/normalize-case-status.py`

