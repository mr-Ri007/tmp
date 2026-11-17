/**
 * sources.js — Book catalog management (Sources + Hard books)
 */
import * as api from './api.js';
import { toast, fmtMoney, fmtStatus, buildTable, eyeIconMarkup, handleApiError, openModal, closeModal, getFormData, renderPagination, debounce, confirmDialog, setButtonLoading } from './utils.js';

let currentPage = 1;
const PAGE_SIZE = 15;
let searchQuery = { query: '', genre: '' };

export async function renderSources(container) {
  container.innerHTML = `
    <div class="page-header">
      <h1>Danh mục sách</h1>
      <div class="page-header-actions">
        <button class="btn btn-primary" id="btn-add-source">Thêm đầu sách</button>
      </div>
    </div>
    <div class="filter-bar">
      <input type="text" id="src-search" placeholder="Tìm theo tên, tác giả…" class="form-control" style="max-width:320px">
      <input type="text" id="src-genre" placeholder="Thể loại" class="form-control" style="max-width:160px">
      <button class="btn btn-secondary" id="btn-src-search">Tìm</button>
      <button class="btn btn-ghost" id="btn-src-clear">Xóa bộ lọc</button>
    </div>
    <div id="sources-table-wrap"></div>
    <div class="pagination" id="sources-pagination"></div>

    <!-- Source Detail Modal -->
    <div class="modal" id="modal-source-detail">
      <div class="modal-box modal-lg">
        <div class="modal-header">
          <h2 id="modal-source-title">Chi tiết sách</h2>
          <button class="modal-close" data-close="modal-source-detail">X</button>
        </div>
        <div class="modal-body" id="source-detail-body">Đang tải…</div>
        <div class="modal-footer">
          <button class="btn btn-edit" id="btn-edit-source">Sửa</button>
          <button class="btn btn-secondary" data-close="modal-source-detail">Đóng</button>
        </div>
      </div>
    </div>

    <!-- Source Form Modal -->
    <div class="modal" id="modal-source-form">
      <div class="modal-box">
        <div class="modal-header">
          <h2 id="source-form-title">Thêm đầu sách</h2>
          <button class="modal-close" data-close="modal-source-form">X</button>
        </div>
        <form id="source-form" class="modal-body">
          <input type="hidden" name="id">
          <div class="form-group"><label>Tiêu đề *</label><input type="text" name="title" required class="form-control"></div>
          <div class="form-group"><label>Tác giả *</label><input type="text" name="author" required class="form-control"></div>
          <div class="form-row">
            <div class="form-group"><label>Thể loại</label><input type="text" name="genre" class="form-control"></div>
            <div class="form-group"><label>Nam xuat ban</label><input type="number" name="publication_year" class="form-control" min="1000" max="2100"></div>
          </div>
          <div class="form-row">
            <div class="form-group"><label>Gia bia (đ) *</label><input type="number" name="price" required class="form-control" min="0" step="1000"></div>
            <div class="form-group"><label>Số trang</label><input type="number" name="page_count" class="form-control" min="1"></div>
          </div>
        </form>
        <div class="modal-footer">
          <button class="btn btn-primary" id="btn-submit-source">Lưu</button>
          <button class="btn btn-delete" id="btn-delete-from-form" style="display:none">Xóa</button>
          <button class="btn btn-secondary" data-close="modal-source-form">Hủy</button>
        </div>
      </div>
    </div>

    <!-- Hard books detail panel -->
    <div class="modal" id="modal-hard-books">
      <div class="modal-box modal-lg">
        <div class="modal-header">
          <h2>Các chi nhánh có sách</h2>
          <button class="modal-close" data-close="modal-hard-books">X</button>
        </div>
        <div class="modal-body" id="hard-books-body">Đang tải…</div>
        <div class="modal-footer">
          <button class="btn btn-secondary" data-close="modal-hard-books">Đóng</button>
        </div>
      </div>
    </div>
  `;

  setupModalClosers(container);
  document.getElementById('btn-add-source').addEventListener('click', () => openSourceForm(null));
  document.getElementById('btn-src-search').addEventListener('click', doSearch);
  document.getElementById('btn-src-clear').addEventListener('click', clearSearch);
  const debouncedSearch = debounce(doSearch, 400);
  document.getElementById('src-search').addEventListener('input', debouncedSearch);
  document.getElementById('src-genre').addEventListener('input', debouncedSearch);
  document.getElementById('src-search').addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });
  document.getElementById('btn-submit-source').addEventListener('click', submitSourceForm);
  document.getElementById('btn-delete-from-form').addEventListener('click', deleteCurrentSource);

  await loadSources();
}

function setupModalClosers(root) {
  root.querySelectorAll('[data-close]').forEach(btn => {
    btn.addEventListener('click', () => closeModal(btn.dataset.close));
  });
  root.querySelectorAll('.modal').forEach(m => {
    m.addEventListener('click', e => { if (e.target === m) closeModal(m.id); });
  });
}

function doSearch() {
  searchQuery.query = document.getElementById('src-search').value.trim();
  searchQuery.genre = document.getElementById('src-genre').value.trim();
  currentPage = 1;
  loadSources();
}

function clearSearch() {
  document.getElementById('src-search').value = '';
  document.getElementById('src-genre').value = '';
  searchQuery = { query: '', genre: '' };
  currentPage = 1;
  loadSources();
}

