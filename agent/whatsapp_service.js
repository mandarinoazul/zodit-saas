const express = require('express');
const app = express();
app.use(express.json());

app.post('/send', (req, res) => {
    console.log(`[WhatsApp] Sending message to ${req.body.phone}: ${req.body.message}`);
    res.json({ status: 'sent' });
});

app.get('/status', (req, res) => {
    res.json({ status: 'connected' });
});

const PORT = process.env.PORT_WHATSAPP || 3001;
app.listen(PORT, () => {
    console.log(`✅ WhatsApp Bridge (Stub) listening on port ${PORT}`);
});
