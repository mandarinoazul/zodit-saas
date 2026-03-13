const express = require('express');
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const app = express();

app.use(express.json());

let qrCodeData = null;
let clientStatus = 'initializing';

const client = new Client({
    authStrategy: new LocalAuth({ dataPath: './sessions/whatsapp' }),
    puppeteer: {
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
        executablePath: process.env.CHROME_PATH || null // Optional manual path
    }
});

client.on('qr', (qr) => {
    console.log('[WhatsApp] QR Received');
    qrCodeData = qr;
    clientStatus = 'qr_ready';
});

client.on('ready', () => {
    console.log('[WhatsApp] Client is ready!');
    qrCodeData = null;
    clientStatus = 'connected';
});

client.on('authenticated', () => {
    console.log('[WhatsApp] Authenticated');
    clientStatus = 'authenticated';
});

client.on('auth_failure', (msg) => {
    console.error('[WhatsApp] Auth failure', msg);
    clientStatus = 'auth_failure';
});

client.on('disconnected', (reason) => {
    console.log('[WhatsApp] Disconnected', reason);
    clientStatus = 'disconnected';
});

app.post('/send', async (req, res) => {
    if (clientStatus !== 'connected') {
        return res.status(503).json({ error: 'WhatsApp not connected' });
    }
    try {
        const { phone, message } = req.body;
        const formattedPhone = phone.includes('@c.us') ? phone : `${phone}@c.us`;
        await client.sendMessage(formattedPhone, message);
        res.json({ status: 'sent' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.get('/status', (req, res) => {
    res.json({ status: clientStatus });
});

app.get('/qr', async (req, res) => {
    if (clientStatus === 'connected') {
        return res.json({ status: 'connected', qr: null });
    }
    if (!qrCodeData) {
        return res.json({ status: clientStatus, qr: null, message: 'QR not generated yet' });
    }
    try {
        const qrImage = await qrcode.toDataURL(qrCodeData);
        res.json({ status: 'qr_ready', qr: qrImage });
    } catch (err) {
        res.status(500).json({ error: 'Failed to generate QR image' });
    }
});

client.initialize();

const PORT = process.env.PORT_WHATSAPP || 3001;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`✅ WhatsApp Bridge ONLINE on port ${PORT}`);
});
