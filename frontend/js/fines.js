/**
 * fines.js — Fine management, damaged assessment, pay fine
 */
import * as api from './api.js';
import { toast, fmtDate, fmtMoney, fmtFineType, fmtPaid, buildTable, eyeIconMarkup, handleApiError, openModal, closeModal, debounce, confirmDialog, setButtonLoading } from './utils.js';

let currentPage = 1;
const PAGE_SIZE = 50;
let filters = { reader_id: '', fine_type: '', unpaid_only: false };
let fineTotal = 0;
let fineLoaded = 0;
let fineLoading = false;
let fineRequestId = 0;

export async function renderFines(container) {
  container.innerHTML = `
    <div class="page-header">
      <h1>Quản lý tiền phạt</h1>
      <div class="page-header-actions">
        <button class="btn btn-secondary" id="btn-assess-damaged">Nhập phạt sách hỏng</button>
      </div>
    </div>

    <!-- Fine formula note -->
    <div class="alert alert-info">
      <strong>Quy tắc tính phạt:</strong>
      Quá hạn: 10% × giá bìa × số ngày &nbsp;|&nbsp;
      Mất sách: 100% × giá bìa &nbsp;|&nbsp;
      Sách hỏng: nhân viên quyết định
    </div>

    <div class="filter-bar">
      <input type="text" id="fine-filter-reader" placeholder="Mã hội viên…" class="form-control" style="max-width:160px">
      <select id="fine-filter-type" class="form-control" style="max-width:160px">
        <option value="">Tất cả loại</option>
        <option value="Late">Quá hạn</option>
        <option value="Lost">Mất sách</option>
        <option value="Damaged">Hỏng sách</option>
      </select>
      <label class="checkbox-label">
        <input type="checkbox" id="fine-filter-unpaid"> Chưa thu
      </label>
      <button class="btn btn-secondary" id="btn-fine-search">Lọc</button>
      <button class="btn btn-ghost" id="btn-fine-clear">Xóa</button>
    </div>

    <div id="fines-table-wrap"></div>

    <!-- Assess Damaged Modal -->
    <div class="modal" id="modal-assess-damaged">
      <div class="modal-box">
        <div class="modal-header">
          <h2>Nhập phạt sách hỏng</h2>
          <button class="modal-close" data-close="modal-assess-damaged">✕</button>
        </div>
        <form id="damaged-form" class="modal-body">
          <div class="alert alert-warning">
            Chỉ dùng biểu mẫu này cho <strong>sách hỏng</strong>. Phạt quá hạn và mất sách do hệ thống tự tính.
          </div>
          <div class="form-group">
            <label>Mã phiếu trả *</label>
            <input type="number" name="return_record_id" required class="form-control" placeholder="Ví dụ: 5">
          </div>
          <div class="form-group">
            <label>Số tiền phạt (₫) *</label>
            <input type="number" name="amount" required class="form-control" min="0" step="1000" placeholder="Ví dụ: 50000">
          </div>
          <div class="form-group">
            <label>Lý do phạt *</label>
            <textarea name="reason" required class="form-control" rows="3" placeholder="Mô tả tình trạng hư hỏng…"></textarea>
          </div>
          <div class="form-group">
            <label>Ghi chú *</label>
            <input type="text" name="assessed_by" required class="form-control" placeholder="Ghi chú đánh giá">
          </div>
        </form>
        <div class="modal-footer">
          <button class="btn btn-primary" id="btn-submit-damaged">Lưu khoản phạt</button>
          <button class="btn btn-secondary" data-close="modal-assess-damaged">Hủy</button>
        </div>
      </div>
    </div>

    <!-- Fine Detail Modal -->
    <div class="modal" id="modal-fine-detail">
      <div class="modal-box">
        <div class="modal-header">
          <h2>Chi tiết khoản phạt</h2>
          <button class="modal-close" data-close="modal-fine-detail">✕</button>
        </div>
        <div class="modal-body" id="fine-detail-body">Đang tải…</div>
        <div class="modal-footer">
          <button class="btn btn-secondary" id="btn-pay-fine">Thu phạt</button>
          <button class="btn btn-secondary" data-close="modal-fine-detail">Đóng</button>
        </div>
      </div>
    </div>
  `;

  setupModalClosers(container);
  document.getElementById('btn-assess-damaged').addEventListener('click', () => { document.getElementById('damaged-form').reset(); openModal('modal-assess-damaged'); });
  document.getElementById('btn-fine-search').addEventListener('click', doSearch);
  document.getElementById('btn-fine-clear').addEventListener('click', clearSearch);
  const debouncedSearch = debounce(doSearch, 400);
  document.getElementById('fine-filter-reader').addEventListener('input', debouncedSearch);
  document.getElementById('fine-filter-type').addEventListener('change', debouncedSearch);
  document.getElementById('fine-filter-unpaid').addEventListener('change', debouncedSearch);
  document.getElementById('btn-submit-damaged').addEventListener('click', submitDamaged);

  await loadFines();
}

