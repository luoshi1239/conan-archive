/* 名侦探柯南 · 案件档案 —— 重写版前端
   设计目标：可查找。左导航常驻、顶部搜索直达、列表高密度、详情用右侧抽屉（不打断浏览）。
   关系图由真实数据计算（力导向 + 真实连线），不再是写死的装饰。

   ⚠ 以下函数/常量被 scripts/verify-*.js 用正则抽取后 eval，改名会破坏验证链：
     LANG_ORDER LABELS_ZH AGE_PAREN_ZH catalog 常量，
     textOf langOf labelOf titleOf entityRecord nameOfRef formatAge formatVictim
     refsText labelZh formatEpisodeNumber formatAnimeRef formatMangaRef detailSections 函数。
   注意：不要在文件顶部注释里写出「const 加花括号」的字面形状，抽取正则会被误捕。
*/

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

const levelNames = { 1: '入门', 2: '深入', 3: '全剧透' };
const catalog = { episodes: [], movies: [], ovas: [], entities: [], sources: new Map() };

// 当前视图：overview | cases | characters | organizations | locations | gadgets | episodes | movies | ovas | graph
let view = 'overview';
let activeLevel = 1;
let sortMode = 'default';
let currentPage = 1;
let pageSize = 30;
let activeDiscipline = 'all';

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
}

// ── 多语言字段 ──────────────────────────────────────────────
// 字段可能是纯字符串（旧数据），也可能是 {zhHans, zhHant, ja, en} 对象。
// 顺序：中文优先，英文兜底；对象直接 String() 会变成 [object Object]，必须走这里。
const LANG_ORDER = ['zhHans', 'zhHant', 'ja', 'en'];

function textOf(value, order = LANG_ORDER) {
  if (value === null || value === undefined) return '';
  if (typeof value === 'string') return value.trim();
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  if (typeof value === 'object') {
    for (const lang of order) {
      const v = value[lang];
      if (typeof v === 'string' && v.trim()) return v.trim();
    }
  }
  return '';
}

// 当前取到的是哪种语言（用于「英文原文·待译」角标）
function langOf(value, order = LANG_ORDER) {
  if (typeof value === 'string') return 'zhHans';
  if (value && typeof value === 'object') {
    for (const lang of order) {
      const v = value[lang];
      if (typeof v === 'string' && v.trim()) return lang;
    }
  }
  return '';
}

// 带语言标注的展示文本
function labelOf(value) {
  const text = textOf(value);
  if (!text) return '';
  const lang = langOf(value);
  if (lang === 'en') return `${text}（英文原文·待译）`;
  if (lang === 'ja') return `${text}（日文原文·待译）`;
  return text;
}

function titleOf(record) {
  return record.title?.zhHans || record.title?.zhHant || record.title?.ja || record.title?.en || '未命名条目';
}

function formatEpisodeNumber(number) {
  const value = Number(number);
  if (!Number.isFinite(value)) return 'SPECIAL';
  return `EP.${String(value).padStart(2, '0')}`;
}

// ── 实体索引：id → 记录，供引用解析与关系图使用 ──────────────
// 索引挂在 catalog 上而不是外部变量：这样本函数被 scripts/verify-*.js 单独抽取后
// 依然能自洽（那些脚本只注入 catalog，不注入模块级私有变量）。
function entityRecord(id) {
  if (typeof id !== 'string') return null;
  const list = catalog.entities || [];
  if (!catalog._index || catalog._index.size !== list.length) {
    catalog._index = new Map(list.map((record) => [record.id, record]));
  }
  return catalog._index.get(id) || null;
}

// 把实体 id 解析成展示名（「关联人物」「出场案件」这类引用字段用）
function nameOfRef(id) {
  if (typeof id !== 'string') return String(id || '');
  const target = entityRecord(id);
  if (!target) return id;
  return target.name ? textOf(target.name) : textOf(target.title) || id;
}

function refsText(ids, limit = 12) {
  // solvedBy 是纯姓名串（772 案），caseRefs/characters 才是 id 数组；
  // 这里统一成数组再解析，避免字符串直接 .map 崩掉。
  const source = Array.isArray(ids) ? ids : String(ids ?? '').split(/[、,，;；]/);
  const list = source.map((x) => String(x).trim()).filter(Boolean).map(nameOfRef).filter(Boolean);
  if (list.length <= limit) return list.join('、');
  return `${list.slice(0, limit).join('、')} 等 ${list.length} 项`;
}

// 动画范围：animeRefs 是剧集 id，形如 episode-0516 / episode-0516-0517（合并区间）。
// 直接 join 会把内部 id 暴露给用户，所以在这里解析成「EP.516」。
function formatAnimeRef(ref) {
  const m = /^episode-(\d+)(?:-(\d+))?$/.exec(ref || '');
  if (!m) return ref;
  const a = Number(m[1]);
  if (!m[2]) return formatEpisodeNumber(a);
  const b = Number(m[2]);
  return b - a <= 3 ? `${formatEpisodeNumber(a)}–${b}` : `${formatEpisodeNumber(a)}–${b}（共 ${b - a + 1} 集）`;
}

// 漫画范围：mangaRefs 是 File id，形如 file-613 / file-613-618。
// files.json 里只有单 File，区间形式查不到实体，按原文形态展示为「File 613-618」。
function formatMangaRef(ref) {
  const m = /^file-(\d+)(?:-(\d+))?$/.exec(ref || '');
  if (!m) return ref;
  return m[2] ? `File ${Number(m[1])}-${Number(m[2])}` : `File ${Number(m[1])}`;
}

// ── 被害者条目 ──────────────────────────────────────────────
// 年龄：数据里存的是英文原句（"25 years old"、"56 years old (Eisuke) and 35 years old (Tatsuya)"），
// 但格式高度规整，属于纯格式化，放展示层转换，不动数据。
const AGE_PAREN_ZH = {
  Tae: '妙', Eisuke: '英介', Tatsuya: '达也', Seiko: '圣子', Kaori: '香织',
  Tatematsu: '立松', Okonogi: '小此木', Kurumatani: '车谷', Rei: '玲',
  Sachiko: '幸子', Kono: '河野', Kashiyama: '柏山', Mizunuma: '水沼',
  Tsujimoto: '辻本', Juukichi: '重吉', 'five years ago': '五年前',
};

function formatAge(age) {
  if (!age) return '';
  return String(age)
    .replace(/(\d+(?:\s*[/\-–]\s*\d+)?)\s*[Yy]ears?\s+old/g, '$1 岁')
    .replace(/\s*&\s*/g, ' 与 ')
    .replace(/\s+and\s+/g, ' 与 ')
    .replace(/\(([^)]+)\)/g, (_, inner) => {
      const key = inner.trim();
      return `（${AGE_PAREN_ZH[key] || key}）`;
    })
    .replace(/\s*,\s*/g, '、')
    .replace(/、\s+/g, '、')
    .replace(/\s+（/g, '（')
    .replace(/\s+）/g, '）')
    .replace(/\s+/g, ' ')
    .trim();
}

function formatVictim(victim) {
  if (!victim) return '';
  if (typeof victim === 'string') return victim;
  // 姓名与死因都优先用回填的中文（nameZh / causeOfDeathZh），
  // 没有中文时退回英文原文，明确露出未译项，不在展示层猜。
  const name = victim.nameZh || victim.name;
  const cause = victim.causeOfDeathZh || victim.causeOfDeath;
  const extras = [formatAge(victim.age), cause].filter(Boolean);
  return extras.length ? `${name}（${extras.join('、')}）` : name;
}

// ── 展示层中文词表 ──────────────────────────────────────────
// 数据里的枚举是英文 slug（caseType / kind / status），直接渲染会在中文界面里
// 露出「serial-murder」这种内部值。这里只做展示映射，不改数据。
// 映射不到的保留原值，方便发现漏项，绝不乱猜。
const LABELS_ZH = {
  'manga-case': '漫画改编案', 'anime-original-case': '动画原创案', 'organization-case': '组织相关案',
  'anime-original': '动画原创', 'manga-adaptation': '漫画改编', 'manga': '漫画改编',
  'anime-manga-adaptation': '动画与漫画双改编',
  'locked-room': '密室', 'locked-room-like': '准密室', 'locked-room-illusion': '密室错觉',
  murder: '杀人', 'serial-murder': '连续杀人', 'serial-identity-start': '连续身份案起点',
  'serial-staged-accident': '连续伪装事故', 'mystery-tour': '推理之旅', 'closed-circle': '封闭空间',
  'impossible-crime': '不可能犯罪', kidnapping: '绑架', organization: '组织事件', poisoning: '毒杀',
  identity: '身份之谜', revenge: '复仇', disguise: '易容', 'cold-case': '陈年旧案', bombing: '爆炸',
  treasure: '寻宝', 'blunt-force': '钝器致死', cipher: '暗号', island: '孤岛', 'music-clue': '音乐线索',
  'rival-detectives': '名侦探对决', legend: '传说', undercover: '卧底', 'intelligence-war': '情报战',
  'drug-dealing': '毒品交易', library: '图书馆', elevator: '电梯', 'fishing-rod-weapon': '钓竿凶器',
  'train-trick': '列车诡计', 'remote-mechanism': '远程机关', surveillance: '监视', demolition: '爆破',
  'framed-suicide': '伪装自杀（嫁祸）', 'art-forgery': '赝品画作', 'staged-suicide': '伪装自杀',
  'staged-footprints': '伪造脚印', 'film-studio': '电影制片厂', 'third-fingerprint': '第三枚指纹',
  'police-corruption': '警界腐败', ransom: '勒索', theater: '剧场', hotel: '旅馆', stalking: '跟踪骚扰',
  triplets: '三胞胎', 'alibi-trick': '不在场证明诡计', 'attempted-murder': '杀人未遂', drowning: '溺亡',
  gunshot: '枪击', heist: '盗窃', 'phantom-thief': '怪盗', framing: '嫁祸', 'double-case': '双案并行',
  arson: '纵火', suicide: '自杀', robbery: '抢劫', accomplice: '共犯', silencing: '灭口',
  'self-defense-question': '正当防卫之争', strangulation: '勒杀', amnesia: '失忆', embezzlement: '侵占公款',
  hostage: '人质', 'trick-floor': '地板机关', 'staged-accident': '伪装事故', 'time-delay-device': '延时装置',
  catalog: '基础目录', reviewed: '已校对', complete: '档案完整', partial: '部分收录',
  released: '已上映', planned: '未上映', aired: '已播出', upcoming: '待播出',
  // 地点 kind：不映射就会把 theme-park / city-district 这种内部 slug 直接显示给用户
  'theme-park': '游乐园', island: '孤岛', 'city-district': '街区', train: '列车',
  'detective-office': '事务所', school: '学校', building: '建筑', ship: '船', mountain: '山',
  // 组织 / 道具 kind
  'criminal-organization': '犯罪组织', 'investigative-agency': '侦查机构',
  'security-agency': '公安机构', 'research-family-line': '家族研究线', gadget: '道具',
  deepSpoilers: '深度剧透', skeleton: '仅有骨架', pending: '待译',
};

