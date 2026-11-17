/**
 * ebooks.js — Ebook catalog and access log management
 */
import * as api from './api.js';
import { toast, fmtDateTime, fmtMoney, buildTable, eyeIconMarkup, handleApiError, openModal, closeModal, getFormData, renderPagination, debounce, confirmDialog, setButtonLoading } from './utils.js';

let currentPage = 1;
const PAGE_SIZE = 15;
let currentEditEbook = null;

export async function renderEbooks(container) {
  container.innerHTML = `
    <div class="page-header">
      <h1>Sách điện tử</h1>
      <div class="page-header-actions">
        <button class="btn btn-primary" id="btn-add-ebook">Thêm sách điện tử</button>
        <button class="btn btn-secondary" id="btn-access-logs">Lịch sử truy cập</button>
      </div>
    </div>
    <div class="filter-bar">
      <input type="text" id="ebook-search" placeholder="Tìm theo tên sách, tác giả…" class="form-control" style="max-width:320px">
      <button class="btn btn-secondary" id="btn-ebook-search">Tìm</button>
      <button class="btn btn-ghost" id="btn-ebook-clear">Xóa bộ lọc</button>
    </div>
    <div id="ebooks-table-wrap"></div>
    <div class="pagination" id="ebooks-pagination"></div>

    <!-- Ebook Detail Modal -->
    <div class="modal" id="modal-ebook-detail">
      <div class="modal-box">
        <div class="modal-header">
          <h2 id="ebook-detail-title">Chi tiết sách điện tử</h2>
          <button class="modal-close" data-close="modal-ebook-detail">✕</button>
        </div>
        <div class="modal-body" id="ebook-detail-body">Đang tải…</div>
        <div class="modal-footer">
          <button class="btn btn-edit" id="btn-edit-ebook-from-detail">Sửa</button>
          <button class="btn btn-secondary" data-close="modal-ebook-detail">Đóng</button>
        </div>
      </div>
    </div>

    <!-- Ebook Form Modal -->
    <div class="modal" id="modal-ebook-form">
      <div class="modal-box">
        <div class="modal-header">
          <h2 id="ebook-form-title">Thêm sách điện tử</h2>
          <button class="modal-close" data-close="modal-ebook-form">✕</button>
        </div>
        <form id="ebook-form" class="modal-body">
          <input type="hidden" name="id">
          <div class="form-group"><label>Mã đầu sách *</label><input type="number" name="source_id" required class="form-control" min="1" step="1"></div>
          <div class="form-group"><label>Dung lượng (MB)</label><input type="number" name="file_size_mb" class="form-control" min="1" step="1"></div>
        </form>
        <div class="modal-footer">
          <button class="btn btn-primary" id="btn-submit-ebook">Lưu</button>
          <button class="btn btn-delete" id="btn-delete-ebook-from-form" style="display:none">Xóa</button>
          <button class="btn btn-secondary" data-close="modal-ebook-form">Hủy</button>
        </div>
      </div>
    </div>

    <!-- Start Access Modal -->
    <div class="modal" id="modal-start-access">
      <div class="modal-box">
        <div class="modal-header">
          <h2>Bắt đầu đọc sách điện tử</h2>
          <button class="modal-close" data-close="modal-start-access">✕</button>
        </div>
        <form id="access-form" class="modal-body">
          <div class="form-group"><label>Mã hội viên *</label><input type="text" name="reader_id" required class="form-control"></div>
          <div class="form-group"><label>Mã sách điện tử *</label><input type="text" name="ebook_id" required class="form-control" id="access-ebook-id"></div>
        </form>
        <div class="modal-footer">
          <button class="btn btn-primary" id="btn-submit-access">Bắt đầu</button>
          <button class="btn btn-secondary" data-close="modal-start-access">Hủy</button>
        </div>
      </div>
    </div>

    <!-- Access Logs Modal -->
    <div class="modal" id="modal-access-logs">
      <div class="modal-box modal-lg">
        <div class="modal-header">
          <h2>Lịch sử truy cập sách điện tử</h2>
          <button class="modal-close" data-close="modal-access-logs">✕</button>
        </div>
        <div class="modal-body" id="access-logs-body">Đang tải…</div>
        <div class="modal-footer">
          <button class="btn btn-secondary" data-close="modal-access-logs">Đóng</button>
        </div>
      </div>
    </div>
  `;

  setupModalClosers(container);
  document.getElementById('btn-add-ebook').addEventListener('click', () => openEbookForm(null));
  document.getElementById('btn-ebook-search').addEventListener('click', doSearch);
  document.getElementById('btn-ebook-clear').addEventListener('click', clearSearch);
  document.getElementById('ebook-search').addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });
  document.getElementById('btn-submit-ebook').addEventListener('click', submitEbookForm);
  document.getElementById('btn-delete-ebook-from-form').addEventListener('click', deleteCurrentEbook);
  document.getElementById('btn-submit-access').addEventListener('click', submitStartAccess);
  document.getElementById('btn-access-logs').addEventListener('click', openAccessLogs);

  await loadEbooks();
}

