/**
 * branches.js — Branch management
 */
import * as api from './api.js';
import { toast, buildTable, handleApiError, openModal, closeModal, getFormData, renderPagination } from './utils.js';

let currentPage = 1;
const PAGE_SIZE = 15;

export async function renderBranches(container) {
  container.innerHTML = `
    <div class="page-header">
      <h1>🏢 Quản lý chi nhánh</h1>
      <button class="btn btn-primary" id="btn-add-branch">+ Thêm chi nhánh</button>
    </div>
    <div id="branches-table-wrap"></div>
    <div class="pagination" id="branches-pagination"></div>

    <!-- Branch Form Modal -->
    <div class="modal" id="modal-branch-form">
      <div class="modal-box">
        <div class="modal-header">
          <h2 id="branch-form-title">Thêm chi nhánh</h2>
          <button class="modal-close" data-close="modal-branch-form">✕</button>
        </div>
        <form id="branch-form" class="modal-body">
          <input type="hidden" name="branch_id">
          <div class="form-group"><label>Tên chi nhánh *</label><input type="text" name="name" required class="form-control"></div>
          <div class="form-group"><label>Địa chỉ</label><input type="text" name="address" class="form-control"></div>
          <div class="form-group"><label>Điện thoại</label><input type="text" name="phone" class="form-control"></div>
          <div class="form-group"><label>Email</label><input type="email" name="email" class="form-control"></div>
        </form>
        <div class="modal-footer">
          <button class="btn btn-primary" id="btn-submit-branch">Lưu</button>
          <button class="btn btn-secondary" data-close="modal-branch-form">Huỷ</button>
        </div>
      </div>
    </div>
  `;

  setupModalClosers(container);
  document.getElementById('btn-add-branch').addEventListener('click', () => openBranchForm(null));
  document.getElementById('btn-submit-branch').addEventListener('click', submitBranchForm);

  await loadBranches();
}

function setupModalClosers(root) {
  root.querySelectorAll('[data-close]').forEach(btn => btn.addEventListener('click', () => closeModal(btn.dataset.close)));
  root.querySelectorAll('.modal').forEach(m => m.addEventListener('click', e => { if (e.target === m) closeModal(m.id); }));
}

async function loadBranches() {
  const wrap = document.getElementById('branches-table-wrap');
  wrap.innerHTML = '<div class="loading-spinner"><div></div><div></div><div></div></div>';
  try {
    const params = { skip: (currentPage - 1) * PAGE_SIZE, limit: PAGE_SIZE };
    const data = await api.getBranches(params);
    const items = data?.items ?? data ?? [];
    const total = data?.total ?? items.length;
    buildTable(wrap,
      [
        { key: 'branch_id', label: 'Mã' },
        { key: 'name',      label: 'Tên chi nhánh' },
        { key: 'address',   label: 'Địa chỉ' },
        { key: 'phone',     label: 'SĐT' },
        { key: 'email',     label: 'Email' },
      ],
      items,
      row => [
        { label: '✏ Sửa', cls: 'btn-warning', onClick: r => openBranchForm(r) },
        { label: '🗑 Xoá', cls: 'btn-danger',  onClick: r => deleteBranch(r) },
      ]
    );
    renderPagination(document.getElementById('branches-pagination'), currentPage, Math.ceil(total / PAGE_SIZE),
      p => { currentPage = p; loadBranches(); });
  } catch (err) {
    wrap.innerHTML = `<p class="text-danger">Lỗi: ${err.detail || err.message}</p>`;
  }
}

function openBranchForm(branch) {
  const form = document.getElementById('branch-form');
  form.reset();
  document.getElementById('branch-form-title').textContent = branch ? 'Sửa chi nhánh' : 'Thêm chi nhánh';
  if (branch) {
    Object.entries(branch).forEach(([k, v]) => {
      const el = form.elements[k];
      if (el && v !== null && v !== undefined) el.value = v;
    });
  }
  openModal('modal-branch-form');
}

async function submitBranchForm() {
  const form = document.getElementById('branch-form');
  if (!form.checkValidity()) { form.reportValidity(); return; }
  const data = getFormData(form);
  const id = data.branch_id;
  delete data.branch_id;
  try {
    if (id) {
      await api.updateBranch(id, data);
      toast('Cập nhật chi nhánh thành công!', 'success');
    } else {
      await api.createBranch(data);
      toast('Thêm chi nhánh thành công!', 'success');
    }
    closeModal('modal-branch-form');
    loadBranches();
  } catch (err) { handleApiError(err); }
}

async function deleteBranch(b) {
  if (!confirm(`Xoá chi nhánh "${b.name}"?`)) return;
  try {
    await api.deleteBranch(b.branch_id);
    toast('Đã xoá chi nhánh.', 'success');
    loadBranches();
  } catch (err) { handleApiError(err); }
}
