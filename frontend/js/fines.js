/**
 * fines.js — Fine management, damaged assessment, pay fine
 */
import * as api from './api.js';
import { toast, fmtDate, fmtMoney, fmtFineType, fmtPaid, buildTable, handleApiError, openModal, closeModal, renderPagination } from './utils.js';

let currentPage = 1;
const PAGE_SIZE = 20;
let filters = { reader_id: '', fine_type: '', unpaid_only: false };

export async function renderFines(container) {
  container.innerHTML = `
    <div class="page-header">
      <h1>💸 Quản lý tiền phạt</h1>
      <button class="btn btn-warning" id="btn-assess-damaged">📝 Nhập phạt hỏng sách</button>
    </div>

    <!-- Fine formula note -->
    <div class="alert alert-info">
      <strong>Quy tắc tính phạt:</strong>
      🕐 Quá hạn: 10% × giá bìa × số ngày &nbsp;|&nbsp;
      📕 Mất sách: 100% × giá bìa &nbsp;|&nbsp;
      🔧 Hỏng sách: nhân viên quyết định
    </div>

    <div class="filter-bar">
      <input type="text" id="fine-filter-reader" placeholder="Mã độc giả…" class="form-control" style="max-width:160px">
      <select id="fine-filter-type" class="form-control" style="max-width:160px">
        <option value="">Tất cả loại</option>
        <option value="Late">Quá hạn</option>
        <option value="Lost">Mất sách</option>
        <option value="Damaged">Hỏng sách</option>
      </select>
      <label class="checkbox-label">
        <input type="checkbox" id="fine-filter-unpaid"> Chưa thu
      </label>
      <button class="btn btn-secondary" id="btn-fine-search">🔍 Lọc</button>
      <button class="btn btn-ghost" id="btn-fine-clear">✕ Xoá</button>
    </div>

    <div id="fines-table-wrap"></div>
    <div class="pagination" id="fines-pagination"></div>

    <!-- Assess Damaged Modal -->
    <div class="modal" id="modal-assess-damaged">
      <div class="modal-box">
        <div class="modal-header">
          <h2>📝 Nhập phạt hỏng sách</h2>
          <button class="modal-close" data-close="modal-assess-damaged">✕</button>
        </div>
        <form id="damaged-form" class="modal-body">
          <div class="alert alert-warning">
            Chỉ dùng form này cho <strong>sách hỏng (Damaged)</strong>. Phạt quá hạn và mất sách do hệ thống tự tính.
          </div>
          <div class="form-group">
            <label>Mã phiếu trả (return_record_id) *</label>
            <input type="number" name="return_record_id" required class="form-control" placeholder="VD: 5">
          </div>
          <div class="form-group">
            <label>Số tiền phạt (₫) *</label>
            <input type="number" name="amount" required class="form-control" min="0" step="1000" placeholder="VD: 50000">
          </div>
          <div class="form-group">
            <label>Lý do / ghi chú *</label>
            <textarea name="reason" required class="form-control" rows="3" placeholder="Mô tả tình trạng hư hỏng…"></textarea>
          </div>
          <div class="form-group">
            <label>Nhân viên đánh giá</label>
            <input type="text" name="assessed_by" class="form-control" placeholder="Tên hoặc mã nhân viên">
          </div>
        </form>
        <div class="modal-footer">
          <button class="btn btn-primary" id="btn-submit-damaged">✔ Lưu khoản phạt</button>
          <button class="btn btn-secondary" data-close="modal-assess-damaged">Huỷ</button>
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
          <button class="btn btn-success" id="btn-pay-fine">💰 Thu phạt</button>
          <button class="btn btn-secondary" data-close="modal-fine-detail">Đóng</button>
        </div>
      </div>
    </div>
  `;

  setupModalClosers(container);
  document.getElementById('btn-assess-damaged').addEventListener('click', () => { document.getElementById('damaged-form').reset(); openModal('modal-assess-damaged'); });
  document.getElementById('btn-fine-search').addEventListener('click', doSearch);
  document.getElementById('btn-fine-clear').addEventListener('click', clearSearch);
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

async function loadFines() {
  const wrap = document.getElementById('fines-table-wrap');
  wrap.innerHTML = '<div class="loading-spinner"><div></div><div></div><div></div></div>';
  try {
    const params = { skip: (currentPage - 1) * PAGE_SIZE, limit: PAGE_SIZE };
    if (filters.reader_id) params.reader_id = filters.reader_id;
    if (filters.fine_type) params.fine_type = filters.fine_type;
    if (filters.unpaid_only) params.unpaid_only = true;
    const data = await api.getFines(params);
    const items = data?.items ?? data ?? [];
    const total = data?.total ?? items.length;

    buildTable(wrap,
      [
        { key: 'fine_id',          label: 'Mã phạt' },
        { key: 'return_record_id', label: 'Phiếu trả' },
        { key: 'fine_type',        label: 'Loại', render: v => fmtFineType(v) },
        { key: 'amount',           label: 'Số tiền', render: v => `<span class="fw-bold ${Number(v) > 0 ? 'text-danger' : ''}">${fmtMoney(v)}</span>` },
        { key: 'paid',             label: 'Trạng thái', render: v => fmtPaid(v) },
        { key: 'reason',           label: 'Ghi chú' },
        { key: 'assessed_by',      label: 'NV đánh giá' },
        { key: 'created_at',       label: 'Ngày tạo', render: v => fmtDate(v) },
      ],
      items,
      row => [
        { label: '👁 Chi tiết',   cls: 'btn-primary',  onClick: r => openFineDetail(r.fine_id) },
        ...(!row.paid ? [{ label: '💰 Thu',  cls: 'btn-success', onClick: r => payFine(r) }] : []),
      ]
    );
    renderPagination(document.getElementById('fines-pagination'), currentPage, Math.ceil(total / PAGE_SIZE),
      p => { currentPage = p; loadFines(); });
  } catch (err) {
    wrap.innerHTML = `<p class="text-danger">Lỗi: ${err.detail || err.message}</p>`;
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
        <div class="detail-item"><span class="detail-label">Mã phạt</span><span>${f.fine_id}</span></div>
        <div class="detail-item"><span class="detail-label">Phiếu trả</span><span>${f.return_record_id}</span></div>
        <div class="detail-item"><span class="detail-label">Loại phạt</span><span>${fmtFineType(f.fine_type)}</span></div>
        <div class="detail-item"><span class="detail-label">Số tiền</span><span class="text-danger fw-bold">${fmtMoney(f.amount)}</span></div>
        <div class="detail-item"><span class="detail-label">Trạng thái</span><span>${fmtPaid(f.paid)}</span></div>
        <div class="detail-item"><span class="detail-label">NV đánh giá</span><span>${f.assessed_by || '—'}</span></div>
        <div class="detail-item"><span class="detail-label">Ngày tạo</span><span>${fmtDate(f.created_at)}</span></div>
      </div>
      <div class="form-group mt-2"><strong>Lý do:</strong><p>${f.reason || '—'}</p></div>
    `;
    const payBtn = document.getElementById('btn-pay-fine');
    if (f.paid) { payBtn.disabled = true; payBtn.textContent = '✔ Đã thu'; }
    else { payBtn.disabled = false; payBtn.onclick = () => payFine(f); }
  } catch (err) { body.innerHTML = `<p class="text-danger">${err.detail}</p>`; }
}

async function payFine(f) {
  if (!confirm(`Thu phạt ${fmtMoney(f.amount)} cho khoản phạt #${f.fine_id}?`)) return;
  try {
    await api.payFine(f.fine_id);
    toast('Đã thu phạt thành công!', 'success');
    closeModal('modal-fine-detail');
    loadFines();
  } catch (err) { handleApiError(err); }
}

async function submitDamaged() {
  const form = document.getElementById('damaged-form');
  if (!form.checkValidity()) { form.reportValidity(); return; }
  const data = {
    return_record_id: parseInt(form.elements['return_record_id'].value),
    amount: parseFloat(form.elements['amount'].value),
    reason: form.elements['reason'].value.trim(),
  };
  const ab = form.elements['assessed_by'].value.trim();
  if (ab) data.assessed_by = ab;
  try {
    const res = await api.assessDamagedFine(data);
    toast(`Đã tạo khoản phạt hỏng sách: ${fmtMoney(res.amount)}`, 'success');
    closeModal('modal-assess-damaged');
    form.reset();
    loadFines();
  } catch (err) { handleApiError(err); }
}
