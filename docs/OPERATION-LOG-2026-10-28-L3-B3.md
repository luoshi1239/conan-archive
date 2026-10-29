# 操作日志 · 2026-10-28 · L3 翻译批处理（批次 3）

> 执行者：cron 任务 `conan-archive L3 翻译批处理`（`7c83c52219de`，每 30 分钟）
> 口径：`docs/TRANSLATION-GLOSSARY.md`（2026-10-27 版）
> 结果：`VALIDATION_OK` ✅

## 一、本批范围

| 项 | 值 |
|---|---|
| 批次号 | **3** |
| 待译字段 | 68（20 案） |
| 写入 | **59** |
| 拒收 | **0** |
| 登记可疑（不译） | **9** |
| 全库剩余待译 | 431 → **363** |

## 二、为什么切成 a–e 五个子批

批 3 原始 dump 达 **53,911 字节**。此前几次 cron 直接整批处理均以失败告终
（输出被截断，模型拿不全原文）。本次沿用批 1/2 已验证的做法：先落盘
`--json`，再按**案件分组不拆散**切块（`~12KB` 上限），得到 5 个子批：

| 子批 | 案数 | 字段数 | 写入 | 登记 |
|---|---|---|---|---|
| 003a | 6 | 14 | 13 | 1 |
| 003b | 4 | 12 | 7 | 5 |
| 003c | 5 | 17 | 16 | 1 |
| 003d | 3 | 15 | 14 | 1 |
| 003e | 2 | 10 | 9 | 1 |
| 合计 | 20 | **68** | **59** | **9** |

同一案的五个字段在同一子批内完成，保证人称、时态、术语一致。

## 三、本批新登记的 9 条可疑字段（`docs/translations/flagged.json`，累计 17 条）

判定沿用既有先例：**字段内完全没有该字段语义的内容**才登记，宁缺勿错。
glossary 第五节已明确「Resolution 块重述手法与证据属来源结构，照译即可」，
故单纯的重复重叠不算错、照译。

| 案件 | 字段 | 问题 |
|---|---|---|
| case-the-hot-chocolate-trap | method | 只有受害者性格描述＋照片证据解读，毫无作案手法 |
| case-cactus-capriccio | motive | 前 5 句全是手法/不在场证明细节，动机只在末尾两句 |
| case-cactus-capriccio | evidence | 无任何证据：一句「要求拿出证据」＋一句动机 |
| case-nagasaki-mystery-theatre | culprit | **沿用 `L3-CULPRIT-REJECTED.json` 既有裁定**：柯南为逼真凶现身故意指控毛利兰，原文下一句即否认 |
| case-nagasaki-mystery-theatre | motive | 装的是推理过程与死亡讯息解读（chouchou/tefutefu），与动机无关 |
| case-nagasaki-mystery-theatre | method | 只有柯南击晕小五郎的固定套路，不是凶手手法 |
| case-froth-steam-and-smoke | motive | 混入「Manga to anime changes」维基导航残片 |
| case-dancing-demon-at-the-noh-mask-mansion | motive | 全是铁签刺杀手法，动机只在 resolution 末尾 |
| case-the-framed-great-detective | motive | 只有一句扶手脚法，原文未提供动机 |

> 其中 Nagasaki 的 `culprit` 是**跨批次复发**问题：该字段原文为误导性陈述，
> 早已被裁定 `rejected-do-not-write`，但 dump 脚本只排除 `flagged.json`，
> 于是每轮都会重新入队。本次登记进 `flagged.json` 后即可根治反复入队。

## 四、专名处理

术语表内角色按表内中文名（Conan→柯南、Kogoro→毛利小五郎、Ran→毛利兰、
Sonoko→铃木园子）。表外人名一律**保留罗马字**，不自行拼汉字，例如
Hisashi Suguro、Toru Tsukano、Morio Yakura、Kaishiro Imaoka、Hatsuho Toba、
Reiji Himuro 等 30 余个。手法专名 `Ebi-Sora` 保留原文，不造中文专名。

## 五、验证结果

```
apply-translations.py  → {"written": 59, "skipped": 179, "rejected": 0}
validate-data.py       → VALIDATION_OK
dump-translation-batch → BATCH 4 | 80 字段 | 20 案 | 全库剩余 363 字段
```

抽查确认：已写入字段 `translationStatus=machine`、`translationSourceHash` 齐全、
`reviewed=false`；9 条可疑字段全部保持 `pending` 且 `zhHans` 为空，未被误写。

## 六、当前全库进度（实测）

| 指标 | 值 |
|---|---|
| L3 五字段 en 槽位 | 618 |
| 已译 zhHans | **238**（38.5%） |
| 未译 | 380（其中 17 条为登记可疑、不入队） |
| 队列内待译 | **363** |

> 注：`docs/HANDOFF-NEW-SESSION.md` 中「409/618、待译 209」与实测不符。
> 实测 `skipped=179` 表明批 1/2 完成后已译数为 179；handoff 该数字口径存疑，
> 下次更新交接单时以本次实测为准。

## 七、后续

下一轮 cron 将自动取 **BATCH 4**（80 字段 / 20 案）。建议同样按案件分组
切子批，避免整批 dump 过大导致输出截断。
