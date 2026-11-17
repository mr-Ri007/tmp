/**
 * dashboard.js — Summary stats page
 */
import * as api from './api.js';
import { fmtMoney, fmtDateTime, toast, setButtonLoading } from './utils.js';

export async function renderDashboard(container) {
  container.innerHTML = `
    <div class="page-header">
      <h1>Tổng quan hệ thống</h1>
      <div class="page-header-actions">
        <button class="btn btn-primary" id="btn-refresh-dash">Làm mới</button>
      </div>
    </div>
    <div class="stats-grid" id="stats-grid">
      ${['Tổng sách', 'Đang mượn', 'Quá hạn', 'Phạt chưa thu'].map(l => `
        <div class="stat-card loading-card">
          <div class="stat-label">${l}</div>
          <div class="stat-value">…</div>
        </div>`).join('')}
    </div>
    <div class="dash-grid">
      <div class="card" id="card-active-loans">
        <h2 class="card-title">Đang mượn gần đây</h2>
        <div class="card-body" id="recent-loans-body">Đang tải…</div>
      </div>
      <div class="card" id="card-unpaid-fines">
        <h2 class="card-title">Phạt chưa thu gần đây</h2>
        <div class="card-body" id="unpaid-fines-body">Đang tải…</div>
      </div>
    </div>
  `;

  document.getElementById('btn-refresh-dash').addEventListener('click', async () => {
    const btn = document.getElementById('btn-refresh-dash');
    setButtonLoading(btn, true);
    await loadDashboard();
    setButtonLoading(btn, false);
  });

  await loadDashboard();
}

async function loadDashboard() {
  try {
    const [sources, loans, fines, readers] = await Promise.allSettled([
      api.getSources({ limit: 1 }),
      api.getActiveLoans({ limit: 100 }),
      api.getFines({ limit: 100 }),
      api.getReaders({ limit: 1 }),
    ]);

    const totalSources = sources.status === 'fulfilled' ? (sources.value?.total ?? sources.value?.length ?? '?') : '?';
    const activeLoansList = loans.status === 'fulfilled' ? (loans.value?.items ?? loans.value ?? []) : [];
    const activeLoansTotal = loans.status === 'fulfilled' ? (loans.value?.total ?? activeLoansList.length) : '?';
    const finesList = fines.status === 'fulfilled' ? (fines.value?.items ?? fines.value ?? []) : [];

    const now = new Date();
    const overdue = activeLoansList.filter(l => l.due_at && new Date(l.due_at) < now).length;
    const unpaidFines = finesList.filter(f => !f.paid_at);
    const unpaidTotal = unpaidFines.reduce((s, f) => s + Number(f.amount || 0), 0);

    // Update stat cards
    const cards = document.querySelectorAll('.stat-card');
    const vals = [totalSources, activeLoansTotal, overdue, fmtMoney(unpaidTotal)];
    const colors = ['blue', 'green', 'orange', 'red'];
    cards.forEach((c, i) => {
      c.classList.remove('loading-card');
      c.classList.add(`stat-${colors[i]}`);
      c.querySelector('.stat-value').textContent = vals[i];
    });

    // Recent active loans table
    renderRecentLoans(activeLoansList.slice(0, 10));
    // Unpaid fines
    renderUnpaidFines(unpaidFines.slice(0, 10));

  } catch (err) {
    toast('Lỗi tải dashboard: ' + err.message, 'error');
  }
}

function renderRecentLoans(list) {
  const body = document.getElementById('recent-loans-body');
  if (!list.length) { body.innerHTML = '<p class="empty-state">Không có lượt mượn nào.</p>'; return; }
  body.innerHTML = `<table class="data-table">
    <thead><tr><th>Mã mượn</th><th>Mã bản sách</th><th>Mã hội viên</th><th>Hạn trả</th></tr></thead>
    <tbody>${list.map(l => `
      <tr>
        <td>${l.id}</td>
        <td>${l.hard_book_id}</td>
        <td>${l.reader_id}</td>
        <td class="${new Date(l.due_at) < new Date() ? 'text-danger' : ''}">${fmtDateTime(l.due_at)}</td>
      </tr>`).join('')}
    </tbody></table>`;
}

function renderUnpaidFines(list) {
  const body = document.getElementById('unpaid-fines-body');
  if (!list.length) { body.innerHTML = '<p class="empty-state">Không có khoản phạt chưa thu.</p>'; return; }
  body.innerHTML = `<table class="data-table">
    <thead><tr><th>Mã phạt</th><th>Loại</th><th>Số tiền</th><th>Ngày tạo</th></tr></thead>
    <tbody>${list.map(f => `
      <tr>
        <td>${f.id}</td>
        <td>${f.fine_type}</td>
        <td class="text-danger fw-bold">${fmtMoney(f.amount)}</td>
        <td>${fmtDateTime(f.created_at)}</td>
      </tr>`).join('')}
    </tbody></table>`;
}
