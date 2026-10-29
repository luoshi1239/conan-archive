# 作业日志 · 2026-10-28 · P4 角色实体化

> 承接 `OPERATION-LOG-2026-10-28-L3-B4-B10.md`（L3 翻译收尾）。
> 本轮目标：把「人物」分区从 14 个角色扩到可用规模，同时修掉扩量后暴露的三个前端缺陷。

---

## 一、为什么做这一步

L3 收尾后，站内最大的空缺不是数据，而是**人物库只有 14 个角色**。
案件页里 `castNames` 存了 388 个英文名（789 案有值），但其中只有 14 个被实体化——
「人物」分区几乎是空的，案件详情也只显示「工藤新一、毛利兰…」寥寥几个。

`docs/PLAN-RECOMMENDED.md` 的 P4 建议口径：只建出现 ≥5 案的角色，不建一次性路人。

---

## 二、口径（三条硬约束）

1. **只搬原文，不编造**：中文名一律留空，`translationStatus: "pending"`。
   `docs/TRANSLATION-GLOSSARY.md` 明确「专名未收录者保留罗马字，不自行拼汉字」，
   所以 `Wataru Takagi` 就是 `Wataru Takagi`，不写「高木涉」——没有可核对的来源。
2. **化名不新建实体**：同一人物的不同名字挂到已有角色的 `aliases`，否则「人物」里会出现
   两个安室透、两个冲矢昴。
3. **无名路人 / 剧中虚构角色不建实体**：`Policeman`、`Presiding judge`、`Kamen Yaiba`
   这类不是「可识别的个人」，建了只会污染人物索引。

---

## 三、实际做了什么

脚本：`scripts/create-character-entities.py`（幂等，二次运行零改动）

| 处置 | 数量 | 说明 |
|---|---|---|
| 新建角色实体 | **87** | 出现 ≥5 案，`kind: "character"` + `name.en` + `caseRefs` + `sources` |
| 化名并入已有角色 | **5** | 见下表 |
| 跳过 | **14** | 无名路人 4、庭审角色 3、泛称 3、指代不明 2、剧中虚构 2 |
| 已存在（只补挂接） | **13** | 原有 14 个角色中的 13 个在 castNames 里出现 |

### 化名并入（避免重复实体）

| castName | 并入 |
|---|---|
| Tooru Amuro（安室透） | `character-rei-furuya` |
| Subaru Okiya（冲矢昴） | `character-shuichi-akai` |
| Scar Akai（伤疤赤井） | `character-shuichi-akai` |
| Shiho Miyano（宫野志保） | `character-ai-haibara` |
| Kaito Kuroba（黑羽快斗） | `character-kaito-kid` |

### 跳过的 14 个

`Detective Boys`（团体，应建 organization 实体，待办）、`Unnamed officer`、`Policeman`、
`Police detective`、`Female forensics member`、`Presiding judge`、`Side judge A`、
`Side judge B`、`Professor`、`Mrs. Kojima`、`Goro`、`Maro`、`Kamen Yaiba`（假面超人）、
`Gomera`（哥美拉）

### 结果

| 指标 | 之前 | 之后 |
|---|---|---|
| 角色实体 | 14 | **101** |
| 案件↔角色挂接 | 2507 | **5334**（792/792 案全覆盖） |
| 剧集↔角色 | 4398 条 / 1217 集 | 不变 |

---

## 四、扩量后暴露的三个前端缺陷（已修）

这三个都是「数据对了、页面还是错的」，靠 `scripts/verify-ui-p4.js` 跑真实 `app.js` 函数抓出来的。

### 1. 87 个新角色被归成「主线」

`entityToCard()` 只凭 `record.role` / `record.kind` 判类型。新角色两个字段都没有，
一路落到兜底分支 → 显示成金色「主线」卡片、标「线」。
**修**：数据侧统一补 `kind: "character"`，`app.js` 里 `kind` 优先于 `role`。

### 2. 琴酒、伏特加、灰原哀等 6 个被归成「组织」

老逻辑 `role.includes('组织')` → 组织。他们的 `role` 写的是「黑衣组织成员」，
于是**成员被判成了组织本身**。这是个一直存在的旧 bug，只是角色少时没人注意。
**修**：`kind === 'character'` 优先，6 个全部回到「人物」。

### 3. 详情页直接打印实体 id

案件详情「关联人物」原本 `raw.characters.join('、')`，之前只有 14 个 id 勉强能看，
扩到 101 个后会把 `character-conan-edogawa、character-wataru-takagi…` 整串倒出来。
**修**：新增 `nameOfRef()` / `refsText()`，把 id 解析成展示名并截断（「等 N 项」）；
角色详情补「出场案件」分区（同样解析成案件标题）。剧集详情的关联字段一并改掉。

---

## 五、一个假通过的坑（值得记）

`normalize-case-status.py` 写 `indent=1`，其余 66 处脚本写 `indent=2`。
两个脚本交替跑，**内容没变但文件一直在重排**，md5 每次都不一样——
看起来像「不幂等」，其实是格式打架。
已把 `normalize-case-status.py` 统一成 `indent=2 + 换行`，现在全链路 5 脚本连跑两次 md5 稳定。

**教训**：md5 对比只能证明「字节没变」，不能证明「内容没变」。
幂等检查要挑同一脚本连跑，或者比语义（load 后 dump 归一化再比）。

---

## 六、验收

```
create-character-entities.py 二次运行      → 新建 0 / 挂接 0
全链路 5 脚本连跑两次                       → 全链路幂等 OK
validate-data.py                           → VALIDATION_OK
verify-ui-p4.js                            → UI_P4_OK（101/101 判为人物，0 处脏文本）
node --check app.js                        → APP_JS_OK
dump-translation-batch.py                  → ALL_TRANSLATED
audit-translations.py                      → 数字丢失 0 / 长度异常 0 / 空壳 0
```

**回滚**：
```bash
cp /tmp/chars_pre_p4.json data/entities/characters.json
cp /tmp/cases_pre_p4.json data/entities/cases.json
python3 scripts/normalize-case-status.py
```

---

## 七、遗留（本轮未做）

1. **87 个角色的中文名待补**：需要官方译名来源（台配/陆配/漫画版），不自行拼汉字。
   补的时候走 `translationStatus: "pending" → "human"`，并把 `note` 改成来源说明。
2. **`Detective Boys` 应建 organization 实体**（291 案出现），成员关系需来源。
3. **741 案标题只有日文**（无 `zhHans`）：所以角色详情「出场案件」显示的是
   `時限爆弾を乗せた車 (Jigen Bakudan o Noseta Kuruma)` 这样的日文原名。这是数据源现状，
   不是本轮引入的问题，需要中文标题来源才能改善。
4. 一次性路人（<5 案，共 269 个）仍未实体化——按 P4 口径有意为之。