function setupModalClosers(root) {
  root.querySelectorAll('[data-close]').forEach(btn => btn.addEventListener('click', () => closeModal(btn.dataset.close)));
  root.querySelectorAll('.modal').forEach(m => m.addEventListener('click', e => { if (e.target === m) closeModal(m.id); }));
}

function doSearch() {
  filters.reader_id   = document.getElementById('fine-filter-reader').value.trim();
  filters.fine_type   = document.getElementById('fine-filter-type').value;
  filters.unpaid_only = document.getElementById('fine-filter-unpaid').checked;
  currentPage = 1;
  loadFines();
}
function clearSearch() {
  document.getElementById('fine-filter-reader').value = '';
  document.getElementById('fine-filter-type').value = '';
  document.getElementById('fine-filter-unpaid').checked = false;
  filters = { reader_id: '', fine_type: '', unpaid_only: false };
  currentPage = 1;
  loadFines();
}

const fineColumns = [
  { key: 'id', label: 'Mã phạt' },
  { key: 'return_record_id', label: 'Phiếu trả' },
  { key: 'fine_type', label: 'Loại', render: value => fmtFineType(value) },
  { key: 'amount', label: 'Số tiền', render: value => `<span class="fw-bold ${Number(value) > 0 ? 'text-danger' : ''}">${fmtMoney(value)}</span>` },
  { key: 'paid_at', label: 'Trạng thái', render: value => fmtPaid(Boolean(value)) },
  { key: 'reason', label: 'Lý do phạt' },
  { key: 'assessed_by', label: 'Ghi chú' },
  { key: 'created_at', label: 'Ngày tạo', render: value => fmtDate(value) },
];

function fineActions(row) {
  return [
    { html: eyeIconMarkup(), ariaLabel: 'Chi tiết khoản phạt', title: 'Chi tiết', cls: 'btn-icon', onClick: item => openFineDetail(item.id) },
    ...(!row.paid_at ? [{ label: 'Thu', cls: 'btn-secondary', onClick: payFine }] : []),
  ];
}