function setupModalClosers(root) {
  root.querySelectorAll('[data-close]').forEach(btn => btn.addEventListener('click', () => closeModal(btn.dataset.close)));
  root.querySelectorAll('.modal').forEach(m => m.addEventListener('click', e => { if (e.target === m) closeModal(m.id); }));
}

let searchQuery = '';
function doSearch() { searchQuery = document.getElementById('ebook-search').value.trim(); currentPage = 1; loadEbooks(); }
function clearSearch() { document.getElementById('ebook-search').value = ''; searchQuery = ''; currentPage = 1; loadEbooks(); }

async function loadEbooks() {
  const wrap = document.getElementById('ebooks-table-wrap');
  wrap.innerHTML = '<div class="loading-spinner"><div></div><div></div><div></div></div>';
  try {
    const params = { skip: (currentPage - 1) * PAGE_SIZE, limit: PAGE_SIZE };
    if (searchQuery) params.query = searchQuery;
    const data = await api.getEbooks(params);
    const items = data?.items ?? data ?? [];
    const total = data?.total ?? items.length;
    buildTable(wrap,
      [
        { key: 'id',          label: 'Mã Ebook' },
        { key: 'source',      label: 'Tên sách', render: source => source?.title ?? '—' },
        { key: 'source',      label: 'Số trang', render: source => source?.page_count ?? '—' },
        { key: 'file_size_mb', label: 'Dung lượng', render: v => v != null ? `${v} MB` : '—' },
      ],
      items,
      row => [
        { html: eyeIconMarkup(), ariaLabel: 'Chi tiết sách điện tử', title: 'Chi tiết', cls: 'btn-icon', onClick: r => openEbookDetail(r.id) },
        { label: 'Đọc', cls: 'btn-secondary', onClick: r => openStartAccess(r.id) },
        { label: 'Sửa', cls: 'btn-edit', onClick: r => openEbookForm(r) },
      ]
    );
    renderPagination(document.getElementById('ebooks-pagination'), currentPage, Math.ceil(total / PAGE_SIZE),
      p => { currentPage = p; loadEbooks(); });
  } catch (err) {
    wrap.innerHTML = `<p class="text-danger">Lỗi: ${err.detail || err.message}</p>`;
  }
}

async function openEbookDetail(id) {
  openModal('modal-ebook-detail');
  const body = document.getElementById('ebook-detail-body');
  body.textContent = 'Đang tải…';
  try {
    const ebook = await api.getEbook(id);
    currentEditEbook = ebook;
    document.getElementById('ebook-detail-title').textContent = ebook.source?.title || `Sách điện tử #${ebook.id}`;
    body.innerHTML = `
      <div class="detail-grid">
        <div class="detail-item"><span class="detail-label">Mã sách điện tử</span><span>${ebook.id}</span></div>
        <div class="detail-item"><span class="detail-label">Tên sách</span><span>${ebook.source?.title || '—'}</span></div>
        <div class="detail-item"><span class="detail-label">Tác giả</span><span>${ebook.source?.author || '—'}</span></div>
        <div class="detail-item"><span class="detail-label">Số trang</span><span>${ebook.source?.page_count ?? '—'}</span></div>
        <div class="detail-item"><span class="detail-label">Dung lượng</span><span>${ebook.file_size_mb != null ? `${ebook.file_size_mb} MB` : '—'}</span></div>
        <div class="detail-item"><span class="detail-label">Giá bìa</span><span>${ebook.source?.price != null ? fmtMoney(ebook.source.price) : '—'}</span></div>
      </div>`;
    document.getElementById('btn-edit-ebook-from-detail').onclick = () => {
      closeModal('modal-ebook-detail');
      openEbookForm(ebook);
    };
  } catch (err) {
    body.innerHTML = `<p class="text-danger">Không tải được chi tiết: ${err.detail || err.message}</p>`;
  }
}

