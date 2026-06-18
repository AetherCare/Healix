#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_ROOT="${PROJECT_ROOT}/UI/MediVault AI UI_UX Design"
TUNNEL_URL_FILE="${PROJECT_ROOT}/.frontend_tunnel_url"
NGROK_API="http://127.0.0.1:4040/api/tunnels"
MAX_POLL_ATTEMPTS=30
POLL_INTERVAL=1

NGROK_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  echo "[cleanup] Stopping frontend tunnel..."
  if [[ -n "${FRONTEND_PID}" ]] && kill -0 "${FRONTEND_PID}" 2>/dev/null; then
    kill "${FRONTEND_PID}" 2>/dev/null || true
    wait "${FRONTEND_PID}" 2>/dev/null || true
  fi
  if [[ -n "${NGROK_PID}" ]] && kill -0 "${NGROK_PID}" 2>/dev/null; then
    kill "${NGROK_PID}" 2>/dev/null || true
    wait "${NGROK_PID}" 2>/dev/null || true
  fi
  echo "[cleanup] Tunnel stopped."
  exit 0
}

trap cleanup SIGINT SIGTERM EXIT

cd "${PROJECT_ROOT}"

echo "=== MediVault AI — Frontend Tunnel Startup ==="

echo "[ngrok] Starting tunnel: ngrok http 5173 -> 127.0.0.1:5173"
# Start the frontend dev server (in background) if available
if [[ -d "${FRONTEND_ROOT}" ]]; then
  echo "[frontend] Starting dev server in ${FRONTEND_ROOT}"
  (cd "${FRONTEND_ROOT}" && npm run dev -- --host) &
  FRONTEND_PID=$!
  sleep 1
fi

# Start ngrok with pooling enabled so it can coexist with other tunnels
ngrok http 5173 --pooling-enabled --log=stdout &
NGROK_PID=$!
echo "[ngrok] PID: ${NGROK_PID}"

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

echo "${PUBLIC_URL}" > "${TUNNEL_URL_FILE}"
echo ""
echo "=============================================="
echo "  FRONTEND PUBLIC URL: ${PUBLIC_URL}"
echo "  Written to: ${TUNNEL_URL_FILE}"
echo "=============================================="
echo ""
echo "Open the UI from any browser using the above public URL."
echo "Press CTRL+C to stop the tunnel."

echo "[ngrok] Tunnel is active. Waiting until termination signal..."
wait "${NGROK_PID}"