function labelZh(value) {
  if (!value) return '';
  return LABELS_ZH[value] || value;
}

// ══════════════════════════════════════════════════════════
//  记录归一化：所有分区都变成同一种「行」结构，列表与详情共用
// ══════════════════════════════════════════════════════════

const KIND_MARK = { case: '案', character: '人', organization: '组', location: '地', gadget: '物', episode: '集', movie: '影', ova: 'OVA' };
const KIND_LABEL = { case: '案件', character: '人物', organization: '组织', location: '地点', gadget: '道具', episode: '动画', movie: '剧场版', ova: '衍生' };

function entityTypeOf(record) {
  const id = record.id || '';
  if (id.startsWith('case-')) return 'case';
  if (id.startsWith('character-')) return 'character';
  if (id.startsWith('organization-')) return 'organization';
  if (id.startsWith('location-')) return 'location';
  if (id.startsWith('gadget-')) return 'gadget';
  return 'arc';
}

function catalogTypeOf(record) {
  const kind = record.kind || '';
  if (kind === 'tv-episode') return 'episode';
  if (kind.includes('movie')) return 'movie';
  return 'ova';
}

function entitySummaryLine(record) {
  const type = entityTypeOf(record);
  if (type === 'case') {
    const refs = (record.animeRefs || []).slice(0, 2).map(formatAnimeRef);
    const types = (record.caseType || []).slice(0, 2).map(labelZh);
    return [...refs, ...types].filter(Boolean).join(' · ') || labelZh(record.kind) || '案件';
  }
  if (type === 'character') {
    const n = (record.caseRefs || []).length;
    return [record.role, n ? `出场 ${n} 案` : ''].filter(Boolean).join(' · ') || '人物';
  }
  if (type === 'organization') {
    const n = (record.members || []).length;
    return [labelZh(record.kind) || record.role, n ? `${n} 名成员` : ''].filter(Boolean).join(' · ') || '组织';
  }
  // 兜底：kind 查不到映射时不再把原始 slug 甩给用户（以前会显示 theme-park 这种内部值），
  // 直接用类别名顶上。漏映射应当去补 LABELS_ZH，而不是靠这里露原值。
  const kindLabel = labelZh(record.kind);
  const shown = kindLabel && kindLabel !== record.kind ? kindLabel : '';
  return [shown || record.role, record.status === 'catalog' ? '基础目录' : ''].filter(Boolean).join(' · ') || KIND_LABEL[type] || '';
}

// 统一成行：type 决定分区与配色，mark 是左侧小标记，cols 是右侧信息列
function toRow(record) {
  if (record.kind === 'tv-episode' || record.kind?.includes('movie')
    || ['ova', 'magic-file', 'bonus-file', '3d-short', 'secret-file', 'ova-file'].includes(record.kind)) {
    const type = catalogTypeOf(record);
    const num = type === 'episode' ? formatEpisodeNumber(record.number ?? record.episode) : String(record.number ?? '').padStart(2, '0');
    // OVA 的 number 按 kind 各自从 1 起（secret-file / magic-file / bonus-file 会重复），
    // 不带前缀会出现三个 OVA01。用 kind 后缀区分：OVA01 / MAGIC01 / BONUS01
    const ovaTag = record.kind === 'magic-file' ? 'MAGIC' : record.kind === 'bonus-file' ? 'BONUS'
      : record.kind === '3d-short' ? '3D' : record.kind === 'secret-file' ? 'SECRET' : 'OVA';
    const mark = type === 'episode' ? `EP${num.replace('EP.', '')}` : type === 'movie' ? `M${num}` : `${ovaTag}${num}`;
    // OVA 没 number 时 mark 会是 OVA01…，但副行目前空白——统一在下方 sub 里拼
    const subParts = [KIND_LABEL[type]];
    if (record.year) subParts.push(record.year);
    if (record.adaptation) subParts.push(labelZh(record.adaptation));
    return {
      id: record.id, type, title: titleOf(record), mark,
      sub: subParts.filter(Boolean).join(' · '),
      col1: record.year || (record.releaseDate ? String(record.releaseDate).slice(0, 4) : '—'),
      col2: labelZh(record.status) || '—',
      spoiler: record.spoiler || 1, raw: record,
    };
  }
  const type = entityTypeOf(record);
  return {
    id: record.id, type, title: record.name ? textOf(record.name) : titleOf(record),
    mark: KIND_MARK[type] || '·',
    sub: entitySummaryLine(record),
    col1: type === 'case' ? (record.animeRefs || []).slice(0, 1).map(formatAnimeRef)[0] || '—' : KIND_LABEL[type] || '—',
    col2: labelZh(record.status) || '—',
    spoiler: record.spoiler || 1, raw: record,
  };
}

// ══════════════════════════════════════════════════════════
//  各视图的数据源
// ══════════════════════════════════════════════════════════

function rowsForView(name) {
  // 列表也要走补丁：爱好者在抽屉里改了简介，列表里立刻跟着变
  const byType = (t) => catalog.entities
    .filter((r) => entityTypeOf(r) === t)
    .map((r) => toRow(typeof patchedRecord === 'function' ? patchedRecord(r) : r));
  switch (name) {
    case 'cases': return byType('case');
    case 'characters': return byType('character');
    case 'organizations': return byType('organization');
    case 'locations': return byType('location');
    case 'gadgets': return byType('gadget');
    case 'episodes': return catalog.episodes.map(toRow);
    case 'movies': return catalog.movies.map(toRow);
    case 'ovas': return catalog.ovas.map(toRow);
    default: return [];
  }
}

function searchText(row) {
  if (!row._search) {
    const raw = row.raw || {};
    row._search = [row.title, row.sub, raw.id, textOf(raw.summary), textOf(raw.title), textOf(raw.name),
      ...(raw.aliases || []), ...(raw.caseType || []), raw.role || ''].join(' ').toLowerCase();
  }
  return row._search;
}

function filteredRows(ignoreLevel = false) {
  const query = $('#searchInput').value.trim().toLowerCase();
  let rows = rowsForView(view);
  // 搜索时不受剧透档限制：查名字就该找到，否则「有这条数据却搜不到」。
  if (!ignoreLevel) rows = rows.filter((row) => (row.spoiler || 1) <= activeLevel);
  if (query) {
    const terms = query.split(/\s+/).filter(Boolean);
    rows = rows.filter((row) => terms.every((t) => searchText(row).includes(t)));
  }
  return rows;
}

// ══════════════════════════════════════════════════════════
//  列表渲染
// ══════════════════════════════════════════════════════════

function renderTableHead() {
  const head = $('#tableHead');
  if (!head) return;
  const labels = {
    cases: ['标记', '案件名称 / 剧集与类型', '动画范围', '收录', '级别'],
    characters: ['标记', '姓名 / 身份', '类别', '收录', '级别'],
    organizations: ['标记', '组织 / 阵营', '类别', '收录', '级别'],
    locations: ['标记', '地点 / 场所', '类别', '收录', '级别'],
    gadgets: ['标记', '道具 / 功能', '类别', '收录', '级别'],
    episodes: ['标记', '剧集标题', '年份', '收录', '级别'],
    movies: ['标记', '剧场版标题', '年份', '收录', '级别'],
    ovas: ['标记', '衍生作品标题', '年份', '收录', '级别'],
  }[view] || ['标记', '名称', '', '', '级别'];
  head.innerHTML = labels.map((t) => `<span>${escapeHtml(t)}</span>`).join('');
}

function renderRow(row) {
  const levelTxt = `LV.${row.spoiler}`;
  return `<div class="row" data-id="${escapeHtml(row.id)}" data-type="${row.type}"
    role="button" tabindex="0" aria-label="${escapeHtml(row.title)}">
    <span class="row-mark kind-${row.type}">${escapeHtml(row.mark)}</span>
    <span class="row-title"><b>${escapeHtml(row.title)}</b><span>${escapeHtml(row.sub)}</span></span>
    <span class="row-cell">${escapeHtml(row.col1)}</span>
    <span class="row-cell opt">${escapeHtml(row.col2)}</span>
    <span class="row-lv">${levelTxt}</span>
  </div>`;
}

function renderPager(total) {
  const host = $('#archivePagination');
  if (!host) return;
  const pages = Math.max(1, Math.ceil(total / pageSize));
  currentPage = Math.min(Math.max(currentPage, 1), pages);
  const nums = [];
  const start = Math.max(1, Math.min(currentPage - 2, pages - 4));
  for (let p = start; p <= Math.min(pages, start + 4); p += 1) {
    nums.push(`<button class="${p === currentPage ? 'active' : ''}" data-page="${p}">${p}</button>`);
  }
  host.innerHTML = `<div class="pager">
    <span>共 <b>${total.toLocaleString('zh-CN')}</b> 条 · 第 ${currentPage} / ${pages} 页</span>
    <div class="pg-btns">
      <button data-nav="first" ${currentPage === 1 ? 'disabled' : ''}>«</button>
      <button data-nav="prev" ${currentPage === 1 ? 'disabled' : ''}>‹</button>
      ${nums.join('')}
      <button data-nav="next" ${currentPage === pages ? 'disabled' : ''}>›</button>
      <button data-nav="last" ${currentPage === pages ? 'disabled' : ''}>»</button>
    </div>
  </div>`;
  $$('#archivePagination [data-nav]').forEach((b) => b.addEventListener('click', () => {
    const a = b.dataset.nav;
    if (a === 'first') currentPage = 1;
    if (a === 'prev') currentPage -= 1;
    if (a === 'next') currentPage += 1;
    if (a === 'last') currentPage = pages;
    renderList();
  }));
  $$('#archivePagination [data-page]').forEach((b) => b.addEventListener('click', () => {
    currentPage = Number(b.dataset.page);
    renderList();
  }));
}

