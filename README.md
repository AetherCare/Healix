# MediVault AI — Backend API

**Your Personal Health Operating System**

Production-grade FastAPI backend with PostgreSQL, JWT authentication, RAG-powered AI chat, Celery background processing, and WAN tunnel exposure for cross-network frontend connectivity.

---

## Architecture Overview

```
Remote Frontend (different city/network)
        │
        ▼ HTTPS
┌───────────────────┐
│  ngrok Public URL │  ← https://abc123.ngrok.io
└────────┬──────────┘
         │
┌────────▼──────────┐
│  FastAPI :8000    │  host=0.0.0.0 (LAN: 192.168.29.95)
│  Uvicorn          │
├───────────────────┤
│  PostgreSQL       │
│  Redis + Celery   │
│  ChromaDB (RAG)   │
│  Local/S3 Storage │
└───────────────────┘
```

---

## Quick Start (Local Development)

### 1. Prerequisites

**Option A — Fedora native (no Docker)** — recommended if `docker` is not installed:

```bash
sudo ./scripts/setup_fedora.sh
```

This installs PostgreSQL, Redis, Tesseract, Poppler, Python deps, creates the `medivault` database, and runs migrations.

**Option B — Docker Compose:**

```bash
docker compose up -d postgres redis
alembic upgrade head
```

**All platforms also need:**

