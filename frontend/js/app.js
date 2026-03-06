/**
 * AI Smart Commerce — Shared Utilities
 * API client, navigation, toast notifications, formatters
 */

const API_BASE = window.location.origin;

// ── API Client ─────────────────────────────────────────────

async function fetchAPI(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const token = localStorage.getItem('auth_token');

  const headers = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };

  const defaults = { headers };

  // Merge options with headers (ensuring custom headers can still override/add)
  const config = {
    ...defaults,
    ...options,
    headers: { ...defaults.headers, ...(options.headers || {}) }
  };

  try {
    const response = await fetch(url, config);
    if (!response.ok) {
      if (response.status === 401 && !window.location.pathname.includes('login.html') && !window.location.pathname.includes('register.html')) {
        // Unauthorized - redirect to login
        localStorage.removeItem('auth_token');
        localStorage.removeItem('merchant_info');
        window.location.href = '/login.html';
        return;
      }
      const error = await response.text();
      throw new Error(error || `HTTP ${response.status}`);
    }
    return await response.json();
  } catch (err) {
    console.error(`API Error [${endpoint}]:`, err);
    throw err;
  }
}

// ── Authentication Check ───────────────────────────────────
function requireAuth() {
  const token = localStorage.getItem('auth_token');
  const path = window.location.pathname;
  if (!token && !path.includes('login.html') && !path.includes('register.html')) {
    window.location.href = '/login.html';
  }

  // Add logout button listener if it exists
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      localStorage.removeItem('auth_token');
      localStorage.removeItem('merchant_info');
      window.location.href = '/login.html';
    });
  }
}

let _commPollTimer = null;
let _lastCommTimestamp = null;

document.addEventListener('DOMContentLoaded', () => {
  requireAuth();
  initNavigation();
  initCommunicationPolling();
});

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
  const d = new Date(isoString.endsWith('Z') || isoString.includes('+') ? isoString : isoString + 'Z');
  return d.toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric' });
}

function formatTime(isoString) {
  if (!isoString) return '—';
  const d = new Date(isoString.endsWith('Z') || isoString.includes('+') ? isoString : isoString + 'Z');
  return d.toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit' });
}

function formatDateTime(isoString) {
  if (!isoString) return '—';
  return `${formatDate(isoString)} ${formatTime(isoString)}`;
}

function timeAgo(isoString) {
  if (!isoString) return '—';
  const d = new Date(isoString.endsWith('Z') || isoString.includes('+') ? isoString : isoString + 'Z');
  const seconds = Math.floor((Date.now() - d.getTime()) / 1000);
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
    shipped: 'badge-info',
    out_for_delivery: 'badge-info',
    delivered: 'badge-success',
    order_delivered: 'badge-success',
    delivery_failed: 'badge-danger',
    delivery_rescheduled: 'badge-warning',
    payment_pending: 'badge-warning',
    returned: 'badge-neutral',
    order_returned: 'badge-neutral',
    refund_requested: 'badge-warning',
    refund_pickup_generated: 'badge-info',
    pickup_done: 'badge-success',
    refund_processed: 'badge-success',
    exchange_requested: 'badge-warning',
    rto_initiated: 'badge-danger',
    cancelled: 'badge-danger',
    customer_replied: 'badge-neutral',
    initiated: 'badge-info',
    completed: 'badge-success',
    success: 'badge-success',
    sent: 'badge-success',
    failed: 'badge-danger',
    skipped: 'badge-neutral',
    all_failed: 'badge-danger',
  };
  const cls = map[status] || 'badge-neutral';
  // Capitalize format for display, replace underscores
  const label = (status || '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  return `<span class="badge ${cls}">${label}</span>`;
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
    order_created: 'badge-success',
    customer_confirmed: 'badge-success',
    payment_pending: 'badge-warning',
    shipped: 'badge-info',
    out_for_delivery: 'badge-info',
    delivery_failed: 'badge-danger',
    delivery_rescheduled: 'badge-warning',
    order_delivered: 'badge-primary',
    order_returned: 'badge-info',
    refund_requested: 'badge-warning',
    refund_pickup_generated: 'badge-info',
    pickup_done: 'badge-success',
    refund_processed: 'badge-success',
    exchange_requested: 'badge-warning',
    rto_initiated: 'badge-danger',
    order_cancellation_requested: 'badge-danger',
    cancelled: 'badge-danger',
    customer_replied: 'badge-neutral',
  };
  const cls = map[eventType] || 'badge-neutral';
  const label = (eventType || '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  return `<span class="badge ${cls}">${label}</span>`;
}

// ── Comm Type Badge ────────────────────────────────────────

function getCommTypeBadge(type) {
  if (type === 'voice') {
    return `<span class="badge badge-primary"><i class="fas fa-phone-alt" style="font-size:0.65rem"></i> Voice</span>`;
  }
  return `<span class="badge badge-success" style="background:rgba(37,211,102,0.15);color:#25d366"><i class="fab fa-whatsapp" style="font-size:0.75rem"></i> WhatsApp</span>`;
}

// ── Lightweight polling for new customer messages ────────────

function initCommunicationPolling() {
  const path = window.location.pathname;
  // Don't poll on auth pages
  if (path.includes('login.html') || path.includes('register.html')) return;

  // Basic MVP: poll every 10s for latest received communications (limited)
  const poll = async () => {
    try {
      const data = await fetchAPI('/api/communications?limit=5&status=received');
      if (!data || !Array.isArray(data.communications)) return;

      const comms = data.communications;
      if (comms.length === 0) return;

      // Initialise baseline without spamming toasts
      if (_lastCommTimestamp === null) {
        _lastCommTimestamp = comms[0].timestamp;
        return;
      }

      // Find messages newer than last seen timestamp
      const newer = comms.filter(c => c.timestamp && c.timestamp > _lastCommTimestamp);
      if (newer.length > 0) {
        // Update last seen to newest
        _lastCommTimestamp = newer[0].timestamp;

        // Show a compact notification for the most recent reply
        const latest = newer[0];
        const name = latest.customer_name || 'Customer';
        showToast(`New WhatsApp reply from ${name}`, 'info');
      }
    } catch (err) {
      // Fail silently for MVP; dashboard continues to work
      console.debug('Comm polling failed', err);
    }
  };

  // Start polling
  poll();
  _commPollTimer = setInterval(poll, 10000);
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
