PROMPT — FRONTEND CONNECTED TO MEDIVAULT AI BACKEND

PROJECT: MEDIVAULT AI (Frontend)
OBJECTIVE: Build the frontend UI so it connects to an EXISTING FastAPI backend already running on the developer's local machine, exposed to the internet via an ngrok HTTPS tunnel. The frontend will run on a SEPARATE device in a DIFFERENT city/network. Do NOT hardcode localhost, 127.0.0.1, or LAN IPs (e.g. 192.168.29.95) anywhere.

================================================================================
BACKEND SYSTEM OUTLINE (already built — do not recreate)
================================================================================

Stack:
  - FastAPI (Python) on port 8000, bound to 0.0.0.0
  - PostgreSQL database (user: medivault, db: medivault)
  - Redis + Celery for background jobs
  - JWT auth (access + refresh tokens)
  - ChromaDB for RAG health memory
  - Groq API for AI chat + Whisper transcription
  - ngrok tunnel exposes backend as public HTTPS URL

API base path:  /api/v1
OpenAPI docs:   {BASE_URL}/docs
Health check:   GET {BASE_URL}/api/v1/system/health

Authentication:
  - Register:  POST /api/v1/auth/register   → { access_token, refresh_token, token_type }
  - Login:     POST /api/v1/auth/login      → { access_token, refresh_token, token_type }
  - Refresh:   POST /api/v1/auth/refresh    → { access_token, refresh_token }
  - Logout:    POST /api/v1/auth/logout       (Bearer + refresh_token body)
  - All protected routes require header: Authorization: Bearer <access_token>

Key endpoints the frontend must wire up:
  POST   /api/v1/auth/register|login|refresh|logout
  POST   /api/v1/records/upload              (multipart file + category)
  GET    /api/v1/records                     (list medical vault files)
  POST   /api/v1/blood/analyze               (multipart PDF/image)
  GET    /api/v1/blood/history
  POST   /api/v1/journal/transcribe          (multipart audio)
  POST   /api/v1/journal/create              (JSON: transcript, symptom_tags, mood_tags)
  GET    /api/v1/journal/history
  GET    /api/v1/timeline/get_chronological_feed
  POST   /api/v1/ai/chat                     (SSE streaming — use EventSource or fetch ReadableStream)
  GET    /api/v1/insights/get_symptom_trends
  GET    /api/v1/insights/get_compliance_metrics
  CRUD   /api/v1/medications
  GET    /api/v1/doctors/query_directory
  POST   /api/v1/doctors/book_appointment
  GET    /api/v1/doctors/list_appointments
  POST   /api/v1/family/manage_members
  GET    /api/v1/family/fetch_profiles
  POST   /api/v1/wearables/sync_telemetry
  GET    /api/v1/wearables/get_historical_metrics
  GET    /api/v1/emergency-card/fetch
  POST   /api/v1/emergency-card/generate_metadata
  GET    /api/v1/system/health               (public, no auth)
  GET    /api/v1/system/tunnel-url           (admin only — for URL rotation)

CORS: Backend accepts origins from ALLOWED_ORIGINS env (set to * in dev).
Response format: JSON (except /ai/chat which streams text/event-stream SSE).

================================================================================
HOW TO CONNECT THE FRONTEND (MANDATORY)
================================================================================

STEP 1 — Get the backend tunnel URL
  The backend operator runs:  ./scripts/start_with_tunnel.sh
  It prints a public URL like:  https://abc123.ngrok-free.app
  Copy that exact HTTPS URL.

STEP 2 — Set the frontend environment variable
  Create .env.local (Next.js) or equivalent:
    NEXT_PUBLIC_API_BASE_URL=https://abc123.ngrok-free.app

  NEVER use localhost or LAN IP. ONLY the ngrok HTTPS URL.

STEP 3 — Centralized API config module (REQUIRED)
  Create /lib/apiConfig.ts (or equivalent):

    export const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL!;

    export const defaultHeaders = (token?: string): HeadersInit => ({
      "Content-Type": "application/json",
      "ngrok-skip-browser-warning": "true",   // REQUIRED for ngrok free tier
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    });

    export const apiFetch = async (path: string, options: RequestInit = {}, token?: string) => {
      const res = await fetch(`${BASE_URL}${path}`, {
        ...options,
        headers: { ...defaultHeaders(token), ...options.headers },
      });
      if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
      return res.json();
    };

  Every fetch, upload, and SSE connection MUST use BASE_URL from this module.
  Zero hardcoded URL strings in components.

STEP 4 — ngrok header (CRITICAL)
  ngrok free tier shows a browser warning page for API clients.
  EVERY request must include:
    ngrok-skip-browser-warning: true

STEP 5 — Validate connectivity before building features
  Run this curl from the frontend device (or browser console):
    curl -s https://YOUR-TUNNEL.ngrok-free.app/api/v1/system/health \
      -H "ngrok-skip-browser-warning: true"

  Expected: {"status":"healthy","app_name":"MediVault AI","version":"1.0.0"}

STEP 6 — Auth token storage
  On login/register, store access_token and refresh_token securely.
  Attach access_token to all protected requests via Authorization header.
  On 401, call POST /api/v1/auth/refresh with refresh_token, retry request.

STEP 7 — SSE streaming for AI chat
  POST /api/v1/ai/chat with body: { "message": "..." }
  Response is text/event-stream. Parse lines starting with "data: ".
  Event types: { "type": "start" }, { "type": "token", "content": "..." }, { "type": "done" }

STEP 8 — File uploads
  Use FormData for:
    - /api/v1/records/upload  (file + category field)
    - /api/v1/blood/analyze     (file field)
    - /api/v1/journal/transcribe (audio field)
  Do NOT set Content-Type manually for multipart — browser sets boundary.
  Still include ngrok-skip-browser-warning and Authorization headers.

STEP 9 — Tunnel URL rotation
  ngrok free URLs change on restart. If API calls fail with connection errors:
    - Ask backend operator for new URL from start_with_tunnel.sh output
    - Update NEXT_PUBLIC_API_BASE_URL and rebuild/restart frontend
    - Or backend admin can call GET /api/v1/system/tunnel-url

================================================================================
DESIGN REQUIREMENTS (from original frontend spec)
================================================================================

Brand: "Your Personal Health Operating System"
Colors: Deep Blue #0A66FF, Teal #00C9A7, canvas #F8F9FA, dark #0D0E12
Build all 15 screens (Landing, Auth, Dashboard, Medical Vault, Blood Analyzer,
Whisper Journal, Timeline, AI Chat, Medications, Doctors, Family Hub,
Smartwatch, Health Twin, Emergency Center, Settings/Admin).

All network calls route through BASE_URL exclusively.
Include README section documenting NEXT_PUBLIC_API_BASE_URL setup.

================================================================================
WHAT THE BACKEND OPERATOR MUST HAVE RUNNING
================================================================================

On the backend machine (Fedora, LAN IP 192.168.29.95):
  1. PostgreSQL + Redis running (./scripts/setup_fedora.sh sets this up)
  2. alembic upgrade head  (database migrated)
  3. ./scripts/start_with_tunnel.sh  (ngrok + uvicorn on :8000)
  4. celery -A app.tasks.celery_app worker --loglevel=info  (background jobs)

The frontend only needs the ngrok HTTPS URL — nothing else from the LAN.