function renderList() {
  if (view === 'overview' || view === 'graph') {
    // 离开列表视图时把 DOM 清空：否则 #archiveGrid 里留着上一页的行，
    // 一旦 .hidden 没生效（旧 CSS 缓存、样式冲突），看到的就是「总览复用案件列表」。
    $('#archiveGrid').innerHTML = '';
    return;
  }
  const searching = Boolean($('#searchInput').value.trim());
  let rows = filteredRows(searching);
  if (sortMode === 'title') rows.sort((a, b) => a.title.localeCompare(b.title, 'zh'));
  if (sortMode === 'level') rows.sort((a, b) => (a.spoiler || 1) - (b.spoiler || 1));
  const total = rows.length;
  const page = rows.slice((currentPage - 1) * pageSize, currentPage * pageSize);
  $('#archiveGrid').innerHTML = page.map(renderRow).join('');
  $('#emptyState').classList.toggle('hidden', total > 0);
  $('#resultLabel').textContent = total
    ? `${KIND_LABEL[view] || '档案'} · 命中 ${total.toLocaleString('zh-CN')} 条${searching ? '（搜索不受剧透档限制）' : `（剧透上限：${levelNames[activeLevel]}）`}`
    : `没有命中${searching ? '' : `（剧透上限：${levelNames[activeLevel]}）`}`;
  renderTableHead();
  renderPager(total);
  $$('#archiveGrid .row').forEach((el) => {
    const open = () => openDetail(el.dataset.id);
    el.addEventListener('click', open);
    el.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); } });
  });
  if (window.history?.replaceState) history.replaceState(null, '', `#${view}${currentPage > 1 ? `/p${currentPage}` : ''}`);
}

// ══════════════════════════════════════════════════════════
//  详情抽屉
// ══════════════════════════════════════════════════════════

// 引用字段渲染成可点击标签，点了切到对应档案——抽屉里能一路走下去
function linkRow(ids, limit = 40) {
  const list = (ids || []).slice(0, limit);
  if (!list.length) return '';
  const btns = list.map((id) => {
    const target = entityRecord(id);
    const label = nameOfRef(id);
    return target
      ? `<button data-goto="${escapeHtml(id)}">${escapeHtml(label)}</button>`
      : `<span>${escapeHtml(label)}</span>`;
  });
  const more = (ids || []).length > limit ? `<span>…共 ${ids.length} 项</span>` : '';
  return `<div class="d-links">${btns.join('')}${more}</div>`;
}

function sourceLabel(id) {
  const item = catalog.sources instanceof Map ? catalog.sources.get(id) : null;
  if (!item) return String(id || '').replace(/^src-/, '');
  // 站名本身是外文专名，保留原样；括注 scope 说明这站用作什么
  return item.scope ? `${item.title}（${item.scope}）` : item.title;
}

function detailSections(record, type) {
  const raw = record.raw || record;
  const sections = [];
  const isCase = (raw.id || '').startsWith('case-');
  const isChar = (raw.id || '').startsWith('character-');

  if (type === 'entity') {
    if (isCase) {
      const summary = labelOf(raw.summary);
      if (summary) sections.push(['案件概述', summary]);
      // 案件事实（M8）：只来自 DCW situation 设定段原文，非剧透。逐字搬运，不拆名不改写。
      if (raw.victims?.length) sections.push(['被害者', raw.victims.map(formatVictim).join('\n'), true]);
      if (raw.suspects?.length) {
        // 嫌疑人优先用 suspectsZh（M14 回填的中文平行数组），回退原文
        const zh = Array.isArray(raw.suspectsZh) && raw.suspectsZh.length === raw.suspects.length
          ? raw.suspectsZh
          : raw.suspects;
        sections.push(['嫌疑人', zh.join('\n'), true]);
      }
      if (raw.solvedBy?.length) sections.push(['解决者', refsText(raw.solvedBy, 10)]);
      if (raw.caseType?.length) sections.push(['案件类型', raw.caseType.map(labelZh).join('、')]);
      if (raw.animeRefs?.length) sections.push(['动画范围', raw.animeRefs.map(formatAnimeRef).join('、')]);
      if (raw.mangaRefs?.length) sections.push(['漫画范围', raw.mangaRefs.map(formatMangaRef).join('、')]);
      const l3 = [['犯人', raw.culprit], ['动机', raw.motive], ['手法', raw.method], ['证据', raw.evidence], ['结局', raw.resolution]];
      const hasL3 = l3.some(([, v]) => textOf(v));
      const spoilerOpen = raw.spoiler >= 3 || raw.detailStatus === 'deepSpoilers' || raw.deepSpoilers === true;
      if (hasL3) {
        if (spoilerOpen) {
          for (const [label, value] of l3) {
            const text = labelOf(value);
            if (text) sections.push([`${label}　全剧透`, text]);
          }
        } else {
          sections.push(['深度剧透', '该案按少剧透收录，犯人／动机／手法／证据／结局未展开。']);
        }
      }
    } else {
      const summary = labelOf(raw.summary);
      if (summary) sections.push(['档案概述', summary]);
      if (raw.role) sections.push(['身份 / 职能', raw.role]);
      if (raw.note) sections.push(['备注', raw.note]);
      if (raw.aliases?.length) sections.push(['别名', raw.aliases.join('、')]);
    }

    if (raw.spoilerNote) sections.push(['收录备注', raw.spoilerNote]);
    if (isChar && raw.caseRefs?.length) sections.push(['出场案件', refsText(raw.caseRefs, 40), false, { links: raw.caseRefs, limit: 40 }]);
    if (raw.characters?.length) sections.push(['关联人物', refsText(raw.characters), false, { links: raw.characters }]);
    if (raw.userRefs?.length) sections.push(['使用者', refsText(raw.userRefs), false, { links: raw.userRefs }]);
    if (raw.members?.length) sections.push(['成员', refsText(raw.members), false, { links: raw.members }]);
    if (raw.relations?.length) sections.push(['关系', refsText(raw.relations), false, { links: raw.relations }]);
    if (raw.relatedCases?.length) sections.push(['关联案件', refsText(raw.relatedCases), false, { links: raw.relatedCases }]);
    if (raw.relatedArcs?.length) sections.push(['关联主线', refsText(raw.relatedArcs), false, { links: raw.relatedArcs }]);
    if (raw.relatedLocations?.length) sections.push(['关联地点', refsText(raw.relatedLocations), false, { links: raw.relatedLocations }]);
    if (raw.locations?.length) {
      // 案发地点优先用 locationsZh（M13 回填的中文平行数组），回退原文
      const zh = Array.isArray(raw.locationsZh) && raw.locationsZh.length === raw.locations.length
        ? raw.locationsZh
        : raw.locations.map((x) => nameOfRef(x));
      sections.push(['关联地点', zh.join('、')]);
    }
    if (raw.organizations?.length) sections.push(['所属组织', refsText(raw.organizations), false, { links: raw.organizations }]);
    return sections;
  }

  if (raw.kind === 'tv-episode') {
    return [
      ['集数', formatEpisodeNumber(raw.number)],
      ['播出年份', String(raw.year || '待补')],
      ['改编类型', labelZh(raw.adaptation) || '待校对'],
      ['所属主线', raw.arc || '独立案件 / 待校对'],
      ['关联案件', '', false, { links: raw.caseRefs, limit: 8 }],
      ['剧情摘要', labelOf(raw.summary) || '目录已收录，详细剧情待补'],
    ];
  }
  return [
    ['作品编号', String(raw.number ?? '—')],
    ['上映日期', raw.releaseDate || '待补'],
    ['片长', raw.runtimeMinutes ? `${raw.runtimeMinutes} 分钟` : '待补'],
    ['关联主线', raw.arc || '独立作品 / 待校对'],
    ['状态', labelZh(raw.status) || '待校对'],
  ];
}

function openDetail(id, type) {
  const base = entityRecord(id) || [...catalog.episodes, ...catalog.movies, ...catalog.ovas].find((r) => r.id === id);
  if (!base) return;
  // 叠上本地爱好者修订，页面立刻反映最新内容
  const raw = typeof patchedRecord === 'function' ? patchedRecord(base) : base;
  const resolvedType = type || (entityRecord(id) ? 'entity' : 'catalog');
  const row = toRow(raw);
  const level = raw.spoiler || 1;
  if (level > activeLevel) { activeLevel = level; $('#spoilerSelect').value = String(activeLevel); renderList(); }

  $('#drawerKicker').textContent = `${KIND_LABEL[row.type] || '档案'} · ${row.mark} · ${levelNames[level]}${raw.__patched ? ' · 含本地修订' : ''}`;
  const tags = [KIND_LABEL[row.type], labelZh(raw.status), ...(raw.caseType || []).slice(0, 4).map(labelZh)].filter(Boolean);
  const body = [];
  body.push(`<h2>${escapeHtml(row.title)}</h2>`);
  if (row.sub) body.push(`<p class="d-sub">${escapeHtml(row.sub)}</p>`);
  body.push(`<div class="d-tags">${[...new Set(tags)].map((t) => `<span>${escapeHtml(t)}</span>`).join('')}</div>`);

  for (const [heading, text, pre, opts] of detailSections(row, resolvedType)) {
    if (opts?.links) {
      const html = linkRow(opts.links, opts.limit || 40);
      if (html) body.push(`<div class="d-sec"><h3>${escapeHtml(heading)}</h3>${html}</div>`);
      continue;
    }
    if (!text) continue;
    body.push(`<div class="d-sec"><h3>${escapeHtml(heading)}</h3><p${pre ? ' class="pre-line"' : ''}>${escapeHtml(text)}</p></div>`);
  }
  const src = (raw.sources || []).map(sourceLabel).join('、');
  if (src) body.push(`<div class="d-foot">${escapeHtml(src)}</div>`);
  // 只有实体（人物/组织/案件…）可修订，剧集目录不开放
  if (resolvedType === 'entity' && typeof patchEditorHtml === 'function') {
    body.push(patchEditorHtml(raw));
  }
  $('#drawerBody').innerHTML = body.join('');
  $('#drawerBody').scrollTop = 0;
  $('#drawer').classList.add('open');
  document.body.classList.add('drawer-open');
  $('#drawer').setAttribute('aria-hidden', 'false');
  $('#scrim').classList.add('on');
  $$('#drawerBody [data-goto]').forEach((b) => b.addEventListener('click', () => openDetail(b.dataset.goto)));
  // 绑定修订表单：保存后重开抽屉，让改动立刻可见
  if (typeof bindPatchEditor === 'function') {
    bindPatchEditor(raw, () => { openDetail(id, type); renderList(); });
  }
  // 抽屉重开时同步左下角「修订」计数，否则改完仍显示 0
  if (typeof refreshPatchBadge === 'function') refreshPatchBadge();
  $$('#archiveGrid .row').forEach((el) => el.classList.toggle('active', el.dataset.id === id));
  localStorage.setItem('conan-last-entry', id);
  if (window.history?.replaceState) history.replaceState(null, '', `#${view}/${id}`);
}

