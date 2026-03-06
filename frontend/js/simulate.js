/**
 * Simulate page — form to create test orders for demo
 */
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('simulate-form');
  form?.addEventListener('submit', handleSimulate);
});

async function handleSimulate(e) {
  e.preventDefault();

  const btn = document.getElementById('simulate-btn');
  const resultDiv = document.getElementById('simulate-result');
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner" style="width:16px;height:16px;border-width:2px"></div> Processing...';
  resultDiv.innerHTML = '';

  const payload = {
    customer_name: document.getElementById('sim-name').value,
    customer_phone: document.getElementById('sim-phone').value,
    platform: document.getElementById('sim-platform').value,
    event_type: document.getElementById('sim-event').value,
    items: document.getElementById('sim-items').value || 'Sample Item x1',
  };

  try {
    const data = await fetchAPI('/api/simulate/order', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    showToast('Order simulated successfully!', 'success');

    // Show result
    resultDiv.innerHTML = `
      <div class="glass-card p-6 mt-6 fade-in">
        <h4 class="text-lg font-bold mb-4 text-indigo-300"><i class="fas fa-check-circle mr-2"></i>Simulation Result</h4>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="p-4 rounded-lg" style="background:rgba(15,23,42,0.5)">
            <p class="text-xs text-slate-500 uppercase font-semibold mb-2">Order</p>
            <p class="font-mono text-sm text-indigo-300">${data.order?.order_id || '—'}</p>
            <p class="text-sm mt-1">${data.order?.customer_name}</p>
            <p class="text-xs text-slate-400 mt-1">${data.order?.platform}</p>
          </div>
          
          <div class="p-4 rounded-lg" style="background:rgba(15,23,42,0.5)">
            <p class="text-xs text-slate-500 uppercase font-semibold mb-2">Event</p>
            ${getEventBadge(data.event?.event_type || payload.event_type)}
            <p class="text-xs text-slate-400 mt-2">${formatDateTime(data.event?.timestamp)}</p>
          </div>
          
          <div class="p-4 rounded-lg" style="background:rgba(15,23,42,0.5)">
            <p class="text-xs text-slate-500 uppercase font-semibold mb-2">Communication</p>
            <p class="text-sm"><strong>Method:</strong> ${data.communication?.method || 'none'}</p>
            <p class="text-sm"><strong>Status:</strong> ${getStatusBadge(data.communication?.status || 'skipped')}</p>
            ${data.communication?.provider ? `<p class="text-xs text-slate-400 mt-1"><strong>Provider:</strong> ${data.communication.provider}</p>` : ''}
            ${data.communication?.whatsapp_link ? `<a href="${data.communication.whatsapp_link}" target="_blank" rel="noopener" class="inline-flex items-center gap-2 mt-3 px-4 py-2 rounded-lg text-sm font-semibold bg-green-500/20 text-green-400 border border-green-500/30 hover:bg-green-500/30 transition-colors"><i class="fab fa-whatsapp"></i> Open in WhatsApp</a>` : ''}
            ${data.communication?.error ? `<p class="text-xs text-yellow-400 mt-2"><i class="fas fa-info-circle"></i> ${data.communication.error}</p>` : ''}
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    showToast('Failed to simulate order: ' + err.message, 'error');
    resultDiv.innerHTML = `
      <div class="glass-card p-6 mt-6 fade-in" style="border-color:rgba(239,68,68,0.3)">
        <p class="text-red-400"><i class="fas fa-exclamation-triangle mr-2"></i>Error: ${err.message}</p>
      </div>
    `;
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-play"></i> Simulate Order';
  }
}