function openEbookForm(ebook) {
  const form = document.getElementById('ebook-form');
  form.reset();
  form.elements['source_id'].readOnly = Boolean(ebook);
  currentEditEbook = ebook || null;
  document.getElementById('btn-delete-ebook-from-form').style.display = ebook ? 'inline-flex' : 'none';
  document.getElementById('ebook-form-title').textContent = ebook ? 'Sửa sách điện tử' : 'Thêm sách điện tử';
  if (ebook) {
    Object.entries(ebook).forEach(([k, v]) => {
      const el = form.elements[k];
      if (el && v !== null && v !== undefined) el.value = v;
    });
  }
  openModal('modal-ebook-form');
}

async function submitEbookForm() {
  const form = document.getElementById('ebook-form');
  const btn = document.getElementById('btn-submit-ebook');
  if (!form.checkValidity()) { form.reportValidity(); return; }
  const data = getFormData(form);
  const id = data.id;
  delete data.id;
  data.source_id = parseInt(data.source_id, 10);
  if (data.file_size_mb) data.file_size_mb = parseInt(data.file_size_mb, 10);
  setButtonLoading(btn, true);
  try {
    if (id) { await api.updateEbook(id, data); toast('Cập nhật sách điện tử thành công!', 'success'); }
    else { await api.createEbook(data); toast('Thêm sách điện tử thành công!', 'success'); }
    closeModal('modal-ebook-form');
    currentEditEbook = null;
    loadEbooks();
  } catch (err) { handleApiError(err); }
  finally { setButtonLoading(btn, false); }
}

async function deleteCurrentEbook() {
  const ebook = currentEditEbook;
  if (!ebook) return;
  const confirmed = await confirmDialog(`Xóa sách điện tử #<b>${ebook.id}</b>?`);
  if (!confirmed) return;
  try {
    await api.deleteEbook(ebook.id);
    toast('Đã xóa sách điện tử.', 'success');
    closeModal('modal-ebook-form');
    currentEditEbook = null;
    loadEbooks();
  }
  catch (err) { handleApiError(err); }
}

function openStartAccess(ebookId) {
  document.getElementById('access-form').reset();
  document.getElementById('access-ebook-id').value = ebookId;
  openModal('modal-start-access');
}

async function submitStartAccess() {
  const form = document.getElementById('access-form');
  if (!form.checkValidity()) { form.reportValidity(); return; }
  const data = {
    reader_id: form.elements['reader_id'].value.trim(),
    ebook_id: form.elements['ebook_id'].value.trim(),
  };
  try {
    const res = await api.startAccess(data);
    toast(`Bắt đầu đọc! Mã log: ${res.id}`, 'success');
    closeModal('modal-start-access');
  } catch (err) { handleApiError(err); }
}

async function openAccessLogs() {
  openModal('modal-access-logs');
  const body = document.getElementById('access-logs-body');
  body.innerHTML = 'Đang tải…';
  try {
    const data = await api.getAccessLogs({ limit: 50 });
    const items = data?.items ?? data ?? [];
    if (!items.length) { body.innerHTML = '<p class="empty-state">Không có lịch sử truy cập.</p>'; return; }
    body.innerHTML = `<table class="data-table">
      <thead><tr><th>Mã log</th><th>Sách điện tử</th><th>Mã hội viên</th><th>Bắt đầu</th><th>Kết thúc</th><th>Thao tác</th></tr></thead>
      <tbody>${items.map(l => `<tr>
        <td>${l.id}</td>
        <td>${l.ebook_id}</td>
        <td>${l.reader_id}</td>
        <td>${fmtDateTime(l.started_at)}</td>
        <td>${fmtDateTime(l.ended_at)}</td>
        <td>${!l.ended_at ? `<button class="btn btn-sm btn-secondary" onclick="endAccessLog(${l.id})">Kết thúc</button>` : '—'}</td>
      </tr>`).join('')}</tbody></table>`;
  } catch (err) { body.innerHTML = `<p class="text-danger">${err.detail}</p>`; }
}

// Expose globally for inline onclick
window.endAccessLog = async (logId) => {
  try {
    await api.endAccess(logId);
    toast('Đã kết thúc phiên đọc.', 'success');
    openAccessLogs();
  } catch (err) { handleApiError(err); }
};
