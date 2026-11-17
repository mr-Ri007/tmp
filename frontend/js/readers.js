/**
 * readers.js — Reader management
 */
import * as api from './api.js';
import { toast, fmtDate, fmtMoney, fmtStatus, fmtPaid, fmtFineType, buildTable, handleApiError, openModal, closeModal, getFormData, renderPagination } from './utils.js';

let currentPage = 1;
const PAGE_SIZE = 15;
let searchQuery = '';

export async function renderReaders(container) {
  container.innerHTML = `
    <div class="page-header">
      <h1>👤 Quản lý bạn đọc</h1>
      <button class="btn btn-primary" id="btn-add-reader">+ Thêm bạn đọc</button>
    </div>
    <div class="filter-bar">
      <input type="text" id="reader-search" placeholder="Tìm theo tên, email, mã thẻ…" class="form-control" style="max-width:320px">
      <button class="btn btn-secondary" id="btn-reader-search">🔍 Tìm</button>
      <button class="btn btn-ghost"     id="btn-reader-clear">✕ Xoá</button>
    </div>
    <div id="readers-table-wrap"></div>
    <div class="pagination" id="readers-pagination"></div>

    <!-- Reader Detail Modal -->
    <div class="modal" id="modal-reader-detail">
      <div class="modal-box modal-lg">
        <div class="modal-header">
          <h2 id="modal-reader-title">Chi tiết bạn đọc</h2>
          <button class="modal-close" data-close="modal-reader-detail">✕</button>
        </div>
        <div class="modal-body">
          <div id="reader-info"></div>
          <div class="tabs mt-3">
            <button class="tab-btn active" data-tab="tab-loans">📋 Đang mượn</button>
            <button class="tab-btn" data-tab="tab-fines">💸 Phạt</button>
          </div>
          <div id="tab-loans" class="tab-content"></div>
          <div id="tab-fines" class="tab-content" style="display:none"></div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-warning" id="btn-edit-reader">✏ Sửa</button>
          <button class="btn btn-danger"  id="btn-delete-reader">🗑 Xoá</button>
          <button class="btn btn-secondary" data-close="modal-reader-detail">Đóng</button>
        </div>
      </div>
    </div>

    <!-- Reader Form Modal -->
    <div class="modal" id="modal-reader-form">
      <div class="modal-box">
        <div class="modal-header">
          <h2 id="reader-form-title">Thêm bạn đọc</h2>
          <button class="modal-close" data-close="modal-reader-form">✕</button>
        </div>
        <form id="reader-form" class="modal-body">
          <input type="hidden" name="reader_id">
          <div class="form-row">
            <div class="form-group"><label>Họ và tên *</label><input type="text" name="full_name" required class="form-control"></div>
            <div class="form-group"><label>Email *</label><input type="email" name="email" required class="form-control"></div>
          </div>
          <div class="form-row">
            <div class="form-group"><label>Điện thoại</label><input type="text" name="phone" class="form-control"></div>
            <div class="form-group"><label>Ngày sinh</label><input type="date" name="birth_date" class="form-control"></div>
          </div>
          <div class="form-row">
            <div class="form-group"><label>Loại bạn đọc</label>
              <select name="reader_type" class="form-control">
                <option value="SinhVien">Sinh viên</option>
                <option value="GiangVien">Giảng viên</option>
                <option value="NhanVien">Nhân viên</option>
                <option value="Khac">Khác</option>
              </select>
            </div>
            <div class="form-group"><label>Ngày hết hạn thẻ</label><input type="date" name="card_expiry" class="form-control"></div>
          </div>
          <div class="form-group"><label>Địa chỉ</label><input type="text" name="address" class="form-control"></div>
        </form>
        <div class="modal-footer">
          <button class="btn btn-primary" id="btn-submit-reader">Lưu</button>
          <button class="btn btn-secondary" data-close="modal-reader-form">Huỷ</button>
        </div>
      </div>
    </div>
  `;

  setupModalClosers(container);
  setupTabs(container);
  document.getElementById('btn-add-reader').addEventListener('click', () => openReaderForm(null));
  document.getElementById('btn-reader-search').addEventListener('click', doSearch);
  document.getElementById('btn-reader-clear').addEventListener('click', clearSearch);
  document.getElementById('reader-search').addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });
  document.getElementById('btn-submit-reader').addEventListener('click', submitReaderForm);

  await loadReaders();
}

