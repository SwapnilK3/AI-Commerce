/**
 * Orders page — loads and displays order list with filters
 */
document.addEventListener('DOMContentLoaded', () => {
    loadOrders();
    document.getElementById('search-input')?.addEventListener('input', debounce(loadOrders, 300));
    document.getElementById('status-filter')?.addEventListener('change', loadOrders);
    document.getElementById('platform-filter')?.addEventListener('change', loadOrders);
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
      <tr class="fade-in">
        <td><span class="font-mono text-xs text-indigo-300">${o.order_id}</span></td>
        <td><strong>${o.customer_name}</strong></td>
        <td class="text-sm text-slate-400">${o.customer_phone}</td>
        <td>${getPlatformBadge(o.platform)}</td>
        <td>${getStatusBadge(o.status)}</td>
        <td class="text-sm">${o.items || '—'}</td>
        <td class="text-sm text-slate-400">${formatDateTime(o.created_at)}</td>
      </tr>
    `).join('');
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
