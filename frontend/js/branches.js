/**
 * branches.js — Branch management
 */
import * as api from './api.js';
import { toast, buildTable, handleApiError, openModal, closeModal, getFormData, renderPagination, confirmDialog, setButtonLoading } from './utils.js';

let currentPage = 1;
const PAGE_SIZE = 15;
let currentEditBranch = null;

export async function renderBranches(container) {
  container.innerHTML = `
    <div class="page-header">
      <h1>Quản lý chi nhánh</h1>
      <div class="page-header-actions">
        <button class="btn btn-primary" id="btn-add-branch">Thêm chi nhánh</button>
      </div>
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
          <input type="hidden" name="id">
          <div class="form-group"><label>Tên chi nhánh *</label><input type="text" name="name" required class="form-control"></div>
          <div class="form-group"><label>Địa chỉ *</label><input type="text" name="address" required class="form-control"></div>
        </form>
        <div class="modal-footer">
          <button class="btn btn-primary" id="btn-submit-branch">Lưu</button>
          <button class="btn btn-delete" id="btn-delete-branch-from-form" style="display:none">Xóa</button>
          <button class="btn btn-secondary" data-close="modal-branch-form">Hủy</button>
        </div>
      </div>
    </div>
  `;

  setupModalClosers(container);
  document.getElementById('btn-add-branch').addEventListener('click', () => openBranchForm(null));
  document.getElementById('btn-submit-branch').addEventListener('click', submitBranchForm);
  document.getElementById('btn-delete-branch-from-form').addEventListener('click', deleteCurrentBranch);

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
        { key: 'id',        label: 'Mã' },
        { key: 'name',      label: 'Tên chi nhánh' },
        { key: 'address',   label: 'Địa chỉ' },
      ],
      items,
      row => [
        { label: 'Sửa', cls: 'btn-edit', onClick: r => openBranchForm(r) },
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
  currentEditBranch = branch || null;
  document.getElementById('btn-delete-branch-from-form').style.display = branch ? 'inline-flex' : 'none';
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
  const btn = document.getElementById('btn-submit-branch');
  if (!form.checkValidity()) { form.reportValidity(); return; }
  const data = getFormData(form);
  const id = data.id;
  delete data.id;
  setButtonLoading(btn, true);
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
  finally { setButtonLoading(btn, false); }
}

async function deleteCurrentBranch() {
  const b = currentEditBranch;
  if (!b) return;
  const confirmed = await confirmDialog(`Xóa chi nhánh "<b>${b.name}</b>"?`);
  if (!confirmed) return;
  try {
    await api.deleteBranch(b.id);
    toast('Đã xóa chi nhánh.', 'success');
    currentEditBranch = null;
    closeModal('modal-branch-form');
    loadBranches();
  } catch (err) { handleApiError(err); }
}
