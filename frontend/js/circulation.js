/**
 * circulation.js — Borrow / Return / Renew / Reserve
 */
import * as api from './api.js';
import { toast, fmtDateTime, fmtStatus, buildTable, handleApiError, openModal, closeModal, renderPagination, debounce, confirmDialog, setButtonLoading } from './utils.js';

let loansPage = 1;
let currentBranchId = '';
let currentBranchBooks = [];
let loansRequestId = 0;
let booksRequestId = 0;
const PAGE_SIZE = 20;

export async function renderCirculation(container) {
  container.innerHTML = `
    <div class="page-header">
      <h1>Mượn / trả sách</h1>
    </div>

    <div class="filter-bar">
      <label for="circulation-branch">Chi nhánh:</label>
      <select id="circulation-branch" class="form-control" style="max-width:360px">
        <option value="">Đang tải chi nhánh…</option>
      </select>
    </div>

    <div class="card mt-3">
      <div class="card-header">
        <h2>Sách tại chi nhánh</h2>
        <span id="branch-books-count"></span>
      </div>
      <div id="branch-books-wrap"></div>
    </div>

    <!-- Action Cards -->
    <div class="action-cards">
      <div class="action-card" id="card-borrow">
        <div class="action-label">Mượn sách</div>
      </div>
      <div class="action-card" id="card-return">
        <div class="action-label">Trả sách</div>
      </div>
      <div class="action-card" id="card-renew">
        <div class="action-label">Gia hạn</div>
      </div>
      <div class="action-card" id="card-reserve">
        <div class="action-label">Đặt trước</div>
      </div>
    </div>

    <!-- Active Loans Table -->
    <div class="card mt-3">
      <div class="card-header">
        <h2>Danh sach dang muon</h2>
        <div style="display:flex;gap:8px;align-items:center">
          <input type="text" id="loans-filter-reader" placeholder="Mã hội viên…" class="form-control" style="width:160px">
          <button class="btn btn-secondary" id="btn-loans-search">Loc</button>
          <button class="btn btn-ghost" id="btn-loans-clear">Xóa</button>
        </div>
      </div>
      <div id="active-loans-wrap"></div>
      <div class="pagination" id="loans-pagination"></div>
    </div>

    <!-- ── MODALS ── -->

    <!-- Borrow Modal -->
    <div class="modal" id="modal-borrow">
      <div class="modal-box">
        <div class="modal-header">
          <h2>Mượn sách</h2>
          <button class="modal-close" data-close="modal-borrow">✕</button>
        </div>
        <form id="borrow-form" class="modal-body">
          <div class="form-group">
            <label>Mã hội viên *</label>
            <input type="number" name="reader_id" required min="1" class="form-control" placeholder="Nhập mã hội viên">
          </div>
          <div class="form-group">
            <label>Bản sách tại chi nhánh đang chọn *</label>
            <select name="hard_book_id" required class="form-control"></select>
          </div>
          <div class="form-group">
            <label>Số ngày mượn</label>
            <input type="number" name="days" class="form-control" value="14" min="1" max="60">
          </div>
        </form>
        <div class="modal-footer">
          <button class="btn btn-primary" id="btn-submit-borrow">Xác nhận mượn</button>
          <button class="btn btn-secondary" data-close="modal-borrow">Huỷ</button>
        </div>
      </div>
    </div>

    <!-- Return Modal -->
    <div class="modal" id="modal-return">
      <div class="modal-box">
        <div class="modal-header">
          <h2>Trả sách</h2>
          <button class="modal-close" data-close="modal-return">✕</button>
        </div>
        <form id="return-form" class="modal-body">
          <div class="form-group">
            <label>Mã phiếu mượn *</label>
            <input type="number" name="loan_id" required min="1" class="form-control" placeholder="Nhập mã lượt mượn">
          </div>
          <div class="form-group">
            <label>Tình trạng sách khi trả *</label>
            <select name="return_condition" required class="form-control">
              <option value="Tot">Tốt (không phạt)</option>
              <option value="Hong">Hỏng (nhân viên quyết định mức phạt)</option>
              <option value="Mat">Mất sách (phạt 100% giá bìa)</option>
            </select>
          </div>
          <div class="form-group">
            <label>Ngay tra thực tế</label>
            <input type="datetime-local" name="returned_at" class="form-control">
          </div>
          <div class="alert alert-info" id="return-info" style="display:none"></div>
        </form>
        <div class="modal-footer">
          <button class="btn btn-primary" id="btn-submit-return">Xác nhận trả</button>
          <button class="btn btn-secondary" data-close="modal-return">Huỷ</button>
        </div>
      </div>
    </div>

    <!-- Renew Modal -->
    <div class="modal" id="modal-renew">
      <div class="modal-box">
        <div class="modal-header">
          <h2>Gia hạn mượn</h2>
          <button class="modal-close" data-close="modal-renew">✕</button>
        </div>
        <form id="renew-form" class="modal-body">
          <div class="form-group">
            <label>Mã phiếu mượn *</label>
            <input type="number" name="loan_id" required readonly min="1" class="form-control">
          </div>
          <div class="form-group">
            <label>Số ngày gia hạn</label>
            <input type="number" name="extension_days" class="form-control" value="7" min="1" max="30">
          </div>
        </form>
        <div class="modal-footer">
          <button class="btn btn-primary" id="btn-submit-renew">Xác nhận gia hạn</button>
          <button class="btn btn-secondary" data-close="modal-renew">Huỷ</button>
        </div>
      </div>
    </div>

    <!-- Reserve Modal -->
    <div class="modal" id="modal-reserve">
      <div class="modal-box">
        <div class="modal-header">
          <h2>Đặt trước sách</h2>
          <button class="modal-close" data-close="modal-reserve">✕</button>
        </div>
        <form id="reserve-form" class="modal-body">
          <div class="form-group">
            <label>Mã hội viên *</label>
            <input type="number" name="reader_id" required min="1" class="form-control">
          </div>
          <div class="form-group">
            <label>Bản sách sẵn sàng tại chi nhánh *</label>
            <select name="hard_book_id" required class="form-control"></select>
          </div>
          <div class="form-group">
            <label>Số ngày giữ chỗ (tối đa 7)</label>
            <input type="number" name="days" class="form-control" value="3" min="1" max="7">
          </div>
        </form>
        <div class="modal-footer">
          <button class="btn btn-primary" id="btn-submit-reserve">Xác nhận đặt trước</button>
          <button class="btn btn-secondary" data-close="modal-reserve">Huỷ</button>
        </div>
      </div>
    </div>
  `;

  setupModalClosers(container);

  document.getElementById('card-borrow').addEventListener('click', () => openBorrowForm());
  document.getElementById('card-return').addEventListener('click', () => {
    const form = document.getElementById('return-form');
    form.reset();
    form.elements['loan_id'].readOnly = false;
    openModal('modal-return');
  });
  document.getElementById('card-renew').addEventListener('click', () => openModal('modal-renew'));
  document.getElementById('card-reserve').addEventListener('click', () => openReserveForm());

  document.getElementById('btn-submit-borrow').addEventListener('click',  submitBorrow);
  document.getElementById('btn-submit-return').addEventListener('click',  submitReturn);
  document.getElementById('btn-submit-renew').addEventListener('click',   submitRenew);
  document.getElementById('btn-submit-reserve').addEventListener('click', submitReserve);

  // Warn on Lost condition
  document.getElementById('return-form').elements['return_condition'].addEventListener('change', e => {
    const info = document.getElementById('return-info');
    if (e.target.value === 'Mat') {
      info.style.display = '';
      info.innerHTML = 'Sách mất: hệ thống sẽ tự phạt <strong>100% giá bìa</strong>. Không tính thêm phạt quá hạn.';
    } else if (e.target.value === 'Hong') {
      info.style.display = '';
      info.innerHTML = 'Sách hỏng: <strong>nhân viên tự quyết định</strong> mức phạt trong mục Tiền phạt.';
    } else {
      info.style.display = 'none';
    }
  });

  document.getElementById('btn-loans-search').addEventListener('click', doLoansSearch);
  document.getElementById('btn-loans-clear').addEventListener('click',  clearLoansSearch);
  document.getElementById('loans-filter-reader').addEventListener('keydown', e => { if (e.key === 'Enter') doLoansSearch(); });

  document.getElementById('circulation-branch').addEventListener('change', e => {
    currentBranchId = e.target.value;
    loansPage = 1;
    loadBranchBooks();
    loadActiveLoans();
  });
  await loadBranches();
  await Promise.all([loadBranchBooks(), loadActiveLoans()]);
}

