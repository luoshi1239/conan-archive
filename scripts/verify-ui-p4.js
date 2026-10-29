// 从 app.js 原样抽出函数，用真实数据验证列表行与详情抽屉的渲染行为
// 重写版（2026-10-29）：卡片 entityToCard 已由列表行 toRow 取代，
// 本脚本同步改为验证 toRow / entityTypeOf / detailSections 的实际产出。
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

const consts = [
  src.match(/const LANG_ORDER = [^;]+;/)[0],
  src.match(/const LABELS_ZH = \{[\s\S]*?\n\};/)[0],
  src.match(/const AGE_PAREN_ZH = \{[\s\S]*?\n\};/)[0],
  src.match(/const KIND_MARK = [^;]+;/)[0],
  src.match(/const KIND_LABEL = [^;]+;/)[0],
].join('\n');

const names = ['textOf', 'langOf', 'labelOf', 'titleOf', 'entityRecord', 'nameOfRef',
  'refsText', 'formatAge', 'formatVictim', 'labelZh', 'formatAnimeRef', 'formatMangaRef',
  'formatEpisodeNumber', 'entityTypeOf', 'catalogTypeOf', 'entitySummaryLine', 'toRow', 'detailSections'];
const code = [consts, ...names.map(extract)].join('\n\n');

const catalog = { entities: [], episodes: [], movies: [], ovas: [] };
const activeLevel = 3;
const $ = () => ({ textContent: '' });
eval(code);

const chars = JSON.parse(fs.readFileSync('data/entities/characters.json', 'utf8'));
const cases = JSON.parse(fs.readFileSync('data/entities/cases.json', 'utf8'));
catalog.entities = [].concat(chars, cases);
catalog._index = null;

let bad = 0;

// 1) 列表行：类型判定必须准确，标题/副标题不得脏
const kindCount = {};
for (const c of chars) {
  const row = toRow(c);
  kindCount[row.type] = (kindCount[row.type] || 0) + 1;
  if (row.type !== 'character') { bad++; console.log('  ✗ 误判类型', c.id, '→', row.type); }
  if (!row.title) { bad++; console.log('  ✗ 空标题', c.id); }
  if (/undefined|\[object/.test(row.title + row.sub)) { bad++; console.log('  ✗ 脏文本', c.id, row.title, row.sub); }
}
console.log('角色行类型分布:', kindCount, '| 异常', bad);

const caseKinds = {};
for (const c of cases) {
  const row = toRow(c);
  caseKinds[row.type] = (caseKinds[row.type] || 0) + 1;
}
console.log('案件行类型分布:', caseKinds);
if (caseKinds.case !== cases.length) { bad++; console.log('  ✗ 案件行类型判定不全'); }

// 2) 样本行
const takagi = chars.find((c) => c.id === 'character-wataru-takagi');
const tRow = toRow(takagi);
console.log('样本行:', JSON.stringify({ title: tRow.title, sub: tRow.sub, mark: tRow.mark, col1: tRow.col1 }));

// 3) 详情：引用必须解析成展示名，不能打印内部 id
const caseRec = cases.find((c) => c.characters && c.characters.length > 6);
const sections = detailSections({ raw: caseRec }, 'entity');
const people = sections.find(([k]) => k === '关联人物');
console.log('案件详情「关联人物」:', people ? people[1].slice(0, 90) : '(缺失)');
if (!people) { bad++; console.log('  ✗ 关联人物段缺失'); }
if (people && /character-[a-z]/.test(people[1])) { bad++; console.log('  ✗ 仍打印原始 id'); }

const charSections = detailSections({ raw: takagi }, 'entity');
const refs = charSections.find(([k]) => k === '出场案件');
console.log('角色详情「出场案件」:', refs ? refs[1].slice(0, 90) : '(缺失)');
if (!refs) { bad++; console.log('  ✗ 出场案件段缺失'); }
if (refs && /case-[a-z]/.test(refs[1])) { bad++; console.log('  ✗ 仍打印原始 id'); }

// 4) 案件详情的动画/漫画范围不得露出 episode- / file- 内部 id
const furin = cases.find((c) => c.id === 'case-furinkazan');
const fsec = detailSections({ raw: furin }, 'entity');
for (const [label] of fsec) {
  const sec = fsec.find(([k]) => k === label);
  if (/episode-\d|file-\d/.test(sec[1])) { bad++; console.log(`  ✗ 「${label}」露出内部 id:`, sec[1]); }
}
console.log('样本案件中文标题:', furin.title.zhHans);

console.log(bad === 0 ? 'UI_P4_OK' : `UI_P4_FAIL(${bad})`);
