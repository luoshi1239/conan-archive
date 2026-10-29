/* ════════════════════════════════════════════════════════════
 *  爱好者修订层
 *
 *  设计要点：
 *  - 原始 data/entities/*.json 是只读的「基线」，任何人本地改动都不写回去
 *  - 改动存在 localStorage（键 conan-patches），结构 { [entityId]: {field: value} }
 *  - 渲染时 patchedRecord() 把补丁叠到基线上，页面立刻生效
 *  - 导出得到 patch JSON，可提交给维护者合入基线；也可导入别人的补丁
 *  - 每条补丁记录 who / when / why，方便追溯（不校验身份，只做提示）
 * ════════════════════════════════════════════════════════════ */

const PATCH_KEY = 'conan-patches';
const PATCH_FIELDS = [
  ['summary', '简介（summary）', 'textarea'],
  ['role', '身份 / 定位（role）', 'input'],
  ['note', '补充说明（note）', 'textarea'],
];

const BOND_LABEL = {
  family: '家人', love: '恋人', colleague: '同僚', subordinate: '上下级',
  rival: '对手', nemesis: '宿敌', mentor: '师从', friend: '朋友',
};

function loadPatches() {
  try {
    const raw = localStorage.getItem(PATCH_KEY);
    if (!raw) return {};
    const obj = JSON.parse(raw);
    return obj && typeof obj === 'object' ? obj : {};
  } catch (err) {
    console.warn('补丁读取失败，已忽略', err);
    return {};
  }
}

function savePatches(patches) {
  try {
    localStorage.setItem(PATCH_KEY, JSON.stringify(patches));
    return true;
  } catch (err) {
    console.warn('补丁保存失败', err);
    return false;
  }
}

let patches = loadPatches();

/** 把补丁叠到基线记录上；返回新对象，不污染 catalog 里的原始记录 */
function patchedRecord(record) {
  if (!record || !record.id) return record;
  const patch = patches[record.id];
  if (!patch) return record;
  const merged = { ...record };
  for (const [key, val] of Object.entries(patch.fields || {})) {
    if (val !== undefined && val !== null && val !== '') merged[key] = val;
  }
  // 追加型：爱好者补的关系与基线合并，不覆盖
  if (patch.bonds?.length) {
    const base = Array.isArray(record.bonds) ? record.bonds : [];
    const seen = new Set(base.map((b) => `${b.to}|${b.type}`));
    const extra = patch.bonds.filter((b) => b.to && b.type && !seen.has(`${b.to}|${b.type}`));
    if (extra.length) merged.bonds = [...base, ...extra];
  }
  merged.__patched = true;
  return merged;
}

/** 记录一条补丁 */
function applyPatch(id, fields, bonds, why) {
  if (!id) return false;
  const cur = patches[id] || { fields: {}, bonds: [] };
  for (const [k, v] of Object.entries(fields || {})) {
    if (v === undefined) continue;
    if (v === '' || v === null) delete cur.fields[k];
    else cur.fields[k] = v;
  }
  if (bonds?.length) {
    const seen = new Set((cur.bonds || []).map((b) => `${b.to}|${b.type}`));
    for (const b of bonds) {
      if (b.to && b.type && !seen.has(`${b.to}|${b.type}`)) {
        cur.bonds.push(b);
        seen.add(`${b.to}|${b.type}`);
      }
    }
  }
  cur.meta = {
    updatedAt: new Date().toISOString(),
    why: why || '',
  };
  // 空补丁直接删掉，别留垃圾
  if (!Object.keys(cur.fields).length && !(cur.bonds || []).length) delete patches[id];
  else patches[id] = cur;
  return savePatches(patches);
}

function revertPatch(id) {
  delete patches[id];
  savePatches(patches);
}

function patchCount() {
  return Object.keys(patches).length;
}

