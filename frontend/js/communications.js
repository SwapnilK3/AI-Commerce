/**
 * Communications page — loads call & WhatsApp logs
 */
document.addEventListener('DOMContentLoaded', () => {
    loadCommunications();
    document.getElementById('comm-type-filter')?.addEventListener('change', loadCommunications);
    document.getElementById('comm-status-filter')?.addEventListener('change', loadCommunications);
});

async function loadCommunications() {
    const tbody = document.getElementById('comms-body');
    const commType = document.getElementById('comm-type-filter')?.value || '';
    const status = document.getElementById('comm-status-filter')?.value || '';

    let endpoint = '/api/communications?limit=100';
    if (commType) endpoint += `&comm_type=${encodeURIComponent(commType)}`;
    if (status) endpoint += `&status=${encodeURIComponent(status)}`;

    tbody.innerHTML = `<tr><td colspan="7"><div class="loading-overlay"><div class="spinner"></div><span>Loading logs...</span></div></td></tr>`;

    try {
        const data = await fetchAPI(endpoint);
        document.getElementById('comms-count').textContent = `${data.total} record${data.total !== 1 ? 's' : ''}`;

        if (!data.communications || data.communications.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><i class="fas fa-comments"></i><p>No communication logs found</p></div></td></tr>`;
            return;
        }

        tbody.innerHTML = data.communications.map(c => {
            let responseHtml = c.response || '—';
            // If the response is a wa.me link, render as a clickable button
            if (c.response && c.response.includes('wa.me')) {
                responseHtml = `<a href="${escapeHtml(c.response)}" target="_blank" rel="noopener" class="inline-flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-semibold bg-green-500/20 text-green-400 border border-green-500/30 hover:bg-green-500/30 transition-colors"><i class="fab fa-whatsapp"></i> Open WhatsApp</a>`;
            }
            return `
          <tr class="fade-in">
            <td>${getCommTypeBadge(c.comm_type)}</td>
            <td><strong>${c.customer_name || '—'}</strong></td>
            <td class="text-sm text-slate-400">${c.customer_phone || '—'}</td>
            <td>${getStatusBadge(c.status)}</td>
            <td class="text-sm max-w-xs truncate" title="${escapeHtml(c.message)}">${truncate(c.message, 50)}</td>
            <td class="text-sm text-indigo-300">${responseHtml}</td>
            <td class="text-sm text-slate-400">${formatDateTime(c.timestamp)}</td>
          </tr>`;
        }).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state text-red-400"><i class="fas fa-exclamation-triangle"></i><p>Failed to load communications</p></div></td></tr>`;
        showToast('Failed to load communications', 'error');
    }
}

function truncate(str, len) {
    if (!str) return '—';
    return str.length > len ? str.substring(0, len) + '...' : str;
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
