# Zodit Gold — Your Personal AI Assistant

## What Is This?

**Zodit Gold** is a personal AI assistant that lives on your computer — not in the cloud. It's like having a brilliant, private secretary that:

- 🗣️ Answers your questions with real intelligence
- 📱 Reads and responds to your **WhatsApp** messages automatically
- 🖥️ Controls your **computer** (opens apps, takes screenshots, types text)
- 📅 Creates and checks your **Google Calendar** events
- 🔍 **Searches the internet** and summarizes results for you
- 🧠 **Remembers** your conversations and important facts over time
- 📂 Reads and analyzes files from your **Google Drive**
- 🎙️ Understands **voice messages** and can reply in audio
- 🖼️ **Analyzes images** you send it
- ⚡ Gets **faster with every use** thanks to a smart memory system

**The best part?** Everything runs locally on your machine. Your data never leaves your computer. No subscriptions. No cloud fees. You own it completely.

---

## Why Is This Different from ChatGPT?

| Feature | ChatGPT | Zodit Gold |
|---|---|---|
| Works without internet | ❌ | ✅ |
| Controls your PC | ❌ | ✅ |
| Reads your WhatsApp | ❌ | ✅ |
| Remembers you over time | ✅ | ✅ |
| Gets faster with use | ✅ | ✅ (Semantic Cache) |
| Your data stays private | ❌ | ✅ |
| Monthly fee | $20+/mo | $0 (you own it) |

---

## The Brain Behind It

Zodit Gold uses **Ollama** — a free, local AI engine — to power its intelligence. Think of it as installing ChatGPT directly on your computer, but smarter: it learns your habits, connects to your real services, and actually does things for you — not just talks.

---

## What Is the Dashboard?

The **Dashboard** is your control center — a beautiful web page you open in your browser to:
- Chat with Zodit directly (like WhatsApp Web, but for your AI)
- Watch in real-time what Zodit is doing
- Turn features on or off with a simple toggle
- See a live view of your computer screen
- Edit Zodit's skills and knowledge base

**Open it at:** `http://localhost:5001` after starting the application.

---

## Step-by-Step: Testing Every Feature

### 1. Open the Dashboard
1. Make sure the application is running (you'll see `✅ Sistema Operativo` in the terminal)
2. Open your browser and go to: **http://localhost:5001**
3. Enter your password (set in the `.env` file under `DASHBOARD_PASS`)
4. You should see the Zodit Omni dashboard

---

### 2. Chat with Zodit
**In the Dashboard → Chat tab:**

Try these messages one by one:

| What to type | What Zodit does |
|---|---|
| `Hola, ¿qué puedes hacer?` | Lists all its capabilities |
| `¿Cuál es la capital de Japón?` | Answers from its knowledge |
| `Busca en internet las noticias de hoy` | Searches the web and summarizes |
| `Crea un evento en mi calendario mañana a las 3pm - Reunión con Daniel` | Adds a Google Calendar event |
| `Toma una captura de pantalla y dime qué ves` | Screenshots your desktop and describes it |
| `Abre el bloc de notas` | Opens Notepad on your PC |

---

### 3. Test the Smart Memory (Semantic Cache ⚡)
This is one of the most impressive features. Ask the **same question twice**:

1. Type: `¿Cuántos planetas tiene el sistema solar?`
2. Wait for the answer (a few seconds)
3. Type the same question again (or almost the same: `Dime cuántos planetas hay en el sistema solar`)
4. The second answer comes back **instantly** — you'll see the `⚡ Cache HIT` badge appear

This means Zodit remembered your question and answered without calling the AI again.

---

### 4. Test WhatsApp Integration
If WhatsApp is connected (QR scanned):

1. Send yourself a WhatsApp message from another phone or contact
2. Zodit will automatically read it and respond
3. Try: `JARVIS, ¿qué hora es?` or `JARVIS, abre Chrome`
4. Watch the response arrive on your WhatsApp in seconds

> You need to scan the QR code the first time Zodit starts. Open WhatsApp → Linked Devices → Link a Device.

---

### 5. Test the Marketplace (Enable/Disable Tools)
1. Click **Marketplace** in the sidebar
2. You'll see all available tools: RAG Knowledge Base, Calendar, WhatsApp, Search, Vision, etc.
3. Toggle any tool **off** — then try asking Zodit to use it
4. It will tell you that tool is currently disabled
5. Toggle it back **on** and it works again

---

### 6. Use the Live View
1. Click **Live View** in the sidebar
2. You'll see a live screenshot of your current desktop — refreshed every 5 seconds
3. Now type in Chat: `¿Qué ves en mi pantalla ahora?`
4. Zodit will describe what's on your screen in natural language

---

### 7. Check the System Monitor
1. Click **Monitor** in the sidebar
2. You'll see every action Zodit takes in real-time (like a flight recorder)
3. When you chat, watch new lines appear: `CACHE_HIT`, `IA_CHAT_OK`, `ACTION_EXEC`, etc.
4. This is how you know exactly what Zodit is doing at every moment

---

### 8. Edit Zodit's Knowledge Base
1. Click **Conocimiento** (Knowledge) in the sidebar
2. You can see all the documents Zodit has learned from
3. Upload new `.txt`, `.pdf`, or `.csv` files to teach it new things
4. After ingesting, ask Zodit about the content — it will answer from YOUR documents

---

### 9. Edit Scripts Live (Code Editor)
1. Click **Editor** in the sidebar
2. Select any Python script from the list on the left
3. Modify the code — then click **Guardar** (Save)
4. Zodit picks up your changes automatically (no need to restart)

---

## Advanced: Test via Command Line (for the curious)

Open a new terminal window and try these commands:

```bash
# Check if everything is alive
curl http://localhost:5000/health

# Ask Zodit a question (replace YOUR_KEY with your ZODIT_API_KEY from .env)
curl -X POST http://localhost:5000/api/chat ^
  -H "Content-Type: application/json" ^
  -H "X-API-Key: YOUR_KEY" ^
  -d "{\"message\": \"Hola Zodit!\", \"sender\": \"test\"}"

# See live metrics (requests, cache hits, response times)
curl http://localhost:5000/metrics
```

---

## Troubleshooting Quick Reference

| Problem | Solution |
|---|---|
| Dashboard won't open | Make sure `start_zodit.py` is running. Check port 5001. |
| WhatsApp not connecting | Scan the QR code that appears in the terminal |
| AI seems slow | Normal on first questions — gets faster with the Semantic Cache |
| Calendar isn't working | Make sure Google Calendar credentials are set up in `assets/` |
| Zodit gives wrong answers | Enable the RAG knowledge base tool in Marketplace and upload your data |

---

## Summary: Your AI Assistant in One Sentence

> **Zodit Gold is a private, all-in-one AI assistant that lives on your computer, connects to your daily tools (WhatsApp, Calendar, Google Drive, your PC), and gets smarter the more you use it — without ever sharing your data with anyone.**

---

*Zodit Gold v3.2 — 2026 · Private Edition · Daniel Eduardo CR*