/** 导出补丁文件（浏览器下载） */
function exportPatches() {
  const payload = {
    version: 1,
    exportedAt: new Date().toISOString(),
    note: 'Conan Archive 爱好者修订补丁。导入后覆盖同 id 同字段；合并前请人工过一遍。',
    patches,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `conan-patches-${new Date().toISOString().slice(0, 10)}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** 导入补丁：与现有补丁按 id + 字段合并，不整体覆盖 */
function importPatches(text) {
  let obj;
  try {
    obj = JSON.parse(text);
  } catch (err) {
    return { ok: false, msg: '不是合法 JSON' };
  }
  const incoming = obj?.patches || obj;
  if (!incoming || typeof incoming !== 'object') return { ok: false, msg: '文件里没有 patches' };
  let n = 0;
  for (const [id, p] of Object.entries(incoming)) {
    if (!p || typeof p !== 'object') continue;
    const cur = patches[id] || { fields: {}, bonds: [] };
    for (const [k, v] of Object.entries(p.fields || {})) {
      if (v !== undefined && v !== null && v !== '') cur.fields[k] = v;
    }
    if (p.bonds?.length) {
      const seen = new Set((cur.bonds || []).map((b) => `${b.to}|${b.type}`));
      for (const b of p.bonds) {
        if (b.to && b.type && !seen.has(`${b.to}|${b.type}`)) {
          cur.bonds.push(b);
          seen.add(`${b.to}|${b.type}`);
        }
      }
    }
    if (p.meta) cur.meta = p.meta;
    patches[id] = cur;
    n += 1;
  }
  savePatches(patches);
  return { ok: true, msg: `已合并 ${n} 条修订` };
}

// ── 抽屉里的修订表单 ──────────────────────────────────────

function patchEditorHtml(record) {
  const id = record.id;
  const cur = patches[id];
  const val = (k) => escapeHtml(cur?.fields?.[k] ?? (typeof record[k] === 'string' ? record[k] : ''));
  const rows = PATCH_FIELDS.map(([key, label, kind]) => {
    const v = val(key);
    const el = kind === 'textarea'
      ? `<textarea data-pf="${key}" rows="3">${v}</textarea>`
      : `<input data-pf="${key}" value="${v}">`;
    return `<label class="pf-row"><span>${label}</span>${el}</label>`;
  }).join('');

  const bondList = (cur?.bonds || []).map((b, i) => `
    <li>${escapeHtml(nameOfRef(b.to))} · ${escapeHtml(BOND_LABEL[b.type] || b.type)}
      ${b.note ? `<em>（${escapeHtml(b.note)}）</em>` : ''}
      <button class="link-mini" data-delbond="${i}">删除</button></li>`).join('');

  return `
  <div class="d-sec patch-box">
    <h3>爱好者修订</h3>
    <p class="patch-tip">改动只存在你自己的浏览器里，不会上传。改完可导出 JSON 交给维护者合入。</p>
    ${rows}
    <label class="pf-row"><span>修订说明</span><input data-pf="__why" placeholder="为什么改，例：原作第 42 卷已确认"></label>
    <div class="pf-actions">
      <button class="primary-btn" id="patchSave">保存修订</button>
      ${cur ? '<button class="ghost-btn" id="patchRevert">撤销本条修订</button>' : ''}
    </div>
    ${bondList ? `<h4 class="pf-h4">你补充的关系</h4><ul class="pf-bonds">${bondList}</ul>` : ''}
  </div>`;
}

function bindPatchEditor(record, afterSave) {
  const box = document.querySelector('.patch-box');
  if (!box) return;

  box.querySelector('#patchSave')?.addEventListener('click', () => {
    const fields = {};
    for (const [key] of PATCH_FIELDS) {
      const el = box.querySelector(`[data-pf="${key}"]`);
      if (!el) continue;
      const next = el.value.trim();
      // 只记录「真的改了」的字段。表单初始值来自基线，若原样提交会把
      // summary/role 的原文一起写进补丁，导出文件全是冗余。
      const baseline = typeof record[key] === 'string' ? record[key].trim() : '';
      if (next !== baseline) fields[key] = next;
    }
    const why = box.querySelector('[data-pf="__why"]')?.value.trim() || '';
    if (!Object.keys(fields).length) {
      alert('没有检测到改动。要清空某个字段请重新编辑该条目。');
      return;
    }
    if (applyPatch(record.id, fields, null, why)) {
      if (typeof refreshPatchBadge === 'function') refreshPatchBadge();
      if (afterSave) afterSave();
    } else {
      alert('保存失败：浏览器存储可能已满或被禁用');
    }
  });

  box.querySelector('#patchRevert')?.addEventListener('click', () => {
    if (!confirm('撤销这一条的全部本地修订？')) return;
    revertPatch(record.id);
    if (afterSave) afterSave();
  });

  box.querySelectorAll('[data-delbond]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const i = Number(btn.dataset.delbond);
      const cur = patches[record.id];
      if (!cur?.bonds) return;
      cur.bonds.splice(i, 1);
      if (!cur.bonds.length && !Object.keys(cur.fields || {}).length) delete patches[record.id];
      else patches[record.id] = cur;
      savePatches(patches);
      if (afterSave) afterSave();
    });
  });
}

// ── 修订管理面板（左下角「修订」按钮） ────────────────────

function refreshPatchBadge() {
  const n = patchCount();
  const badge = document.querySelector('#patchBadge');
  if (badge) {
    badge.textContent = String(n);
    badge.classList.toggle('on', n > 0);
  }
  const cnt = document.querySelector('#pmCount');
  if (cnt) cnt.textContent = String(n);
}

function renderPatchList() {
  const list = document.querySelector('#pmList');
  if (!list) return;
  const ids = Object.keys(patches);
  if (!ids.length) {
    list.innerHTML = '<li class="pm-empty">还没有任何修订。打开任意人物 / 组织 / 案件的详情，底部有「爱好者修订」表单。</li>';
    return;
  }
  list.innerHTML = ids.map((id) => {
    const p = patches[id] || {};
    const fields = Object.keys(p.fields || {});
    const bonds = (p.bonds || []).length;
    const when = p.meta?.updatedAt ? p.meta.updatedAt.slice(0, 10) : '';
    const why = p.meta?.why ? ` · ${escapeHtml(p.meta.why)}` : '';
    return `<li data-pid="${escapeHtml(id)}">
      <button class="pm-name" data-open="${escapeHtml(id)}">${escapeHtml(nameOfRef(id) || id)}</button>
      <span class="pm-desc">${fields.length ? `${fields.length} 个字段` : ''}${bonds ? ` · ${bonds} 条关系` : ''}${when ? ` · ${when}` : ''}${why}</span>
      <button class="link-mini" data-drop="${escapeHtml(id)}">删除</button>
    </li>`;
  }).join('');

  list.querySelectorAll('[data-open]').forEach((b) => b.addEventListener('click', () => {
    closePatchPanel();
    openDetail(b.dataset.open);
  }));
  list.querySelectorAll('[data-drop]').forEach((b) => b.addEventListener('click', () => {
    revertPatch(b.dataset.drop);
    renderPatchList();
    refreshPatchBadge();
    renderList();
  }));
}

function openPatchPanel() {
  const m = document.querySelector('#patchModal');
  if (!m) return;
  renderPatchList();
  refreshPatchBadge();
  m.classList.add('open');
  m.setAttribute('aria-hidden', 'false');
}

function closePatchPanel() {
  const m = document.querySelector('#patchModal');
  if (!m) return;
  m.classList.remove('open');
  m.setAttribute('aria-hidden', 'true');
}

function bindPatchPanel() {
  const btn = document.querySelector('#patchBtn');
  const modal = document.querySelector('#patchModal');
  if (!btn || !modal) return;

  btn.addEventListener('click', openPatchPanel);
  document.querySelector('#patchClose')?.addEventListener('click', closePatchPanel);
  modal.addEventListener('click', (e) => { if (e.target === modal) closePatchPanel(); });

  document.querySelector('#pmExport')?.addEventListener('click', () => {
    if (!patchCount()) { alert('还没有任何修订，没什么可导出的。'); return; }
    exportPatches();
  });

  document.querySelector('#pmImport')?.addEventListener('click', () => {
    document.querySelector('#pmFile')?.click();
  });

  document.querySelector('#pmFile')?.addEventListener('change', (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const r = importPatches(String(reader.result || ''));
      if (r.ok) {
        alert(r.msg);
        renderPatchList();
        refreshPatchBadge();
        renderList();
      } else {
        alert(`导入失败：${r.msg}`);
      }
      e.target.value = '';
    };
    reader.readAsText(file);
  });

  document.querySelector('#pmClear')?.addEventListener('click', () => {
    if (!patchCount()) return;
    if (!confirm(`清空全部 ${patchCount()} 条本地修订？此操作不可撤销。`)) return;
    patches = {};
    savePatches(patches);
    renderPatchList();
    refreshPatchBadge();
    renderList();
  });

  refreshPatchBadge();
}