function setupModalClosers(root) {
  root.querySelectorAll('[data-close]').forEach(btn => btn.addEventListener('click', () => closeModal(btn.dataset.close)));
  root.querySelectorAll('.modal').forEach(m => m.addEventListener('click', e => { if (e.target === m) closeModal(m.id); }));
}

let loansFilterReader = '';
function doLoansSearch() {
  loansFilterReader = document.getElementById('loans-filter-reader').value.trim();
  loansPage = 1;
  loadActiveLoans();
}
function clearLoansSearch() {
  document.getElementById('loans-filter-reader').value = '';
  loansFilterReader = '';
  loansPage = 1;
  loadActiveLoans();
}

async function loadBranches() {
  const select = document.getElementById('circulation-branch');
  try {
    const data = await api.getBranches({ limit: 100 });
    const branches = data?.items ?? data ?? [];
    if (!branches.length) {
      select.innerHTML = '<option value="">Chưa có chi nhánh</option>';
      return;
    }
    select.innerHTML = branches.map(branch =>
      `<option value="${branch.id}">${branch.name}</option>`
    ).join('');
    currentBranchId = String(branches[0].id);
    select.value = currentBranchId;
  } catch (err) {
    select.innerHTML = '<option value="">Không tải được chi nhánh</option>';
    handleApiError(err);
  }
}

