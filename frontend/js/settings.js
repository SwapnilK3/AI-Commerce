/**
 * Settings page — WhatsApp Web linking + merchant config + API status
 */
let waPollingInterval = null;

document.addEventListener('DOMContentLoaded', () => {
    loadMerchantConfig();
    loadProviderStatus();
    loadWhatsAppWebStatus();

    document.getElementById('merchant-form')?.addEventListener('submit', saveMerchantConfig);

    // Poll WhatsApp Web status every 5 seconds (for QR updates)
    waPollingInterval = setInterval(loadWhatsAppWebStatus, 5000);
});

// ── WhatsApp Web Session ─────────────────────────────────

async function loadWhatsAppWebStatus() {
    const container = document.getElementById('wa-qr-container');
    const statusBadge = document.getElementById('wa-session-status');

    try {
        const data = await fetchAPI('/api/config/whatsapp-web/status');

        if (data.connected) {
            // ✅ Connected — show account info
            const acct = data.account || {};
            statusBadge.innerHTML = `<span class="badge badge-success"><i class="fas fa-check-circle" style="font-size:0.6rem"></i> Connected</span>`;
            container.innerHTML = `
                <div class="text-center">
                    <div class="w-16 h-16 mx-auto mb-3 rounded-full bg-green-500/20 flex items-center justify-center">
                        <i class="fab fa-whatsapp text-green-400 text-3xl"></i>
                    </div>
                    <p class="text-green-400 font-bold text-lg mb-1">Connected!</p>
                    <p class="text-sm text-slate-300">${acct.name || 'WhatsApp Account'}</p>
                    <p class="text-xs text-slate-500 mt-1">+${acct.phone || ''}</p>
                    <p class="text-xs text-slate-500 mt-1">Session stored — will auto-reconnect</p>
                    <button onclick="disconnectWhatsApp()" class="btn btn-outline text-xs mt-4 px-4 py-2 text-red-400 border-red-500/30 hover:bg-red-500/10">
                        <i class="fas fa-unlink"></i> Disconnect
                    </button>
                </div>`;
            // Stop frequent polling when connected
            if (waPollingInterval) {
                clearInterval(waPollingInterval);
                waPollingInterval = setInterval(loadWhatsAppWebStatus, 30000); // Poll every 30s when connected
            }
            return;
        }

        // Not connected — try to get QR code
        const qrData = await fetchAPI('/api/config/whatsapp-web/qr');

        if (qrData.qr) {
            // 📱 QR available — show it
            statusBadge.innerHTML = `<span class="badge badge-warning"><i class="fas fa-qrcode" style="font-size:0.6rem"></i> Scan QR</span>`;
            container.innerHTML = `
                <div class="text-center">
                    <img src="${qrData.qr}" alt="WhatsApp QR Code" class="mx-auto rounded-lg border-2 border-green-500/30" style="width:250px;height:250px;">
                    <p class="text-sm text-green-300 mt-3 font-medium"><i class="fas fa-mobile-alt mr-1"></i> Scan with WhatsApp</p>
                    <p class="text-xs text-slate-500 mt-1">Open WhatsApp → Settings → Linked Devices → Link a Device</p>
                </div>`;
        } else {
            // ⏳ Waiting for QR
            statusBadge.innerHTML = `<span class="badge badge-warning"><i class="fas fa-spinner fa-spin" style="font-size:0.6rem"></i> Initializing</span>`;
            container.innerHTML = `
                <div class="text-center">
                    <div class="spinner mb-3" style="width:32px;height:32px"></div>
                    <p class="text-sm text-slate-400">${qrData.message || 'Initializing WhatsApp service...'}</p>
                    <p class="text-xs text-slate-500 mt-2">QR code will appear shortly</p>
                </div>`;
        }
    } catch (err) {
        // Service not available
        statusBadge.innerHTML = `<span class="badge badge-warning"><i class="fas fa-exclamation" style="font-size:0.6rem"></i> Service Offline</span>`;
        container.innerHTML = `
            <div class="text-center">
                <div class="w-14 h-14 mx-auto mb-3 rounded-full bg-slate-700/50 flex items-center justify-center">
                    <i class="fab fa-whatsapp text-slate-600 text-2xl"></i>
                </div>
                <p class="text-sm text-slate-500 mb-2">WhatsApp Web service not running</p>
                <p class="text-xs text-slate-600">Start with: <code class="bg-slate-800 px-2 py-0.5 rounded text-xs">docker-compose up -d</code></p>
                <p class="text-xs text-slate-600 mt-2">Deep links will be used instead</p>
            </div>`;
    }
}

