/**
 * api.js — Central API client for Library Management System
 * All fetch calls go through here. Base URL points to FastAPI backend.
 */

const API_BASE = 'http://127.0.0.1:8000/api/v1';

class ApiError extends Error {
  constructor(status, detail) {
    super(detail || `HTTP ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

async function request(method, path, body = null, params = null) {
  let url = `${API_BASE}${path}`;
  if (params) {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v !== null && v !== undefined && v !== ''))
    ).toString();
    if (qs) url += `?${qs}`;
  }
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try { const j = await res.json(); detail = j.detail || JSON.stringify(j); } catch {}
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

const get  = (path, params) => request('GET',    path, null, params);
const post = (path, body)   => request('POST',   path, body);
const put  = (path, body)   => request('PUT',    path, body);
const patch= (path, body)   => request('PATCH',  path, body);
const del  = (path)         => request('DELETE', path);

// ── Health ────────────────────────────────────────────────────────────────────
export const healthCheck = () => get('/health'); // hits /health, not /api/v1

// ── Sources (Books catalog) ───────────────────────────────────────────────────
export const getSources   = (p) => get('/sources', p);
export const getSource    = (id) => get(`/sources/${id}`);
export const createSource = (d)  => post('/sources', d);
export const updateSource = (id, d) => put(`/sources/${id}`, d);
export const deleteSource = (id)    => del(`/sources/${id}`);

// ── Hard Books ────────────────────────────────────────────────────────────────
export const getHardBooks   = (p)       => get('/hard-books', p);
export const getHardBook    = (id)      => get(`/hard-books/${id}`);
export const createHardBook = (d)       => post('/hard-books', d);
export const updateHardBook = (id, d)   => put(`/hard-books/${id}`, d);
export const deleteHardBook = (id)      => del(`/hard-books/${id}`);

// ── Ebooks ────────────────────────────────────────────────────────────────────
export const getEbooks   = (p)     => get('/ebooks', p);
export const getEbook    = (id)    => get(`/ebooks/${id}`);
export const createEbook = (d)     => post('/ebooks', d);
export const updateEbook = (id, d) => put(`/ebooks/${id}`, d);
export const deleteEbook = (id)    => del(`/ebooks/${id}`);

// ── Readers ───────────────────────────────────────────────────────────────────
export const getReaders   = (p)     => get('/readers', p);
export const getReader    = (id)    => get(`/readers/${id}`);
export const createReader = (d)     => post('/readers', d);
export const updateReader = (id, d) => put(`/readers/${id}`, d);
export const deleteReader = (id)    => del(`/readers/${id}`);

// ── Branches ──────────────────────────────────────────────────────────────────
export const getBranches   = (p)     => get('/branches', p);
export const getBranch     = (id)    => get(`/branches/${id}`);
export const createBranch  = (d)     => post('/branches', d);
export const updateBranch  = (id, d) => put(`/branches/${id}`, d);
export const deleteBranch  = (id)    => del(`/branches/${id}`);

// ── Courses ───────────────────────────────────────────────────────────────────
export const getCourses   = (p)     => get('/courses', p);
export const getCourse    = (id)    => get(`/courses/${id}`);
export const createCourse = (d)     => post('/courses', d);
export const updateCourse = (id, d) => put(`/courses/${id}`, d);
export const deleteCourse = (id)    => del(`/courses/${id}`);

// ── Circulation ───────────────────────────────────────────────────────────────
export const borrowBook      = (d) => post('/circulation/borrow', d);
export const returnBook      = (d) => post('/circulation/return', d);
export const renewLoan       = (d) => post('/circulation/renew', d);
export const reserveBook     = (d) => post('/circulation/reserve', d);
export const cancelReserve   = (id) => put(`/circulation/reserve/${id}/cancel`);
export const getActiveLoans  = (p)  => get('/circulation/active-loans', p);

// ── Fines ─────────────────────────────────────────────────────────────────────
export const getFines         = (p)     => get('/fines', p);
export const getFine          = (id)    => get(`/fines/${id}`);
export const assessDamagedFine= (d)     => post('/fines/assess-damaged', d);
export const payFine          = (id)    => post(`/fines/${id}/pay`);
export const checkDebtor      = (rid)   => get(`/fines/debtors/check/${rid}`);

// ── Access Logs ───────────────────────────────────────────────────────────────
export const getAccessLogs  = (p)   => get('/access-logs', p);
export const startAccess    = (d)   => post('/access-logs/start', d);
export const endAccess      = (id)  => post(`/access-logs/${id}/end`);

// ── Root health (not under /api/v1) ──────────────────────────────────────────
export async function pingBackend() {
  const res = await fetch('http://127.0.0.1:8000/health');
  if (!res.ok) throw new Error('Backend offline');
  return res.json();
}