async function loadBranchBooks() {
  const wrap = document.getElementById('branch-books-wrap');
  const count = document.getElementById('branch-books-count');
  const branchId = currentBranchId;
  if (!branchId) {
    currentBranchBooks = [];
    wrap.innerHTML = '<p class="empty-state">Chọn chi nhánh để xem bản sách.</p>';
    count.textContent = '';
    updateCopyOptions();
    return;
  }
  const requestId = ++booksRequestId;
  wrap.innerHTML = '<div class="loading-spinner"><div></div><div></div><div></div></div>';
  try {
    const data = await api.getHardBooks({ branch_id: branchId, limit: 100 });
    if (requestId !== booksRequestId || branchId !== currentBranchId) return;
    currentBranchBooks = data?.items ?? data ?? [];
    count.textContent = `Tổng ${data?.total ?? currentBranchBooks.length} bản`;
    buildTable(wrap, [
      { key: 'id', label: 'Mã bản sách' },
      { key: 'source', label: 'Tên sách', render: source => source?.title || '—' },
      { key: 'source', label: 'Tác giả', render: source => source?.author || '—' },
      { key: 'status', label: 'Tình trạng', render: status => fmtStatus(status) },
    ], currentBranchBooks, book =>
      book.status === 'SanSang' || book.status === 'DangCho'
        ? [{ label: book.status === 'DangCho' ? 'Nhận sách' : 'Mượn', cls: 'btn-primary', onClick: row => openBorrowForm(row.id) }]
        : []);
    updateCopyOptions();
  } catch (err) {
    if (requestId !== booksRequestId) return;
    currentBranchBooks = [];
    wrap.innerHTML = `<p class="text-danger">Lỗi: ${err.detail || err.message}</p>`;
    handleApiError(err);
  }
}

function updateCopyOptions() {
  const borrowSelect = document.querySelector('#borrow-form [name="hard_book_id"]');
  const reserveSelect = document.querySelector('#reserve-form [name="hard_book_id"]');
  const copies = currentBranchBooks.filter(book =>
    book.status === 'SanSang' || book.status === 'DangCho');
  borrowSelect.innerHTML = copies.length
    ? copies.map(book => `<option value="${book.id}">${book.id} — ${book.source?.title || 'Chưa rõ tên'} (${book.status})</option>`).join('')
    : '<option value="">Chi nhánh chưa có bản sách khả dụng</option>';
  const reservable = currentBranchBooks.filter(book => book.status === 'SanSang');
  reserveSelect.innerHTML = reservable.length
    ? reservable.map(book => `<option value="${book.id}">${book.id} — ${book.source?.title || 'Chưa rõ tên'}</option>`).join('')
    : '<option value="">Không có bản sách sẵn sàng để đặt trước</option>';
}

function openBorrowForm(hardBookId = null) {
  updateCopyOptions();
  const select = document.querySelector('#borrow-form [name="hard_book_id"]');
  if (hardBookId !== null) select.value = String(hardBookId);
  if (!currentBranchId || !select.value) {
    toast('Chi nhánh này chưa có bản sách có thể mượn.', 'error');
    return;
  }
  openModal('modal-borrow');
}

function openReserveForm() {
  updateCopyOptions();
  const select = document.querySelector('#reserve-form [name="hard_book_id"]');
  if (!currentBranchId || !select.value) {
    toast('Chi nhánh này chưa có bản sách sẵn sàng để đặt trước.', 'error');
    return;
  }
  openModal('modal-reserve');
}

