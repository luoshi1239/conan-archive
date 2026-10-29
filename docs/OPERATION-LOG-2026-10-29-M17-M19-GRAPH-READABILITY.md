# 操作日志 2026-10-29 · M17–M19：关系图可读性根治 + 人物档案补全 + 纳入版本控制

## 一、这轮的起因

用户连说两次「你用视觉能力去看整个站，看看效果达到你的预期没有」，随后授权「做完视觉检查，有问题就修正」。

上一轮结束时我已经把 10 个视图逐一看过并修了 10 个真 bug，但那时的关系图只有 6 分：标签糊、中心挤、大片节点没有名字。这轮的重点就是承认这个分数不达标，然后找到真因。

## 二、关系图：终于找到「标签糊」的真因

### 症状与误判过程

表象是「标签重叠、中心糊成一团」。我先按常规思路调了三轮参数，全部无效或更差：

| 尝试 | 结果 |
|---|---|
| 加大斥力（hop 度数加权） | zoom 从 0.58 掉到 0.424，更差 |
| 降低共演边上限 5→2 | 边 197→157，zoom 0.52，标签仍糊 |
| 给 y 向斥力加画布比例权重 | 包围盒被拉成 1172×1268，zoom 0.447 |

调参调不动，说明我对症状的归因错了。

### 真因：字号写在世界坐标里

`drawGraph()` 里 canvas 已经 `ctx.scale(graph.zoom)` 过，但设置字体时写的是：

```js
const fsPx = 11;
const fs = fsPx / graph.zoom;   // 算对了世界单位
ctx.font = `${fsPx}px ...`;     // ← 却用了 fsPx
```

`ctx.font` 的单位是**世界坐标**，会被 `scale(zoom)` 再乘一次。zoom 0.55 时，11px 的标签实际只渲染成 **6 像素**。

**这跟避让算法一点关系都没有**：无论标签摆到哪里、避让多完美，字本身就是小的，看上去必然是「糊成一片」。

同一个坑还有第二处：标签碰撞检测的留白写的是 `free(b.x - 3, ...)`，3 也是世界单位，zoom 0.6 时只剩 1.8 屏幕像素——所以「留了 3px 呼吸」的标签实际上贴在一起。

修法：

```js
ctx.font = `${fs}px ...`;              // 用世界单位 → 屏幕上正好 fsPx 像素
const tw = ctx.measureText(dispLabel).width;  // 已是世界单位，不再除 zoom
const padWorld = 3 / graph.zoom;       // 留白也换成世界单位
```

### 连带修掉的三个缺陷

1. **布局不可复现**：`seedPositions` 用 `Math.random()`，同一份数据三次刷新包围盒宽 1133 / 1498 / 1830，zoom 在 0.43–0.69 之间跳。用户每次看到的疏密都不一样，也没法调参。改为固定种子的 `seededRandom()`，三次实测完全一致。
2. **长标题横穿画布**：案件标题常二三十字（「黑色冲击！黑衣组织伸出魔爪的瞬间」），一条就能盖住几十个节点。超过 9 字截断为 8 字 + 省略号，完整名字在悬停和抽屉里仍可见。
3. **外围节点永远匿名**：标签候选要求 `deg >= 3`，只连一两条边的角色永远拿不到名字。改为 `deg >= 1`，并加一档「更远」的候选位置。标签预算从 22 提到 48——**预算只是尝试上限，放不下的位置会被 `free()` 拒绝，所以调高是安全的**。

### 硬性碰撞分离

力导向的斥力是「软」的，枢纽周围挤十几个节点时压不住。加了一道 O(n²) 的硬分离，按最小间距直接把重叠节点推开：

```js
const minSep = Math.max(26, 62 / Math.max(0.35, graph.zoom));
```

关键前提：字号改成屏幕像素后，**拉开节点不会让字变小**，所以这一步是纯收益。

### 各图最终效果（vision 打分）

| 图 | 修前 | 修后 | 可读标签数 |
|---|---|---|---|
| 人物关系 87 点 / 168 边 | 6 | **8** | 20 → 47 |
| 组织成员 29 点 / 83 边 | 8 | 8 | 18 |
| 人物—案件 128 点 / 240 边 | 6 | **7** | 20 → 48 |

人物—案件图从 40 人×12 案（196 节点）收到 30 人×8 案（128 节点），并给长标签截断，这是它从 6 分到 7 分的主要原因。

## 三、M17：补 12 对人物关系

回填脚本 `scripts/backfill-character-bonds-batch2.py`。

上一轮 102 对 bonds 里，有 5 位高出场人物一条关系都没有——冲野洋子（61 案）、十和警官（41）、榎本梓（30）、横沟参悟（29）、比护隆佑（20），在关系图上是孤立点。

补了 14 对定义，实际新增 12 对，总数 102 → **114**。原则沿用上一轮：只写原作确定成立的关系，任何一端 id 不存在就整批拒绝写盘，二遍幂等。

## 四、M18：补 60 人的 role / summary

**这是这轮发现的另一个大缺口**：147 个人物里 **133 个** `role` 和 `summary` 都是空的。列表页副行只能显示「出场 N 案」，看着像没录数据。

按出场案数补了前 60 位（警视厅刑警、FBI、黑衣组织、主要配角），每人一句身份 + 一句与主线的关联，不复述单个案件情节以避免剧透。

脚本 `scripts/backfill-character-roles.py`，只填空值不覆盖已有内容，二遍幂等。

## 五、验证

```
validate-data.py                VALIDATION_OK
verify-en-titles                PASS
verify-p3-spoilernote           PASS
verify-nav-kinds                PASS
verify-ui-p4                    PASS
verify-m8-case-facts            PASS
node --check app.js / edit.js    OK
backfill-character-bonds-batch2  IDEMPOTENT_OK
backfill-character-roles         IDEMPOTENT_OK
backfill-character-bonds         IDEMPOTENT_OK
backfill-org-members             IDEMPOTENT_OK
```

## 六、备份点

| 文件 | 备份 |
|---|---|
| `data/entities/characters.json` | `/tmp/chars_pre_m17.json`（M17 前） |
| `data/entities/characters.json` | `/tmp/chars_pre_m18.json`（M18 前） |

## 七、纳入版本控制

`conan-archive` 之前一直没有版本控制。用户授权「达到满意就 pull 到 git」。

注意：`conan-archive` 位于 `/Users/ls/Desktop/agent/Hermes` 这个已有仓库内，而那个仓库的远端是 `bio-inspired-agent`（skill 仓库），旁边还有 `abuse_evidence/`、`frp-backup-20261010/` 等 24 个未跟踪目录。把本站混进去推到那个远端是错的，所以**在 `conan-archive` 内部单独初始化仓库**。

`.gitignore` 排除 `data/raw/`——那是 112MB 的页面块快照，由 scripts 重新抓取即可再生，进库会让仓库从 ~17MB 膨胀到 130MB。

## 八、遗留

- 人物记录中仍有 73 人 `role`/`summary` 为空（出场较少的配角），可继续按批补。
- 部分案件 `summary` 仍是英文（427 条），属另一条数据治理线。
- `character-shizuka-hattori`（服部静华）不在角色库，服部平藏–静华的夫妻关系仍未写入。
- 人物—案件图中心区在默认缩放下仍偏挤，属于 128 节点在 1190×743 画布的固有密度；再往上只能做聚类折叠。
