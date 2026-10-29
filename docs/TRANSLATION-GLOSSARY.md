# L3 中文翻译规范与术语表

> 本文件是无人值守翻译的**唯一口径**。任何一批翻译都必须遵守。
> 违反规范的批次在 `scripts/apply-translations.py` 的长度校验里会被拒收。

## 一、总则

1. **忠实原文**：只翻译 `en` 字段里已有的事实，**不补充、不推测、不删减**。
   原文说"三人中两人合谋"，译文不得写成"三人合谋"。
2. **不编造专名**：人名、地名、手法名一律按下列规则处理。
3. **保持结构**：原文是两句还是五句，译文也大致对应；不要合并成一段抽象概括。
4. **不加评价**：不写"这个手法非常巧妙"这类原文没有的评论。
5. **不改事实**：原文的时态、先后顺序（先迷晕→再藏尸→再勒死）必须保持。
6. **数字与证据一致**：时间、金额、年龄、致死原因照抄，不换算不四舍五入。

## 二、专名处理（最重要的防编造规则）

| 情况 | 处理 |
|---|---|
| 下文术语表里有的角色 | 用表里的中文名，首次出现括注罗马字，如「江户川柯南（Conan Edogawa）」 |
| 术语表里没有的人名 | **保留罗马字原样**，不要自己拼汉字（例：`Mitsuyuki Arimori` 就写 `Mitsuyuki Arimori`） |
| 地名 / 建筑名 | 有通行译名的用（东京、大阪、米花町、鸟取），没有的保留罗马字或原文英文 |
| 组织名 | 黑衣组织（Black Organization）、FBI、CIA、警视厅、大阪府警、少年侦探团 |
| 手法专名（如 "hang-glider"） | 译成通用说法（悬挂式滑翔翼），不造专名 |

> 为什么不自己拼汉字：罗马字→汉字的写法（如 Arimori → 有森）在中文社区并不唯一，
> 拼错就是给知识库注入错误事实。**保留罗马字是"未翻译"，不是"错误"。**

## 三、术语表（持续补充）

### 主要角色

| 罗马字 / 英文 | 中文 |
|---|---|
| Conan Edogawa | 江户川柯南 |
| Shinichi Kudo | 工藤新一 |
| Ran Mouri | 毛利兰 |
| Kogoro Mouri | 毛利小五郎 |
| Ai Haibara / Shiho Miyano | 灰原哀 / 宫野志保 |
| Hiroshi Agasa | 阿笠博士 |
| Heiji Hattori | 服部平次 |
| Kazuha Toyama | 远山和叶 |
| Juzo Megure | 目暮十三 |
| Wataru Takagi | 高木涉 |
| Miwako Sato | 佐藤美和子 |
| Kazunobu Chiba | 千叶和伸 |
| Ninzaburo Shiratori | 白鸟任三郎 |
| Sonoko Suzuki | 铃木园子 |
| Eri Kisaki | 妃英理 |
| Yoko Okino | 冲野洋子 |
| Kaito Kid | 怪盗基德 |
| Gin | 琴酒 |
| Vodka | 伏特加 |
| Vermouth | 贝尔摩德 |
| Shuichi Akai | 赤井秀一 |
| Rei Furuya / Toru Amuro | 降谷零 / 安室透 |
| Masumi Sera | 世良真纯 |
| Mary Sera | 玛丽·世良 |
| Shiho's sister / Akemi Miyano | 宫野明美 |
| Detective Boys | 少年侦探团 |
| Ayumi Yoshida / Genta Kojima / Mitsuhiko Tsuburaya | 吉田步美 / 小岛元太 / 圆谷光彦 |
| Kamen Yaiba | 假面超人 |
| Osaka Prefectural Police | 大阪府警 |
| Metropolitan Police | 警视厅 |

## 四、字段写法

| 字段 | 写法 |
|---|---|
| `culprit` | 只写犯人身份；原文若只有人名，译文也只有人名（可加括注说明其身份，若原文有） |
| `motive` | 动机，保持原文因果顺序 |
| `method` | 手法，保持作案步骤顺序 |
| `evidence` | 证据，保持原文列举顺序 |
| `resolution` | 结局/收束；DCW 的 Resolution 块常把手法与证据重述一遍，**照译即可**（重复是来源结构，不是错误） |

## 五、批次文件格式

`docs/translations/batch-XXX.json`：

```json
{
  "batch": 1,
  "translator": "ai",
  "glossaryVersion": "2026-10-27",
  "items": [
    {"caseId": "case-...", "field": "motive", "zhHans": "译文"}
  ]
}
```

写入后 `translationStatus` 自动变为 `machine`、`reviewed` 为 `false`，等人工抽检。
