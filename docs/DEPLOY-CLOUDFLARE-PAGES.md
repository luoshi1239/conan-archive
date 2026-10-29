# 部署到 Cloudflare Pages

纯静态站，没有后端、没有构建步骤。数据是 JSON 文件，前端 `fetch` 读取。

## 一、先回答三个问题

### `data/raw/` 是什么

`data/raw/` 是我从 detectiveconanworld 抓下来的**原始页面快照**，112MB：

```
data/raw/
├── dcw-pages/              793 个 HTML 原文件，97MB   ← 大头
├── dcw-page-blocks.json    10.8MB   从 HTML 抽出的内容块
├── dcw-page-sections.json   3.1MB
├── dcw-page-facts.json      824KB
├── dcw-anime-index.json     682KB
└── 几个剧集索引 json
```

它是**加工原料**，不是站点数据。回填脚本（`backfill-*.py`）读它、解析出中文标题、
年份、死者、死因，写进 `data/entities/*.json` 和 `data/episodes/*.json`。
**前端一次都不读它**。

### 影响部署吗

不影响。技术上塞得进（CF 单文件限 25MiB，最大的 `dcw-page-blocks.json` 10.8MB；
总文件数限 20000，全站才 3303 个），但传上去是错的：

1. **纯浪费**：97MB 的 HTML 访客永远不会请求，部署时间从几秒变几分钟
2. **版权风险**：那是别人的网页原文，整站抄到公网 CDN 上，被投诉会直接下架整个项目
3. **已经在 `.gitignore` 里**：CF 走 Git 集成部署时，git 里没有的文件根本不会被部署

要归档原料另存一处（私有仓库或 release 压缩包），别塞进 Pages。

### 数据能全部上去吗

**站点真正需要的 7.5MB 全部在库里，一个不缺**：

| 目录 | 内容 | 进库 |
|---|---|---|
| `data/index/` | 索引分片，首屏加载 | ✅ 1.5MB |
| `data/detail/` | 详情分片，按需加载 | ✅ 9.9MB |
| `data/entities/` | 原始全量（verify 脚本用） | ✅ |
| `data/episodes/` `data/movies/` `data/ovas/` `data/manga/` | 原始全量 | ✅ |
| `data/sources.json` | 来源清单 | ✅ |
| `data/candidates/` | 人工复核候选池 | ✅ 但不影响运行 |
| `data/raw/` | 抓取原料 | ❌ 刻意排除 |

## 二、部署步骤

### 方式 A：Git 集成（推荐）

1. 把本仓库推到 GitHub、GitLab 或 Bitbucket
2. CF Dashboard → Workers & Pages → Create → Pages → Connect to Git
3. 选仓库，配置：
   - **Framework preset**：`None`
   - **Build command**：留空（不需要构建）
   - **Build output directory**：`/`
4. Save and Deploy

缓存头和 JSON 的 `Content-Type` 由根目录的 `_headers` 文件自动生效，CF Pages 原生支持，不用额外配置。

### 方式 B：直接上传（wrangler）

```bash
npx wrangler pages deploy . --project-name=conan-archive
```

同样会自动读取 `_headers`。

### 方式 C：拖拽上传

CF Dashboard 创建项目时选 "Direct Upload"，把整个目录拖进去。
注意：拖拽不会自动排除 `data/raw/`（它不在 git 里但物理上存在），
**上传前先手动移走 `data/raw/`**，否则多传 112MB。

## 三、加载性能：做了什么

### 改造前

首屏 `Promise.all` 一次性拉 12 个文件、**7.47MB 全量数据**，全部下载完并
`JSON.parse` 完才渲染第一行。手机 4G 上白屏 2 秒以上，中端机 `JSON.parse`
7.5MB 文本还要 150–300ms。

### 改造后

数据切成**索引 + 详情**两层，由 `scripts/build-split.py` 生成：

```
data/index/*.json              首屏只拉这个
data/detail/cases/<id>.json    打开抽屉时才拉，单条 gzip 后 0.7K
data/detail/episodes/<id>.json 单条 gzip 后 1.1K
data/detail/characters/<id>.json
```

索引只保留列表渲染、搜索、筛选、剧透档真正需要的字段。
大字段（`summary` 全文、`victims`、`suspects`、`locationsZh`、`castNames`）全部切到详情。

| | 原始 | gzip | 估算 brotli |
|---|---|---|---|
| 改造前（全量） | 7.47M | 1395K | 1185K |
| 改造后（索引） | 1.43M | **257K** | **218K** |
| 降幅 | **81%** | **82%** | **82%** |

单条详情平均 gzip 后不到 1K，打开抽屉只多一次几十毫秒的请求。

### 缓存策略（`_headers`）

| 路径 | 策略 | 为什么 |
|---|---|---|
| `/data/*` | `max-age=31536000, immutable` | 一天内不重复请求；靠 `?v=` 破缓存 |
| `/*.js` `/*.css` | 同上 | 版本戳在 `index.html` 里 |
| `/index.html` | `max-age=0, must-revalidate` | **绝不能缓存**，否则拿不到新 JS 地址 |

第二项是关键：`index.html` 里写着 `app.js?v=7f91f4`，HTML 一旦被缓存，
用户永远加载到旧 JS。

### 首屏骨架

索引到达前 `#archiveGrid` 里放 12 行 `.skeleton-row` 占位，避免白屏。
抽屉打开时如果详情还没回来，显示转圈 + 「正在读取档案…」，不是点了没反应。

### 实测效果（本机 CDP）

```
首屏数据请求 11 个 · 索引合计 1.43MB（本地未压缩）
DOMContentLoaded 41ms · load 41ms
点开案件 → 只请求 1 个详情文件
第二次开同一条 → 无请求（命中缓存）
三种图谱都能正常绘制（覆盖率 8.5%–9.4%）
搜索「怪盗基德」命中 10 行
```

## 四、数据更新流程

改了 `data/entities/*.json` 或 `data/episodes/*.json` 之后**必须重跑分片**，
否则前端读到的还是旧索引：

```bash
python3 scripts/build-split.py          # 重建 data/index + data/detail
md5 -q app.js | cut -c1-6             # 拿到新 hash
# 更新 index.html 里的 ?v=，并改 app.js 的 DATA_VERSION
```

`DATA_VERSION` 变了才会破 `/data/*` 的长缓存。

## 五、CF 限额对照

| 项 | CF Pages 限额 | 本站 |
|---|---|---|
| 单文件 | 25 MiB | 最大 10.8MB（`data/raw`，已排除）；索引最大 659KB |
| 总文件数 | 20,000 | **3,303** |
| 静态请求 | 免费不限量 | — |
| 月流量 | 无限（静态资源） | — |

都在限额内，免费版够用。
