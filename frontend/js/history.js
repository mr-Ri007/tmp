/**
 * Lịch sử mượn theo tháng và thống kê toàn tháng.
 */
import * as api from './api.js';
import { fmtDateTime, buildTable, toast, renderPagination } from './utils.js';

let currentPage = 1;
const PAGE_SIZE = 25;
let month = new Date().getMonth() + 1;
let year = new Date().getFullYear();

export async function renderHistory(container) {
  const now = new Date();
  month = now.getMonth() + 1;
  year = now.getFullYear();
  currentPage = 1;

  container.innerHTML = `
    <div class="page-header">
      <h1>Lịch sử mượn trong tháng</h1>
    </div>

    <div class="stats-grid history-stats" id="history-stats">
      ${[
        ['Tổng lượt mượn', 'history-total'],
        ['Hội viên đã mượn', 'history-members'],
        ['Đang mượn', 'history-active'],
        ['Đã trả', 'history-returned'],
      ].map(([label, id]) => `
        <div class="stat-card loading-card">
          <div class="stat-label">${label}</div>
          <div class="stat-value" id="${id}">…</div>
        </div>`).join('')}
    </div>

    <div class="history-rankings">
      <section class="card">
        <h2 class="card-title">Hội viên mượn nhiều nhất</h2>
        <ol class="ranking-list" id="history-top-readers"></ol>
      </section>
      <section class="card">
        <h2 class="card-title">Sách được mượn nhiều nhất</h2>
        <ol class="ranking-list" id="history-top-books"></ol>
      </section>
    </div>

    <div class="filter-bar">
      <label for="history-month">Tháng:</label>
      <select id="history-month" class="form-control" style="max-width:140px"></select>
      <label for="history-year">Năm:</label>
      <select id="history-year" class="form-control" style="max-width:120px"></select>
      <button class="btn btn-secondary" id="btn-history-load">Xem lịch sử</button>
    </div>

    <div class="card">
      <div class="card-header">
        <h2 id="history-table-title">Lượt mượn</h2>
        <span id="history-result-count"></span>
      </div>
      <div class="card-body">
        <div id="history-table-wrap"></div>
        <div class="pagination" id="history-pagination"></div>
      </div>
    </div>
  `;

  const monthSelect = document.getElementById('history-month');
  const yearSelect = document.getElementById('history-year');
  for (let m = 1; m <= 12; m++) {
    const option = new Option(`Tháng ${m}`, m, m === month, m === month);
    monthSelect.add(option);
  }
  for (let y = now.getFullYear() - 2; y <= now.getFullYear(); y++) {
    const option = new Option(String(y), y, y === year, y === year);
    yearSelect.add(option);
  }

  document.getElementById('btn-history-load').addEventListener('click', () => {
    month = Number(monthSelect.value);
    year = Number(yearSelect.value);
    currentPage = 1;
    loadHistory();
  });

  await loadHistory();
}

async function loadHistory() {
  const wrap = document.getElementById('history-table-wrap');
  wrap.innerHTML = '<div class="loading-spinner"><div></div><div></div><div></div></div>';
  document.getElementById('history-result-count').textContent = '';
  document.getElementById('history-table-title').textContent = `Lượt mượn tháng ${month}/${year}`;
  document.querySelectorAll('#history-stats .stat-card').forEach(card => card.classList.add('loading-card'));

  try {
    const data = await api.getLoanHistory({
      skip: (currentPage - 1) * PAGE_SIZE,
      limit: PAGE_SIZE,
      month,
      year,
    });
    const items = data.items || [];
    const total = data.total || 0;
    const stats = data.stats || {};

    document.getElementById('history-total').textContent = stats.total_loans ?? total;
    document.getElementById('history-members').textContent = stats.member_count ?? 0;
    document.getElementById('history-active').textContent = stats.active_loans ?? 0;
    document.getElementById('history-returned').textContent = stats.returned_loans ?? 0;
    document.querySelectorAll('#history-stats .stat-card').forEach(card => card.classList.remove('loading-card'));
    renderRankings('history-top-readers', stats.top_readers, item =>
      `${item.reader_name} — ${item.loan_count} lượt`);
    renderRankings('history-top-books', stats.top_books, item =>
      `${item.title} — ${item.loan_count} lượt`);

    buildTable(wrap, [
      { key: 'id', label: 'Mã phiếu mượn' },
      { key: 'reader_id', label: 'Mã hội viên' },
      { key: 'reader_name', label: 'Tên hội viên' },
      { key: 'hard_book_id', label: 'Mã bản sách' },
      { key: 'title', label: 'Tên sách' },
      { key: 'borrowed_at', label: 'Ngày mượn', render: fmtDateTime },
      { key: 'due_at', label: 'Hạn trả', render: fmtDateTime },
      { key: 'returned_at', label: 'Ngày trả', render: value => value ? fmtDateTime(value) : 'Chưa trả' },
      { key: 'status', label: 'Trạng thái' },
    ], items);
    document.getElementById('history-result-count').textContent = `Hiển thị ${items.length} / ${total}`;
    renderPagination(
      document.getElementById('history-pagination'),
      currentPage,
      Math.ceil(total / PAGE_SIZE),
      page => { currentPage = page; loadHistory(); },
    );
  } catch (err) {
    wrap.innerHTML = `<p class="text-danger">Không tải được lịch sử: ${err.detail || err.message}</p>`;
    toast('Không tải được lịch sử mượn.', 'error');
  }
}

function renderRankings(id, entries = [], getLabel) {
  const list = document.getElementById(id);
  list.replaceChildren();
  if (!entries.length) {
    const empty = document.createElement('li');
    empty.className = 'ranking-empty';
    empty.textContent = 'Chưa có dữ liệu trong tháng này.';
    list.appendChild(empty);
    return;
  }
  entries.forEach((entry, index) => {
    const item = document.createElement('li');
    const rank = document.createElement('span');
    rank.className = 'ranking-position';
    rank.textContent = String(index + 1);
    const label = document.createElement('span');
    label.textContent = getLabel(entry);
    item.append(rank, label);
    list.appendChild(item);
  });
}
