/**
 * AI Smart Commerce — Shared Utilities
 * API client, navigation, toast notifications, formatters
 */

const API_BASE = window.location.origin;

// ── API Client ─────────────────────────────────────────────

async function fetchAPI(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const defaults = {
    headers: { 'Content-Type': 'application/json' },
  };
  const config = { ...defaults, ...options };

  try {
    const response = await fetch(url, config);
    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || `HTTP ${response.status}`);
    }
    return await response.json();
  } catch (err) {
    console.error(`API Error [${endpoint}]:`, err);
    throw err;
  }
}

// ── Toast Notifications ────────────────────────────────────

function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const icons = { success: 'fa-check-circle', error: 'fa-exclamation-circle', info: 'fa-info-circle' };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => toast.remove(), 4000);
}

// ── Date/Time Formatters ───────────────────────────────────

function formatDate(isoString) {
  if (!isoString) return '—';
  const d = new Date(isoString);
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function formatTime(isoString) {
  if (!isoString) return '—';
  const d = new Date(isoString);
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
}

function formatDateTime(isoString) {
  if (!isoString) return '—';
  return `${formatDate(isoString)} ${formatTime(isoString)}`;
}

function timeAgo(isoString) {
  if (!isoString) return '—';
  const seconds = Math.floor((Date.now() - new Date(isoString)) / 1000);
  const intervals = [
    { label: 'year', seconds: 31536000 },
    { label: 'month', seconds: 2592000 },
    { label: 'day', seconds: 86400 },
    { label: 'hour', seconds: 3600 },
    { label: 'minute', seconds: 60 },
  ];
  for (const { label, seconds: s } of intervals) {
    const count = Math.floor(seconds / s);
    if (count >= 1) return `${count} ${label}${count > 1 ? 's' : ''} ago`;
  }
  return 'Just now';
}

// ── Status Badge Helper ────────────────────────────────────

function getStatusBadge(status) {
  const map = {
    pending: 'badge-warning',
    confirmed: 'badge-info',
    delivered: 'badge-success',
    order_delivered: 'badge-success',
    delivery_failed: 'badge-danger',
    payment_pending: 'badge-warning',
    returned: 'badge-neutral',
    order_returned: 'badge-neutral',
    initiated: 'badge-info',
    completed: 'badge-success',
    success: 'badge-success',
    sent: 'badge-success',
    failed: 'badge-danger',
    skipped: 'badge-neutral',
    all_failed: 'badge-danger',
  };
  const cls = map[status] || 'badge-neutral';
  return `<span class="badge ${cls}">${status}</span>`;
}

// ── Platform Badge ─────────────────────────────────────────

function getPlatformBadge(platform) {
  const icons = {
    shopify: '<i class="fab fa-shopify"></i>',
    woocommerce: '<i class="fab fa-wordpress"></i>',
  };
  const icon = icons[platform] || '<i class="fas fa-store"></i>';
  return `<span class="platform-badge ${platform}">${icon} ${platform}</span>`;
}

// ── Event Type Badge ───────────────────────────────────────

function getEventBadge(eventType) {
  const map = {
    delivery_failed: 'badge-danger',
    order_created: 'badge-success',
    payment_pending: 'badge-warning',
    order_returned: 'badge-info',
    order_delivered: 'badge-primary',
  };
  const cls = map[eventType] || 'badge-neutral';
  const label = eventType.replace(/_/g, ' ');
  return `<span class="badge ${cls}">${label}</span>`;
}

// ── Comm Type Badge ────────────────────────────────────────

function getCommTypeBadge(type) {
  if (type === 'voice') {
    return `<span class="badge badge-primary"><i class="fas fa-phone-alt" style="font-size:0.65rem"></i> Voice</span>`;
  }
  return `<span class="badge badge-success" style="background:rgba(37,211,102,0.15);color:#25d366"><i class="fab fa-whatsapp" style="font-size:0.75rem"></i> WhatsApp</span>`;
}

// ── Sidebar Active Link ────────────────────────────────────

function initNavigation() {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(item => {
    const href = item.getAttribute('href');
    if (href === path || (path === '/' && href === '/')) {
      item.classList.add('active');
    }
  });

  // Mobile toggle
  const toggle = document.getElementById('sidebar-toggle');
  const sidebar = document.getElementById('sidebar');
  if (toggle && sidebar) {
    toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  }
}

document.addEventListener('DOMContentLoaded', initNavigation);