function closeDetail() {
  $('#drawer').classList.remove('open');
  document.body.classList.remove('drawer-open');
  $('#drawer').setAttribute('aria-hidden', 'true');
  $('#scrim').classList.remove('on');
  $$('#archiveGrid .row.active').forEach((el) => el.classList.remove('active'));
  if (window.history?.replaceState) history.replaceState(null, '', `#${view}`);
}

// ══════════════════════════════════════════════════════════
//  总览
// ══════════════════════════════════════════════════════════

function renderOverview() {
  const grid = $('#disciplineGrid');
  if (grid) {
    grid.innerHTML = disciplines.map((d) => {
      const n = entries.filter((e) => e.discipline === d.id).length;
      return `<button class="tile" data-discipline="${d.id}"><h3>${escapeHtml(d.title)}</h3><p>${escapeHtml(d.desc)}</p><div class="tile-foot"><span>${escapeHtml(d.en)}</span><span>${n} 篇导读</span></div></button>`;
    }).join('');
    $$('#disciplineGrid .tile').forEach((b) => b.addEventListener('click', () => {
      activeDiscipline = b.dataset.discipline;
      renderFeatured();
      $('#featuredGrid').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }));
  }

  const sc = $('#scenarioGrid');
  if (sc) {
    sc.innerHTML = scenarios.map((s) => `<button class="tile" data-scenario="${s.id}"><h3>${escapeHtml(s.title)}</h3><p>${escapeHtml(s.desc)}</p><div class="tile-foot"><span>${s.level === 'spoiler' ? '全剧透' : s.level === 'deep' ? '深入' : '入门'}</span><span>切换 →</span></div></button>`).join('');
    $$('#scenarioGrid .tile').forEach((b) => b.addEventListener('click', () => {
      const s = scenarios.find((x) => x.id === b.dataset.scenario);
      activeLevel = s.level === 'beginner' ? 1 : s.level === 'deep' ? 2 : 3;
      $('#spoilerSelect').value = String(activeLevel);
      setView(s.id === 'organization' ? 'organizations' : s.id === 'relationship' ? 'graph' : s.id === 'casecraft' ? 'cases' : s.id === 'movie' ? 'movies' : 'cases');
    }));
  }

  const tl = $('#timelineList');
  if (tl) tl.innerHTML = timeline.map((t) => `<li><span class="tl-year">${escapeHtml(t.year)}</span><div><h3>${escapeHtml(t.title)}</h3><p>${escapeHtml(t.desc)}</p></div></li>`).join('');

  const gl = $('#glossary');
  if (gl) {
    gl.innerHTML = glossary.map(([term, desc]) => `<button title="${escapeHtml(desc)}" data-term="${escapeHtml(term)}">${escapeHtml(term)}</button>`).join('');
    $$('#glossary button').forEach((b) => b.addEventListener('click', () => {
      $('#searchInput').value = b.dataset.term;
      setView('cases');
    }));
  }

  renderFeatured();
}

function renderFeatured() {
  const host = $('#featuredGrid');
  if (!host) return;
  const list = entries.filter((e) => activeDiscipline === 'all' || e.discipline === activeDiscipline);
  host.innerHTML = list.map((e) => `<div class="row" data-entry="${escapeHtml(e.id)}" role="button" tabindex="0">
    <span class="row-mark kind-person">${escapeHtml(e.mark || 'C')}</span>
    <span class="row-title"><b>${escapeHtml(e.title)}</b><span>${escapeHtml(e.subtitle || '')}</span></span>
    <span class="row-cell">${escapeHtml(disciplineTitle(e.discipline))}</span>
    <span class="row-cell opt">${escapeHtml((e.tags || []).slice(0, 2).join(' / '))}</span>
    <span class="row-lv">LV.${e.spoiler || 1}</span>
  </div>`).join('');
  $$('#featuredGrid .row').forEach((el) => {
    el.addEventListener('click', () => openEntry(el.dataset.entry));
    el.addEventListener('keydown', (ev) => { if (ev.key === 'Enter') openEntry(el.dataset.entry); });
  });
}

function disciplineTitle(id) {
  return disciplines.find((d) => d.id === id)?.title || '导读';
}

// 编辑精选不经过 catalog，单独开抽屉
function openEntry(id) {
  const e = entries.find((x) => x.id === id);
  if (!e) return;
  const level = e.spoiler || 1;
  if (level > activeLevel) { activeLevel = level; $('#spoilerSelect').value = String(activeLevel); }
  $('#drawerKicker').textContent = `${disciplineTitle(e.discipline)} · 导读 · ${levelNames[level]}`;
  const body = [
    `<h2>${escapeHtml(e.title)}</h2>`,
    e.subtitle ? `<p class="d-sub">${escapeHtml(e.subtitle)}</p>` : '',
    `<div class="d-tags">${(e.tags || []).map((t) => `<span>${escapeHtml(t)}</span>`).join('')}</div>`,
    e.intro ? `<div class="d-sec"><p>${escapeHtml(e.intro)}</p></div>` : '',
    ...(e.sections || []).map(([h, t]) => `<div class="d-sec"><h3>${escapeHtml(h)}</h3><p>${escapeHtml(t)}</p></div>`),
    e.source ? `<div class="d-foot">${escapeHtml(e.source)}</div>` : '',
  ];
  $('#drawerBody').innerHTML = body.join('');
  $('#drawerBody').scrollTop = 0;
  $('#drawer').classList.add('open');
  document.body.classList.add('drawer-open');
  $('#drawer').setAttribute('aria-hidden', 'false');
  $('#scrim').classList.add('on');
}

// ══════════════════════════════════════════════════════════
//  关系图：真实数据 + 力导向布局
// ══════════════════════════════════════════════════════════

const graph = {
  mode: 'relations',
  nodes: [],
  edges: [],
  canvas: null,
  ctx: null,
  dpr: 1,
  drag: null,
  raf: 0,
  alpha: 1,
  hover: null,
  panX: 0,
  panY: 0,
  zoom: 1,
};