async function loadSources() {
  const wrap = document.getElementById('sources-table-wrap');
  wrap.innerHTML = '<div class="loading-spinner"><div></div><div></div><div></div></div>';
  try {
    const params = { skip: (currentPage - 1) * PAGE_SIZE, limit: PAGE_SIZE };
    if (searchQuery.query) params.query = searchQuery.query;
    if (searchQuery.genre) params.genre = searchQuery.genre;
    const data = await api.getSources(params);
    const items = data?.items ?? data ?? [];
    const total = data?.total ?? items.length;
    const totalPages = Math.ceil(total / PAGE_SIZE);

    buildTable(wrap,
      [
        { key: 'id', label: 'ID' },
        { key: 'title',     label: 'Tiêu đề' },
        { key: 'author',    label: 'Tác giả' },
        { key: 'genre',     label: 'Thể loại' },
        { key: 'publication_year', label: 'Năm' },
        { key: 'page_count', label: 'Số trang' },
        { key: 'price',     label: 'Giá bìa', render: v => fmtMoney(v) },
      ],
      items,
      row => [
        { html: eyeIconMarkup(), ariaLabel: 'Chi tiết', title: 'Chi tiết', cls: 'btn-icon', onClick: r => openSourceDetail(r.id) },
        { label: 'Chi nhánh', cls: 'btn-secondary', onClick: r => openHardBooks(r.id, r.title) },
        { label: 'Sửa', cls: 'btn-edit', onClick: r => openSourceForm(r) },
      ]
    );

    renderPagination(
      document.getElementById('sources-pagination'),
      currentPage, totalPages,
      p => { currentPage = p; loadSources(); }
    );
  } catch (err) {
    wrap.innerHTML = `<p class="text-danger">Lỗi: ${err.detail || err.message}</p>`;
    handleApiError(err);
  }
}

async function openSourceDetail(id) {
  openModal('modal-source-detail');
  const body = document.getElementById('source-detail-body');
  body.innerHTML = 'Đang tải…';
  try {
    const s = await api.getSource(id);
    document.getElementById('modal-source-title').textContent = s.title;
    body.innerHTML = `
      <div class="detail-grid">
        <div class="detail-item"><span class="detail-label">ID</span><span>${s.id}</span></div>
        <div class="detail-item"><span class="detail-label">Tác giả</span><span>${s.author}</span></div>
        <div class="detail-item"><span class="detail-label">Thể loại</span><span>${s.genre || '—'}</span></div>
        <div class="detail-item"><span class="detail-label">Năm xuất bản</span><span>${s.publication_year || '—'}</span></div>
        <div class="detail-item"><span class="detail-label">Số trang</span><span>${s.page_count || '—'}</span></div>
        <div class="detail-item"><span class="detail-label">Giá bìa</span><span class="text-primary fw-bold">${fmtMoney(s.price)}</span></div>
      </div>
    `;
    document.getElementById('btn-edit-source').onclick = () => { closeModal('modal-source-detail'); openSourceForm(s); };
  } catch (err) { body.innerHTML = `<p class="text-danger">${err.detail}</p>`; }
}

async function openHardBooks(sourceId, title) {
  openModal('modal-hard-books');
  const body = document.getElementById('hard-books-body');
  body.innerHTML = 'Đang tải…';
  document.querySelector('#modal-hard-books h2').textContent = `Các chi nhánh có sách: ${title}`;
  try {
    const data = await api.getHardBooks({ source_id: sourceId, limit: 100 });
    const items = data?.items ?? data ?? [];
    if (!items.length) { body.innerHTML = '<p class="empty-state">Chưa có sách tại chi nhánh này.</p>'; return; }
    body.innerHTML = `<table class="data-table">
      <thead><tr><th>Mã bản sách</th><th>Chi nhánh</th><th>Trạng thái</th></tr></thead>
      <tbody>${items.map(h => `<tr>
        <td>${h.id}</td>
        <td>${h.branch?.name || h.branch_id}</td>
        <td>${fmtStatus(h.status)}</td>
      </tr>`).join('')}</tbody></table>`;
  } catch (err) { body.innerHTML = `<p class="text-danger">${err.detail}</p>`; }
}

let currentEditSource = null;

function openSourceForm(source) {
  const form = document.getElementById('source-form');
  const delBtn = document.getElementById('btn-delete-from-form');
  form.reset();
  currentEditSource = source || null;
  document.getElementById('source-form-title').textContent = source ? 'Sửa đầu sách' : 'Thêm đầu sách';
  delBtn.style.display = source ? 'inline-block' : 'none';
  if (source) {
    Object.entries(source).forEach(([k, v]) => {
      const el = form.elements[k];
      if (el && v !== null && v !== undefined) el.value = v;
    });
  }
  openModal('modal-source-form');
}

async function deleteCurrentSource() {
  if (!currentEditSource) return;
  const ok = await confirmDialog(`Xóa đầu sách "<b>${currentEditSource.title}</b>"?`);
  if (!ok) return;
  try {
    await api.deleteSource(currentEditSource.id);
    toast('Đã xóa đầu sách.', 'success');
    closeModal('modal-source-form');
    currentEditSource = null;
    loadSources();
  } catch (err) { handleApiError(err); }
}

async function submitSourceForm() {
  const form = document.getElementById('source-form');
  const btn = document.getElementById('btn-submit-source');
  if (!form.checkValidity()) { form.reportValidity(); return; }
  const data = getFormData(form);
  const id = data.id;
  delete data.id;
  if (data.publication_year) data.publication_year = parseInt(data.publication_year);
  if (data.page_count) data.page_count = parseInt(data.page_count);
  if (data.price) data.price = parseFloat(data.price);
  setButtonLoading(btn, true);
  try {
    if (id) {
      await api.updateSource(id, data);
      toast('Cập nhật đầu sách thành công!', 'success');
    } else {
      await api.createSource(data);
      toast('Thêm đầu sách thành công!', 'success');
    }
    closeModal('modal-source-form');
    currentEditSource = null;
    loadSources();
  } catch (err) { handleApiError(err); }
  finally { setButtonLoading(btn, false); }
}
