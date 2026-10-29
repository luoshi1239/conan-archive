// M8 验证：被害者/嫌疑人是否被 detailSections 渲染，年龄死因是否按块配对（不串人）
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

const consts = src.match(/const LANG_ORDER = [^;]+;/)[0];
const labelsZh = src.match(/const LABELS_ZH = \{[\s\S]*?\n\};/)[0];
const ageParen = src.match(/const AGE_PAREN_ZH = \{[\s\S]*?\n\};/)[0];
const names = ['textOf', 'langOf', 'labelOf', 'titleOf', 'entityRecord', 'nameOfRef',
  'formatAge', 'formatVictim', 'refsText', 'labelZh', 'formatEpisodeNumber', 'formatAnimeRef', 'formatMangaRef', 'detailSections'];
const code = [consts, labelsZh, ageParen, ...names.map(extract)].join('\n\n');

const catalog = { entities: [], episodes: [], movies: [], ovas: [] };
const $ = () => ({ value: '' });
const fn = new Function('catalog', '$', `${code}\nreturn { detailSections, formatVictim };`);
const { detailSections, formatVictim } = fn(catalog, $);

const cases = JSON.parse(fs.readFileSync('data/entities/cases.json', 'utf8'));
catalog.entities = cases;

let problems = [];
let checked = 0;

// 1) 逐案渲染，确认有 victims 的都能渲染出「被害者」段，且没有裸对象字符串
for (const c of cases) {
  const secs = detailSections(c, 'entity');
  const v = secs.find((s) => s[0] === '被害者');
  if (c.victims?.length) {
    if (!v) problems.push(`${c.id}: 有 victims 但未渲染`);
    else {
      checked++;
      if (v[1].includes('[object')) problems.push(`${c.id}: 渲染出 [object Object]`);
      if (!v[2]) problems.push(`${c.id}: 被害者段未标记 pre-line`);
      for (const victim of c.victims) {
        // M12 起渲染用 nameZh，原文 name 不再直接出现在页面上；
        // 两个都没有才算真缺（nameZh 必有 name 兜底，见 validate-data.py）。
        const shown = victim.nameZh || victim.name;
        if (!v[1].includes(shown)) problems.push(`${c.id}: 缺少被害者 ${shown}`);
      }
    }
  } else if (v) {
    problems.push(`${c.id}: 无 victims 却渲染了被害者段`);
  }
  const s = secs.find((x) => x[0] === '嫌疑人');
  if (c.suspects?.length && !s) problems.push(`${c.id}: 有 suspects 但未渲染`);
  if (!c.suspects?.length && s) problems.push(`${c.id}: 无 suspects 却渲染了嫌疑人段`);
}

// 2) 年龄/死因必须与被害人同块配对（用已知样本核对，防串人）
const byId = Object.fromEntries(cases.map((c) => [c.id, c]));
const furin = byId['case-furinkazan'];
if (furin) {
  const ayaka = furin.victims.find((v) => v.name === 'Ayaka Tatsuo');
  const shige = furin.victims.find((v) => v.name === 'Shigetsugu Torada');
  if (!ayaka || ayaka.age !== '27 years old') problems.push('Furinkazan: Ayaka 年龄配对错误');
  if (!shige || shige.age !== '31 years old') problems.push('Furinkazan: Shigetsugu 年龄配对错误');
  if (ayaka && ayaka.causeOfDeath !== 'Hanging') problems.push('Furinkazan: Ayaka 死因配对错误');
  // 前三个被害人原文没写年龄，绝不能凭空得到年龄
  for (const n of ['Yoshiro Torada', 'Koji Tatsuo', 'Kuroto Kai']) {
    const v = furin.victims.find((x) => x.name === n);
    if (v && v.age) problems.push(`Furinkazan: ${n} 不该有年龄却有了 ${v.age}`);
  }
}

// 3) 全库：所有年龄值必须出现在该案原文 situation 里
const pages = JSON.parse(fs.readFileSync('data/raw/dcw-page-sections.json', 'utf8')).pages;
for (const c of cases) {
  const sit = ((pages[c.dcwPage] || {}).situation || []).join(' ');
  for (const v of c.victims || []) {
    if (v.age && !sit.includes(v.age)) problems.push(`${c.id}: 年龄 ${v.age} 不在原文`);
    if (v.causeOfDeath && !sit.includes(v.causeOfDeath)) problems.push(`${c.id}: 死因 ${v.causeOfDeath} 不在原文`);
  }
}

console.log(`渲染核验案件 ${checked} 个`);
if (problems.length) {
  console.log('M8_FAILED');
  problems.slice(0, 20).forEach((p) => console.log(' -', p));
  process.exit(1);
}
console.log('M8_OK');