// 三种模式都从数据现算，不写死：
//  relations 人物关系（characters[].relations，稀疏但语义最强）
//  orgs      组织成员（organizations[].members + relations）
//  cases     人物—案件（characters[].caseRefs，边最多，用 Top-N 控规模）
function buildGraph(mode) {
  const nodes = new Map();
  const edges = [];
  const addNode = (id, kind) => {
    if (!nodes.has(id)) nodes.set(id, { id, kind, label: nameOfRef(id), x: 0, y: 0, vx: 0, vy: 0, deg: 0 });
    return nodes.get(id);
  };
  const hasEdge = new Set();
  const addEdge = (a, b, kind) => {
    if (!a || !b || a === b) return;
    const key = a < b ? `${a}|${b}` : `${b}|${a}`;
    if (hasEdge.has(key)) return;
    hasEdge.add(key);
    edges.push({ source: a, target: b, kind });
    nodes.get(a).deg += 1;
    nodes.get(b).deg += 1;
  };

  const chars = catalog.entities.filter((r) => entityTypeOf(r) === 'character');
  const charById = new Map(chars.map((c) => [c.id, c]));

  // 从案件反推人物共同出场：这是全库最密的关系证据（792 案 / 5459 次出场）。
  // 同一案件里同时登场的人物 → 一条「共演」边，权重=共演案件数。
  const coAppear = new Map();
  for (const cs of catalog.entities) {
    if (entityTypeOf(cs) !== 'case') continue;
    const cast = (cs.characters || []).filter((id) => charById.has(id));
    if (cast.length < 2 || cast.length > 12) continue; // 全明星案不参与两两配对，否则一万条边
    for (let i = 0; i < cast.length; i += 1) {
      for (let j = i + 1; j < cast.length; j += 1) {
        const key = cast[i] < cast[j] ? `${cast[i]}|${cast[j]}` : `${cast[j]}|${cast[i]}`;
        coAppear.set(key, (coAppear.get(key) || 0) + 1);
      }
    }
  }

  if (mode === 'relations') {
    // 人物关系 = 结构化 bonds（带类型，103 对）+ 显式 relations（裸 id，旧数据）
    //            + 共演强度 Top-N（覆盖全库，解决「图上只有 18 个人」）
    const explicit = new Set();
    const bondPair = new Set();
    for (const c of chars) {
      for (const b of c.bonds || []) {
        if (!b || !b.to || !entityRecord(b.to)) continue;
        const rec = entityRecord(b.to);
        addNode(c.id, 'character');
        addNode(b.to, entityTypeOf(rec) || 'character');
        const key = c.id < b.to ? `${c.id}|${b.to}` : `${b.to}|${c.id}`;
        if (bondPair.has(key)) continue; // 双向登记只画一条
        bondPair.add(key);
        addEdge(c.id, b.to, 'bond');
        const e = edges[edges.length - 1];
        e.bondType = b.type;
        e.note = b.note;
        explicit.add(key);
      }
    }
    for (const c of chars) {
      for (const r of c.relations || []) {
        if (!charById.has(r) && !entityRecord(r)) continue;
        addNode(c.id, 'character');
        addNode(r, entityTypeOf(entityRecord(r)) || 'character');
        addEdge(c.id, r, 'relation');
        explicit.add(c.id < r ? `${c.id}|${r}` : `${r}|${c.id}`);
      }
    }
    // 共演边：只用来补「语义关系没覆盖到」的空白，不能喧宾夺主。
    // 之前是「补到 900 条」，结果 800 条同案边把 120 个节点强拉成一个小团，
    // fitGraph 按包围盒缩到 44%，画布四周全空——局部糊成一坨、整体很稀。
    // 改成：按共演强度降序，给每个节点限一个共演度数上限，超了就不再连。
    // 共演边只做「补白」，默认上限压到 2，让 102 条语义关系成为骨架。
    // 之前是 5，结果 197 条边把枢纽人物（柯南/小兰/毛利）连成一坨，
    // 42% 缩放下中心彻底糊死。真要按共演看关系，点节点悬停展开。
    const COSTAR_DEGREE_CAP = 2;
    const costarDeg = new Map();
    const pairs = [...coAppear.entries()]
      .filter(([k, n]) => n >= 4 && !explicit.has(k))
      .sort((a, b) => b[1] - a[1]);
    for (const [k, n] of pairs) {
      const [a, b] = k.split('|');
      if ((costarDeg.get(a) || 0) >= COSTAR_DEGREE_CAP) continue;
      if ((costarDeg.get(b) || 0) >= COSTAR_DEGREE_CAP) continue;
      addNode(a, 'character');
      addNode(b, 'character');
      addEdge(a, b, 'costar');
      const e = edges[edges.length - 1];
      e.weight = n;
      costarDeg.set(a, (costarDeg.get(a) || 0) + 1);
      costarDeg.set(b, (costarDeg.get(b) || 0) + 1);
    }
  } else if (mode === 'orgs') {
    // 组织成员：members（现任）+ formerMembers（离任/叛离/身亡）都要画，
    // 否则黑衣组织只剩 10 人、宫野家只剩 1 人，用户看到的仍是「缺很多东西」
    for (const o of catalog.entities) {
      if (entityTypeOf(o) !== 'organization') continue;
      addNode(o.id, 'organization');
      for (const m of o.members || []) {
        const rec = entityRecord(m);
        if (!rec) continue;
        addNode(m, entityTypeOf(rec));
        addEdge(o.id, m, 'member');
      }
      for (const m of o.formerMembers || []) {
        const rec = entityRecord(m);
        if (!rec) continue;
        addNode(m, entityTypeOf(rec));
        addEdge(o.id, m, 'former');
        const e = edges[edges.length - 1];
        e.note = '离任 / 叛离 / 身亡';
      }
    }
    // 组织在案件中被引用：<组织> — <案件> 边
    for (const cs of catalog.entities) {
      if (entityTypeOf(cs) !== 'case') continue;
      for (const oid of cs.organizations || []) {
        if (!nodes.has(oid)) continue;
        addNode(cs.id, 'case');
        addEdge(oid, cs.id, 'case');
      }
    }
    // 同组织成员之间补「同僚」边（只连现任；离任者与在职者已不同僚）
    // 用 peer 类：淡实线，和「组织—成员」的虚点线区分开，否则满屏虚线看不出层级
    for (const o of catalog.entities) {
      if (entityTypeOf(o) !== 'organization') continue;
      const ms = (o.members || []).filter((m) => entityRecord(m));
      for (let i = 0; i < ms.length; i += 1) {
        for (let j = i + 1; j < ms.length; j += 1) addEdge(ms[i], ms[j], 'peer');
      }
    }
  } else {
    // 人物—案件：密度控制很关键。409 节点 / 1165 边实测糊成一片（pixel 覆盖 45%）。
    // 40 人 × 12 案仍有 196 节点挤在 1190×743 画布上，中心区标签必粘连，
    // 收到 30 人 × 最多 8 案（≈130 节点），题目级关系仍然完整，但留出标签空间。
    const ranked = chars
      .map((r) => ({ r, n: (r.caseRefs || []).length }))
      .filter((x) => x.n >= 3)
      .sort((a, b) => b.n - a.n)
      .slice(0, 30);
    for (const { r, n } of ranked) {
      addNode(r.id, 'character');
      // 出场越多挂的案件越多，但封顶 8，避免柯南一个人拖 792 条边
      const cap = Math.min(8, Math.max(4, Math.round(Math.log2(n) * 1.6)));
      for (const cid of (r.caseRefs || []).slice(0, cap)) {
        if (!entityRecord(cid)) continue;
        addNode(cid, 'case');
        addEdge(r.id, cid, 'case');
      }
    }
  }

  graph.nodes = [...nodes.values()];
  graph.edges = edges.filter((e) => nodes.has(e.source) && nodes.has(e.target));
  return { nodes: graph.nodes, edges: graph.edges };
}

function nodeColor(kind) {
  const map = { character: '--person', organization: '--org', case: '--case', location: '--place', gadget: '--gadget' };
  return getComputedStyle(document.body).getPropertyValue(map[kind] || '--muted').trim() || '#7fe0c8';
}

// 确定性伪随机：布局每次刷新必须长一个样。
// 用 Math.random() 时实测同一份数据三次刷新包围盒宽 1133 / 1498 / 1830，
// zoom 跟着在 0.43–0.69 之间跳，用户每次看到的疏密都不一样，没法调参也没法复现问题。
let seededRndState = 1;
function seededRandom() {
  seededRndState = (seededRndState * 1103515245 + 12345) % 2147483648;
  return seededRndState / 2147483648;
}

function seedPositions() {
  const n = graph.nodes.length;
  if (!n) return;
  // 初始位置铺满画布：以前用固定 280 半径，18 个节点全挤在中间一小块，
  // 大画布上看着像「没画」。现在按画布宽高取椭圆半径，并按度数分层。
  const stage = $('#graphStage');
  const rect = stage ? stage.getBoundingClientRect() : { width: 1200, height: 600 };
  const rw = Math.max(160, rect.width * 0.36);
  const rh = Math.max(120, rect.height * 0.36);
  seededRndState = 987654321; // 每次重置种子，保证可复现
  // 度数高的往外圈放，度数低的塞里圈，避免全堆一处
  const sorted = [...graph.nodes].sort((a, b) => b.deg - a.deg);
  sorted.forEach((node, i) => {
    const a = (i / n) * Math.PI * 2 + (i % 3) * 0.12;
    const ring = 0.55 + (i / n) * 0.45;
    node.x = Math.cos(a) * rw * ring * (0.85 + seededRandom() * 0.3);
    node.y = Math.sin(a) * rh * ring * (0.85 + seededRandom() * 0.3);
    node.vx = 0;
    node.vy = 0;
  });
  graph.alpha = 1;
}

// 力导向：斥力 + 弹簧 + 向心，跑在动画帧里；参数按节点数自适应
function tick() {
  const nodes = graph.nodes;
  const n = nodes.length;
  if (!n) return;
  const alpha = graph.alpha;
  // 目标：让布局的「自然尺寸」≈ 画布尺寸，这样 fitGraph 的 zoom 落在 0.8~1.2，
  // 标签才有地方放。之前 springLen 用固定公式（n=87 时 150），布局自然铺到 2000+ 宽，
  // 换算成 zoom 0.39，11px 标签缩到 4px，必然糊成一片。
  // 按画布真实比例播种：画布是扁的（1252×639 ≈ 2:1），而原来的圆环播种是圆形的，
  // 力导向最后收敛成一个近方形的团，fitGraph 只能被高度限制住，宽度白白空着一半。
  // 用画布宽高比拉伸初始圆环，布局自然会铺成和画布同形状的椭圆，zoom 才能上去。
  const stageEl = document.querySelector('#graphStage');
  const stageW = stageEl ? stageEl.clientWidth : 1200;
  const stageH = stageEl ? stageEl.clientHeight : 600;
  const aspect = Math.max(0.5, Math.min(3, stageW / Math.max(1, stageH)));
  // 每个节点在画布上应占的方块边长
  const cell = Math.max(34, Math.min(84, Math.sqrt((stageW * stageH) / Math.max(1, n)) * 0.82));
  const springLen = cell * 1.6;
  // 斥力：决定布局铺开的面积。M17 后骨架从 102 对涨到 114 对、多了跨簇长边，
  // 斥力太小时弹簧把整图压成细高一条（实测包围盒 1172×1268，zoom 被高度限死）。
  const repel = cell * cell * 0.62;

  for (let i = 0; i < n; i += 1) {
    const a = nodes[i];
    for (let j = i + 1; j < n; j += 1) {
      const b = nodes[j];
      let dx = b.x - a.x;
      let dy = b.y - a.y;
      let d2 = dx * dx + dy * dy;
      if (d2 < 1) { dx = Math.random() - 0.5; dy = Math.random() - 0.5; d2 = 1; }
      const d = Math.sqrt(d2);
      // 枢纽之间轻微加斥力：度高的节点连着几十条边，纯统一斥力会把它们叠在一起。
      // 系数必须保守——之前放到 1+2.2 直接让布局发散，包围盒从 1081 宽爆到 5334。
      const hubA = 1 + Math.min(0.5, (a.deg || 0) * 0.03);
      const hubB = 1 + Math.min(0.5, (b.deg || 0) * 0.03);
      const f = (repel / d2) * alpha * ((hubA + hubB) * 0.5);
      // 按画布形状定向施力：画布 1252×639 是 2:1 的扁条，而力导向自然收敛成近方形的团
      // （实测包围盒 1039 高 / 1277 宽），fitGraph 只能按高度缩到 0.55，宽度白白空着。
      // 横向斥力加权重、纵向减权重 → 布局铺成扁椭圆，与画布同形，zoom 才上得去。
      const aniso = Math.min(1.9, Math.max(0.6, Math.sqrt(aspect * 0.62)));
      const fx = (dx / d) * f * aniso;
      const fy = (dy / d) * f / aniso;
      a.vx -= fx; a.vy -= fy;
      b.vx += fx; b.vy += fy;
    }
  }

  const byId = new Map(nodes.map((x) => [x.id, x]));
  for (const e of graph.edges) {
    const a = byId.get(e.source);
    const b = byId.get(e.target);
    if (!a || !b) continue;
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const d = Math.hypot(dx, dy) || 1;
    // 权重高的边弹簧更硬，关系紧密的节点自然靠在一起
    const stiff = 0.012 + Math.min(0.02, (e.weight || 1) * 0.002);
    const f = ((d - springLen) / d) * stiff * alpha;
    const fx = dx * f;
    const fy = dy * f;
    a.vx += fx; a.vy += fy;
    b.vx -= fx; b.vy -= fy;
  }

  for (const node of nodes) {
    // 向心只做兜底。M17 补了 12 对跨簇关系（洋子/榎本/横沟兄弟/山村），
    // 骨架从 102 对涨到 114 对，图被这些跨簇长边拽散，zoom 从 0.84 掉到 0.35。
    // 系数从 0.00035 抬到 0.0011，把散开的簇拉回来。
    node.vx -= node.x * 0.0011 * alpha;
    node.vy -= node.y * 0.0011 * alpha;
    node.vx *= 0.80;
    node.vy *= 0.80;
    node.x += node.vx;
    node.y += node.vy;
  }

  // 硬性碰撞分离：力导向的斥力是「软」的，枢纽周围挤十几个节点时它压不住，
  // 中心区必然标签叠字。这里直接按最小间距把重叠的节点推开，是唯一能保证
  // 「屏幕上的节点之间真的有空隙」的手段（字号已改屏幕像素后，拉开节点不会让字变小）。
  const minSep = Math.max(26, 62 / Math.max(0.35, graph.zoom));
  for (let i = 0; i < nodes.length; i += 1) {
    for (let j = i + 1; j < nodes.length; j += 1) {
      const a = nodes[i];
      const b = nodes[j];
      let dx = b.x - a.x;
      let dy = b.y - a.y;
      let d = Math.hypot(dx, dy);
      if (d >= minSep) continue;
      if (d < 0.01) { dx = 0.01; dy = 0; d = 0.01; } // 完全重合时随便挑个方向
      const pushOut = (minSep - d) * 0.5;
      const ux = (dx / d) * pushOut;
      const uy = (dy / d) * pushOut;
      a.x -= ux; a.y -= uy;
      b.x += ux; b.y += uy;
    }
  }
  graph.alpha = Math.max(0.02, alpha * 0.985);
}