async function disconnectWhatsApp() {
    if (!confirm('Disconnect WhatsApp? You will need to scan QR again.')) return;
    try {
        await fetchAPI('/api/config/whatsapp-web/disconnect', { method: 'POST' });
        showToast('WhatsApp disconnected', 'info');
        loadWhatsAppWebStatus();
    } catch (err) {
        showToast('Failed to disconnect: ' + err.message, 'error');
    }
}

// ── Merchant Config ──────────────────────────────────────

async function loadMerchantConfig() {
    try {
        const config = await fetchAPI('/api/config/merchant');
        document.getElementById('merchant-whatsapp').value = config.merchant_whatsapp || '';
        document.getElementById('merchant-name').value = config.merchant_name || '';
        document.getElementById('business-name').value = config.business_name || '';

        // Omnichannel fields
        document.getElementById('shopify-store-url').value = config.shopify_store_url || '';
        document.getElementById('woocommerce-store-url').value = config.woocommerce_store_url || '';
        document.getElementById('instagram-handle').value = config.instagram_handle || '';
        document.getElementById('facebook-page').value = config.facebook_page || '';

        // API Keys (now managed here instead of .env)
        if (config.whatsapp_api_token) {
            document.getElementById('whatsapp-api-token').value = config.whatsapp_api_token;
        }
        if (config.whatsapp_phone_number_id) {
            document.getElementById('whatsapp-phone-id').value = config.whatsapp_phone_number_id;
        }

        renderOmniStatus(config);
    } catch (err) {
        console.error('Failed to load merchant config:', err);
    }
}

async function saveMerchantConfig(e) {
    e.preventDefault();
    const btn = document.getElementById('save-merchant-btn');
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner" style="width:14px;height:14px;border-width:2px"></div> Saving...';

    const payload = {
        merchant_whatsapp: document.getElementById('merchant-whatsapp').value.trim(),
        merchant_name: document.getElementById('merchant-name').value.trim(),
        business_name: document.getElementById('business-name').value.trim(),
        shopify_store_url: document.getElementById('shopify-store-url').value.trim(),
        woocommerce_store_url: document.getElementById('woocommerce-store-url').value.trim(),
        instagram_handle: document.getElementById('instagram-handle').value.trim().replace(/^@/, ''),
        facebook_page: document.getElementById('facebook-page').value.trim(),
        whatsapp_api_token: document.getElementById('whatsapp-api-token').value.trim(),
        whatsapp_phone_number_id: document.getElementById('whatsapp-phone-id').value.trim(),
    };

    try {
        await fetchAPI('/api/config/merchant', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        showToast('Merchant settings saved!', 'success');

        // Force reload of status chips
        setTimeout(loadProviderStatus, 1000);
    } catch (err) {
        showToast('Failed to save: ' + err.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Save Settings';
    }
}

function renderOmniStatus(config) {
    const el = document.getElementById('omni-status-summary');
    if (!el) return;

    const chips = [];
    const addChip = (connected, icon, label) => {
        const baseCls = 'inline-flex items-center gap-1 px-2 py-1 rounded-full border text-[11px]';
        if (connected) {
            chips.push(`<span class="${baseCls} border-emerald-500/40 bg-emerald-500/15 text-emerald-300"><i class="${icon}"></i>${label}</span>`);
        } else {
            chips.push(`<span class="${baseCls} border-slate-600/60 text-slate-400"><i class="${icon}"></i>${label}</span>`);
        }
    };

    addChip(!!config.shopify_store_url, 'fab fa-shopify', 'Shopify');
    addChip(!!config.woocommerce_store_url, 'fab fa-wordpress', 'WooCommerce');
    addChip(!!config.instagram_handle, 'fab fa-instagram', 'Instagram');
    addChip(!!config.facebook_page, 'fab fa-facebook-f', 'Facebook');

    el.innerHTML = chips.join('');
}

// ── Provider Status ──────────────────────────────────────

async function loadProviderStatus() {
    try {
        const data = await fetchAPI('/api/providers');
        const providers = data.providers || {};
        const statusEls = document.querySelectorAll('.api-status');
        const providerKeys = ['voice', 'messaging', 'speech'];

        statusEls.forEach((el, i) => {
            const key = providerKeys[i];
            const name = providers[key] || '';
            const isLocal = name.toLowerCase().includes('local') || name.toLowerCase().includes('deep link') || name.toLowerCase().includes('whisper');

            if (isLocal) {
                el.innerHTML = `<span class="badge badge-warning" style="font-size:0.65rem"><i class="fas fa-cog"></i> ${name}</span>`;
            } else {
                el.innerHTML = `<span class="badge badge-success" style="font-size:0.65rem"><i class="fas fa-check"></i> ${name}</span>`;
            }
        });
    } catch (err) {
        document.querySelectorAll('.api-status').forEach(el => {
            el.innerHTML = `<span class="badge badge-warning"><i class="fas fa-key" style="font-size:0.6rem"></i> Set in .env</span>`;
        });
    }
}
