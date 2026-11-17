/**
 * app.js — SPA router, navbar, page-switching logic
 */
import { pingBackend } from './api.js';
import { toast } from './utils.js';
import { renderDashboard } from './dashboard.js';
import { renderSources } from './sources.js';
import { renderReaders } from './readers.js';
import { renderCirculation } from './circulation.js';
import { renderFines } from './fines.js';
import { renderBranches } from './branches.js';
import { renderEbooks } from './ebooks.js';

// ── Route table ───────────────────────────────────────────────────────────────
const ROUTES = {
  dashboard:   { label: '🏠 Tổng quan',       render: renderDashboard },
  sources:     { label: '📚 Danh mục sách',    render: renderSources },
  ebooks:      { label: '💻 Sách điện tử',     render: renderEbooks },
  readers:     { label: '👤 Bạn đọc',          render: renderReaders },
  circulation: { label: '🔄 Mượn / Trả',       render: renderCirculation },
  fines:       { label: '💸 Tiền phạt',         render: renderFines },
  branches:    { label: '🏢 Chi nhánh',         render: renderBranches },
};

let currentPage = null;

function navigate(page) {
  if (!ROUTES[page]) page = 'dashboard';
  currentPage = page;
  // Update URL hash
  location.hash = page;
  // Highlight nav
  document.querySelectorAll('.nav-link').forEach(a => {
    a.classList.toggle('active', a.dataset.page === page);
  });
  // Render
  const main = document.getElementById('main-content');
  main.innerHTML = '';
  ROUTES[page].render(main);
}

function buildNav() {
  const nav = document.getElementById('sidebar-nav');
  nav.innerHTML = '';
  for (const [key, cfg] of Object.entries(ROUTES)) {
    const a = document.createElement('a');
    a.className = 'nav-link';
    a.dataset.page = key;
    a.textContent = cfg.label;
    a.href = `#${key}`;
    a.addEventListener('click', (e) => { e.preventDefault(); navigate(key); });
    nav.appendChild(a);
  }
}

async function checkBackend() {
  const dot = document.getElementById('status-dot');
  const txt = document.getElementById('status-text');
  try {
    await pingBackend();
    dot.className = 'status-dot online';
    txt.textContent = 'Backend online';
  } catch {
    dot.className = 'status-dot offline';
    txt.textContent = 'Backend offline';
    toast('Không thể kết nối backend. Hãy khởi động uvicorn.', 'error', 6000);
  }
}

// ── Sidebar toggle (mobile) ───────────────────────────────────────────────────
function setupSidebar() {
  const toggle = document.getElementById('sidebar-toggle');
  const sidebar = document.getElementById('sidebar');
  if (toggle) {
    toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  }
  // Close on nav click (mobile)
  document.querySelectorAll('.nav-link').forEach(a => {
    a.addEventListener('click', () => sidebar.classList.remove('open'));
  });
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  buildNav();
  setupSidebar();
  checkBackend();
  // Ping every 30s
  setInterval(checkBackend, 30000);

  // Handle hash routing
  const hash = location.hash.replace('#', '') || 'dashboard';
  navigate(hash);
});

window.addEventListener('hashchange', () => {
  const hash = location.hash.replace('#', '') || 'dashboard';
  if (hash !== currentPage) navigate(hash);
});