function setupModalClosers(root) {
  root.querySelectorAll('[data-close]').forEach(btn => btn.addEventListener('click', () => closeModal(btn.dataset.close)));
  root.querySelectorAll('.modal').forEach(m => m.addEventListener('click', e => { if (e.target === m) closeModal(m.id); }));
}

function setupTabs(root) {
  root.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      root.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      root.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
      btn.classList.add('active');
      root.getElementById ? root.getElementById(btn.dataset.tab).style.display = '' : document.getElementById(btn.dataset.tab).style.display = '';
    });
  });
}

function doSearch() {
  searchQuery = document.getElementById('reader-search').value.trim();
  currentPage = 1;
  loadReaders();
}

function clearSearch() {
  document.getElementById('reader-search').value = '';
  searchQuery = '';
  currentPage = 1;
  loadReaders();
}

async function loadReaders() {
  const wrap = document.getElementById('readers-table-wrap');
  wrap.innerHTML = '<div class="loading-spinner"><div></div><div></div><div></div></div>';
  try {
    const params = { skip: (currentPage - 1) * PAGE_SIZE, limit: PAGE_SIZE };
    if (searchQuery) params.query = searchQuery;
    const data = await api.getReaders(params);
    const items = data?.items ?? data ?? [];
    const total = data?.total ?? items.length;
    buildTable(wrap,
      [
        { key: 'reader_id',   label: 'Mã' },
        { key: 'full_name',   label: 'Họ tên' },
        { key: 'email',       label: 'Email' },
        { key: 'phone',       label: 'SĐT' },
        { key: 'reader_type', label: 'Loại' },
        { key: 'card_expiry', label: 'Hạn thẻ', render: v => fmtDate(v) },
      ],
      items,
      row => [
        { label: '👁 Chi tiết', cls: 'btn-primary', onClick: r => openReaderDetail(r.reader_id, r.full_name) },
        { label: '✏ Sửa',       cls: 'btn-warning',  onClick: r => openReaderForm(r) },
        { label: '🗑 Xoá',       cls: 'btn-danger',   onClick: r => deleteReader(r) },
      ]
    );
    renderPagination(document.getElementById('readers-pagination'), currentPage, Math.ceil(total / PAGE_SIZE),
      p => { currentPage = p; loadReaders(); });
  } catch (err) {
    wrap.innerHTML = `<p class="text-danger">Lỗi: ${err.detail || err.message}</p>`;
  }
}

