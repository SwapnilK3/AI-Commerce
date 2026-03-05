/**
 * Dashboard page — loads stats, recent orders, and activity feed
 */
document.addEventListener('DOMContentLoaded', loadDashboard);

async function loadDashboard() {
    await Promise.all([loadStats(), loadRecentOrders(), loadRecentActivity(), loadProviderInfo()]);
}

async function loadProviderInfo() {
    const container = document.getElementById('provider-info');
    if (!container) return;
    try {
        const data = await fetchAPI('/api/providers');
        const providers = data.providers || {};
        const icons = {
            voice: 'fa-phone-alt',
            messaging: 'fa-comment',
            speech: 'fa-microphone',
        };
        const isLocal = (name) => name.toLowerCase().includes('local') || name.toLowerCase().includes('simul') || name.toLowerCase().includes('whisper') || name.toLowerCase().includes('pyttsx');

        let html = '';
        for (const [key, name] of Object.entries(providers)) {
            const local = isLocal(name);
            const badgeCls = local ? 'badge-warning' : 'badge-success';
            const label = local ? 'Fallback' : 'Production';
            html += `
              <div class="flex items-center justify-between py-2 border-b border-slate-700/30">
                <div class="flex items-center gap-2">
                  <i class="fas ${icons[key] || 'fa-cog'} text-indigo-400 w-5 text-center"></i>
                  <span class="text-sm capitalize font-medium">${key}</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-xs text-slate-400">${name}</span>
                  <span class="badge ${badgeCls}" style="font-size:0.65rem">${label}</span>
                </div>
              </div>`;
        }
        // Queue & DB
        html += `
          <div class="flex items-center justify-between py-2 border-b border-slate-700/30">
            <div class="flex items-center gap-2"><i class="fas fa-layer-group text-cyan-400 w-5 text-center"></i><span class="text-sm font-medium">Queue</span></div>
            <span class="text-xs text-slate-400">${data.queue || 'In-Memory'}</span>
          </div>
          <div class="flex items-center justify-between py-2">
            <div class="flex items-center gap-2"><i class="fas fa-database text-green-400 w-5 text-center"></i><span class="text-sm font-medium">Database</span></div>
            <span class="text-xs text-slate-400">${data.database || 'SQLite'}</span>
          </div>`;
        container.innerHTML = html;
    } catch (err) {
        container.innerHTML = '<p class="text-xs text-slate-500">Could not load provider info</p>';
    }
}

async function loadStats() {
    try {
        const stats = await fetchAPI('/api/dashboard/stats');
        document.getElementById('stat-orders').textContent = stats.total_orders;
        document.getElementById('stat-events').textContent = stats.total_events;
        document.getElementById('stat-calls').textContent = stats.total_calls;
        document.getElementById('stat-whatsapp').textContent = stats.total_whatsapp;

        // Animate numbers
        document.querySelectorAll('.stat-value').forEach(el => {
            el.classList.add('fade-in');
        });
    } catch (err) {
        showToast('Failed to load dashboard stats', 'error');
    }
}

async function loadRecentOrders() {
    const tbody = document.getElementById('recent-orders-body');
    try {
        const data = await fetchAPI('/api/orders?limit=5');
        if (!data.orders || data.orders.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center py-8"><div class="empty-state"><i class="fas fa-inbox"></i><p>No orders yet. Use the Simulate page to create test orders.</p></div></td></tr>`;
            return;
        }
        tbody.innerHTML = data.orders.map(o => `
      <tr class="fade-in">
        <td class="font-mono text-xs">${o.order_id}</td>
        <td>${o.customer_name}</td>
        <td>${getPlatformBadge(o.platform)}</td>
        <td>${getStatusBadge(o.status)}</td>
        <td class="text-sm text-slate-400">${o.items || '—'}</td>
        <td class="text-sm text-slate-400">${timeAgo(o.created_at)}</td>
      </tr>
    `).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center py-8 text-slate-500">Failed to load orders</td></tr>`;
    }
}

async function loadRecentActivity() {
    const container = document.getElementById('activity-feed');
    try {
        const [eventsData, commsData] = await Promise.all([
            fetchAPI('/api/events?limit=5'),
            fetchAPI('/api/communications?limit=5'),
        ]);

        const activities = [];

        (eventsData.events || []).forEach(e => {
            activities.push({
                type: 'event',
                icon: 'fa-bolt',
                color: 'text-yellow-400',
                text: `<strong>${e.customer_name || 'Customer'}</strong> — ${e.event_type.replace(/_/g, ' ')}`,
                time: e.timestamp,
            });
        });

        (commsData.communications || []).forEach(c => {
            const icon = c.comm_type === 'voice' ? 'fa-phone-alt' : 'fa-comment';
            const color = c.comm_type === 'voice' ? 'text-indigo-400' : 'text-green-400';
            activities.push({
                type: 'comm',
                icon, color,
                text: `<strong>${c.customer_name || 'Customer'}</strong> — ${c.comm_type} ${c.status}`,
                time: c.timestamp,
            });
        });

        // Sort by time descending
        activities.sort((a, b) => new Date(b.time) - new Date(a.time));

        if (activities.length === 0) {
            container.innerHTML = `<div class="empty-state"><i class="fas fa-stream"></i><p>No activity yet</p></div>`;
            return;
        }

        container.innerHTML = activities.slice(0, 8).map(a => `
      <div class="flex items-start gap-3 py-3 border-b border-slate-700/50 fade-in">
        <div class="mt-1"><i class="fas ${a.icon} ${a.color}"></i></div>
        <div class="flex-1">
          <p class="text-sm">${a.text}</p>
          <p class="text-xs text-slate-500 mt-1">${timeAgo(a.time)}</p>
        </div>
      </div>
    `).join('');
    } catch (err) {
        container.innerHTML = `<div class="empty-state"><i class="fas fa-stream"></i><p>Failed to load activity</p></div>`;
    }
}