function drawGraph() {
  const { ctx, canvas } = graph;
  if (!ctx || !canvas) return;
  const w = canvas.width / graph.dpr;
  const h = canvas.height / graph.dpr;
  ctx.setTransform(graph.dpr, 0, 0, graph.dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);
  ctx.save();
  // 视口：先平移再缩放，zoom 以画布中心为基准
  ctx.translate(w / 2 + graph.panX, h / 2 + graph.panY);
  ctx.scale(graph.zoom, graph.zoom);

  const dark = !document.body.classList.contains('light');
  const lineBase = dark ? 'rgba(190,224,214,' : 'rgba(20,60,50,';
  // 缩小时线要更淡更细，否则糊成一片
  const lw = 1 / Math.sqrt(graph.zoom);

  // 关系类型配色：语义关系用彩色，共演用中性灰绿，避免抢视觉
  const BOND_COLOR = {
    family: dark ? 'rgba(232,150,110,' : 'rgba(176,74,30,',
    love: dark ? 'rgba(240,130,170,' : 'rgba(186,40,100,',
    colleague: dark ? 'rgba(120,190,230,' : 'rgba(30,110,160,',
    subordinate: dark ? 'rgba(150,160,235,' : 'rgba(70,76,170,',
    rival: dark ? 'rgba(235,200,110,' : 'rgba(150,110,10,',
    nemesis: dark ? 'rgba(240,110,110,' : 'rgba(176,40,40,',
    mentor: dark ? 'rgba(180,215,120,' : 'rgba(96,130,20,',
    friend: dark ? 'rgba(130,220,190,' : 'rgba(20,130,100,',
  };

  // 先画边：按权重分级，弱边更淡，避免 900 条一起糊成一片
  // 悬停聚焦：有 hover 时无关边压到几乎隐形，中心区不再糊成白斑
  for (const e of graph.edges) {
    const a = graph.nodes.find((x) => x.id === e.source);
    const b = graph.nodes.find((x) => x.id === e.target);
    if (!a || !b) continue;
    const hot = graph.hover && (graph.hover === a.id || graph.hover === b.id);
    const dimmed = graph.hover && !hot;
    const w = e.weight || 1;
    // 共演 2 次的边几乎透明，只有反复同案的关键关系才实
    const base = e.kind === 'case' ? 0.10
      : e.kind === 'member' ? 0.24
      : e.kind === 'former' ? 0.30
      : e.kind === 'peer' ? 0.07
      : e.kind === 'relation' ? 0.32
      : Math.min(0.30, 0.05 + w * 0.022);
    const alphaEdge = dimmed ? 0.018 : base;
    // bonds 用关系类型色；其余用中性线色
    const strokeBase = (e.kind === 'bond' && BOND_COLOR[e.bondType]) || lineBase;
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.strokeStyle = `${strokeBase}${hot ? '.75' : (e.kind === 'bond' ? Math.max(0.55, alphaEdge) : alphaEdge).toFixed(3)})`;
    ctx.lineWidth = (hot ? 2.2 : (e.kind === 'bond' ? 1.6 : 0.7 + Math.min(1.1, (w - 1) * 0.16))) * lw;
    if (e.kind === 'member') ctx.setLineDash([3 * lw, 3 * lw]);
    else if (e.kind === 'former') ctx.setLineDash([1.5 * lw, 3.5 * lw]);
    else ctx.setLineDash([]);
    ctx.stroke();
  }
  ctx.setLineDash([]);

  // 再画节点：大节点后画，压在小节点上面
  const ordered = [...graph.nodes].sort((x, y) => x.deg - y.deg);
  // 已经占据的标签位置，用来做简单避让
  const taken = [];
  const free = (bx, by, bw, bh) => !taken.some((t) =>
    bx < t.x + t.w && bx + bw > t.x && by < t.y + t.h && by + bh > t.y);

  for (const node of ordered) {
    const r = 4 + Math.min(10, Math.sqrt(node.deg) * 2.2);
    const color = nodeColor(node.kind);
    const isHover = graph.hover === node.id;
    ctx.beginPath();
    ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.globalAlpha = isHover ? 1 : 0.85;
    ctx.fill();
    ctx.globalAlpha = 1;
    if (isHover) {
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.6 * lw;
      ctx.beginPath();
      ctx.arc(node.x, node.y, r + 5 * lw, 0, Math.PI * 2);
      ctx.stroke();
    }
  }

  // 标签单独一轮：只标重要的，且互不重叠
  // 注意：这里所有量都是世界坐标，字号要除以 zoom 才是世界尺寸
  // 缩放越小、节点越多，越只标「枢纽人物」；放大后逐步放开，
  // 否则 87 个节点在 49% 缩放下全标 11px 必然糊成一片。
  const total = graph.nodes.length || 1;
  // 预算：屏幕面积够放多少个标签（按 60×14 估），再取比例
  // 之前 /2600 算出来 287 > 87，等于全标，避让必然失败；改成 /4800 且硬上限 34
  // 标签预算：只是「尝试上限」，不是「保证标注数」——放不下的位置会被 free() 拒绝，
  // 所以这里调高是安全的：多试几个，能放就放，不会因此产生重叠。
  // 之前上限 22 让 87 个节点只有 20 个带名字，外围一片匿名点。
  const budget = Math.min(48, Math.max(12, Math.round((w * h) / 16000)));
  const rank = [...graph.nodes].sort((a, b) => b.deg - a.deg);
  const labeled = rank.filter((n) => graph.hover === n.id || graph.zoom >= 2.2);
  // 语义关系两端 / 高连接度优先，再按度数补足到预算。
  // 以前这里要求 deg>=3，导致外围只连一两条边的角色永远没有名字（图上全是匿名点）。
  for (const n of rank) {
    if (labeled.length >= budget) break;
    if (labeled.includes(n)) continue;
    if (n.deg >= 1) labeled.push(n);
  }
  // 长名字截断：案件标题常常二三十字（「黑色冲击！黑衣组织伸出魔爪的瞬间」），
  // 一条就能横穿整个画布挡住几十个节点。超过 9 字截断，完整名字在悬停和抽屉里仍能看到。
  const clipLabel = (s) => (s && s.length > 9 ? `${s.slice(0, 8)}…` : s || '');
  // 两轮：第一轮只试「节点上方」，放不下就试下方/左右，仍放不下才跳过。
  // 之前只有一个候选位、撞车就跳过，中心区枢纽全被跳过 → 看着像「名字没了」。
  for (const node of labeled) {
    const dispLabel = clipLabel(node.label);
    const r = 4 + Math.min(10, Math.sqrt(node.deg) * 2.2);
    const isHover = graph.hover === node.id;
    const fsPx = isHover ? 15 : 13;
    const fs = fsPx / graph.zoom; // 世界单位下的字高，乘回 zoom 正好是 fsPx 屏幕像素
    // 必须用世界单位的 fs：ctx 已经 scale(zoom) 过，写 fsPx 会被再乘一次 zoom。
    // 之前这里写 fsPx，zoom 0.6 时 11px 的标签实际只渲染成 6.6px——这才是「标签糊」的真因，
    // 和避让算法无关：无论怎么挪位置，字本身就是小的。
    ctx.font = `${fs}px "Noto Sans SC", system-ui, sans-serif`;
    ctx.textAlign = 'center';
    const tw = ctx.measureText(dispLabel).width; // 已是世界单位，不再除 zoom
    const gap = 6 / graph.zoom;
    const h = fs * 1.25;
    // 候选位置：上、下、右、左，再沿「背离图中心」的方向外推一档。
    // 中心区枢纽挤在一起，只试四个紧贴位置全被占，标签就整片消失了。
    const outDx = node.x;
    const outDy = node.y;
    const outNorm = Math.hypot(outDx, outDy) || 1;
    const push = 16 / graph.zoom;
    const ex = (outDx / outNorm) * push;
    const ey = (outDy / outNorm) * push;
    const cands = [
      { x: node.x - tw / 2, y: node.y - r - gap - fs, ax: node.x, ay: node.y - r - gap },
      { x: node.x - tw / 2, y: node.y + r + gap, ax: node.x, ay: node.y + r + gap + fs * 0.82 },
      { x: node.x + r + gap, y: node.y - h / 2, ax: node.x + r + gap, ay: node.y, align: 'left' },
      { x: node.x - r - gap - tw, y: node.y - h / 2, ax: node.x - r - gap, ay: node.y, align: 'right' },
      { x: node.x + ex - tw / 2, y: node.y + ey - h, ax: node.x + ex, ay: node.y + ey },
      // 再远一档：中心区实在挤，宁可把标签甩到稍远的位置也别压字
      { x: node.x + ex * 2 - tw / 2, y: node.y + ey * 2 - h, ax: node.x + ex * 2, ay: node.y + ey * 2 },
      { x: node.x - tw / 2, y: node.y - r - gap - fs * 2.2, ax: node.x, ay: node.y - r - gap - fs * 1.2 },
    ];
    let spot = null;
    // 注意：b 的坐标是世界单位，留白也必须换成世界单位（3 屏幕像素 / zoom）。
    // 之前直接写 3，zoom 0.6 时只剩 1.8 屏幕像素，标签看着就是贴在一起的——和字号是同一个坑。
    const padWorld = 3 / graph.zoom;
    for (const c of cands) {
      const b = { x: c.x, y: c.y, w: tw, h };
      if (free(b.x - padWorld, b.y - padWorld, b.w + padWorld * 2, b.h + padWorld * 2)) {
        spot = { ...c, box: b };
        break;
      }
    }
    if (!spot) {
      if (!isHover) continue;
      spot = { ...cands[0], box: { x: cands[0].x, y: cands[0].y, w: tw, h } };
    }
    taken.push(spot.box);
    ctx.textAlign = spot.align || 'center';
    // canvas 已 scale(zoom)，所以描边宽度也要按世界单位写
    ctx.lineWidth = (3 / Math.sqrt(graph.zoom)) / graph.zoom;
    ctx.strokeStyle = dark ? 'rgba(11,17,22,.9)' : 'rgba(255,255,255,.92)';
    ctx.strokeText(dispLabel, spot.ax, spot.ay);
    ctx.fillStyle = dark ? (isHover ? '#e8f1ee' : 'rgba(232,241,238,.88)') : (isHover ? '#14211d' : 'rgba(20,33,29,.88)');
    ctx.fillText(dispLabel, spot.ax, spot.ay);
    ctx.textAlign = 'center';
  }
  ctx.restore();
}