async function loadActiveLoans() {
  const wrap = document.getElementById('active-loans-wrap');
  const requestId = ++loansRequestId;
  wrap.innerHTML = '<div class="loading-spinner"><div></div><div></div><div></div></div>';
  try {
    const params = { skip: (loansPage - 1) * PAGE_SIZE, limit: PAGE_SIZE };
    if (currentBranchId) params.branch_id = currentBranchId;
    if (loansFilterReader) params.reader_id = loansFilterReader;
    const data = await api.getActiveLoans(params);
    if (requestId !== loansRequestId) return;
    const items = data?.items ?? data ?? [];
    const total = data?.total ?? items.length;
    buildTable(wrap,
      [
        { key: 'id',          label: 'Mã mượn' },
        { key: 'source_title',label: 'Tên sách' },
        { key: 'hard_book_id',label: 'Mã bản sách' },
        { key: 'reader_id',   label: 'Mã hội viên' },
        { key: 'borrowed_at', label: 'Ngày mượn', render: v => fmtDateTime(v) },
        { key: 'due_at',      label: 'Hạn trả',   render: v =>
          `<span class="${new Date(v) < new Date() ? 'text-danger fw-bold' : ''}">${fmtDateTime(v)}</span>` },
        { key: 'renewals_count', label: 'Số lần gia hạn' },
      ],
      items,
      row => [
        { label: 'Trả', cls: 'btn-primary', onClick: r => prefillReturn(r.id) },
        { label: 'Gia hạn', cls: 'btn-secondary', onClick: r => prefillRenew(r.id) },
      ]
    );
    renderPagination(document.getElementById('loans-pagination'), loansPage, Math.ceil(total / PAGE_SIZE),
      p => { loansPage = p; loadActiveLoans(); });
  } catch (err) {
    if (requestId !== loansRequestId) return;
    wrap.innerHTML = `<p class="text-danger">Lỗi: ${err.detail || err.message}</p>`;
  }
}

function prefillReturn(loanId) {
  const form = document.getElementById('return-form');
  form.reset();
  form.elements['loan_id'].value = loanId;
  form.elements['loan_id'].readOnly = true;
  document.getElementById('return-info').style.display = 'none';
  openModal('modal-return');
}
function prefillRenew(loanId) {
  document.getElementById('renew-form').elements['loan_id'].value = loanId;
  openModal('modal-renew');
}

async function submitBorrow() {
  const form = document.getElementById('borrow-form');
  const btn = document.getElementById('btn-submit-borrow');
  if (!form.checkValidity()) { form.reportValidity(); return; }
  const data = {
    reader_id: parseInt(form.elements['reader_id'].value),
    hard_book_id: parseInt(form.elements['hard_book_id'].value),
    days: parseInt(form.elements['days'].value) || 14,
  };
  setButtonLoading(btn, true);
  try {
    const res = await api.borrowBook(data);
    toast(`Muon sach thành công! Mã phiếu: ${res.id}`, 'success');
    closeModal('modal-borrow');
    form.reset();
    await Promise.all([loadActiveLoans(), loadBranchBooks()]);
  } catch (err) { handleApiError(err); }
  finally { setButtonLoading(btn, false); }
}

async function submitReturn() {
  const form = document.getElementById('return-form');
  const btn = document.getElementById('btn-submit-return');
  if (!form.checkValidity()) { form.reportValidity(); return; }
  const data = {
    loan_id: parseInt(form.elements['loan_id'].value),
    return_condition: form.elements['return_condition'].value,
  };
  const retDate = form.elements['returned_at'].value;
  if (retDate) data.returned_at = retDate;
  setButtonLoading(btn, true);
  try {
    const res = await api.returnBook(data);
    let msg = 'Tra sach thành công!';
    if (res.fine_generated) msg += ` Phạt: ${res.fine_generated.fine_type} — ${Number(res.fine_generated.amount).toLocaleString('vi-VN')} ₫`;
    toast(msg, 'success', 5000);
    closeModal('modal-return');
    form.reset();
    await Promise.all([loadActiveLoans(), loadBranchBooks()]);
  } catch (err) { handleApiError(err); }
  finally { setButtonLoading(btn, false); }
}

async function submitRenew() {
  const form = document.getElementById('renew-form');
  const btn = document.getElementById('btn-submit-renew');
  if (!form.checkValidity()) { form.reportValidity(); return; }
  const data = {
    loan_id: parseInt(form.elements['loan_id'].value),
    extension_days: parseInt(form.elements['extension_days'].value) || 7,
  };
  setButtonLoading(btn, true);
  try {
    const res = await api.renewLoan(data);
    toast(`Gia han thành công! Hạn mới: ${fmtDateTime(res.new_due_at)}`, 'success');
    closeModal('modal-renew');
    loadActiveLoans();
  } catch (err) { handleApiError(err); }
  finally { setButtonLoading(btn, false); }
}

async function submitReserve() {
  const form = document.getElementById('reserve-form');
  const btn = document.getElementById('btn-submit-reserve');
  if (!form.checkValidity()) { form.reportValidity(); return; }
  const data = {
    reader_id: parseInt(form.elements['reader_id'].value),
    hard_book_id: parseInt(form.elements['hard_book_id'].value),
    days: parseInt(form.elements['days'].value) || 3,
  };
  setButtonLoading(btn, true);
  try {
    const res = await api.reserveBook(data);
    toast(`Dat truoc thành công! Mã: ${res.id}`, 'success');
    closeModal('modal-reserve');
    form.reset();
    await loadBranchBooks();
  } catch (err) { handleApiError(err); }
  finally { setButtonLoading(btn, false); }
}