async function openReaderDetail(id, name) {
  openModal('modal-reader-detail');
  document.getElementById('modal-reader-title').textContent = name;
  document.getElementById('reader-info').innerHTML = 'Đang tải…';
  document.getElementById('tab-loans').innerHTML = 'Đang tải…';
  document.getElementById('tab-fines').innerHTML = 'Đang tải…';

  try {
    const [reader, loans, fines, debtInfo] = await Promise.allSettled([
      api.getReader(id),
      api.getActiveLoans({ reader_id: id }),
      api.getFines({ reader_id: id }),
      api.checkDebtor(id),
    ]);

    if (reader.status === 'fulfilled') {
      const r = reader.value;
      document.getElementById('reader-info').innerHTML = `
        <div class="detail-grid">
          <div class="detail-item"><span class="detail-label">Mã</span><span>${r.reader_id}</span></div>
          <div class="detail-item"><span class="detail-label">Email</span><span>${r.email}</span></div>
          <div class="detail-item"><span class="detail-label">SĐT</span><span>${r.phone || '—'}</span></div>
          <div class="detail-item"><span class="detail-label">Loại</span><span>${r.reader_type}</span></div>
          <div class="detail-item"><span class="detail-label">Ngày sinh</span><span>${fmtDate(r.birth_date)}</span></div>
          <div class="detail-item"><span class="detail-label">Hạn thẻ</span><span>${fmtDate(r.card_expiry)}</span></div>
          ${debtInfo.status === 'fulfilled' && debtInfo.value?.has_debt
            ? `<div class="detail-item full-width"><span class="badge badge-danger">⚠ Còn nợ ${fmtMoney(debtInfo.value.total_debt)}</span></div>` : ''}
        </div>`;
      document.getElementById('btn-edit-reader').onclick = () => { closeModal('modal-reader-detail'); openReaderForm(r); };
      document.getElementById('btn-delete-reader').onclick = () => { closeModal('modal-reader-detail'); deleteReader(r); };
    }

    // Active loans tab
    const loanList = loans.status === 'fulfilled' ? (loans.value?.items ?? loans.value ?? []) : [];
    const loansHtml = loanList.length
      ? `<table class="data-table"><thead><tr><th>Mã mượn</th><th>Mã sách</th><th>Hạn trả</th><th>Trạng thái</th></tr></thead><tbody>
          ${loanList.map(l => `<tr>
            <td>${l.loan_id}</td><td>${l.hard_book_id}</td>
            <td class="${new Date(l.due_date) < new Date() ? 'text-danger' : ''}">${fmtDate(l.due_date)}</td>
            <td>${l.is_returned ? 'Đã trả' : 'Đang mượn'}</td>
          </tr>`).join('')}</tbody></table>`
      : '<p class="empty-state">Không có lượt mượn nào đang hoạt động.</p>';
    document.getElementById('tab-loans').innerHTML = loansHtml;

    // Fines tab
    const fineList = fines.status === 'fulfilled' ? (fines.value?.items ?? fines.value ?? []) : [];
    const finesHtml = fineList.length
      ? `<table class="data-table"><thead><tr><th>Mã phạt</th><th>Loại</th><th>Số tiền</th><th>Trạng thái</th><th>Ngày</th></tr></thead><tbody>
          ${fineList.map(f => `<tr>
            <td>${f.fine_id}</td><td>${fmtFineType(f.fine_type)}</td>
            <td class="fw-bold ${f.paid ? '' : 'text-danger'}">${fmtMoney(f.amount)}</td>
            <td>${fmtPaid(f.paid)}</td>
            <td>${fmtDate(f.created_at)}</td>
          </tr>`).join('')}</tbody></table>`
      : '<p class="empty-state">Không có khoản phạt nào.</p>';
    document.getElementById('tab-fines').innerHTML = finesHtml;

  } catch (err) { handleApiError(err); }
}

function openReaderForm(reader) {
  const form = document.getElementById('reader-form');
  form.reset();
  document.getElementById('reader-form-title').textContent = reader ? 'Sửa bạn đọc' : 'Thêm bạn đọc';
  if (reader) {
    Object.entries(reader).forEach(([k, v]) => {
      const el = form.elements[k];
      if (el && v !== null && v !== undefined) el.value = v;
    });
  }
  openModal('modal-reader-form');
}

async function submitReaderForm() {
  const form = document.getElementById('reader-form');
  if (!form.checkValidity()) { form.reportValidity(); return; }
  const data = getFormData(form);
  const id = data.reader_id;
  delete data.reader_id;
  try {
    if (id) {
      await api.updateReader(id, data);
      toast('Cập nhật bạn đọc thành công!', 'success');
    } else {
      await api.createReader(data);
      toast('Thêm bạn đọc thành công!', 'success');
    }
    closeModal('modal-reader-form');
    loadReaders();
  } catch (err) { handleApiError(err); }
}

async function deleteReader(r) {
  if (!confirm(`Xoá bạn đọc "${r.full_name}"?`)) return;
  try {
    await api.deleteReader(r.reader_id);
    toast('Đã xoá bạn đọc.', 'success');
    loadReaders();
  } catch (err) { handleApiError(err); }
}