function graphLoop() {
  cancelAnimationFrame(graph.raf);
  const step = () => {
    tick();
    drawGraph();
    if (graph.alpha > 0.03 || graph.drag) graph.raf = requestAnimationFrame(step);
    else { drawGraph(); graph.raf = 0; }
  };
  graph.raf = requestAnimationFrame(step);
}

function resizeGraph() {
  const stage = $('#graphStage');
  const canvas = $('#graphCanvas');
  if (!stage || !canvas) return;
  const rect = stage.getBoundingClientRect();
  graph.dpr = Math.min(2, window.devicePixelRatio || 1);
  canvas.width = Math.max(1, Math.floor(rect.width * graph.dpr));
  canvas.height = Math.max(1, Math.floor(rect.height * graph.dpr));
  canvas.style.width = `${rect.width}px`;
  canvas.style.height = `${rect.height}px`;
  drawGraph();
}

function renderGraph() {
  const stage = $('#graphStage');
  if (!stage) return;
  const canvas = $('#graphCanvas');
  graph.canvas = canvas;
  graph.ctx = canvas.getContext('2d');
  graph.panX = 0;
  graph.panY = 0;
  graph.hover = null;
  resizeGraph();
  const { nodes, edges } = buildGraph(graph.mode);
  seedPositions();
  graphLoop();

  const legend = $('#graphLegend');
  if (legend) {
    if (graph.mode === 'relations') legend.innerHTML = `<span><i style="background:#e8966e"></i>家人</span><span><i style="background:#f082aa"></i>恋人</span><span><i style="background:#78bee6"></i>同僚</span><span><i style="background:#96a0eb"></i>上下级</span><span><i style="background:#ebc86e"></i>对手</span><span><i style="background:#ff6e6e"></i>宿敌</span><span><i style="background:#b4d778"></i>师从</span><span><i style="background:#82dcbe"></i>朋友</span><span class="lg-note">灰色为同案共演</span>`;
    else if (graph.mode === 'orgs') legend.innerHTML = `<span><i style="background:var(--org)"></i>组织</span><span><i style="background:var(--person)"></i>现任成员</span><span><i style="background:var(--case)"></i>相关案件</span><span class="lg-note">虚点线为离任 / 叛离</span>`;
    else legend.innerHTML = `<span><i style="background:var(--person)"></i>人物</span><span><i style="background:var(--case)"></i>案件</span>`;
  }
  const hint = $('#graphHint');
  if (hint) hint.textContent = `${nodes.length} 个节点 · ${edges.length} 条连线`;

  attachGraphInteraction();
  updateZoomLabel();
  // 等布局真正稳定（alpha 收干）再适配，否则测到的包围盒是还在飞的位置
  waitSettleThenFit();
}

let fitTimer = 0;
function waitSettleThenFit() {
  clearTimeout(fitTimer);
  const startedAt = performance.now();
  const tick = () => {
    const elapsed = performance.now() - startedAt;
    // 布局仍在跑就等；alpha 收干或超过 3 秒就强行适配一次
    if (graph.canvas && graph.raf && graph.alpha > 0.032 && elapsed < 3000) {
      fitTimer = setTimeout(tick, 150);
      return;
    }
    fitGraph();
  };
  fitTimer = setTimeout(tick, 200);
}

// 自动适配：按节点包围盒缩放到画布内（留 8% 边距）
function fitGraph() {
  const canvas = graph.canvas;
  if (!canvas || !graph.nodes.length) return;
  const w = canvas.width / graph.dpr;
  const h = canvas.height / graph.dpr;
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const n of graph.nodes) {
    const r = 4 + Math.min(10, Math.sqrt(n.deg) * 2.2) + 14; // 含标签余量
    minX = Math.min(minX, n.x - r); maxX = Math.max(maxX, n.x + r);
    minY = Math.min(minY, n.y - r); maxY = Math.max(maxY, n.y + r);
  }
  const bw = Math.max(1, maxX - minX);
  const bh = Math.max(1, maxY - minY);
  const pad = 0.92;
  const z = Math.min(6, Math.max(0.25, Math.min((w * pad) / bw, (h * pad) / bh)));
  graph.zoom = z;
  // 让包围盒中心对齐画布中心
  graph.panX = -((minX + maxX) / 2) * z;
  graph.panY = -((minY + maxY) / 2) * z;
  updateZoomLabel();
  drawGraph();
}

function attachGraphInteraction() {
  const canvas = graph.canvas;
  if (!canvas || canvas.dataset.bound) return;
  canvas.dataset.bound = '1';

  // 屏幕坐标 → 世界坐标：要连同 zoom 一起反变换，否则放大会点不中节点
  const toWorld = (ev) => {
    const rect = canvas.getBoundingClientRect();
    const cx = ev.clientX - rect.left - rect.width / 2 - graph.panX;
    const cy = ev.clientY - rect.top - rect.height / 2 - graph.panY;
    return { x: cx / graph.zoom, y: cy / graph.zoom };
  };
  const nodeAt = (p) => {
    let best = null;
    let bestD = Infinity;
    for (const node of graph.nodes) {
      const d = Math.hypot(node.x - p.x, node.y - p.y);
      const r = 8 + Math.min(10, Math.sqrt(node.deg) * 2.2);
      const hit = Math.max(r, 10 / graph.zoom);
      if (d < hit + 4 && d < bestD) { best = node; bestD = d; }
    }
    return best;
  };

  // 以光标为锚点缩放：缩放前后光标下的世界坐标保持不变
  const zoomAt = (factor, clientX, clientY) => {
    const rect = canvas.getBoundingClientRect();
    const next = Math.min(6, Math.max(0.25, graph.zoom * factor));
    const k = next / graph.zoom;
    const ox = clientX - rect.left - rect.width / 2 - graph.panX;
    const oy = clientY - rect.top - rect.height / 2 - graph.panY;
    graph.panX += ox - ox * k;
    graph.panY += oy - oy * k;
    graph.zoom = next;
    updateZoomLabel();
    drawGraph();
  };

  canvas.addEventListener('wheel', (ev) => {
    ev.preventDefault();
    const factor = Math.pow(1.0015, -ev.deltaY);
    zoomAt(factor, ev.clientX, ev.clientY);
  }, { passive: false });

  canvas.addEventListener('pointerdown', (ev) => {
    const p = toWorld(ev);
    const node = nodeAt(p);
    canvas.setPointerCapture(ev.pointerId);
    if (node) {
      graph.drag = { node, moved: false };
      node.vx = 0; node.vy = 0;
      canvas.classList.add('dragging');
    } else {
      graph.drag = { pan: true, sx: ev.clientX, sy: ev.clientY, px: graph.panX, py: graph.panY };
      canvas.classList.add('panning');
    }
  });

  canvas.addEventListener('pointermove', (ev) => {
    const p = toWorld(ev);
    if (graph.drag?.node) {
      graph.drag.node.x = p.x;
      graph.drag.node.y = p.y;
      graph.drag.node.vx = 0;
      graph.drag.node.vy = 0;
      graph.drag.moved = true;
      graph.alpha = Math.max(graph.alpha, 0.35);
      drawGraph();
      return;
    }
    if (graph.drag?.pan) {
      graph.panX = graph.drag.px + (ev.clientX - graph.drag.sx);
      graph.panY = graph.drag.py + (ev.clientY - graph.drag.sy);
      drawGraph();
      return;
    }
    const node = nodeAt(p);
    const id = node?.id || null;
    if (id !== graph.hover) {
      graph.hover = id;
      canvas.style.cursor = id ? 'pointer' : 'grab';
      drawGraph();
    }
  });

  canvas.addEventListener('pointerup', (ev) => {
    const drag = graph.drag;
    graph.drag = null;
    canvas.classList.remove('dragging', 'panning');
    if (drag?.node && !drag.moved) openDetail(drag.node.id);
    else if (drag?.node) { graph.alpha = Math.max(graph.alpha, 0.5); graphLoop(); }
  });

  canvas.addEventListener('pointerleave', () => {
    graph.hover = null;
    drawGraph();
  });

  // 双击空白处复位视图
  canvas.addEventListener('dblclick', (ev) => {
    if (nodeAt(toWorld(ev))) return;
    graph.zoom = 1;
    graph.panX = 0;
    graph.panY = 0;
    updateZoomLabel();
    drawGraph();
  });
}

