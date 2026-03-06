/**
 * WhatsApp Web Session Service
 * 
 * - Multi-tenant update: manages a Map of { merchantId -> Client }
 * - Generates QR code for WhatsApp Web linking per merchant
 * - Stores session for reuse across restarts in ./session_data/{merchantId}
 * - Exposes REST API for sending messages
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const express = require('express');
const qrcode = require('qrcode');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(express.json());

const PORT = process.env.WA_SERVICE_PORT || 3001;
const SESSION_DIR = './session_data';

if (!fs.existsSync(SESSION_DIR)) {
    fs.mkdirSync(SESSION_DIR, { recursive: true });
}

// ── State: Map of merchantId -> { client, qr, isReady, info } ──
const sessions = new Map();

function getSession(merchantId) {
    if (!sessions.has(merchantId)) {
        sessions.set(merchantId, {
            client: null,
            qr: null,
            isReady: false,
            info: null
        });
    }
    return sessions.get(merchantId);
}

function initializeClient(merchantId) {
    const session = getSession(merchantId);
    if (session.client) return; // already initialized

    console.log(`[Merchant ${merchantId}] ⏳ Initializing client...`);
    const client = new Client({
        authStrategy: new LocalAuth({
            dataPath: path.join(SESSION_DIR, `merchant_${merchantId}`)
        }),
        puppeteer: {
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--disable-gpu',
            ]
        }
    });

    session.client = client;

    client.on('qr', async (qr) => {
        session.qr = qr;
        session.isReady = false;
        console.log(`[Merchant ${merchantId}] 📱 QR Code generated`);
    });

    client.on('ready', () => {
        session.isReady = true;
        session.qr = null;
        session.info = client.info;
        console.log(`[Merchant ${merchantId}] ✅ Connected as: ${client.info?.pushname || 'Unknown'}`);
    });

    client.on('authenticated', () => {
        console.log(`[Merchant ${merchantId}] 🔐 Authenticated`);
    });

    client.on('auth_failure', (msg) => {
        session.isReady = false;
        session.qr = null;
        console.error(`[Merchant ${merchantId}] ❌ Auth failed:`, msg);
    });

    client.on('disconnected', (reason) => {
        session.isReady = false;
        session.qr = null;
        session.info = null;
        console.log(`[Merchant ${merchantId}] 🔌 Disconnected:`, reason);
        setTimeout(() => {
            console.log(`[Merchant ${merchantId}] 🔄 Reconnecting...`);
            client.initialize();
        }, 5000);
    });

    client.on('message', async (msg) => {
        if (msg.isStatus || msg.author || msg.from.includes('-')) return;

        console.log(`[Merchant ${merchantId}] 📩 Msg from ${msg.from}: ${msg.body}`);

        try {
            // using native fetch
            const BACKEND_URL = process.env.BACKEND_WEBHOOK_URL || 'http://backend:8000/api/webhooks/whatsapp-incoming';

            const urlWithParams = new URL(BACKEND_URL);
            urlWithParams.searchParams.set('merchant_id', merchantId);

            const response = await fetch(urlWithParams.toString(), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    from: msg.from,
                    body: msg.body,
                    timestamp: msg.timestamp,
                    message_id: msg.id._serialized
                })
            });

            if (!response.ok) {
                console.error(`[Merchant ${merchantId}] ❌ Webhook error: ${response.status}`);
            } else {
                console.log(`[Merchant ${merchantId}] ✅ Webhook sent`);
            }
        } catch (err) {
            console.error(`[Merchant ${merchantId}] ❌ Webhook forward failed:`, err.message);
        }
    });

    client.initialize();
}

// ── API Routes ─────────────────────────────────────────────

app.get('/status', async (req, res) => {
    const merchantId = req.query.merchant_id || '1';
    const session = getSession(merchantId);

    // Auto-initialize if not exist
    if (!session.client) {
        initializeClient(merchantId);
    }

    const result = {
        connected: session.isReady,
        account: null,
        qr_available: !!session.qr,
    };

    if (session.isReady && session.info) {
        result.account = {
            name: session.info.pushname,
            phone: session.info.wid?.user,
            platform: session.info.platform,
        };
    }

    res.json(result);
});

app.get('/qr', async (req, res) => {
    const merchantId = req.query.merchant_id || '1';
    const session = getSession(merchantId);

    if (!session.client) {
        initializeClient(merchantId);
    }

    if (session.isReady) {
        return res.json({ connected: true, qr: null, message: 'Already connected' });
    }

    if (!session.qr) {
        return res.json({ connected: false, qr: null, message: 'QR not yet generated, please wait...' });
    }

    try {
        const qrBase64 = await qrcode.toDataURL(session.qr, { width: 300 });
        res.json({ connected: false, qr: qrBase64, message: 'Scan this QR with WhatsApp' });
    } catch (err) {
        res.status(500).json({ error: 'Failed to generate QR image' });
    }
});

app.post('/send', async (req, res) => {
    const { phone, message, merchant_id } = req.body;
    const merchantId = merchant_id || req.query.merchant_id || '1';

    const session = getSession(merchantId);

    if (!session.isReady || !session.client) {
        return res.status(503).json({
            success: false,
            error: 'WhatsApp not connected. Please scan QR code first.',
        });
    }

    if (!phone || !message) {
        return res.status(400).json({
            success: false,
            error: 'Both phone and message are required',
        });
    }

    try {
        let cleanPhone = phone.replace(/\D/g, '');
        if (cleanPhone.length === 10) cleanPhone = '91' + cleanPhone;

        const numberDetails = await session.client.getNumberId(cleanPhone);

        if (!numberDetails) {
            return res.status(400).json({
                success: false,
                error: `Phone number not registered on WhatsApp.`,
            });
        }

        const chatId = numberDetails._serialized;
        const result = await session.client.sendMessage(chatId, message);

        res.json({
            success: true,
            message_id: result.id?._serialized || result.id,
            timestamp: result.timestamp || Math.floor(Date.now() / 1000),
            to: phone,
        });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

app.post('/disconnect', async (req, res) => {
    const merchantId = req.body.merchant_id || req.query.merchant_id || '1';
    const session = getSession(merchantId);

    if (session.client) {
        try {
            await session.client.logout();
        } catch (e) { }
        session.isReady = false;
        session.qr = null;
        session.info = null;
        try { await session.client.destroy(); } catch (e) { }
        session.client = null;
    }

    res.json({ status: 'disconnected', message: 'Session cleared.' });
});

// Auto-initialize default merchant '1' so legacy features work out-of-box
initializeClient('1');

app.listen(PORT, () => {
    console.log(`\n🚀 WhatsApp Web Service running on port ${PORT} (Multi-tenant)`);
});
