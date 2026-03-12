#  Zodit Gold — AI Personal Agent

> **Enterprise-grade, fully local AI assistant** built on FastAPI, Ollama, and WhatsApp Web.  
> Semantic caching, async architecture, Prometheus observability, and a real-time dashboard — all running 100% on your machine.

---

##  Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Running with Docker](#running-with-docker)
- [Testing](#testing)
- [Dashboard Usage](#dashboard-usage)
- [Observability (Prometheus + Grafana)](#observability)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                    User Interfaces                   │
│    WhatsApp (port 3001)   Dashboard (port 5001)      │
└───────────────┬──────────────────┬───────────────────┘
                │                  │
        Webhook │          HTTP API│
                ▼                  ▼
┌──────────────────────────────────────────────────────┐
│            Gateway (main_agent.py : 5000)            │
│  ┌─────────────┐   ┌─────────────────────────────┐   │
│  │ Semantic    │   │ NLU Router → Tool Dispatcher│   │
│  │ Cache       │   │ (PC, CALENDAR, SEARCH, CHAT)│   │
│  └─────────────┘   └──────────────┬──────────────┘   │
└──────────────────────────────────────────────────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 ▼                  ▼                  ▼
        ┌────────────┐    ┌──────────────┐   ┌────────────────┐
        │ Ollama LLM │    │ Tool Server  │   │ Skills Library │
        │ :11434     │    │ :5005        │   │ /skills_jarvis │
        └────────────┘    └──────────────┘   └────────────────┘
```

**Ports at a glance:**

| Service            | Port  | Description                      |
|--------------------|-------|----------------------------------|
| Gateway (API)      | 5000  | Main orchestrator & webhook      |
| Dashboard          | 5001  | Web control panel                |
| Tool Server        | 5005  | Isolated tool execution          |
| WhatsApp Bridge    | 3001  | whatsapp-web.js service          |
| Ollama             | 11434 | Local LLM inference engine       |
| Prometheus         | 9090  | Metrics scraper (Docker)         |
| Grafana            | 3000  | Metrics visualization (Docker)   |

---

## Prerequisites

Before starting, make sure you have all of the following installed:

| Dependency | Version | Download |
|---|---|---|
| Python | 3.11+ | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| Ollama | latest | [ollama.ai](https://ollama.ai) |
| Docker Desktop | latest | [docker.com](https://docker.com) *(optional)* |
| Git | latest | [git-scm.com](https://git-scm.com) |

### Required Ollama Models

Pull all models before first launch:

```bash
# Main reasoning model
ollama pull llama3.1:8b

# Vision-capable model
ollama pull llama3.2-vision:latest

# Fast router/dispatcher model
ollama pull qwen2.5:3b

# Embedding model for Semantic Cache 
ollama pull nomic-embed-text
```

---

## Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd mi-agente
```

### 2. Create a Python Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install WhatsApp Service Dependencies

```bash
cd skills/sales-assistant/scripts
npm install
cd ../../..
```

---

## Configuration

Copy and edit the environment file:

```bash
copy .env.example .env   # Windows
cp .env.example .env     # macOS/Linux
```

Edit `.env` and set at minimum:

```env
# --- SECURITY (REQUIRED!) ---
ZODIT_API_KEY=change_me_to_a_long_random_secret
DASHBOARD_SECRET=change_me_dashboard_secret
DASHBOARD_PASS=your_dashboard_password

# --- YOUR DETAILS ---
USER_NAME=YourName
OWNER_PHONE=1234567890        # WhatsApp phone number (no + or spaces)

# --- AI MODELS ---
PREFERRED_MODEL=llama3.1:8b
VISION_MODEL=llama3.2-vision:latest

# --- PORTS (defaults work fine) ---
PORT_GATEWAY=5000
PORT_TOOLS=5005
PORT_WHATSAPP=3001
```

>  **Security:** Never commit `.env` to Git. It is already in `.gitignore`.

---

## Running the Application

### Option A: Single Command (Recommended)

The `start_zodit.py` launcher starts all services automatically:

```bash
python start_zodit.py
```

This starts:
- 🌐 **Gateway** on `http://localhost:5000`
- 🖥️ **Dashboard** on `http://localhost:5001`
- 🔧 **Tool Server** on `http://localhost:5005`
- 📱 **WhatsApp Bridge** on port `3001`

### Option B: Run Services Individually

```bash
# Terminal 1 — Core AI Agent Gateway
python main_agent.py

# Terminal 2 — Dashboard
cd skills/sales-assistant/scripts
python dashboard.py

# Terminal 3 — Tool Server
python tool_server.py

# Terminal 4 — WhatsApp Bridge
cd skills/sales-assistant/scripts
node whatsapp_service.js
```

### First-Time WhatsApp Setup

On first launch, the WhatsApp service will display a **QR code** in your terminal. Scan it with your WhatsApp mobile app:

1. Open WhatsApp on your phone
2. Tap ⋮ → Linked Devices → Link a Device
3. Scan the QR code shown in the terminal
4. Wait ~5s for confirmation

---

## Running with Docker

### Start the Full Stack

```bash
docker compose up --build
```

This brings up:
- Zodit Core + Dashboard
- Prometheus (`:9090`)
- Grafana (`:3000`)

### Stop

```bash
docker compose down
```

>  **Note:** For WhatsApp to work inside Docker, you'll need to pre-authenticate (copy `.wwebjs_auth/` into the container volume) or run the WhatsApp bridge separately on the host.

---

## Testing

### Run the Full Test Suite

```bash
pytest tests/ -v
```

### Run a Specific Test

```bash
pytest tests/test_config.py -v
```

### What's Tested

| Test File | What it covers |
|---|---|
| `tests/test_config.py` | .env loading, Pydantic model validation |
| `tests/test_endpoints.py` | `/health`, `/status`, `/api/chat` HTTP responses |
| `tests/test_cache.py` | Semantic Cache cosine similarity threshold |

### Manual API Testing

```bash
# Health check
curl http://localhost:5000/health

# Status of all services
curl http://localhost:5000/status

# Chat (requires API Key)
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_zodit_api_key" \
  -d '{"message": "Hola, ¿qué puedes hacer?", "sender": "test_user"}'

# Prometheus metrics
curl http://localhost:5000/metrics
```

### Testing the Semantic Cache 

Send the same (or highly similar) question twice:

```bash
# First call — will trigger CACHE MISS and LLM generation
curl -s -X POST http://localhost:5000/api/chat \
  -H "X-API-Key: your_key" \
  -H "Content-Type: application/json" \
  -d '{"message": "Cual es la capital de Bulgaria?", "sender": "test"}'

# Second call — should return CACHE HIT instantly
curl -s -X POST http://localhost:5000/api/chat \
  -H "X-API-Key: your_key" \
  -H "Content-Type: application/json" \
  -d '{"message": "Dime la capital de Bulgaria", "sender": "test"}'
```

The second response will begin with ` *[Cache HIT]*`.

---

## Dashboard Usage

Navigate to **`http://localhost:5001`** and log in with the password set in `DASHBOARD_PASS`.

| Tab | Function |
|---|---|
| **Chat** | Full AI assistant interface with model selector |
| **Monitor** | Real-time system event logs |
| **Marketplace** | Enable/disable tools (RAG, Calendar, etc.) |
| **Editor** | Live Python script editor with syntax highlighting |
| **Live View** | Real-time screenshot of your desktop |
| **Conocimiento** | RAG knowledge base file manager |

---

## Observability

### Prometheus

After starting with Docker Compose, visit: **`http://localhost:9090`**

Useful queries:
```promql
# Total requests by tool
zodit_requests_total

# Cache hit rate
rate(zodit_cache_hits_total[5m]) / rate(zodit_requests_total[5m])

# LLM response latency (p95)
histogram_quantile(0.95, rate(zodit_llm_response_seconds_bucket[5m]))

# Active sessions
zodit_active_sessions
```

### Grafana

Visit **`http://localhost:3000`** — Login: `admin` / `zodit123`

1. Go to **Configuration → Data Sources → Add Prometheus**
2. URL: `http://prometheus:9090`
3. Save & Test
4. Create dashboards using the PromQL queries above

---

## API Reference

All protected endpoints require header: `X-API-Key: <your_key>`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/health` | No | Service health check |
| GET | `/status` | No | Status of all subsystems |
| POST | `/webhook` | No | WhatsApp message webhook |
| POST | `/api/chat` | ✅ | Chat with the AI |
| GET | `/api/telemetry` | ✅ | System logs (last 100 events) |
| GET | `/api/integrations` | No | List available tools |
| POST | `/api/integrations/toggle` | No | Enable/disable a tool |
| GET | `/api/rag/files` | ✅ | List knowledge base files |
| POST | `/api/admin/ingest` | ✅ | Ingest new RAG documents |
| POST | `/api/admin/memory/reset` | ✅ | Clear vector memory |
| GET | `/metrics` | No | Prometheus metrics scrape |

---

## Project Structure

```
mi-agente/
├── main_agent.py          #  Core Gateway & Orchestrator (Port 5000)
├── jarvis_core.py         #  AI Core (Port 8001)
├── tool_server.py         #  Tool Execution Server (Port 5005)
├── start_zodit.py         #  Application launcher
│
├── config.py              #  Centralized config via pydantic-settings
├── logger.py              #  Loguru structured logging
├── db.py                  #  SQLAlchemy async DB (sessions.db)
├── metrics.py             #  Prometheus metrics
├── semantic_cache.py      #  Semantic Vector Cache engine
├── session_manager.py     #  Conversation session management
├── memory_manager.py      #  Long-term memory (ChromaDB/RAG)
├── nlu_tools.py           #  NLU regex detectors
│
├── skills_jarvis/         #   Tool library
│   ├── pc_control.py      #   Desktop automation
│   ├── web_tools.py       #   Search & web scraping
│   ├── calendar_tools.py  #   Google Calendar
│   ├── vision_tools.py    #   Image analysis
│   ├── drive_tools.py     #   Google Drive reader
│   └── whatsapp_tools.py  #   WhatsApp messaging
│
├── skills/sales-assistant/
│   └── scripts/
│       ├── dashboard.py       #   Dashboard server (Port 5001)
│       ├── template.html      #   Dashboard UI
│       └── whatsapp_service.js #   WhatsApp Web bridge
│
├── assets/
│   ├── settings_gold.json    #   AI personality & settings
│   └── semantic_cache.json   #   Persisted vector cache
│
├── tests/                     #   Pytest test suite
├── monitoring/
│   └── prometheus.yml         #   Prometheus scrape config
├── .github/workflows/
│   └── ci.yml                 #   GitHub Actions CI pipeline
├── Dockerfile
├── docker-compose.yml
└── .env                       #   Environment secrets (do not commit!)
```

---

## Troubleshooting

### Ollama not connecting

```bash
# Verify Ollama is running
ollama list
curl http://localhost:11434/api/tags
```

### WhatsApp QR not showing

```bash
# Re-run the WA bridge in a visible terminal
node skills/sales-assistant/scripts/whatsapp_service.js
```

### Port already in use

```bash
# Windows — find and kill process on port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Dashboard login fails

- Check `DASHBOARD_PASS` in your `.env` file
- Clear your browser cookies for `localhost:5001`

### `ZODIT_API_KEY` error on startup

- Ensure `.env` has a real key set (not `CHANGE_ME_TO_A_RANDOM_SECRET_KEY`)
- The gateway will **refuse to start** with a weak key by design

### Reset the Semantic Cache

```bash
del assets\semantic_cache.json   # Windows
rm assets/semantic_cache.json    # macOS/Linux
```

---

## License

Private — All rights reserved to me Daniel Eduardo CR. Zodit Gold v3.2 — 2026
