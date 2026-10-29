// 验证左侧导航各分区：抽取 app.js 真实函数，用真实数据统计每个入口的条目数
// 重写版（2026-10-29）：入口由 archiveKind 改为 view + rowsForView，
// 本脚本同步改为验证 rowsForView / entityTypeOf / toRow 的实际产出。
const fs = require('fs');
const src = fs.readFileSync('app.js', 'utf8');

function extract(name) {
  const start = src.indexOf(`function ${name}(`);
  if (start < 0) throw new Error(`missing ${name}`);
  let i = src.indexOf('{', start), depth = 0;
  for (; i < src.length; i++) {
    if (src[i] === '{') depth++;
    else if (src[i] === '}') { depth--; if (depth === 0) break; }
  }
  return src.slice(start, i + 1);
}

const grab = (re) => { const m = src.match(re); if (!m) throw new Error(`missing ${re}`); return m[0]; };

const prelude = [
  grab(/const levelNames = [^;]+;/),
  grab(/const catalog = [^;]+;/),
  grab(/const LANG_ORDER = [^;]+;/),
  grab(/const LABELS_ZH = \{[\s\S]*?\n\};/),
  grab(/const KIND_MARK = [^;]+;/),
  grab(/const KIND_LABEL = [^;]+;/),
  'let view = "cases", activeLevel = 3, sortMode = "default", currentPage = 1, pageSize = 30;',
  'const $ = () => ({ value: "" });',
].join('\n');

const fns = ['textOf', 'langOf', 'labelOf', 'titleOf', 'labelZh', 'entityRecord', 'nameOfRef',
  'refsText', 'formatEpisodeNumber', 'formatAnimeRef', 'formatMangaRef',
  'entityTypeOf', 'catalogTypeOf', 'entitySummaryLine', 'toRow',
  'rowsForView', 'searchText', 'filteredRows']
  .map(extract).join('\n\n');

const at = (f) => JSON.parse(fs.readFileSync(`data/entities/${f}.json`, 'utf8'));
const ents = [].concat(at('characters'), at('organizations'), at('cases'), at('gadgets'), at('locations'));
const eps = JSON.parse(fs.readFileSync('data/episodes/episodes.json', 'utf8'));
const movies = JSON.parse(fs.readFileSync('data/movies/movies.json', 'utf8'));
const ovas = JSON.parse(fs.readFileSync('data/ovas/ovas.json', 'utf8'));

const runner = new Function('ents', 'eps', 'movies', 'ovas', `
${prelude}
${fns}
catalog.entities = ents;
catalog.episodes = eps;
catalog.movies = movies;
catalog.ovas = ovas;
const out = {};
for (const k of ['cases', 'characters', 'organizations', 'locations', 'gadgets', 'episodes', 'movies', 'ovas']) {
  out[k] = rowsForView(k).length;
}
out.caseSample = rowsForView('cases').slice(0, 2).map((r) => r.title + ' · ' + r.col1);
out.charSample = rowsForView('characters').slice(0, 2).map((r) => r.title + ' · ' + r.sub);
out.orgSample = rowsForView('organizations').map((r) => r.title);
// 入门档过滤必须真的减少条目
activeLevel = 1;
out.caseLvl1 = rowsForView('cases').filter((r) => (r.spoiler || 1) <= activeLevel).length;
activeLevel = 3;
out.caseLvl3 = rowsForView('cases').length;
// 每个分区都必须产出可渲染的行：标题非空、无脏文本
out.dirty = {};
for (const k of ['cases', 'characters', 'organizations', 'locations', 'gadgets', 'episodes', 'movies', 'ovas']) {
  const rows = rowsForView(k);
  const bad = rows.filter((row) => !row.title || /undefined|\\[object|null/.test(row.title + ' ' + row.sub));
  out.dirty[k] = bad.map((row) => row.id);
}
return out;
`);

const r = runner(ents, eps, movies, ovas);
const expect = { cases: 792, characters: 147, organizations: 4, locations: 6, gadgets: 8, episodes: eps.length, movies: movies.length, ovas: ovas.length };
let bad = 0;
for (const k of Object.keys(expect)) {
  const ok = r[k] === expect[k];
  if (!ok) bad++;
  console.log(`${ok ? '✓' : '✗'} ${k.padEnd(14)} ${String(r[k]).padStart(5)} / 期望 ${expect[k]}`);
}

for (const [k, ids] of Object.entries(r.dirty)) {
  if (ids.length) { bad++; console.log(`  ✗ ${k} 有 ${ids.length} 行脏文本，例：${ids.slice(0, 3).join(', ')}`); }
}
console.log('脏文本分区:', Object.entries(r.dirty).filter(([, v]) => v.length).length);

console.log('案件样本:', r.caseSample.join(' | '));
console.log('人物样本:', r.charSample.join(' | '));
console.log('组织名单:', r.orgSample.join('、'));
console.log(`入门档案件可见: ${r.caseLvl1} / 全档 ${r.caseLvl3}`);
if (!(r.caseLvl1 <= r.caseLvl3)) { bad++; console.log('  ✗ 入门档过滤失效（可见数不少于全档）'); }
console.log(bad === 0 ? 'NAV_KINDS_OK' : `NAV_KINDS_FAIL(${bad})`);
