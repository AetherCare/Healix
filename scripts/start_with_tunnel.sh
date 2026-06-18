#!/usr/bin/env bash
# MediVault AI — Start ngrok tunnel + Uvicorn with clean SIGTERM teardown.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TUNNEL_URL_FILE="${PROJECT_ROOT}/.tunnel_url"
NGROK_API="http://127.0.0.1:4040/api/tunnels"
MAX_POLL_ATTEMPTS=30
POLL_INTERVAL=1

NGROK_PID=""
UVICORN_PID=""

cleanup() {
    echo ""
    echo "[cleanup] Received shutdown signal — tearing down processes..."
    if [[ -n "${UVICORN_PID}" ]] && kill -0 "${UVICORN_PID}" 2>/dev/null; then
        kill "${UVICORN_PID}" 2>/dev/null || true
        wait "${UVICORN_PID}" 2>/dev/null || true
    fi
    if [[ -n "${NGROK_PID}" ]] && kill -0 "${NGROK_PID}" 2>/dev/null; then
        kill "${NGROK_PID}" 2>/dev/null || true
        wait "${NGROK_PID}" 2>/dev/null || true
    fi
    echo "[cleanup] All processes stopped."
    exit 0
}

trap cleanup SIGTERM SIGINT EXIT

cd "${PROJECT_ROOT}"

# Note: .env is loaded by Pydantic in app/core/config.py — do NOT bash-source it here
# (unquoted values like APP_NAME=MediVault AI break shell parsing).

echo "=== MediVault AI — Tunnel + Server Startup ==="
echo "Project root: ${PROJECT_ROOT}"

# Verify ngrok is installed
if ! command -v ngrok &>/dev/null; then
    echo "ERROR: ngrok is not installed. See README Cross-Network Setup Guide."
    exit 1
fi

# Start ngrok tunnel targeting local Uvicorn port (enable pooling to allow multiple endpoints)
echo "[ngrok] Starting tunnel: ngrok http 8000 -> 127.0.0.1:8000"
ngrok http 8000 --pooling-enabled --log=stdout &
NGROK_PID=$!
echo "[ngrok] PID: ${NGROK_PID}"

# Poll ngrok local API for public HTTPS URL
echo "[ngrok] Polling ${NGROK_API} for public URL..."
PUBLIC_URL=""
for ((i = 1; i <= MAX_POLL_ATTEMPTS; i++)); do
    sleep "${POLL_INTERVAL}"
    RESPONSE=$(curl -s "${NGROK_API}" 2>/dev/null || echo "")
    if [[ -n "${RESPONSE}" ]]; then
        PUBLIC_URL=$(echo "${RESPONSE}" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for t in data.get('tunnels', []):
        if t.get('proto') == 'https':
            print(t['public_url'])
            break
except Exception:
    pass
" 2>/dev/null || echo "")
        if [[ -n "${PUBLIC_URL}" ]]; then
            break
        fi
    fi
    echo "[ngrok] Attempt ${i}/${MAX_POLL_ATTEMPTS} — waiting for tunnel..."
done

if [[ -z "${PUBLIC_URL}" ]]; then
    echo "ERROR: Could not retrieve ngrok public URL after ${MAX_POLL_ATTEMPTS} attempts."
    cleanup
fi

# Write tunnel URL to file and stdout
echo "${PUBLIC_URL}" > "${TUNNEL_URL_FILE}"
echo ""
echo "=============================================="
echo "  PUBLIC TUNNEL URL: ${PUBLIC_URL}"
echo "  Written to: ${TUNNEL_URL_FILE}"
echo "=============================================="
echo ""
echo "Set this in your frontend .env:"
echo "  NEXT_PUBLIC_API_BASE_URL=${PUBLIC_URL}"
echo ""

# Launch Uvicorn bound to all interfaces for tunnel reachability
echo "[uvicorn] Starting server on 0.0.0.0:8000"
if [[ -x "${PROJECT_ROOT}/.venv/bin/uvicorn" ]]; then
    "${PROJECT_ROOT}/.venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --reload &
elif command -v uvicorn &>/dev/null; then
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
elif command -v python3 &>/dev/null; then
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
else
    echo "ERROR: uvicorn is not installed or not on PATH. Activate your virtualenv or install uvicorn."
    cleanup
fi
UVICORN_PID=$!
echo "[uvicorn] PID: ${UVICORN_PID}"

# Wait for Uvicorn (foreground behavior)
wait "${UVICORN_PID}"