async function loadFines(append = false) {
  const wrap = document.getElementById('fines-table-wrap');
  if (append && fineLoading) return;
  if (!append) {
    fineRequestId++;
    fineLoaded = 0;
    fineTotal = 0;
    currentPage = 1;
    wrap.innerHTML = '<div class="scroll-table dynamic-scroll"><div class="loading-spinner"><div></div><div></div><div></div></div></div><div class="fine-scroll-status" aria-live="polite"></div>';
  }
  const requestId = fineRequestId;
  const page = append ? currentPage + 1 : 1;
  fineLoading = true;
  try {
    const params = { skip: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE };
    if (filters.reader_id) params.reader_id = filters.reader_id;
    if (filters.fine_type) params.fine_type = filters.fine_type;
    if (filters.unpaid_only) params.unpaid_only = true;
    const data = await api.getFinesPage(params);
    if (requestId !== fineRequestId) return;
    const items = data.items || [];
    fineTotal = data.total || 0;
    currentPage = page;
    const scroll = wrap.querySelector('.scroll-table');
    if (append) {
      const temp = document.createElement('div');
      buildTable(temp, fineColumns, items, fineActions);
      const newBody = temp.querySelector('tbody');
      const tableBody = scroll.querySelector('tbody');
      if (newBody && tableBody) tableBody.append(...Array.from(newBody.children));
    } else {
      buildTable(scroll, fineColumns, items, fineActions);
      scroll.addEventListener('scroll', () => {
        if (fineLoading || fineLoaded >= fineTotal) return;
        if (scroll.scrollTop + scroll.clientHeight >= scroll.scrollHeight - 100) loadFines(true);
      });
    }
    fineLoaded += items.length;
    wrap.querySelector('.fine-scroll-status').textContent =
      fineLoaded < fineTotal ? `Đang hiển thị ${fineLoaded} / ${fineTotal} khoản phạt · Cuộn xuống để tải tiếp` :
        `${fineLoaded} khoản phạt`;
  } catch (err) {
    if (requestId !== fineRequestId) return;
    wrap.innerHTML = `<p class="text-danger">Lỗi: ${err.detail || err.message}</p>`;
  } finally {
    if (requestId === fineRequestId) fineLoading = false;
  }
}

async function openFineDetail(id) {
  openModal('modal-fine-detail');
  const body = document.getElementById('fine-detail-body');
  body.innerHTML = 'Đang tải…';
  try {
    const f = await api.getFine(id);
    body.innerHTML = `
      <div class="detail-grid">
        <div class="detail-item"><span class="detail-label">Mã phạt</span><span>${f.id}</span></div>
        <div class="detail-item"><span class="detail-label">Phiếu trả</span><span>${f.return_record_id}</span></div>
        <div class="detail-item"><span class="detail-label">Loại phạt</span><span>${fmtFineType(f.fine_type)}</span></div>
        <div class="detail-item"><span class="detail-label">Số tiền</span><span class="text-danger fw-bold">${fmtMoney(f.amount)}</span></div>
        <div class="detail-item"><span class="detail-label">Trạng thái</span><span>${fmtPaid(Boolean(f.paid_at))}</span></div>
        <div class="detail-item"><span class="detail-label">Ghi chú</span><span>${f.assessed_by || '—'}</span></div>
        <div class="detail-item"><span class="detail-label">Ngày tạo</span><span>${fmtDate(f.created_at)}</span></div>
      </div>
      <div class="form-group mt-2"><strong>Lý do:</strong><p>${f.reason || '—'}</p></div>
    `;
    const payBtn = document.getElementById('btn-pay-fine');
    if (f.paid_at) { payBtn.disabled = true; payBtn.textContent = 'Đã thu'; }
    else { payBtn.disabled = false; payBtn.onclick = () => payFine(f); }
  } catch (err) { body.innerHTML = `<p class="text-danger">${err.detail}</p>`; }
}

async function payFine(f) {
  const confirmed = await confirmDialog(`Thu phạt ${fmtMoney(f.amount)} cho khoản phạt #${f.id}?`);
  if (!confirmed) return;
  try {
    await api.payFine(f.id);
    toast('Đã thu phạt thành công!', 'success');
    closeModal('modal-fine-detail');
    loadFines();
  } catch (err) { handleApiError(err); }
}

async function submitDamaged() {
  const form = document.getElementById('damaged-form');
  const btn = document.getElementById('btn-submit-damaged');
  if (!form.checkValidity()) { form.reportValidity(); return; }
  const data = {
    return_record_id: parseInt(form.elements['return_record_id'].value),
    amount: parseFloat(form.elements['amount'].value),
    reason: form.elements['reason'].value.trim(),
  };
  const ab = form.elements['assessed_by'].value.trim();
  if (ab) data.assessed_by = ab;
  setButtonLoading(btn, true);
  try {
    const res = await api.assessDamagedFine(data);
    toast(`Đã tạo khoản phạt sách hỏng: ${fmtMoney(res.amount)}`, 'success');
    closeModal('modal-assess-damaged');
    form.reset();
    loadFines();
  } catch (err) { handleApiError(err); }
  finally { setButtonLoading(btn, false); }
}
