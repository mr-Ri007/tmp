/**
 * utils.js — Shared helpers used across all page modules
 */

// ── Toast notification ────────────────────────────────────────────────────────
export function toast(msg, type = 'info', duration = 3500) {
  const wrap = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.innerHTML = `<span class="toast-icon">${icons[type] || ''}</span><span>${msg}</span>`;
  wrap.appendChild(el);
  requestAnimationFrame(() => el.classList.add('show'));
  setTimeout(() => {
    el.classList.remove('show');
    setTimeout(() => el.remove(), 350);
  }, duration);
}
const icons = { success: '✔', error: '✖', info: 'ℹ', warning: '⚠' };

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
        btn.textContent = a.label;
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
