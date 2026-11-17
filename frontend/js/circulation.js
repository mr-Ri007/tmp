/**
 * circulation.js — Borrow / Return / Renew / Reserve
 */
import * as api from './api.js';
import { toast, fmtDate, fmtStatus, buildTable, handleApiError, openModal, closeModal, renderPagination } from './utils.js';

let loansPage = 1;
const PAGE_SIZE = 20;

export async function renderCirculation(container) {
  container.innerHTML = `
    <div class="page-header">
      <h1>🔄 Mượn / Trả sách</h1>
    </div>

    <!-- Action Cards -->
    <div class="action-cards">
      <div class="action-card" id="card-borrow">
        <div class="action-icon">📥</div>
        <div class="action-label">Mượn sách</div>
      </div>
      <div class="action-card" id="card-return">
        <div class="action-icon">📤</div>
        <div class="action-label">Trả sách</div>
      </div>
      <div class="action-card" id="card-renew">
        <div class="action-icon">🔁</div>
        <div class="action-label">Gia hạn</div>
      </div>
      <div class="action-card" id="card-reserve">
        <div class="action-icon">📌</div>
        <div class="action-label">Đặt trước</div>
      </div>
    </div>

    <!-- Active Loans Table -->
    <div class="card mt-3">
      <div class="card-header">
        <h2>📋 Danh sách đang mượn</h2>
        <div style="display:flex;gap:8px;align-items:center">
          <input type="text" id="loans-filter-reader" placeholder="Mã bạn đọc…" class="form-control" style="width:160px">
          <button class="btn btn-secondary" id="btn-loans-search">🔍 Lọc</button>
          <button class="btn btn-ghost" id="btn-loans-clear">✕</button>
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
          <h2>📥 Mượn sách</h2>
          <button class="modal-close" data-close="modal-borrow">✕</button>
        </div>
        <form id="borrow-form" class="modal-body">
          <div class="form-group">
            <label>Mã độc giả *</label>
            <input type="text" name="reader_id" required class="form-control" placeholder="VD: R001">
          </div>
          <div class="form-group">
            <label>Mã sách vật lý *</label>
            <input type="text" name="hard_book_id" required class="form-control" placeholder="VD: HB001">
          </div>
          <div class="form-group">
            <label>Số ngày mượn</label>
            <input type="number" name="days" class="form-control" value="14" min="1" max="90">
          </div>
        </form>
        <div class="modal-footer">
          <button class="btn btn-primary" id="btn-submit-borrow">✔ Xác nhận mượn</button>
          <button class="btn btn-secondary" data-close="modal-borrow">Huỷ</button>
        </div>
      </div>
    </div>

    <!-- Return Modal -->
    <div class="modal" id="modal-return">
      <div class="modal-box">
        <div class="modal-header">
          <h2>📤 Trả sách</h2>
          <button class="modal-close" data-close="modal-return">✕</button>
        </div>
        <form id="return-form" class="modal-body">
          <div class="form-group">
            <label>Mã phiếu mượn *</label>
            <input type="text" name="loan_id" required class="form-control" placeholder="VD: 1">
          </div>
          <div class="form-group">
            <label>Tình trạng sách khi trả *</label>
            <select name="return_condition" required class="form-control">
              <option value="Tot">Tốt (không phạt)</option>
              <option value="HongNhe">Hỏng nhẹ (nhân viên quyết định)</option>
              <option value="HongNang">Hỏng nặng (nhân viên quyết định)</option>
              <option value="MatSach">Mất sách (phạt 100% giá bìa)</option>
            </select>
          </div>
          <div class="form-group">
            <label>Ngày trả thực tế</label>
            <input type="date" name="returned_at" class="form-control">
          </div>
          <div class="alert alert-info" id="return-info" style="display:none"></div>
        </form>
        <div class="modal-footer">
          <button class="btn btn-primary" id="btn-submit-return">✔ Xác nhận trả</button>
          <button class="btn btn-secondary" data-close="modal-return">Huỷ</button>
        </div>
      </div>
    </div>

    <!-- Renew Modal -->
    <div class="modal" id="modal-renew">
      <div class="modal-box">
        <div class="modal-header">
          <h2>🔁 Gia hạn mượn</h2>
          <button class="modal-close" data-close="modal-renew">✕</button>
        </div>
        <form id="renew-form" class="modal-body">
          <div class="form-group">
            <label>Mã phiếu mượn *</label>
            <input type="text" name="loan_id" required class="form-control">
          </div>
          <div class="form-group">
            <label>Số ngày gia hạn</label>
            <input type="number" name="extension_days" class="form-control" value="7" min="1" max="30">
          </div>
        </form>
        <div class="modal-footer">
          <button class="btn btn-primary" id="btn-submit-renew">✔ Gia hạn</button>
          <button class="btn btn-secondary" data-close="modal-renew">Huỷ</button>
        </div>
      </div>
    </div>

    <!-- Reserve Modal -->
    <div class="modal" id="modal-reserve">
      <div class="modal-box">
        <div class="modal-header">
          <h2>📌 Đặt trước sách</h2>
          <button class="modal-close" data-close="modal-reserve">✕</button>
        </div>
        <form id="reserve-form" class="modal-body">
          <div class="form-group">
            <label>Mã độc giả *</label>
            <input type="text" name="reader_id" required class="form-control">
          </div>
          <div class="form-group">
            <label>Mã đầu sách (source_id) *</label>
            <input type="text" name="source_id" required class="form-control">
          </div>
          <div class="form-group">
            <label>Mã chi nhánh</label>
            <input type="text" name="branch_id" class="form-control">
          </div>
        </form>
        <div class="modal-footer">
          <button class="btn btn-primary" id="btn-submit-reserve">✔ Đặt trước</button>
          <button class="btn btn-secondary" data-close="modal-reserve">Huỷ</button>
        </div>
      </div>
    </div>
  `;

  setupModalClosers(container);

  document.getElementById('card-borrow').addEventListener('click', () => openModal('modal-borrow'));
  document.getElementById('card-return').addEventListener('click', () => { document.getElementById('return-form').reset(); openModal('modal-return'); });
  document.getElementById('card-renew').addEventListener('click', () => openModal('modal-renew'));
  document.getElementById('card-reserve').addEventListener('click', () => openModal('modal-reserve'));

  document.getElementById('btn-submit-borrow').addEventListener('click',  submitBorrow);
  document.getElementById('btn-submit-return').addEventListener('click',  submitReturn);
  document.getElementById('btn-submit-renew').addEventListener('click',   submitRenew);
  document.getElementById('btn-submit-reserve').addEventListener('click', submitReserve);

  // Warn on Lost condition
  document.getElementById('return-form').elements['return_condition'].addEventListener('change', e => {
    const info = document.getElementById('return-info');
    if (e.target.value === 'MatSach') {
      info.style.display = '';
      info.innerHTML = '⚠ Sách mất → hệ thống sẽ tự phạt <strong>100% giá bìa</strong>. Không tính thêm phạt quá hạn.';
    } else if (e.target.value.startsWith('Hong')) {
      info.style.display = '';
      info.innerHTML = '📝 Sách hỏng → <strong>nhân viên tự quyết định</strong> mức phạt trong mục Tiền phạt.';
    } else {
      info.style.display = 'none';
    }
  });

  document.getElementById('btn-loans-search').addEventListener('click', doLoansSearch);
  document.getElementById('btn-loans-clear').addEventListener('click',  clearLoansSearch);
  document.getElementById('loans-filter-reader').addEventListener('keydown', e => { if (e.key === 'Enter') doLoansSearch(); });

  await loadActiveLoans();
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

async function loadActiveLoans() {
  const wrap = document.getElementById('active-loans-wrap');
  wrap.innerHTML = '<div class="loading-spinner"><div></div><div></div><div></div></div>';
  try {
    const params = { skip: (loansPage - 1) * PAGE_SIZE, limit: PAGE_SIZE };
    if (loansFilterReader) params.reader_id = loansFilterReader;
    const data = await api.getActiveLoans(params);
    const items = data?.items ?? data ?? [];
    const total = data?.total ?? items.length;
    buildTable(wrap,
      [
        { key: 'loan_id',     label: 'Mã mượn' },
        { key: 'hard_book_id',label: 'Mã sách' },
        { key: 'reader_id',   label: 'Mã độc giả' },
        { key: 'loan_date',   label: 'Ngày mượn', render: v => fmtDate(v) },
        { key: 'due_date',    label: 'Hạn trả',   render: (v, row) =>
          `<span class="${new Date(v) < new Date() ? 'text-danger fw-bold' : ''}">${fmtDate(v)}</span>` },
        { key: 'renewals_count', label: 'Gia hạn' },
      ],
      items,
      row => [
        { label: '📤 Trả',   cls: 'btn-primary', onClick: r => prefillReturn(r.loan_id) },
        { label: '🔁 Gia hạn', cls: 'btn-warning', onClick: r => prefillRenew(r.loan_id) },
      ]
    );
    renderPagination(document.getElementById('loans-pagination'), loansPage, Math.ceil(total / PAGE_SIZE),
      p => { loansPage = p; loadActiveLoans(); });
  } catch (err) {
    wrap.innerHTML = `<p class="text-danger">Lỗi: ${err.detail || err.message}</p>`;
  }
}

function prefillReturn(loanId) {
  document.getElementById('return-form').reset();
  document.getElementById('return-form').elements['loan_id'].value = loanId;
  document.getElementById('return-info').style.display = 'none';
  openModal('modal-return');
}
function prefillRenew(loanId) {
  document.getElementById('renew-form').elements['loan_id'].value = loanId;
  openModal('modal-renew');
}

async function submitBorrow() {
  const form = document.getElementById('borrow-form');
  if (!form.checkValidity()) { form.reportValidity(); return; }
  const data = {
    reader_id: form.elements['reader_id'].value.trim(),
    hard_book_id: form.elements['hard_book_id'].value.trim(),
    days: parseInt(form.elements['days'].value) || 14,
  };
  try {
    const res = await api.borrowBook(data);
    toast(`Mượn sách thành công! Mã phiếu: ${res.loan_id}`, 'success');
    closeModal('modal-borrow');
    form.reset();
    loadActiveLoans();
  } catch (err) { handleApiError(err); }
}

async function submitReturn() {
  const form = document.getElementById('return-form');
  if (!form.checkValidity()) { form.reportValidity(); return; }
  const data = {
    loan_id: parseInt(form.elements['loan_id'].value),
    return_condition: form.elements['return_condition'].value,
  };
  const retDate = form.elements['returned_at'].value;
  if (retDate) data.returned_at = retDate;
  try {
    const res = await api.returnBook(data);
    let msg = 'Trả sách thành công!';
    if (res.fine) msg += ` Phạt: ${res.fine.fine_type} — ${Number(res.fine.amount).toLocaleString('vi-VN')} ₫`;
    toast(msg, 'success', 5000);
    closeModal('modal-return');
    form.reset();
    loadActiveLoans();
  } catch (err) { handleApiError(err); }
}

async function submitRenew() {
  const form = document.getElementById('renew-form');
  if (!form.checkValidity()) { form.reportValidity(); return; }
  const data = {
    loan_id: parseInt(form.elements['loan_id'].value),
    extension_days: parseInt(form.elements['extension_days'].value) || 7,
  };
  try {
    const res = await api.renewLoan(data);
    toast(`Gia hạn thành công! Hạn mới: ${fmtDate(res.due_date)}`, 'success');
    closeModal('modal-renew');
    loadActiveLoans();
  } catch (err) { handleApiError(err); }
}

async function submitReserve() {
  const form = document.getElementById('reserve-form');
  if (!form.checkValidity()) { form.reportValidity(); return; }
  const data = {
    reader_id: form.elements['reader_id'].value.trim(),
    source_id: form.elements['source_id'].value.trim(),
  };
  const bid = form.elements['branch_id'].value.trim();
  if (bid) data.branch_id = bid;
  try {
    const res = await api.reserveBook(data);
    toast(`Đặt trước thành công! Mã: ${res.reservation_id}`, 'success');
    closeModal('modal-reserve');
    form.reset();
  } catch (err) { handleApiError(err); }
}