- Python 3.12+
- [ngrok](https://ngrok.com/download) (for cross-network access)
- Tesseract OCR (included in `setup_fedora.sh` on Fedora)

### Windows / WSL Notes

On Windows, the safest path is to use WSL or Git Bash because `scripts/start_with_tunnel.sh` is a Bash script.

- Install Python 3.12+ and ngrok.
- Create and activate the backend virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

- If you prefer WSL, activate with:

```bash
source .venv/bin/activate
```

- Start the backend and tunnel from WSL / Git Bash:

```bash
./scripts/start_with_tunnel.sh
```

- If you must run the backend from PowerShell directly, use:

```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
ngrok http 8000 --log=stdout
```

- On the remote UI machine, set the public ngrok URL with:

```env
NEXT_PUBLIC_API_BASE_URL=https://<your-tunnel>.ngrok-free.dev
```

Then restart the frontend dev server.

### 2. Setup

```bash
cd "project for group"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — set SECRET_KEY, JWT_SECRET_KEY, and GROQ_API_KEY
# IMPORTANT: APP_NAME must be quoted: APP_NAME="MediVault AI"
```

Verify services before starting:

```bash
chmod +x scripts/check_services.sh
./scripts/check_services.sh
```

### 3. Database Migration

```bash
# Start PostgreSQL & Redis (or use docker-compose)
docker compose up -d postgres redis

alembic upgrade head
```

### 4. Start with Tunnel (Recommended for WAN)

```bash
chmod +x scripts/start_with_tunnel.sh
./scripts/start_with_tunnel.sh
```

This script:
1. Starts `ngrok http 8000` targeting `127.0.0.1:8000`
2. Polls `http://127.0.0.1:4040/api/tunnels` for the public HTTPS URL
3. Writes the URL to `.tunnel_url` and prints it to stdout
4. Launches Uvicorn with `--host 0.0.0.0 --port 8000 --reload`
5. On SIGTERM, tears down both processes cleanly

### 5. Start Celery Worker (separate terminal)

```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

### 6. Docker Compose (All Services)

```bash
docker compose up --build
```

---

## Cross-Network Setup Guide

This guide enables a frontend running on a **remote device in a different city** to communicate with the backend on your local machine (`192.168.29.95`).

### Step 1: Install ngrok

```bash
# Linux (snap)
sudo snap install ngrok

# Or download from https://ngrok.com/download
```

### Step 2: Authenticate ngrok

1. Create a free account at [https://ngrok.com](https://ngrok.com)
2. Copy your authtoken from the dashboard
3. Run:

```bash
ngrok config add-authtoken YOUR_NGROK_AUTHTOKEN
```

### Step 3: Start Backend with Tunnel

```bash
./scripts/start_with_tunnel.sh
```

Copy the printed URL, e.g.:
```
PUBLIC TUNNEL URL: https://abc123.ngrok-free.app
```

### Step 4: Configure Frontend

On your **remote frontend device**, set the environment variable:

```env
NEXT_PUBLIC_API_BASE_URL=https://abc123.ngrok-free.app
```

Every API call from the frontend must include this header to bypass ngrok's browser warning interstitial:

```
ngrok-skip-browser-warning: true
```

Example frontend fetch configuration:

```typescript
// lib/apiConfig.ts
export const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL!;

export const apiHeaders = (token?: string) => ({
  "Content-Type": "application/json",
  "ngrok-skip-browser-warning": "true",
  ...(token ? { Authorization: `Bearer ${token}` } : {}),
});
```

### Step 5: Validate End-to-End Connectivity

From the remote device (or any machine with internet access):

```bash
curl -s https://YOUR-TUNNEL-URL.ngrok-free.app/api/v1/system/health \
  -H "ngrok-skip-browser-warning: true"
```

Expected response:

```json
{"status":"healthy","app_name":"MediVault AI","version":"1.0.0"}
```

### Tunnel URL Rotation

ngrok free-tier URLs rotate on every restart. Options:

1. **Manual**: Re-copy the URL from `start_with_tunnel.sh` output into frontend `.env`
2. **Admin API**: Call `GET /api/v1/system/tunnel-url` (admin JWT required) to fetch the current URL from `.tunnel_url`
3. **Persistent URLs**: Upgrade to ngrok paid plan, or use Cloudflare Tunnel (see below)

### Alternative Tunnel Options

**Cloudflare Tunnel** (zero-auth, more persistent URLs):

```bash
cloudflared tunnel --url http://localhost:8000
```

**frp** (self-hosted tunnel control):

```bash
# Configure frpc.ini pointing to your frps server
frpc -c frpc.ini
```

---

## AI Configuration (Groq)

AI chat, blood report analysis, and Whisper transcription require a Groq API key.

1. Get a free key at [https://console.groq.com](https://console.groq.com)
2. Add to `.env`:

```env
GROQ_API_KEY=your-groq-api-key-here
LLM_PROVIDER=groq
```

To switch LLM providers later:

```env
LLM_PROVIDER=openai    # requires OPENAI_API_KEY
LLM_PROVIDER=anthropic # requires ANTHROPIC_API_KEY
```

---

## API Documentation

Once running, access interactive docs at:

- **Swagger UI**: `http://localhost:8000/docs` or `https://<tunnel>/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

### Route Inventory (`/api/v1`)

| Prefix | Methods | Description |
|--------|---------|-------------|
| `/auth` | POST register, login, refresh, logout | JWT authentication |
| `/records` | POST upload, GET list/get, DELETE | Medical vault files |
| `/blood` | POST analyze, GET history | Blood report AI analysis |
| `/journal` | POST transcribe, create, GET history | Voice journal |
| `/timeline` | GET get_chronological_feed | Unified health timeline |
| `/ai` | POST chat (SSE stream) | RAG health assistant |
| `/insights` | GET symptom trends, compliance | Health analytics |
| `/medications` | CRUD | Medication tracking |
| `/doctors` | GET directory, POST book, GET list | Appointments |
| `/family` | POST manage, GET profiles | Family health hub |
| `/wearables` | POST sync, GET historical | Smartwatch telemetry |
| `/emergency-card` | GET fetch, POST generate | Emergency health card |
| `/system` | GET health, GET tunnel-url | System endpoints |

---

## CORS Configuration

CORS origins are **not** hardcoded to LAN IPs. Configure via environment:

```env
# Development — allow ngrok and any remote frontend origin
ALLOWED_ORIGINS=*

# Production — lock to deployed frontend domain
ALLOWED_ORIGINS=https://app.medivault.ai,https://www.medivault.ai
```

Settings: `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`

---

## Security

- **Passwords**: bcrypt via PassLib
- **Auth**: JWT Bearer tokens (access + refresh) with RBAC (`user`, `admin`, `doctor`)
- **Rate limiting**: Redis-backed on `/auth` routes (10/minute default)
- **File validation**: MIME allowlist + max size enforcement
- **Audit logging**: All write operations logged to `audit.log`

---

## Project Structure

```
/app
  /api/v1/          # Modular APIRouter endpoints
  /core/            # Config, security, database, deps
  /models/          # SQLAlchemy async models
  /schemas/         # Pydantic v2 validation
  /services/        # Business logic, OCR, LLM, vectors
  /tasks/           # Celery worker definitions
  main.py
/scripts/
  start_with_tunnel.sh
Dockerfile
docker-compose.yml
requirements.txt
.env.example
README.md
```

---

## Environment Variables

See [`.env.example`](.env.example) for the full list. Critical variables:

| Variable | Description |
|----------|-------------|
| `ALLOWED_ORIGINS` | CORS origins (comma-separated or `*`) |
| `DATABASE_URL` | PostgreSQL async connection string |
| `REDIS_URL` | Redis for rate limiting and Celery |
| `GROQ_API_KEY` | Groq API key for AI features |
| `JWT_SECRET_KEY` | JWT signing secret (min 32 chars) |
| `STORAGE_BACKEND` | `local` or `s3` |

---

## License

Proprietary — MediVault AI
