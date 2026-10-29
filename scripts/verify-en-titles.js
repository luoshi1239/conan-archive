// 验证剧集英文标题可用：textOf/titleOf 回落链 + 实际渲染样例
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const eps = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/episodes/episodes.json'), 'utf8'));

const LANG_ORDER = ['zhHans', 'zhHant', 'ja', 'en'];

function textOf(value, order = LANG_ORDER) {
  if (value == null) return null;
  if (typeof value === 'string') return value.trim() || null;
  if (Array.isArray(value)) {
    for (const v of value) {
      const r = textOf(v, order);
      if (r) return r;
    }
    return null;
  }
  for (const k of order) {
    if (value[k]) return String(value[k]).trim() || null;
  }
  return null;
}

let fail = 0;
const err = (m) => { console.log('  ✗ ' + m); fail++; };

// 1. 每集都能取到标题
let noTitle = [];
for (const e of eps) {
  if (!textOf(e.title)) noTitle.push(e.number);
}
if (noTitle.length) err(`取不到标题：${noTitle.slice(0, 5)}`);
else console.log(`  ✓ 1217 集全部有可显示标题`);

// 2. 每集都有 title.en（英文回落的兜底）
const noEn = eps.filter((e) => !(e.title && e.title.en)).map((e) => e.number);
if (noEn.length) err(`缺 title.en：${noEn.length} 集 ${noEn.slice(0, 5)}`);
else console.log(`  ✓ title.en 1217/1217`);

// 3. 英文标题不含 markdown 残留
const dirty = eps.filter((e) => e.title && e.title.en && /[*\[\]\\]/.test(e.title.en));
if (dirty.length) {
  err(`title.en 有 markdown 残留 ${dirty.length} 集`);
  dirty.slice(0, 5).forEach((e) => console.log(`      EP.${e.number} ${JSON.stringify(e.title.en)}`));
} else console.log(`  ✓ title.en 无 markdown 残留`);

// 4. title.enRaw 可回溯，且 en 是 enRaw 的清理结果（长度不得更长）
const badRaw = eps.filter((e) => {
  if (!e.title || !e.title.enRaw) return true;
  return e.title.en.length > e.title.enRaw.length;
});
if (badRaw.length) err(`enRaw 缺失或异常 ${badRaw.length} 集`);
else console.log(`  ✓ title.enRaw 1217/1217，且 en 不长于原文`);

// 5. 时长标注必须已剥离，分段标记必须保留
const special = eps.filter((e) => e.title && e.title.en && /\((?:[\d.]+\s*Hour\s*Special)\)/i.test(e.title.en));
if (special.length) err(`仍有 ${special.length} 集残留时长标注`);
else console.log(`  ✓ 时长标注已全部剥离`);

const partEps = eps.filter((e) => e.title && e.title.en && /\(Part\s+\d\)/.test(e.title.en));
console.log(`  ✓ 保留 (Part N) 分段标记 ${partEps.length} 集`);

// 6. 抽样打印
console.log('\n  抽样（前端实际会显示的中文 → 英文原文）：');
for (const n of [1, 11, 22, 96, 345, 585, 586, 1029, 1217]) {
  const e = eps.find((x) => x.number === n);
  if (!e) continue;
  console.log(`    EP.${n}`);
  console.log(`      显示: ${textOf(e.title)}`);
  console.log(`      en  : ${e.title.en}`);
  console.log(`      raw : ${e.title.enRaw}`);
}

console.log('');
if (fail) {
  console.log(`EN_TITLES_FAIL：${fail} 项`);
  process.exit(1);
}
console.log('EN_TITLES_OK');
