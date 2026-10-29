// P3 验证：spoilerNote 是否被 detailSections 渲染出来
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
  grab(/const LANG_ORDER = [^;]+;/),
  grab(/const LABELS_ZH = \{[\s\S]*?\n\};/),
  grab(/const AGE_PAREN_ZH = \{[\s\S]*?\n\};/),
  grab(/const catalog = [^;]+;/),
  'const $ = () => ({ value: "" });',
].join('\n');

const fns = ['textOf', 'langOf', 'labelOf', 'titleOf', 'entityRecord', 'nameOfRef', 'formatAge', 'formatVictim', 'refsText', 'labelZh', 'formatEpisodeNumber', 'formatAnimeRef', 'formatMangaRef', 'detailSections']
  .map(extract).join('\n\n');

const at = (f) => JSON.parse(fs.readFileSync(`data/entities/${f}.json`, 'utf8'));
const entities = [].concat(at('characters'), at('organizations'), at('cases'), at('gadgets'), at('locations'));

const runner = new Function('ents', `
${prelude}
${fns}
catalog.entities = ents;
return detailSections;
`);

const detailSections = runner(entities);
const cases = at('cases');

let bad = 0;
const withNote = cases.filter((c) => c.spoilerNote);
console.log(`带 spoilerNote 案件: ${withNote.length}`);
for (const c of withNote) {
  const secs = detailSections(c, 'entity');
  const hit = secs.find((s) => s[0] === '收录备注');
  if (!hit) bad++;
  console.log(`${hit ? '✓' : '✗'} ${c.id.padEnd(34)} ${hit ? `${hit[1].length} 字` : '未渲染'}`);
}

const without = cases.find((c) => !c.spoilerNote);
const secs = detailSections(without, 'entity');
const leaked = secs.some((s) => s[0] === '收录备注');
if (leaked) bad++;
console.log(`无备注案件（${without.id}）不应出现该分区: ${leaked ? '✗ 出现了' : '✓ 正常'}`);

// 污染复查：spoiler 必须是数字
const badSpoiler = cases.filter((c) => typeof c.spoiler !== 'number');
if (badSpoiler.length) bad++;
console.log(`spoiler 类型非数字: ${badSpoiler.length}`);

console.log(bad === 0 ? 'P3_OK' : `P3_FAIL(${bad})`);
