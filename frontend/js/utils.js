/**
 * utils.js — Shared helpers used across all page modules
 */

// ── Toast notification ────────────────────────────────────────────────────────
export function toast(msg, type = 'info', duration = 3500) {
  const wrap = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.innerHTML = `<span>${msg}</span>`;
  wrap.appendChild(el);
  requestAnimationFrame(() => el.classList.add('show'));
  setTimeout(() => {
    el.classList.remove('show');
    setTimeout(() => el.remove(), 350);
  }, duration);
}
// ── Debounce ──────────────────────────────────────────────────────────────────
export function debounce(fn, wait) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), wait);
  };
}

// ── Custom confirm dialog (replaces browser confirm) ──────────────────────────
export function confirmDialog(message, title = 'Xác nhận') {
  return new Promise((resolve) => {
    const overlay = document.createElement('div');
    overlay.className = 'modal open';
    overlay.innerHTML = `
      <div class="modal-box" style="max-width:420px">
        <div class="modal-header" style="background:var(--danger-lt);border-color:var(--danger)">
          <h2 style="color:var(--danger);margin:0">${title}</h2>
          <button class="modal-close" style="color:var(--danger)">✕</button>
        </div>
        <div class="modal-body" style="text-align:center;padding:32px 24px">
          <p style="margin:0 0 24px;color:var(--text)">${message}</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" id="confirm-cancel">Huỷ</button>
          <button class="btn btn-danger" id="confirm-ok">Đồng ý</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    const ok = overlay.querySelector('#confirm-ok');
    const cancel = overlay.querySelector('#confirm-cancel');
    const closeBtn = overlay.querySelector('.modal-close');
    const cleanup = () => { overlay.remove(); };
    ok.addEventListener('click', () => { cleanup(); resolve(true); });
    cancel.addEventListener('click', () => { cleanup(); resolve(false); });
    closeBtn.addEventListener('click', () => { cleanup(); resolve(false); });
    overlay.addEventListener('click', (e) => { if (e.target === overlay) { cleanup(); resolve(false); } });
  });
}

// ── Button loading state ──────────────────────────────────────────────────────
export function setButtonLoading(btn, loading, originalText = null) {
  if (!btn) return;
  if (loading) {
    if (originalText === null) btn.dataset.originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span style="display:inline-block;width:16px;height:16px;border:2px solid rgba(255,255,255,0.3);border-top-color:#fff;border-radius:50%;animation:spin 0.8s linear infinite"></span> Đang xử lý…';
  } else {
    btn.disabled = false;
    btn.innerHTML = btn.dataset.originalText || originalText || btn.innerHTML;
    delete btn.dataset.originalText;
  }
}

// ── Spinner CSS (injected once) ───────────────────────────────────────────────
if (!document.getElementById('util-spinner-style')) {
  const s = document.createElement('style');
  s.id = 'util-spinner-style';
  s.textContent = `@keyframes spin { to { transform: rotate(360deg); } }`;
  document.head.appendChild(s);
}

// ── Loading spinner ───────────────────────────────────────────────────────────
export function showLoading(selector = '#main-content') {
  const el = document.querySelector(selector);
  if (el) el.innerHTML = '<div class="loading-spinner"><div></div><div></div><div></div></div>';
}

// ── Format helpers ────────────────────────────────────────────────────────────
export function fmtDate(str) {
  if (!str) return '—';
  return new Date(str).toLocaleDateString('vi-VN');
}

export function fmtDateTime(str) {
  if (!str) return '—';
  return new Date(str).toLocaleString('vi-VN');
}

export function fmtMoney(val) {
  if (val === null || val === undefined) return '—';
  return Number(val).toLocaleString('vi-VN') + ' ₫';
}

export function fmtStatus(s) {
  const map = {
    SanSang: '<span class="badge badge-success">Sẵn sàng</span>',
    DangCho: '<span class="badge badge-info">Đang giữ</span>',
    DangMuon: '<span class="badge badge-warning">Đang mượn</span>',
    MatSach: '<span class="badge badge-danger">Mất sách</span>',
    HongSach: '<span class="badge badge-secondary">Hỏng sách</span>',
    DatTruoc: '<span class="badge badge-info">Đặt trước</span>',
  };
  return map[s] || `<span class="badge">${s}</span>`;
}

export function fmtCondition(c) {
  const map = {
    Tot: '<span class="badge badge-success">Tốt</span>',
    Hong: '<span class="badge badge-warning">Hỏng</span>',
    Mat: '<span class="badge badge-danger">Mất sách</span>',
    HongNhe: '<span class="badge badge-warning">Hỏng nhẹ</span>',
    HongNang: '<span class="badge badge-danger">Hỏng nặng</span>',
    MatSach: '<span class="badge badge-danger">Mất sách</span>',
  };
  return map[c] || `<span class="badge">${c}</span>`;
}

export function fmtFineType(t) {
  const map = {
    Late: '<span class="badge badge-warning">Quá hạn</span>',
    Lost: '<span class="badge badge-danger">Mất sách</span>',
    Damaged: '<span class="badge badge-secondary">Hỏng sách</span>',
  };
  return map[t] || `<span class="badge">${t}</span>`;
}

export function fmtPaid(p) {
  return p
    ? '<span class="badge badge-success">Đã nộp</span>'
    : '<span class="badge badge-danger">Chưa nộp</span>';
}

// ── Pagination helper ─────────────────────────────────────────────────────────
export function renderPagination(container, page, totalPages, onPageChange) {
  container.innerHTML = '';
  if (totalPages <= 1) return;
  const mkBtn = (label, pg, disabled = false, active = false) => {
    const b = document.createElement('button');
    b.className = 'page-btn' + (active ? ' active' : '') + (disabled ? ' disabled' : '');
    b.textContent = label;
    if (!disabled) b.addEventListener('click', () => onPageChange(pg));
    return b;
  };
  container.appendChild(mkBtn('«', 1, page === 1));
  container.appendChild(mkBtn('‹', page - 1, page === 1));
  for (let i = Math.max(1, page - 2); i <= Math.min(totalPages, page + 2); i++) {
    container.appendChild(mkBtn(i, i, false, i === page));
  }
  container.appendChild(mkBtn('›', page + 1, page === totalPages));
  container.appendChild(mkBtn('»', totalPages, page === totalPages));
}

// ── Modal helpers ─────────────────────────────────────────────────────────────
export function openModal(id) {
  const m = document.getElementById(id);
  if (m) { m.style.display = 'flex'; m.classList.add('open'); }
}
export function closeModal(id) {
  const m = document.getElementById(id);
  if (m) { m.style.display = 'none'; m.classList.remove('open'); }
}
export function closeAllModals() {
  document.querySelectorAll('.modal').forEach(m => { m.style.display = 'none'; m.classList.remove('open'); });
}

// ── Generic table builder ─────────────────────────────────────────────────────
export function buildTable(container, columns, rows, actions = null) {
  if (!rows.length) {
    container.innerHTML = '<p class="empty-state">Không có dữ liệu.</p>';
    return;
  }
  const tbl = document.createElement('table');
  tbl.className = 'data-table';
  const thead = document.createElement('thead');
  const hrow = document.createElement('tr');
  columns.forEach(c => {
    const th = document.createElement('th');
    th.textContent = c.label;
    hrow.appendChild(th);
  });
  if (actions) { const th = document.createElement('th'); th.textContent = 'Thao tác'; hrow.appendChild(th); }
  thead.appendChild(hrow);
  tbl.appendChild(thead);
  const tbody = document.createElement('tbody');
  rows.forEach(row => {
    const tr = document.createElement('tr');
    columns.forEach(c => {
      const td = document.createElement('td');
      td.innerHTML = c.render ? c.render(row[c.key], row) : (row[c.key] ?? '—');
      tr.appendChild(td);
    });
    if (actions) {
      const td = document.createElement('td');
      td.className = 'action-cell';
      actions(row).forEach(a => {
        const btn = document.createElement('button');
        btn.className = `btn btn-sm ${a.cls || 'btn-secondary'}`;
        if (a.html) btn.innerHTML = a.html;
        else btn.textContent = a.label;
        if (a.ariaLabel) btn.setAttribute('aria-label', a.ariaLabel);
        if (a.title) btn.title = a.title;
        btn.addEventListener('click', () => a.onClick(row));
        td.appendChild(btn);
      });
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  });
  tbl.appendChild(tbody);
  container.innerHTML = '';
  container.appendChild(tbl);
}

export function eyeIconMarkup() {
  return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></svg>';
}

export function eyeOffIconMarkup() {
  return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m3 3 18 18"/><path d="M10.6 10.6a2 2 0 0 0 2.8 2.8"/><path d="M9.9 5.2A10.7 10.7 0 0 1 12 5c6.4 0 10 7 10 7a15.7 15.7 0 0 1-3.1 3.8"/><path d="M6.2 6.2C3.5 8 2 12 2 12s3.6 7 10 7a10.7 10.7 0 0 0 2.1-.2"/></svg>';
}

// ── Form value helpers ────────────────────────────────────────────────────────
export function getFormData(form) {
  const fd = new FormData(form);
  const obj = {};
  for (const [k, v] of fd.entries()) {
    obj[k] = v === '' ? null : v;
  }
  return obj;
}

export function setFormData(form, data) {
  for (const [k, v] of Object.entries(data)) {
    const el = form.elements[k];
    if (el && v !== null && v !== undefined) el.value = v;
  }
}

export function handleApiError(err) {
  toast(err.detail || err.message || 'Lỗi không xác định', 'error');
}
