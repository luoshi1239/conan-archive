# CONAN INDEX · 名侦探柯南结构化知识库

`conan-archive` 是一个纯静态、无后端的《名侦探柯南》粉丝知识库。新版不是单页展示，而是按“知识分区 → 问题场景 → 档案详情 → 关系与主线”组织的可扩展索引系统。

## 当前内容与覆盖状态

当前项目已经从早期的 20 条示例档案升级为分层数据仓库：

- 电视动画目录：1—1216 集，编号连续、无重复、无缺号
- 动画改编元数据：639 条漫画改编或带卷号记录，577 条动画原创记录
- 常规剧场版：30 条，其中 M30 单独标记为 `planned`
- 特殊电影 / 合作电影 / 总集篇 / 3D：6 条
- OVA / Magic File / Bonus File：18 条
- 核心人物：14 条
- 组织 / 阵营：4 条
- 主线篇章：7 条
- 案件索引：7 条
- 道具索引：8 条
- 来源登记：23 条
- 地点实体：6 条
- 主线优先结构化动画：136 集（含组织线、身份线、波本/朗姆线、基尔线、漆黑的特快列车和怪盗基德专题；深度犯人/手法/证据/结局仍未填）
- 结构化动画到漫画 File 映射：636 集，规范化 File 索引 323 条
- 电影与特殊电影：36 条，基础事实已统一标记为 `reviewed`
- OVA / Magic File / Bonus File：18 条，基础事实已统一标记为 `reviewed`
- 内容覆盖报告：`docs/CONTENT-COVERAGE.json`，区分目录覆盖、基础事实、结构化详情和深度剧透
- 关系闭合报告：`docs/RELATION-CLOSURE.json`，记录案件/篇章正向引用、动画反向引用和未闭合范围
- 字段可信度报告：`docs/FIELD-CONFIDENCE.json`，区分字段存在、来源存在、来源可识别和审核状态
- 内容批次清单：`docs/CONTENT-BATCHES.json`
- 批次进度报告：`docs/BATCH-PROGRESS.json`
- 案件覆盖报告：`docs/CASE-COVERAGE.json`

“目录覆盖”不等于“每条都有完整剧情详情”。普通动画集目前以目录、标题、日期、改编类型和来源状态为主；犯人、手法、证据、结局、出场人物等深度字段按批次校对补录，无法确认的字段保持待补，不用猜测填充。

## 当前内容

- 8 个知识分区：人物、组织与阵营、故事主线、案件与诡计、道具与技术、剧场版宇宙、地点与文化、作品与作者
- 6 条阅读场景：入门、组织线、人物关系、案件研究、剧场版、全剧透
- 分层 JSON 数据：原始底稿、规范化动画、电影、OVA、实体和来源登记
- 主线推进器：从缩小事件到当前连载的阅读骨架
- 关系图谱：柯南、新一、兰、灰原、组织、FBI/公安、平次与剧场版的入口关系
- 本地全文搜索：标题、别名、简介、标签、目录字段和实体字段均可检索
- 分类筛选、名称/剧透等级排序和分页
- 入门 / 深入 / 全剧透三档阅读级别
- 档案详情弹窗、随机档案、快捷键 `/` 搜索、`⌘K` / `Ctrl+K` 随机打开
- 深色 / 浅色主题切换，并记住本地偏好
- 手机响应式布局与 `prefers-reduced-motion` 处理

## 文件结构