function updateZoomLabel() {
  const el = $('#graphZoom');
  if (el) el.textContent = `${Math.round(graph.zoom * 100)}%`;
}

// ══════════════════════════════════════════════════════════
//  视图切换 / 启动
// ══════════════════════════════════════════════════════════

function syncNav() {
  $$('.nav-item').forEach((b) => b.classList.toggle('active', b.dataset.view === view));
}

function setView(name) {
  view = name;
  currentPage = 1;
  // 切分区必须清空搜索词：否则上一个分区的查询会继续过滤新分区，
  // 结果就是「除了总览全空」。
  if (name !== 'overview') {
    $('#searchInput').value = '';
    // 入门档在案件分区只放行 5 条（数据里 763 案是 2 档），
    // 进入分区时若仍是入门档，自动抬到「深入」，避免一进来就看到空列表。
    if (activeLevel === 1) {
      activeLevel = 2;
      $('#spoilerSelect').value = '2';
    }
  }
  $$('.view').forEach((v) => v.classList.add('hidden'));
  if (name === 'overview') {
    // 必须在这里清空：#archiveGrid 属于 #view-list 容器，切到总览时它只是被
    // 隐藏而不是销毁，DOM 里还留着上一个视图的整页行。以前把清空写在
    // renderList() 的 overview 分支里——但总览根本不调 renderList()，那段是死代码，
    // 结果一旦 .hidden 没生效（旧 CSS 缓存、样式冲突）就会看到「总览复用上一页列表」。
    $('#archiveGrid').innerHTML = '';
    $('#view-overview').classList.remove('hidden');
    renderOverview();
  } else if (name === 'graph') {
    $('#archiveGrid').innerHTML = '';
    $('#view-graph').classList.remove('hidden');
    renderGraph();
  } else {
    $('#view-list').classList.remove('hidden');
    renderList();
  }
  syncNav();
  // 状态条只对列表视图有意义：关系图/总览不该挂着「档案 · 命中 N 条」
  const bar = $('.statusbar');
  if (bar) bar.classList.toggle('hidden', name === 'graph' || name === 'overview');
  window.scrollTo({ top: 0 });
}

function updateCounts() {
  const counts = {
    cases: 0, characters: 0, organizations: 0, locations: 0, gadgets: 0,
    episodes: catalog.episodes.length, movies: catalog.movies.length, ovas: catalog.ovas.length,
  };
  for (const r of catalog.entities) {
    const t = entityTypeOf(r);
    const key = t === 'case' ? 'cases' : t === 'character' ? 'characters' : t === 'organization' ? 'organizations' : t === 'location' ? 'locations' : t === 'gadget' ? 'gadgets' : null;
    if (key) counts[key] += 1;
  }
  for (const [key, n] of Object.entries(counts)) {
    const el = document.querySelector(`[data-count="${key}"]`);
    if (el) el.textContent = n.toLocaleString('zh-CN');
  }
}

function loadCatalogData() {
  return Promise.all([
    fetch('data/episodes/episodes.json').then((r) => r.json()),
    fetch('data/movies/movies.json').then((r) => r.json()),
    fetch('data/movies/special-movies.json').then((r) => r.json()),
    fetch('data/ovas/ovas.json').then((r) => r.json()),
    fetch('data/entities/characters.json').then((r) => r.json()),
    fetch('data/entities/organizations.json').then((r) => r.json()),
    fetch('data/entities/cases.json').then((r) => r.json()),
    fetch('data/entities/gadgets.json').then((r) => r.json()),
    fetch('data/entities/locations.json').then((r) => r.json()),
    fetch('data/manga/mainline-arcs.json').then((r) => r.json()),
    // 来源清单：把 src-xxx 内部 id 解析成可读站名
    fetch('data/sources.json').then((r) => r.json()),
  ]).then(([episodes, movies, specialMovies, ovas, characters, organizations, cases, gadgets, locations, arcs, sources]) => {
    catalog.episodes = episodes;
    catalog.movies = movies.concat(specialMovies);
    catalog.ovas = ovas;
    catalog.entities = characters.concat(organizations, cases, gadgets, locations, arcs);
    // sources.json 是 {items:[...]}，建 id → {title, url} 索引
    catalog.sources = new Map();
    for (const item of (sources.items || sources.sources || sources || [])) {
      if (item && item.id) catalog.sources.set(item.id, item);
    }
    // 让 entityRecord 下次调用时重建索引（它按 size 变化自动失效）
    catalog._index = null;
    updateCounts();
  }).catch((error) => {
    console.error('catalog load failed', error);
    const label = $('#resultLabel');
    if (label) label.textContent = '数据加载失败：请用本地 HTTP 服务打开（python3 -m http.server）';
  });
}

// ── 事件绑定 ────────────────────────────────────────────────
$$('.nav-item').forEach((b) => b.addEventListener('click', () => setView(b.dataset.view)));
$('.brand')?.addEventListener('click', () => setView('overview'));

$('#searchInput').addEventListener('input', () => {
  currentPage = 1;
  if (view === 'overview' || view === 'graph') setView('cases');
  else renderList();
});

$('#spoilerSelect').addEventListener('change', (e) => {
  activeLevel = Number(e.target.value);
  currentPage = 1;
  renderList();
});

$('#pageSizeSelect').addEventListener('change', (e) => {
  pageSize = Number(e.target.value);
  currentPage = 1;
  renderList();
});

$$('#sortBar .sort-btn').forEach((b) => b.addEventListener('click', () => {
  $$('#sortBar .sort-btn').forEach((x) => x.classList.remove('active'));
  b.classList.add('active');
  sortMode = b.dataset.sort;
  renderList();
}));

$('#randomBtn').addEventListener('click', () => {
  const pool = rowsForView(view === 'overview' || view === 'graph' ? 'cases' : view);
  if (!pool.length) return;
  openDetail(pool[Math.floor(Math.random() * pool.length)].id);
});

$$('#graphMode .seg-btn').forEach((b) => b.addEventListener('click', () => {
  $$('#graphMode .seg-btn').forEach((x) => x.classList.remove('active'));
  b.classList.add('active');
  graph.mode = b.dataset.mode;
  renderGraph();
}));

$('#graphReset')?.addEventListener('click', () => {
  graph.zoom = 1;
  graph.panX = 0;
  graph.panY = 0;
  updateZoomLabel();
  renderGraph();
});

// 缩放按钮：以画布中心为锚点
$('#graphZoomIn')?.addEventListener('click', () => nudgeZoom(1.25));
$('#graphZoomOut')?.addEventListener('click', () => nudgeZoom(1 / 1.25));
function nudgeZoom(factor) {
  const canvas = graph.canvas;
  if (!canvas) return;
  const rect = canvas.getBoundingClientRect();
  const next = Math.min(6, Math.max(0.25, graph.zoom * factor));
  graph.zoom = next;
  updateZoomLabel();
  drawGraph();
}
$('#drawerClose').addEventListener('click', closeDetail);
$('#scrim').addEventListener('click', closeDetail);

$('#themeBtn').addEventListener('click', () => {
  document.body.classList.toggle('light');
  localStorage.setItem('conan-theme', document.body.classList.contains('light') ? 'light' : 'dark');
  if (view === 'graph') drawGraph();
});

window.addEventListener('keydown', (event) => {
  const typing = ['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement?.tagName);
  if (event.key === '/' && !typing) { event.preventDefault(); $('#searchInput').focus(); }
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); $('#randomBtn').click(); }
  if (event.key === 'Escape') {
    if ($('#drawer').classList.contains('open')) closeDetail();
    else if (typing) document.activeElement.blur();
  }
});

let resizeTimer = 0;
window.addEventListener('resize', () => {
  if (view !== 'graph') return;
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(resizeGraph, 160);
});

// ── 启动 ────────────────────────────────────────────────────
if (localStorage.getItem('conan-theme') === 'light') document.body.classList.add('light');

const startView = (location.hash || '').replace('#', '').split('/')[0];
const START = ['cases', 'characters', 'organizations', 'locations', 'gadgets',
  'episodes', 'movies', 'ovas', 'graph', 'overview'].includes(startView) ? startView : 'cases';

// 先加载数据再切视图：否则 setView 会用空 catalog 渲染一遍，
// 关系图画布拿到 0 个节点，总览渲染出空壳——刷新时闪一下空白。
$('#resultLabel').textContent = '正在加载档案…';
loadCatalogData().then(() => {
  // 修订面板独立于数据加载，先挂上事件；badge 显示本机已有修订条数
  if (typeof bindPatchPanel === 'function') bindPatchPanel();
  setView(START);
  if (START === 'graph') renderGraph();
}).catch((err) => {
  $('#resultLabel').textContent = '数据加载失败：' + (err && err.message ? err.message : err)
    + '（请用本地 HTTP 服务打开，直接双击 file:// 会被浏览器拦截）';
});
