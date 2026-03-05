/**
 * Events page — loads and displays event log
 */
document.addEventListener('DOMContentLoaded', () => {
    loadEvents();
    document.getElementById('event-type-filter')?.addEventListener('change', loadEvents);
});

async function loadEvents() {
    const tbody = document.getElementById('events-body');
    const eventType = document.getElementById('event-type-filter')?.value || '';

    let endpoint = '/api/events?limit=100';
    if (eventType) endpoint += `&event_type=${encodeURIComponent(eventType)}`;

    tbody.innerHTML = `<tr><td colspan="5"><div class="loading-overlay"><div class="spinner"></div><span>Loading events...</span></div></td></tr>`;

    try {
        const data = await fetchAPI(endpoint);
        document.getElementById('events-count').textContent = `${data.total} event${data.total !== 1 ? 's' : ''}`;

        if (!data.events || data.events.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5"><div class="empty-state"><i class="fas fa-bolt"></i><p>No events found</p></div></td></tr>`;
            return;
        }

        tbody.innerHTML = data.events.map(e => `
      <tr class="fade-in">
        <td>
          <span class="event-dot ${e.event_type}"></span>
        </td>
        <td>${getEventBadge(e.event_type)}</td>
        <td><strong>${e.customer_name || '—'}</strong></td>
        <td>${getPlatformBadge(e.platform || 'unknown')}</td>
        <td class="text-sm text-slate-400">${formatDateTime(e.timestamp)}</td>
      </tr>
    `).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="5"><div class="empty-state text-red-400"><i class="fas fa-exclamation-triangle"></i><p>Failed to load events</p></div></td></tr>`;
        showToast('Failed to load events', 'error');
    }
}
