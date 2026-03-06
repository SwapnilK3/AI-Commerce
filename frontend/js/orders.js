/**
 * Orders page — loads and displays order list with filters
 */
document.addEventListener('DOMContentLoaded', () => {
  loadOrders();
  document.getElementById('search-input')?.addEventListener('input', debounce(loadOrders, 300));
  document.getElementById('status-filter')?.addEventListener('change', loadOrders);
  document.getElementById('platform-filter')?.addEventListener('change', loadOrders);

  // Clear activity panel
  document.getElementById('clear-activity-btn')?.addEventListener('click', () => {
    const card = document.getElementById('order-activity-card');
    const body = document.getElementById('order-activity-body');
    const header = document.getElementById('order-activity-header');
    if (card && body && header) {
      body.innerHTML = '<p class="text-xs text-slate-500">Select an order to see its full timeline: events and WhatsApp / call activity.</p>';
      header.textContent = '';
      card.style.display = 'none';
    }
  });
});

async function loadOrders() {
  const tbody = document.getElementById('orders-body');
  const search = document.getElementById('search-input')?.value || '';
  const status = document.getElementById('status-filter')?.value || '';
  const platform = document.getElementById('platform-filter')?.value || '';

  let endpoint = '/api/orders?limit=100';
  if (search) endpoint += `&search=${encodeURIComponent(search)}`;
  if (status) endpoint += `&status=${encodeURIComponent(status)}`;
  if (platform) endpoint += `&platform=${encodeURIComponent(platform)}`;

  tbody.innerHTML = `<tr><td colspan="7"><div class="loading-overlay"><div class="spinner"></div><span>Loading orders...</span></div></td></tr>`;

  try {
    const data = await fetchAPI(endpoint);
    document.getElementById('orders-count').textContent = `${data.total} order${data.total !== 1 ? 's' : ''}`;

    if (!data.orders || data.orders.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><i class="fas fa-inbox"></i><p>No orders found</p></div></td></tr>`;
      return;
    }

    tbody.innerHTML = data.orders.map(o => `
      <tr class="fade-in hover:bg-slate-800/50 cursor-pointer" data-order-id="${o.id}">
        <td>
          <button type="button"
                  class="text-xs font-mono text-indigo-300 hover:text-indigo-100 underline order-detail-trigger"
                  data-order-id="${o.id}"
                  title="View full activity timeline">
            ${o.order_id}
          </button>
        </td>
        <td><strong>${o.customer_name}</strong></td>
        <td class="text-sm text-slate-400">${o.customer_phone}</td>
        <td>${getPlatformBadge(o.platform)}</td>
        <td>${getStatusBadge(o.status)}</td>
        <td class="text-sm">${o.items || '—'}</td>
        <td class="text-sm text-slate-400">${formatDateTime(o.created_at)}</td>
      </tr>
    `).join('');

    // Attach click handler (event delegation) for activity panel
    tbody.addEventListener('click', (e) => {
      const target = e.target;
      if (!(target instanceof HTMLElement)) return;

      const btn = target.closest('.order-detail-trigger');
      const row = target.closest('tr[data-order-id]');
      const orderId = (btn || row)?.getAttribute('data-order-id');
      if (orderId) {
        loadOrderActivity(orderId);
      }
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state text-red-400"><i class="fas fa-exclamation-triangle"></i><p>Failed to load orders</p></div></td></tr>`;
    showToast('Failed to load orders', 'error');
  }
}

function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

async function loadOrderActivity(orderId) {
  const card = document.getElementById('order-activity-card');
  const body = document.getElementById('order-activity-body');
  const header = document.getElementById('order-activity-header');
  if (!card || !body || !header) return;

  card.style.display = 'block';
  body.innerHTML = `
      <div class="loading-overlay" style="padding:16px">
        <div class="spinner"></div><span>Loading activity...</span>
      </div>`;
  header.textContent = '';

  try {
    const data = await fetchAPI(`/api/orders/${encodeURIComponent(orderId)}`);

    if (data.error) {
      body.innerHTML = `<p class="text-xs text-red-400"><i class="fas fa-exclamation-triangle mr-1"></i>${data.error}</p>`;
      return;
    }

    // Header with basic order info
    header.innerHTML = `
          <div class="flex flex-col gap-1">
            <div class="text-xs text-slate-300">
              <span class="font-mono text-indigo-300">${data.order_id}</span>
            </div>
            <div class="text-xs text-slate-400">
              <strong>${data.customer_name}</strong>
              <span class="text-slate-500 ml-1">${data.customer_phone || ''}</span>
            </div>
          </div>`;

    const events = (data.events || []).map(e => {
      let metaHtml = '';
      if (e.metadata && Object.keys(e.metadata).length > 0) {
        const pairs = Object.entries(e.metadata).map(([k, v]) => `
                    <div class="flex items-center gap-2 mb-1">
                        <span class="text-slate-500 font-mono text-[10px] uppercase tracking-wider">${k.replace(/_/g, ' ')}:</span>
                        <span class="text-slate-300 text-xs">${v}</span>
                    </div>
                `).join('');
        metaHtml = `<div class="mt-2 bg-slate-900/50 rounded p-2 border border-slate-700/50">${pairs}</div>`;
      }

      return {
        type: 'event',
        timestamp: e.timestamp,
        label: e.event_type.replace(/_/g, ' '),
        html: `
                  <div class="flex items-start gap-3">
                    <div class="mt-0.5 z-10">
                      <div class="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700">
                         <i class="fas fa-bolt text-[10px] text-yellow-400"></i>
                      </div>
                    </div>
                    <div class="flex-1 pb-4">
                      <div class="flex items-center justify-between mb-1">
                          <div class="text-xs">${getEventBadge(e.event_type)}</div>
                          <div class="text-[10px] text-slate-500">${formatDateTime(e.timestamp)}</div>
                      </div>
                      ${metaHtml}
                    </div>
                  </div>
                `
      };
    });

    const comms = (data.communications || []).map(c => ({
      type: 'comm',
      timestamp: c.timestamp,
      label: `${c.comm_type} ${c.status}`,
      html: `
              <div class="flex items-start gap-3">
                <div class="mt-0.5">
                  ${c.comm_type === 'voice'
          ? '<i class="fas fa-phone-alt text-indigo-400"></i>'
          : '<i class="fab fa-whatsapp text-green-400"></i>'}
                </div>
                <div class="flex-1">
                  <div class="flex items-center gap-2 text-xs mb-0.5">
                    ${getCommTypeBadge(c.comm_type)}
                    ${getStatusBadge(c.status)}
                  </div>
                  <div class="text-[11px] text-slate-400 mb-1">${c.message || '—'}</div>
                  <div class="text-[11px] text-slate-500">${formatDateTime(c.timestamp)}</div>
                </div>
              </div>
            `
    }));

    const all = [...events, ...comms].filter(a => a.timestamp).sort(
      (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
    );

    if (all.length === 0) {
      body.innerHTML = `<p class="text-xs text-slate-500">No events or communications logged yet for this order.</p>`;
      return;
    }

    body.innerHTML = all.map(a => `
          <div class="py-2 border-b border-slate-800/60 last:border-0">
            ${a.html}
          </div>
        `).join('');
  } catch (err) {
    body.innerHTML = `<p class="text-xs text-red-400"><i class="fas fa-exclamation-triangle mr-1"></i>Failed to load order activity.</p>`;
  }
}
