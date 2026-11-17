/**
 * ebooks.js — Ebook catalog and access log management
 */
import * as api from './api.js';
import { toast, fmtDate, fmtDateTime, buildTable, handleApiError, openModal, closeModal, getFormData, renderPagination } from './utils.js';

let currentPage = 1;
const PAGE_SIZE = 15;

export async function renderEbooks(container) {
  container.innerHTML = `
    <div class="page-header">
      <h1>💻 Sách điện tử</h1>
      <button class="btn btn-primary" id="btn-add-ebook">+ Thêm Ebook</button>
      <button class="btn btn-secondary" id="btn-access-logs">📊 Lịch sử truy cập</button>
    </div>
    <div class="filter-bar">
      <input type="text" id="ebook-search" placeholder="Tìm theo tên, URL…" class="form-control" style="max-width:320px">
      <button class="btn btn-secondary" id="btn-ebook-search">🔍 Tìm</button>
      <button class="btn btn-ghost" id="btn-ebook-clear">✕</button>
    </div>
    <div id="ebooks-table-wrap"></div>
    <div class="pagination" id="ebooks-pagination"></div>

    <!-- Ebook Form Modal -->
    <div class="modal" id="modal-ebook-form">
      <div class="modal-box">
        <div class="modal-header">
          <h2 id="ebook-form-title">Thêm Ebook</h2>
          <button class="modal-close" data-close="modal-ebook-form">✕</button>
        </div>
        <form id="ebook-form" class="modal-body">
          <input type="hidden" name="ebook_id">
          <div class="form-group"><label>Đầu sách (source_id) *</label><input type="text" name="source_id" required class="form-control"></div>
          <div class="form-group"><label>URL/Đường dẫn *</label><input type="url" name="file_url" required class="form-control" placeholder="https://…"></div>
          <div class="form-row">
            <div class="form-group"><label>Định dạng</label>
              <select name="format" class="form-control">
                <option value="PDF">PDF</option>
                <option value="EPUB">EPUB</option>
                <option value="MOBI">MOBI</option>
                <option value="HTML">HTML</option>
              </select>
            </div>
            <div class="form-group"><label>Dung lượng (MB)</label><input type="number" name="file_size_mb" class="form-control" min="0" step="0.1"></div>
          </div>
          <div class="form-group"><label>Giới hạn lượt xem đồng thời</label><input type="number" name="max_concurrent" class="form-control" value="5" min="1"></div>
        </form>
        <div class="modal-footer">
          <button class="btn btn-primary" id="btn-submit-ebook">Lưu</button>
          <button class="btn btn-secondary" data-close="modal-ebook-form">Huỷ</button>
        </div>
      </div>
    </div>

    <!-- Start Access Modal -->
    <div class="modal" id="modal-start-access">
      <div class="modal-box">
        <div class="modal-header">
          <h2>🔓 Bắt đầu đọc Ebook</h2>
          <button class="modal-close" data-close="modal-start-access">✕</button>
        </div>
        <form id="access-form" class="modal-body">
          <div class="form-group"><label>Mã độc giả *</label><input type="text" name="reader_id" required class="form-control"></div>
          <div class="form-group"><label>Mã Ebook *</label><input type="text" name="ebook_id" required class="form-control" id="access-ebook-id"></div>
        </form>
        <div class="modal-footer">
          <button class="btn btn-primary" id="btn-submit-access">▶ Bắt đầu</button>
          <button class="btn btn-secondary" data-close="modal-start-access">Huỷ</button>
        </div>
      </div>
    </div>

    <!-- Access Logs Modal -->
    <div class="modal" id="modal-access-logs">
      <div class="modal-box modal-lg">
        <div class="modal-header">
          <h2>📊 Lịch sử truy cập Ebook</h2>
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
        { key: 'ebook_id',    label: 'Mã Ebook' },
        { key: 'source_id',   label: 'Đầu sách' },
        { key: 'format',      label: 'Định dạng' },
        { key: 'file_size_mb', label: 'Dung lượng', render: v => v ? `${v} MB` : '—' },
        { key: 'max_concurrent', label: 'Tối đa đồng thời' },
        { key: 'file_url',    label: 'URL', render: v => v ? `<a href="${v}" target="_blank" class="link">🔗 Mở</a>` : '—' },
      ],
      items,
      row => [
        { label: '▶ Đọc',   cls: 'btn-primary', onClick: r => openStartAccess(r.ebook_id) },
        { label: '✏ Sửa',  cls: 'btn-warning',  onClick: r => openEbookForm(r) },
        { label: '🗑 Xoá',  cls: 'btn-danger',   onClick: r => deleteEbook(r) },
      ]
    );
    renderPagination(document.getElementById('ebooks-pagination'), currentPage, Math.ceil(total / PAGE_SIZE),
      p => { currentPage = p; loadEbooks(); });
  } catch (err) {
    wrap.innerHTML = `<p class="text-danger">Lỗi: ${err.detail || err.message}</p>`;
  }
}

function openEbookForm(ebook) {
  const form = document.getElementById('ebook-form');
  form.reset();
  document.getElementById('ebook-form-title').textContent = ebook ? 'Sửa Ebook' : 'Thêm Ebook';
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
  if (!form.checkValidity()) { form.reportValidity(); return; }
  const data = getFormData(form);
  const id = data.ebook_id;
  delete data.ebook_id;
  if (data.file_size_mb) data.file_size_mb = parseFloat(data.file_size_mb);
  if (data.max_concurrent) data.max_concurrent = parseInt(data.max_concurrent);
  try {
    if (id) { await api.updateEbook(id, data); toast('Cập nhật ebook thành công!', 'success'); }
    else { await api.createEbook(data); toast('Thêm ebook thành công!', 'success'); }
    closeModal('modal-ebook-form');
    loadEbooks();
  } catch (err) { handleApiError(err); }
}

async function deleteEbook(e) {
  if (!confirm(`Xoá ebook #${e.ebook_id}?`)) return;
  try { await api.deleteEbook(e.ebook_id); toast('Đã xoá ebook.', 'success'); loadEbooks(); }
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
    toast(`Bắt đầu đọc! Mã log: ${res.log_id}`, 'success');
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
      <thead><tr><th>Mã log</th><th>Ebook</th><th>Độc giả</th><th>Bắt đầu</th><th>Kết thúc</th><th>Thao tác</th></tr></thead>
      <tbody>${items.map(l => `<tr>
        <td>${l.log_id}</td>
        <td>${l.ebook_id}</td>
        <td>${l.reader_id}</td>
        <td>${fmtDateTime(l.start_time)}</td>
        <td>${fmtDateTime(l.end_time)}</td>
        <td>${!l.end_time ? `<button class="btn btn-sm btn-warning" onclick="endAccessLog(${l.log_id})">■ Kết thúc</button>` : '—'}</td>
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