```text
conan-archive/
├── index.html
├── data.js                         # 旧版主题分区、场景、关系和术语
├── app.js                          # 统一加载、搜索、筛选、分页和详情
├── styles.css
├── data/
│   ├── raw/                        # 原始第三方目录底稿，只读保留
│   ├── candidates/                 # 待审核候选字段，不直接供前端读取
│   ├── episodes/episodes.json      # 规范化电视动画 1—1216
│   ├── movies/                     # 常规与特殊电影
│   ├── ovas/ovas.json              # OVA / Magic File / Bonus File
│   ├── manga/mainline-arcs.json    # 主线篇章索引
│   ├── entities/                   # 人物、组织、案件、道具、地点
│   └── sources.json                # 来源登记
├── docs/DATA-SCHEMA.md
├── scripts/
│   ├── normalize-episodes.py
│   ├── enrich-mainline-episodes.py
│   ├── enrich-arc-coverage.py
│   ├── enrich-catalog-records.py
│   ├── report-content-coverage.py
│   ├── report-relation-closure.py
│   ├── report-field-confidence.py
│   ├── report-batch-progress.py
│   ├── validate-candidates.py
│   ├── autonomous-content-worker.py
│   └── validate-data.py
└── legacy.html                     # 第一版页面备份
```

原始底稿不直接供页面读取；规范化 JSON 由脚本生成，校验脚本负责检查编号、重复、来源和实体引用。

### 内容层级与批处理状态

每条动画记录区分四个口径：

- `directory`：目录记录存在；
- `basicFacts`：标题、年份、改编类型等基础事实可用；
- `structure`：已关联主线、案件、人物、组织、地点或案件类型；
- `deepSpoilers`：犯人、动机、手法、证据、结局等深度字段已校对。

当前主线优先批次已完成 136 集的 `reviewed + structure`，并支持 `arcRefs` 表示跨篇章交叉归属；没有填入未经核对的犯人、手法、证据和结局。重新运行 `normalize-episodes.py` 会保留已审核增强字段。

## 本地运行

```bash
cd /Users/ls/Desktop/agent/Hermes/conan-archive
python3 -m http.server 4173
```

打开 <http://127.0.0.1:4173>。

## 内容扩展方式

以后新增档案时，直接编辑 `data.js` 的 `entries` 数组，字段格式如下：

```js
{
  id: 'unique-id',
  discipline: 'core',
  title: '档案标题',
  subtitle: '一句副标题',
  mark: 'C',
  color: 'cyan',
  level: 'beginner',
  tags: ['人物', '主线'],
  intro: '目录卡片简介。',
  sections: [['段落标题', '详情内容']],
  source: '来源说明',
  spoiler: 1
}
```

`spoiler` 取值：

- `1`：入门
- `2`：深入
- `3`：全剧透

档案只会在当前阅读级别允许时显示，因此可以继续扩充完整主线而不破坏入门体验。

## Cloudflare Pages

### GitHub 自动部署

Cloudflare Dashboard → **Workers & Pages** → **Create application** → **Pages** → **Import an existing Git repository**。

纯静态站点配置：

| 配置 | 值 |
|---|---|
| Production branch | `main` |
| Framework preset | `None` |
| Build command | `exit 0` |
| Build output directory | `.` |
| Root directory | `/` |

如果仓库根目录就是 `conan-archive`，直接将这个目录作为仓库根目录即可。新版不需要 Node 构建，也不需要环境变量。

### Wrangler Direct Upload

```bash
npm install -g wrangler
wrangler login
cd /Users/ls/Desktop/agent/Hermes/conan-archive
wrangler pages project create conan-index
wrangler pages deploy . --project-name conan-index
```

## 来源与版权边界

- 官方作品站：<https://detective-conan.com>
- 道具与作品资料：<https://www.detectiveconanworld.com/wiki/Gadgets>
- Cloudflare Pages 静态 HTML 文档：<https://developers.cloudflare.com/pages/framework-guides/deploy-anything/>
- 结构设计参考：<https://mungermodels.com/>，仅借鉴“分区、场景、档案、关系图谱”的信息架构，不复制其品牌、文案或视觉资产

这是非官方粉丝整理项目。页面使用原创 CSS、文字摘要和抽象图形，不嵌入未经授权的官方剧照、动画片段或角色立绘。作品事实会随着漫画、动画和剧场版更新，档案应持续校对并保留来源。
